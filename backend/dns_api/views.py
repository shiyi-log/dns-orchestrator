from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from backend.app.godaddy_client import GoDaddyAPIError
from backend.providers.factory import UnsupportedProviderError
from .account_serializers import AccountCreateSerializer, AccountRecordSerializer, AccountSummarySerializer, AccountUpdateSerializer
from .account_service import PROVIDER_METADATA
from . import services
from .serializers import RecordSerializer


def _record_payload(record):
    return record.model_dump()


def _error_response(exc: GoDaddyAPIError):
    return Response(
        {"detail": exc.message, "status_code": exc.status_code, "retryable": exc.retryable},
        status=exc.status_code,
    )


@api_view(["GET"])
def health(request):
    settings = services.service.settings
    ready = settings.godaddy_demo_mode or bool(settings.godaddy_pat)
    return Response({"status": "ok" if ready else "degraded", "demo_mode": settings.godaddy_demo_mode, "ready": ready})


@api_view(["GET"])
def domains(request):
    try:
        default_account = services.account_service.default_account()
        if default_account is not None and default_account.provider == "godaddy":
            zones = services.account_service.list_zones(str(default_account.id))
            return Response([
                {
                    "domain": zone.name,
                    "status": zone.status,
                    "record_count": zone.record_count,
                }
                for zone in zones
            ])
        return Response([item.model_dump() for item in services.service.list_domains()])
    except GoDaddyAPIError as exc:
        return _error_response(exc)


@api_view(["GET", "POST"])
def records(request, domain: str):
    default_account = services.account_service.default_account()
    if default_account is not None and default_account.provider == "godaddy":
        serializer = None
        try:
            if request.method == "POST":
                serializer = RecordSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                legacy = serializer.to_record_create()
                from backend.providers.base import DNSRecordDraft

                record = services.account_service.create_record(
                    str(default_account.id),
                    domain,
                    DNSRecordDraft(
                        type=legacy.type,
                        name=legacy.name,
                        content=legacy.data,
                        ttl=legacy.ttl,
                        priority=legacy.priority,
                    ),
                )
                return Response(
                    {
                        "id": record.id,
                        "type": record.type,
                        "name": record.name,
                        "data": record.content,
                        "ttl": record.ttl,
                        "priority": record.priority,
                        "status": record.status,
                    },
                    status=status.HTTP_201_CREATED,
                )
            return Response([
                {
                    "id": record.id,
                    "type": record.type,
                    "name": record.name,
                    "data": record.content,
                    "ttl": record.ttl,
                    "priority": record.priority,
                    "status": record.status,
                }
                for record in services.account_service.list_records(str(default_account.id), domain)
            ])
        except Exception as exc:
            if serializer is not None and hasattr(exc, "detail"):
                raise
            return _account_error_response(exc)
    if request.method == "POST":
        serializer = RecordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            record = services.service.create_record(domain, serializer.to_record_create())
            return Response(_record_payload(record), status=status.HTTP_201_CREATED)
        except GoDaddyAPIError as exc:
            return _error_response(exc)
    try:
        return Response([_record_payload(item) for item in services.service.list_records(domain)])
    except GoDaddyAPIError as exc:
        return _error_response(exc)


