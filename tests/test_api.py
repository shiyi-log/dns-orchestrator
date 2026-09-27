import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings")

import django

django.setup()

from rest_framework.test import APIClient

from backend.app.config import Settings
from backend.app.service import DNSService
from backend.dns_api import services as services_module


def client_for_demo():
    services_module.service = DNSService(Settings(godaddy_demo_mode=True))
    return APIClient()


def test_demo_health_and_records():
    client = client_for_demo()

    health = client.get("/api/health")
    domains = client.get("/api/domains")
    records = client.get("/api/domains/example.com/records")

    assert health.status_code == 200
    assert health.json()["demo_mode"] is True
    assert domains.json()[0]["domain"] == "example.com"
    assert records.json()[0]["data"] == "3.0.3.205"


def test_record_validation_error_is_readable():
    client = client_for_demo()

    response = client.post(
        "/api/domains/example.com/records",
        {"type": "A", "name": "", "data": "1.2.3.4", "ttl": 600},
        format="json",
    )

    assert response.status_code == 400
    assert response.json()["name"]


def test_demo_write_creates_activity_entry():
    client = client_for_demo()

    response = client.post(
        "/api/domains/example.com/records",
        {"type": "A", "name": "api", "data": "1.2.3.4", "ttl": 600},
        format="json",
    )
    activity = client.get("/api/activity")

    assert response.status_code == 201
    assert response.json()["name"] == "api"
    assert activity.json()[0]["action"] == "create"
