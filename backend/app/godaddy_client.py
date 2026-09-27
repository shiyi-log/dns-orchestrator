from __future__ import annotations

import time
from typing import Any, Callable, Optional
from urllib.parse import quote

import httpx

from .config import Settings
from .models import DNSRecord, DomainSummary, RecordCreate, RecordUpdate


RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class GoDaddyAPIError(RuntimeError):
    def __init__(self, status_code: int, message: str, retryable: bool = False):
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.retryable = retryable


class GoDaddyClient:
    def __init__(
        self,
        settings: Settings,
        http_client: Optional[httpx.Client] = None,
        sleeper: Callable[[float], None] = time.sleep,
    ):
        if not settings.godaddy_demo_mode and not settings.godaddy_pat:
            raise ValueError("GODADDY_PAT is required when GODADDY_DEMO_MODE=false")
        self.settings = settings
        self.http = http_client or httpx.Client(timeout=settings.request_timeout_seconds)
        self.sleeper = sleeper

    def list_domains(self) -> list[DomainSummary]:
        payload = self._request("GET", "/v1/domains")
        items = payload if isinstance(payload, list) else payload.get("items", [])
        return [
            DomainSummary(
                domain=item.get("domain", ""),
                status=item.get("status", "active"),
                expires_at=item.get("expiresAt") or item.get("expirationDate"),
                auto_renew=item.get("renewAuto") if "renewAuto" in item else item.get("autoRenew"),
            )
            for item in items
            if item.get("domain")
        ]

    def list_records(self, domain: str) -> list[DNSRecord]:
        zone = quote(domain, safe="")
        payload = self._request(
            "GET",
            f"/v3/domains/zones/{zone}/dns-records",
            params={"page": 1, "pageSize": 100},
        )
        items = payload if isinstance(payload, list) else payload.get("items", [])
        return [self._normalize_record(item) for item in items]

    def create_record(self, domain: str, record: RecordCreate) -> DNSRecord:
        zone = quote(domain, safe="")
        response = self._request(
            "POST",
            f"/v3/domains/zones/{zone}/dns-records",
            json=self._write_payload(record),
            retry_read=False,
            return_response=True,
        )
        record_id = self._record_id_from_response(response)
        return DNSRecord(id=record_id, **record.model_dump())

    def update_record(self, domain: str, record_id: str, record: RecordUpdate) -> DNSRecord:
        zone = quote(domain, safe="")
        encoded_id = quote(record_id, safe="")
        self._request(
            "PUT",
            f"/v3/domains/zones/{zone}/dns-records/{encoded_id}",
            json=self._write_payload(record),
            retry_read=False,
        )
        return DNSRecord(id=record_id, **record.model_dump())

    def delete_record(self, domain: str, record_id: str) -> None:
        zone = quote(domain, safe="")
        encoded_id = quote(record_id, safe="")
        self._request(
            "DELETE",
            f"/v3/domains/zones/{zone}/dns-records/{encoded_id}",
            retry_read=False,
        )

    def _write_payload(self, record: RecordCreate) -> dict[str, Any]:
        return {key: value for key, value in record.model_dump().items() if value is not None}

    def _record_id_from_response(self, response: httpx.Response) -> str:
        location = response.headers.get("location", "").rstrip("/")
        if location:
            return location.rsplit("/", 1)[-1]
        try:
            payload = response.json()
        except ValueError:
            payload = {}
        if isinstance(payload, dict) and (payload.get("recordId") or payload.get("id")):
            return str(payload.get("recordId") or payload.get("id"))
        return "pending"

    def _normalize_record(self, item: dict[str, Any]) -> DNSRecord:
        known = {
            "id": item.get("id") or item.get("recordId") or "unknown",
            "type": item.get("type"),
            "name": item.get("name"),
            "data": item.get("data"),
            "ttl": item.get("ttl", 600),
            "priority": item.get("priority"),
            "weight": item.get("weight"),
            "port": item.get("port"),
            "service": item.get("service"),
            "protocol": item.get("protocol"),
            "flags": item.get("flags"),
            "tag": item.get("tag"),
        }
        return DNSRecord(**known)

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[dict[str, Any]] = None,
        json: Optional[dict[str, Any]] = None,
        retry_read: bool = True,
        return_response: bool = False,
    ) -> Any:
        headers = {"Accept": "application/json"}
        if self.settings.godaddy_pat:
            headers["Authorization"] = f"Bearer {self.settings.godaddy_pat}"
        if json is not None:
            headers["Content-Type"] = "application/json"

        attempts = 2 if method == "GET" and retry_read else 1
        url = f"{self.settings.godaddy_api_base}{path}"
        for attempt in range(attempts):
            try:
                response = self.http.request(
                    method,
                    url,
                    headers=headers,
                    params=params,
                    json=json,
                )
            except httpx.HTTPError as exc:
                if attempt + 1 < attempts:
                    self.sleeper(0.05)
                    continue
                raise GoDaddyAPIError(503, str(exc), retryable=True) from exc

            if response.status_code in RETRYABLE_STATUS_CODES and attempt + 1 < attempts:
                self.sleeper(0.05)
                continue
            if response.is_error:
                raise GoDaddyAPIError(
                    response.status_code,
                    self._error_message(response),
                    retryable=response.status_code in RETRYABLE_STATUS_CODES,
                )
            if return_response:
                return response
            if response.status_code == 204 or not response.content:
                return {}
            return response.json()
        raise GoDaddyAPIError(503, "GoDaddy request failed", retryable=True)

    @staticmethod
    def _error_message(response: httpx.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            return response.text or f"GoDaddy returned HTTP {response.status_code}"
        if isinstance(payload, dict):
            return str(payload.get("message") or payload.get("error") or payload)
        return str(payload)
