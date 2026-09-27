from types import SimpleNamespace

from backend.app.models import DNSRecord as LegacyDNSRecord
from backend.app.models import DomainSummary, RecordCreate
from backend.providers.godaddy import GoDaddyAdapter


class FakeGoDaddyClient:
    def list_domains(self):
        return [DomainSummary(domain="example.com", record_count=1)]

    def list_records(self, domain):
        return [
            LegacyDNSRecord(
                id="record-1",
                type="A",
                name="@",
                data="3.0.3.205",
                ttl=600,
            )
        ]

    def create_record(self, domain, record):
        return LegacyDNSRecord(id="record-2", **record.model_dump())

    def update_record(self, domain, record_id, record):
        return LegacyDNSRecord(id=record_id, **record.model_dump())

    def delete_record(self, domain, record_id):
        return None


def test_godaddy_adapter_normalizes_zones_and_records():
    adapter = GoDaddyAdapter(
        account=SimpleNamespace(api_base="https://api.godaddy.com"),
        credential_values={"token": "pat-test"},
        client=FakeGoDaddyClient(),
    )

    zones = adapter.list_zones()
    records = adapter.list_records(zones[0])

    assert zones[0].name == "example.com"
    assert records[0].content == "3.0.3.205"
    assert records[0].zone == "example.com"


def test_godaddy_adapter_exposes_supported_capabilities():
    adapter = GoDaddyAdapter(
        account=SimpleNamespace(api_base="https://api.godaddy.com"),
        credential_values={"token": "pat-test"},
        client=FakeGoDaddyClient(),
    )

    capabilities = adapter.capabilities()

    assert capabilities.provider == "godaddy"
    assert "A" in capabilities.record_types
