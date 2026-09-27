import httpx
import pytest

from backend.app.config import Settings
from backend.app.godaddy_client import GoDaddyAPIError, GoDaddyClient
from backend.app.models import RecordCreate


def test_client_sends_bearer_header_and_normalizes_records():
    observed = {}

    def handler(request: httpx.Request) -> httpx.Response:
        observed["path"] = request.url.path
        observed["authorization"] = request.headers["authorization"]
        return httpx.Response(
            200,
            json=[{"recordId": "r1", "type": "A", "name": "@", "data": "1.2.3.4", "ttl": 600}],
        )

    transport = httpx.MockTransport(handler)
    client = GoDaddyClient(
        Settings(godaddy_pat="pat-test", godaddy_demo_mode=False),
        http_client=httpx.Client(transport=transport),
    )

    records = client.list_records("example.com")

    assert observed == {
        "path": "/v3/domains/zones/example.com/dns-records",
        "authorization": "Bearer pat-test",
    }
    assert records[0].id == "r1"
    assert records[0].data == "1.2.3.4"


def test_client_retries_retryable_read_once():
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] == 1:
            return httpx.Response(503, json={"message": "temporary"})
        return httpx.Response(200, json=[])

    client = GoDaddyClient(
        Settings(godaddy_pat="pat-test", godaddy_demo_mode=False),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    assert client.list_records("example.com") == []
    assert calls["count"] == 2


def test_client_does_not_retry_write():
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        return httpx.Response(503, json={"message": "temporary"})

    client = GoDaddyClient(
        Settings(godaddy_pat="pat-test", godaddy_demo_mode=False),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(GoDaddyAPIError):
        client.create_record(
            "example.com",
            RecordCreate(type="A", name="api", data="1.2.3.4", ttl=600),
        )

    assert calls["count"] == 1


def test_client_ignores_provider_managed_soa_record():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json=[
                {"recordId": "soa", "type": "SOA", "name": "@", "data": "", "ttl": 3600},
                {"recordId": "a1", "type": "A", "name": "@", "data": "192.0.2.1", "ttl": 600},
            ],
        )
    )
    client = GoDaddyClient(
        Settings(godaddy_pat="pat-test", godaddy_demo_mode=False),
        http_client=httpx.Client(transport=transport),
    )

    records = client.list_records("example.com")

    assert [record.id for record in records] == ["a1"]
