from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .config import Settings
from .demo_data import demo_activity, demo_domains, demo_records
from .godaddy_client import GoDaddyAPIError, GoDaddyClient
from .models import ActivityEntry, DNSRecord, DomainSummary, RecordCreate, RecordUpdate


class DNSService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = None if settings.godaddy_demo_mode else GoDaddyClient(settings)
        self._records = {domain.domain: demo_records(domain.domain) for domain in demo_domains()}
        self._activities: list[ActivityEntry] = [
            ActivityEntry(**entry) for entry in demo_activity()
        ]

    def list_domains(self) -> list[DomainSummary]:
        if self.settings.godaddy_demo_mode:
            domains = demo_domains()
            for domain in domains:
                domain.record_count = len(self._records.get(domain.domain, []))
            return domains
        return self.client.list_domains()

    def list_records(self, domain: str) -> list[DNSRecord]:
        if self.settings.godaddy_demo_mode:
            return list(self._records.get(domain, []))
        return self.client.list_records(domain)

    def create_record(self, domain: str, record: RecordCreate) -> DNSRecord:
        created = (
            self._demo_create(domain, record)
            if self.settings.godaddy_demo_mode
            else self.client.create_record(domain, record)
        )
        self._record_activity("create", domain, created, "新增")
        return created

    def update_record(self, domain: str, record_id: str, record: RecordUpdate) -> DNSRecord:
        updated = (
            self._demo_update(domain, record_id, record)
            if self.settings.godaddy_demo_mode
            else self.client.update_record(domain, record_id, record)
        )
        self._record_activity("update", domain, updated, "更新")
        return updated

    def delete_record(self, domain: str, record_id: str) -> None:
        if self.settings.godaddy_demo_mode:
            records = self._records.get(domain, [])
            self._records[domain] = [record for record in records if record.id != record_id]
        else:
            self.client.delete_record(domain, record_id)
        self._activities.insert(
            0,
            ActivityEntry(
                id=str(uuid4()),
                action="delete",
                domain=domain,
                record_id=record_id,
                summary=f"删除记录 {record_id}",
                created_at=datetime.now(timezone.utc).isoformat(),
            ),
        )

    def activity(self) -> list[ActivityEntry]:
        return list(self._activities)

    def _demo_create(self, domain: str, record: RecordCreate) -> DNSRecord:
        created = DNSRecord(id=f"demo-{uuid4().hex[:8]}", **record.model_dump())
        self._records.setdefault(domain, []).insert(0, created)
        return created

    def _demo_update(self, domain: str, record_id: str, record: RecordUpdate) -> DNSRecord:
        records = self._records.setdefault(domain, [])
        for index, current in enumerate(records):
            if current.id == record_id:
                updated = DNSRecord(id=record_id, **record.model_dump())
                records[index] = updated
                return updated
        raise GoDaddyAPIError(404, f"Record {record_id} was not found")

    def _record_activity(self, action: str, domain: str, record: DNSRecord, label: str) -> None:
        self._activities.insert(
            0,
            ActivityEntry(
                id=str(uuid4()),
                action=action,
                domain=domain,
                record_id=record.id,
                summary=f"{label} {record.type} {record.name} → {record.data}",
                created_at=datetime.now(timezone.utc).isoformat(),
            ),
        )
