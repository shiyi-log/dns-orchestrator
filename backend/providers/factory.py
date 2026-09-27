from __future__ import annotations

from .base import DNSProviderAdapter
from .godaddy import GoDaddyAdapter


class UnsupportedProviderError(ValueError):
    pass


class ProviderFactory:
    def __init__(self, repository, demo_mode: bool = False):
        self.repository = repository
        self.demo_mode = demo_mode
        self._demo_adapters = {}

    def for_account(self, account) -> DNSProviderAdapter:
        if account.provider == "godaddy":
            if self.demo_mode and str(account.id) in self._demo_adapters:
                return self._demo_adapters[str(account.id)]
            adapter = GoDaddyAdapter(
                account,
                self.repository.decrypt(account),
                demo_mode=self.demo_mode,
            )
            if self.demo_mode:
                self._demo_adapters[str(account.id)] = adapter
            return adapter
        raise UnsupportedProviderError(
            f"Provider '{account.provider}' is not implemented in this phase"
        )
