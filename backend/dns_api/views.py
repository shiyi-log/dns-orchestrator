from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from backend.app.godaddy_client import GoDaddyAPIError
from .serializers import RecordSerializer
from .services import service


def _record_payload(record):
    return record.model_dump()


def _error_response(exc: GoDaddyAPIError):
    return Response(
        {"detail": exc.message, "status_code": exc.status_code, "retryable": exc.retryable},
        status=exc.status_code,
    )


@api_view(["GET"])
def health(request):
    settings = service.settings
    ready = settings.godaddy_demo_mode or bool(settings.godaddy_pat)
    return Response({"status": "ok" if ready else "degraded", "demo_mode": settings.godaddy_demo_mode, "ready": ready})


@api_view(["GET"])
def domains(request):
    try:
        return Response([item.model_dump() for item in service.list_domains()])
    except GoDaddyAPIError as exc:
        return _error_response(exc)


@api_view(["GET", "POST"])
def records(request, domain: str):
    if request.method == "POST":
        serializer = RecordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            record = service.create_record(domain, serializer.to_record_create())
            return Response(_record_payload(record), status=status.HTTP_201_CREATED)
        except GoDaddyAPIError as exc:
            return _error_response(exc)
    try:
        return Response([_record_payload(item) for item in service.list_records(domain)])
    except GoDaddyAPIError as exc:
        return _error_response(exc)


@api_view(["PUT", "DELETE"])
def record_detail(request, domain: str, record_id: str):
    if request.method == "PUT":
        serializer = RecordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            record = service.update_record(domain, record_id, serializer.to_record_update())
            return Response(_record_payload(record))
        except GoDaddyAPIError as exc:
            return _error_response(exc)
    try:
        service.delete_record(domain, record_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
    except GoDaddyAPIError as exc:
        return _error_response(exc)


@api_view(["GET"])
def activity(request):
    return Response([entry.model_dump() for entry in service.activity()])
