import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings")

import django

django.setup()

import pytest
from rest_framework.test import APIClient

from backend.app.config import Settings
from backend.dns_api import services as services_module


pytestmark = pytest.mark.django_db


def account_client():
    services_module.configure_account_service(Settings(godaddy_demo_mode=True))
    return APIClient()


def create_account(client, name):
    response = client.post(
        "/api/accounts",
        {
            "provider": "godaddy",
            "display_name": name,
            "credential": {"token": f"pat-{name}"},
        },
        format="json",
    )
    assert response.status_code == 201
    return response.json()


def test_provider_metadata_marks_future_adapters_unsupported():
    client = account_client()

    response = client.get("/api/providers")

    assert response.status_code == 200
    providers = {item["id"]: item for item in response.json()}
    assert providers["godaddy"]["implemented"] is True
    assert providers["cloudflare"]["implemented"] is False


def test_account_response_redacts_credentials_and_verification_updates_status():
    client = account_client()
    account = create_account(client, "生产 GoDaddy")

    assert "credential" not in account
    assert "credential_ciphertext" not in account
    verified = client.post(f"/api/accounts/{account['id']}/verify")

    assert verified.status_code == 200
    assert verified.json()["status"] == "active"
    assert verified.json()["zone_count"] >= 1


def test_default_switch_and_account_scoped_records_are_isolated():
    client = account_client()
    first = create_account(client, "账号一")
    second = create_account(client, "账号二")

    default_response = client.post(f"/api/accounts/{second['id']}/set-default")
    created = client.post(
        f"/api/accounts/{first['id']}/zones/example.com/records",
        {"type": "A", "name": "isolated", "content": "192.0.2.44", "ttl": 600},
        format="json",
    )
    first_records = client.get(f"/api/accounts/{first['id']}/zones/example.com/records")
    second_records = client.get(f"/api/accounts/{second['id']}/zones/example.com/records")
    legacy_domains = client.get("/api/domains")

    assert default_response.status_code == 200
    assert created.status_code == 201
    assert any(item["name"] == "isolated" for item in first_records.json())
    assert all(item["name"] != "isolated" for item in second_records.json())
    assert legacy_domains.status_code == 200


def test_unsupported_provider_account_is_rejected():
    client = account_client()

    response = client.post(
        "/api/accounts",
        {
            "provider": "cloudflare",
            "display_name": "Cloudflare future",
            "credential": {"token": "future-token"},
        },
        format="json",
    )

    assert response.status_code == 409
