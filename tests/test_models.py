import pytest
from pydantic import ValidationError

from backend.app.models import DNSRecord, RecordCreate


def test_dns_record_accepts_a_record():
    record = DNSRecord(
        id="rec-001",
        type="A",
        name="@",
        data="3.0.3.205",
        ttl=600,
        status="active",
    )

    assert record.type == "A"
    assert record.ttl == 600


def test_record_create_rejects_empty_dns_fields():
    with pytest.raises(ValidationError):
        RecordCreate(type="", name="", data="", ttl=0)
