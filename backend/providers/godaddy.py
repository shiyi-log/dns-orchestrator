from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any, Optional

from backend.app.config import Settings
from backend.app.demo_data import demo_domains, demo_records
from backend.app.godaddy_client import GoDaddyAPIError, GoDaddyClient
from backend.app.models import DNSRecord as LegacyDNSRecord
from backend.app.models import RecordCreate, RecordUpdate

from .base import (
    DNSProviderAdapter,
    DNSRecord,
    DNSRecordDraft,
    ProviderCapabilities,
    ProviderStatus,
    Zone,
)


class GoDaddyAdapter(DNSProviderAdapter):
    provider = "godaddy"

    def __init__(
        self,
        account: Any,
        credential_values: dict[str, str],
        client: Optional[GoDaddyClient] = None,
        demo_mode: bool = False,
    ):
        self.account = account
        self.credential_values = credential_values
        self.demo_mode = demo_mode
        self._demo_records = {
            domain.domain: demo_records(domain.domain)
            for domain in demo_domains()
        }
        self.client = client or GoDaddyClient(
            Settings(
                godaddy_pat=credential_values["token"],
                godaddy_demo_mode=False,
                godaddy_api_base=account.api_base or "https://api.godaddy.com",
            )
        )

    def verify_connection(self) -> ProviderStatus:
        try:
            zones = self.list_zones()
            return ProviderStatus(provider=self.provider, status="active", zone_count=len(zones))
        except Exception as exc:
            return ProviderStatus(provider=self.provider, status="error", error=str(exc))

    def list_zones(self) -> list[Zone]:
        if self.demo_mode:
            return [
                Zone(
                    id=domain.domain,
                    name=domain.domain,
                    status=domain.status,
                    record_count=len(self._demo_records.get(domain.domain, [])),
                )
                for domain in demo_domains()
            ]
        domains = [
            domain
            for domain in self.client.list_domains()
            if domain.status.upper() in {"ACTIVE", "PENDING"}
        ]

        def probe(domain: Any):
            try:
                return domain, len(self.client.list_records(domain.domain))
            except GoDaddyAPIError:
                return domain, None

        zones = []
        # Zone discovery is read-only. Probe a small bounded batch in parallel so
        # one unavailable domain cannot make the dashboard look empty for minutes.
        with ThreadPoolExecutor(max_workers=4) as executor:
            probes = executor.map(probe, domains)
            for domain, record_count in probes:
                if record_count is None:
                    continue
                zones.append(
                    Zone(
                        id=domain.domain,
                        name=domain.domain,
                        status=domain.status,
                        record_count=record_count,
                    )
                )
        return zones

    def list_records(self, zone: Zone) -> list[DNSRecord]:
        if self.demo_mode:
            return [self._normalize_record(zone, record) for record in self._demo_records.get(zone.name, [])]
        return [self._normalize_record(zone, record) for record in self.client.list_records(zone.name)]

    def create_record(self, zone: Zone, draft: DNSRecordDraft) -> DNSRecord:
        if self.demo_mode:
            record = LegacyDNSRecord(
                id=f"demo-account-{len(self._demo_records.get(zone.name, [])) + 1}",
                type=draft.type,
                name=draft.name,
                data=draft.content,
                ttl=draft.ttl,
                priority=draft.priority,
            )
            self._demo_records.setdefault(zone.name, []).insert(0, record)
            return self._normalize_record(zone, record)
        record = self.client.create_record(
            zone.name,
            RecordCreate(
                type=draft.type,
                name=draft.name,
                data=draft.content,
                ttl=draft.ttl,
                priority=draft.priority,
            ),
        )
        return self._normalize_record(zone, record)

    def update_record(self, zone: Zone, record_id: str, draft: DNSRecordDraft) -> DNSRecord:
        if self.demo_mode:
            for index, current in enumerate(self._demo_records.get(zone.name, [])):
                if current.id == record_id:
                    record = LegacyDNSRecord(
                        id=record_id,
                        type=draft.type,
                        name=draft.name,
                        data=draft.content,
                        ttl=draft.ttl,
                        priority=draft.priority,
                    )
                    self._demo_records[zone.name][index] = record
                    return self._normalize_record(zone, record)
            raise ValueError(f"Record {record_id} was not found")
        record = self.client.update_record(
            zone.name,
            record_id,
            RecordUpdate(
                type=draft.type,
                name=draft.name,
                data=draft.content,
                ttl=draft.ttl,
                priority=draft.priority,
            ),
        )
        return self._normalize_record(zone, record)

    def delete_record(self, zone: Zone, record_id: str) -> None:
        if self.demo_mode:
            self._demo_records[zone.name] = [
                record for record in self._demo_records.get(zone.name, [])
                if record.id != record_id
            ]
            return
        self.client.delete_record(zone.name, record_id)

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            provider=self.provider,
            implemented=True,
            record_types=["A", "AAAA", "CNAME", "MX", "TXT", "NS", "SRV", "CAA"],
            fields=["name", "content", "ttl", "priority"],
        )

    @staticmethod
    def _normalize_record(zone: Zone, record: Any) -> DNSRecord:
        return DNSRecord(
            id=record.id,
            zone=zone.name,
            type=record.type,
            name=record.name,
            content=record.data,
            ttl=record.ttl,
            priority=record.priority,
            status=record.status,
        )
