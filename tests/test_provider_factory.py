from types import SimpleNamespace

import pytest

from backend.providers.factory import ProviderFactory, UnsupportedProviderError


class FakeRepository:
    def decrypt(self, account):
        return {"token": "pat-from-account"}


def test_factory_rejects_future_provider_until_adapter_exists():
    account = SimpleNamespace(provider="cloudflare")

    with pytest.raises(UnsupportedProviderError):
        ProviderFactory(FakeRepository()).for_account(account)
