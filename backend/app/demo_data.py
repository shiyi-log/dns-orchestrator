from __future__ import annotations

from datetime import datetime, timezone

from .models import DNSRecord, DomainSummary


def demo_domains() -> list[DomainSummary]:
    return [
        DomainSummary(
            domain="example.com",
            status="active",
            expires_at="2027-09-27T00:00:00Z",
            auto_renew=True,
            record_count=5,
        ),
        DomainSummary(domain="api-service.com", status="active", auto_renew=True, record_count=3),
        DomainSummary(domain="shiyi.dev", status="active", auto_renew=False, record_count=4),
    ]


def demo_records(domain: str) -> list[DNSRecord]:
    if domain != "example.com":
        return []
    return [
        DNSRecord(id="rec-001", type="A", name="@", data="3.0.3.205", ttl=600),
        DNSRecord(id="rec-002", type="CNAME", name="www", data="example.com", ttl=600),
        DNSRecord(
            id="rec-003",
            type="TXT",
            name="@",
            data="v=spf1 include:_spf.example.net ~all",
            ttl=3600,
        ),
        DNSRecord(
            id="rec-004",
            type="MX",
            name="@",
            data="mail.example.com",
            ttl=3600,
            priority=10,
            status="pending",
        ),
        DNSRecord(
            id="rec-005",
            type="AAAA",
            name="api",
            data="2001:db8:85a3::8a2e:370:7334",
            ttl=600,
        ),
    ]


def demo_activity() -> list[dict[str, str]]:
    return [
        {
            "id": "activity-001",
            "action": "update",
            "domain": "example.com",
            "record_id": "rec-001",
            "summary": "更新 A @ → 3.0.3.205",
            "status": "success",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    ]
