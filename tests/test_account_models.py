import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings")

import django

django.setup()

from django.test import TestCase

from backend.accounts.models import ProviderAccount, Workspace
from backend.accounts.repository import ProviderAccountRepository
from backend.app.accounts import AccountCredential


class ProviderAccountModelTests(TestCase):
    def setUp(self):
        self.workspace = Workspace.get_default()
        self.repository = ProviderAccountRepository("test-encryption-key")

    def test_default_workspace_is_reused(self):
        assert Workspace.get_default().pk == self.workspace.pk

    def test_repository_persists_encrypted_goDaddy_accounts(self):
        account = self.repository.create(
            self.workspace,
            provider="godaddy",
            display_name="生产 GoDaddy",
            credential=AccountCredential(provider="godaddy", values={"token": "pat-prod"}),
        )

        assert account.provider == "godaddy"
        assert account.credential_ciphertext != "pat-prod"
        assert self.repository.decrypt(account)["token"] == "pat-prod"

    def test_setting_default_clears_previous_default(self):
        first = self.repository.create(
            self.workspace,
            provider="godaddy",
            display_name="生产 GoDaddy",
            credential=AccountCredential(provider="godaddy", values={"token": "pat-prod"}),
        )
        second = self.repository.create(
            self.workspace,
            provider="godaddy",
            display_name="测试 GoDaddy",
            credential=AccountCredential(provider="godaddy", values={"token": "pat-test"}),
        )

        self.repository.set_default(first)
        self.repository.set_default(second)

        assert ProviderAccount.objects.get(pk=first.pk).is_default is False
        assert ProviderAccount.objects.get(pk=second.pk).is_default is True