@api_view(["PUT", "DELETE"])
def record_detail(request, domain: str, record_id: str):
    default_account = services.account_service.default_account()
    if default_account is not None and default_account.provider == "godaddy":
        try:
            if request.method == "DELETE":
                services.account_service.delete_record(str(default_account.id), domain, record_id)
                return Response(status=status.HTTP_204_NO_CONTENT)
            serializer = RecordSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            legacy = serializer.to_record_update()
            from backend.providers.base import DNSRecordDraft

            record = services.account_service.update_record(
                str(default_account.id),
                domain,
                record_id,
                DNSRecordDraft(
                    type=legacy.type,
                    name=legacy.name,
                    content=legacy.data,
                    ttl=legacy.ttl,
                    priority=legacy.priority,
                ),
            )
            return Response({
                "id": record.id,
                "type": record.type,
                "name": record.name,
                "data": record.content,
                "ttl": record.ttl,
                "priority": record.priority,
                "status": record.status,
            })
        except Exception as exc:
            return _account_error_response(exc)
    if request.method == "PUT":
        serializer = RecordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            record = services.service.update_record(domain, record_id, serializer.to_record_update())
            return Response(_record_payload(record))
        except GoDaddyAPIError as exc:
            return _error_response(exc)
    try:
        services.service.delete_record(domain, record_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
    except GoDaddyAPIError as exc:
        return _error_response(exc)


@api_view(["GET"])
def activity(request):
    if services.account_service.activity():
        return Response([entry.model_dump() for entry in services.account_service.activity()])
    return Response([entry.model_dump() for entry in services.service.activity()])


def _account_error_response(exc: Exception):
    if isinstance(exc, GoDaddyAPIError):
        return Response(
            {"detail": exc.message, "status_code": exc.status_code, "retryable": exc.retryable},
            status=exc.status_code,
        )
    if isinstance(exc, UnsupportedProviderError):
        return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
    if isinstance(exc, ValueError):
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"detail": "account operation failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _account_summary_response(summary):
    return Response(AccountSummarySerializer(summary.model_dump()).data)


@api_view(["GET"])
def providers(request):
    return Response(PROVIDER_METADATA)


@api_view(["GET", "POST"])
def accounts(request):
    if request.method == "GET":
        return Response(AccountSummarySerializer(
            [item.model_dump() for item in services.account_service.list_accounts()],
            many=True,
        ).data)
    serializer = AccountCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        summary = services.account_service.create_account(
            provider=serializer.validated_data["provider"],
            display_name=serializer.validated_data["display_name"],
            credential=serializer.to_credential(),
            api_base=serializer.validated_data.get("api_base"),
        )
        response = _account_summary_response(summary)
        response.status_code = status.HTTP_201_CREATED
        return response
    except Exception as exc:
        response = _account_error_response(exc)
        return response


@api_view(["PATCH", "DELETE"])
def account_detail(request, account_id: str):
    try:
        if request.method == "DELETE":
            services.account_service.delete_account(account_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = AccountUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        summary = services.account_service.update_account(
            account_id,
            display_name=serializer.validated_data.get("display_name"),
            is_enabled=serializer.validated_data.get("is_enabled"),
            credential=serializer.credential_for(
                services.account_service._get_account(account_id).provider
            ),
        )
        return _account_summary_response(summary)
    except Exception as exc:
        return _account_error_response(exc)


@api_view(["POST"])
def verify_account(request, account_id: str):
    try:
        return _account_summary_response(services.account_service.verify(account_id))
    except Exception as exc:
        return _account_error_response(exc)


@api_view(["POST"])
def set_default_account(request, account_id: str):
    try:
        return _account_summary_response(services.account_service.set_default(account_id))
    except Exception as exc:
        return _account_error_response(exc)


def _zone_payload(zone):
    return zone.model_dump()


@api_view(["GET"])
def account_zones(request, account_id: str):
    try:
        return Response([_zone_payload(zone) for zone in services.account_service.list_zones(account_id)])
    except Exception as exc:
        return _account_error_response(exc)


@api_view(["GET", "POST"])
def account_records(request, account_id: str, zone: str):
    try:
        if request.method == "GET":
            return Response([
                record.model_dump()
                for record in services.account_service.list_records(account_id, zone)
            ])
        serializer = AccountRecordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        record = services.account_service.create_record(account_id, zone, serializer.to_draft())
        return Response(record.model_dump(), status=status.HTTP_201_CREATED)
    except Exception as exc:
        return _account_error_response(exc)


@api_view(["PUT", "DELETE"])
def account_record_detail(request, account_id: str, zone: str, record_id: str):
    try:
        if request.method == "DELETE":
            services.account_service.delete_record(account_id, zone, record_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = AccountRecordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        record = services.account_service.update_record(account_id, zone, record_id, serializer.to_draft())
        return Response(record.model_dump())
    except Exception as exc:
        return _account_error_response(exc)
