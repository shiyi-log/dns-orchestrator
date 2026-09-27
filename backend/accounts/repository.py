from __future__ import annotations

import json
from typing import Optional

from django.db import transaction

from backend.app.accounts import AccountCredential
from backend.app.crypto import decrypt_secret, encrypt_secret

from .models import ProviderAccount, Workspace


DEFAULT_API_BASES = {
    "godaddy": "https://api.godaddy.com",
    "cloudflare": "https://api.cloudflare.com",
    "aliyun": "",
    "tencent": "",
}


class ProviderAccountRepository:
    def __init__(self, encryption_key: str):
        self.encryption_key = encryption_key

    def list(self, workspace: Workspace):
        return list(
            ProviderAccount.objects.filter(workspace=workspace)
            .order_by("-is_default", "display_name", "created_at")
        )

    def create(
        self,
        workspace: Workspace,
        provider: str,
        display_name: str,
        credential: AccountCredential,
        api_base: Optional[str] = None,
    ) -> ProviderAccount:
        has_accounts = ProviderAccount.objects.filter(workspace=workspace).exists()
        return ProviderAccount.objects.create(
            workspace=workspace,
            provider=provider,
            display_name=display_name.strip(),
            api_base=api_base or DEFAULT_API_BASES.get(provider, ""),
            credential_ciphertext=encrypt_secret(
                json.dumps(credential.values, sort_keys=True),
                self.encryption_key,
            ),
            is_default=not has_accounts,
        )

    def decrypt(self, account: ProviderAccount) -> dict[str, str]:
        return json.loads(decrypt_secret(account.credential_ciphertext, self.encryption_key))

    @transaction.atomic
    def set_default(self, account: ProviderAccount) -> ProviderAccount:
        ProviderAccount.objects.filter(workspace=account.workspace).update(is_default=False)
        ProviderAccount.objects.filter(pk=account.pk).update(is_default=True)
        return ProviderAccount.objects.get(pk=account.pk)

    def delete(self, account_id):
        ProviderAccount.objects.filter(pk=account_id).delete()
