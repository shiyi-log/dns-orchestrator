import pytest
from pydantic import ValidationError

from backend.app.accounts import AccountCredential, ProviderAccountSummary


def test_account_credential_accepts_supported_provider():
    credential = AccountCredential(provider="godaddy", values={"token": "pat-value"})

    assert credential.provider == "godaddy"
    assert credential.values["token"] == "pat-value"


def test_account_credential_rejects_unknown_provider():
    with pytest.raises(ValidationError):
        AccountCredential(provider="unknown", values={"token": "value"})


def test_account_summary_contains_redacted_operational_fields():
    summary = ProviderAccountSummary(
        id="account-1",
        provider="godaddy",
        display_name="生产 GoDaddy",
        status="active",
        is_default=True,
        zone_count=2,
    )

    assert summary.is_default is True
    assert not hasattr(summary, "credential")
