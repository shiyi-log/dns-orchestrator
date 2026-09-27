from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from backend.accounts.models import ProviderAccount, Workspace
from backend.accounts.repository import ProviderAccountRepository
from backend.app.accounts import AccountCredential, ProviderAccountSummary
from backend.app.config import Settings
from backend.app.crypto import CredentialError
from backend.app.demo_data import demo_domains
from backend.app.models import ActivityEntry
from backend.providers.base import DNSRecord, DNSRecordDraft, ProviderStatus, Zone
from backend.providers.factory import ProviderFactory, UnsupportedProviderError


PROVIDER_METADATA = [
    {
        "id": "godaddy",
        "name": "GoDaddy",
        "implemented": True,
        "credential_fields": ["token"],
    },
    {
        "id": "cloudflare",
        "name": "Cloudflare",
        "implemented": False,
        "credential_fields": ["token", "account_id"],
    },
    {
        "id": "aliyun",
        "name": "阿里云 DNS",
        "implemented": False,
        "credential_fields": ["access_key_id", "access_key_secret"],
    },
    {
        "id": "tencent",
        "name": "腾讯云 DNS",
        "implemented": False,
        "credential_fields": ["secret_id", "secret_key"],
    },
]


class AccountService:
    def __init__(self, settings: Settings):
        self.settings = settings
        encryption_key = settings.account_encryption_key
        if not encryption_key and settings.godaddy_demo_mode:
            encryption_key = "demo-account-encryption-key"
        if not encryption_key:
            raise CredentialError("ACCOUNT_ENCRYPTION_KEY is required")
        self.repository = ProviderAccountRepository(encryption_key)
        self.factory = ProviderFactory(self.repository, demo_mode=settings.godaddy_demo_mode)
        self._activities: list[ActivityEntry] = []

    def activity(self) -> list[ActivityEntry]:
        return list(self._activities)

    def providers(self) -> list[dict[str, Any]]:
        return PROVIDER_METADATA

    def list_accounts(self) -> list[ProviderAccountSummary]:
        self._ensure_demo_account()
        workspace = Workspace.get_default()
        return [self._summary(account) for account in self.repository.list(workspace)]

    def create_account(
        self,
        provider: str,
        display_name: str,
        credential: AccountCredential,
        api_base: str | None = None,
    ) -> ProviderAccountSummary:
        if provider != "godaddy":
            raise UnsupportedProviderError(
                f"Provider '{provider}' is not implemented in this phase"
            )
        workspace = Workspace.get_default()
        account = self.repository.create(
            workspace,
            provider=provider,
            display_name=display_name,
            credential=credential,
            api_base=api_base,
        )
        return self._summary(account)

    def update_account(
        self,
        account_id: str,
        display_name: str | None = None,
        is_enabled: bool | None = None,
        credential: AccountCredential | None = None,
    ) -> ProviderAccountSummary:
        account = self._get_account(account_id)
        if display_name is not None:
            account.display_name = display_name.strip()
        if is_enabled is not None:
            account.is_enabled = is_enabled
            if not is_enabled:
                account.status = "disabled"
        if credential is not None:
            if credential.provider != account.provider:
                raise ValueError("credential provider does not match account provider")
            from backend.app.crypto import encrypt_secret
            import json

            account.credential_ciphertext = encrypt_secret(
                json.dumps(credential.values, sort_keys=True),
                self.repository.encryption_key,
            )
            account.status = "unknown"
            account.last_error = ""
        account.save()
        return self._summary(account)

    def delete_account(self, account_id: str) -> None:
        account = self._get_account(account_id)
        self.repository.delete(account.id)
        remaining = self.repository.list(account.workspace)
        if remaining and not any(item.is_default for item in remaining):
            self.repository.set_default(remaining[0])

    def set_default(self, account_id: str) -> ProviderAccountSummary:
        account = self.repository.set_default(self._get_account(account_id))
        return self._summary(account)

    def verify(self, account_id: str) -> ProviderAccountSummary:
        account = self._get_account(account_id)
        adapter = self.factory.for_account(account)
        status = adapter.verify_connection()
        self._apply_status(account, status)
        return self._summary(account)

    def list_zones(self, account_id: str) -> list[Zone]:
        return self.factory.for_account(self._get_account(account_id)).list_zones()

    def list_records(self, account_id: str, zone_name: str) -> list[DNSRecord]:
        zone = self._zone(account_id, zone_name)
        return self.factory.for_account(self._get_account(account_id)).list_records(zone)

    def create_record(self, account_id: str, zone_name: str, draft: DNSRecordDraft) -> DNSRecord:
        zone = self._zone(account_id, zone_name)
        record = self.factory.for_account(self._get_account(account_id)).create_record(zone, draft)
        self._record_activity("create", zone_name, record, "新增")
        return record

    def update_record(
        self,
        account_id: str,
        zone_name: str,
        record_id: str,
        draft: DNSRecordDraft,
    ) -> DNSRecord:
        zone = self._zone(account_id, zone_name)
        record = self.factory.for_account(self._get_account(account_id)).update_record(
            zone, record_id, draft
        )
        self._record_activity("update", zone_name, record, "更新")
        return record

    def delete_record(self, account_id: str, zone_name: str, record_id: str) -> None:
        zone = self._zone(account_id, zone_name)
        self.factory.for_account(self._get_account(account_id)).delete_record(zone, record_id)
        self._activities.insert(
            0,
            ActivityEntry(
                id=f"account-delete-{record_id}",
                action="delete",
                domain=zone_name,
                record_id=record_id,
                summary=f"删除记录 {record_id}",
                created_at=datetime.now(timezone.utc).isoformat(),
            ),
        )

    def default_account(self) -> ProviderAccount | None:
        self._ensure_demo_account()
        workspace = Workspace.get_default()
        return next((item for item in self.repository.list(workspace) if item.is_default), None)

    def _ensure_demo_account(self) -> None:
        if not self.settings.godaddy_demo_mode:
            return
        workspace = Workspace.get_default()
        existing = self.repository.list(workspace)
        if existing:
            demo = next((item for item in existing if item.display_name == "演示 GoDaddy"), None)
            if demo and (demo.status != "active" or demo.last_zone_count != len(demo_domains())):
                demo.status = "active"
                demo.last_zone_count = len(demo_domains())
                demo.last_error = ""
                demo.save(update_fields=["status", "last_zone_count", "last_error", "updated_at"])
            return
        account = self.repository.create(
            workspace,
            provider="godaddy",
            display_name="演示 GoDaddy",
            credential=AccountCredential(provider="godaddy", values={"token": "demo-token"}),
        )
        account.status = "active"
        account.last_zone_count = len(demo_domains())
        account.save(update_fields=["status", "last_zone_count", "updated_at"])

    def _get_account(self, account_id: str) -> ProviderAccount:
        workspace = Workspace.get_default()
        try:
            return ProviderAccount.objects.get(id=account_id, workspace=workspace)
        except ProviderAccount.DoesNotExist as exc:
            raise ValueError("account was not found") from exc

    def _zone(self, account_id: str, zone_name: str) -> Zone:
        for zone in self.list_zones(account_id):
            if zone.name == zone_name:
                return zone
        raise ValueError("zone was not found")

    @staticmethod
    def _apply_status(account: ProviderAccount, status: ProviderStatus) -> None:
        account.status = status.status if status.status != "unsupported" else "error"
        account.last_zone_count = status.zone_count
        account.last_error = status.error or ""
        account.last_verified_at = datetime.now(timezone.utc) if status.status == "active" else account.last_verified_at
        account.save()

    @staticmethod
    def _summary(account: ProviderAccount) -> ProviderAccountSummary:
        return ProviderAccountSummary(
            id=str(account.id),
            provider=account.provider,
            display_name=account.display_name,
            status=account.status,
            is_default=account.is_default,
            zone_count=account.last_zone_count,
            last_verified_at=account.last_verified_at.isoformat() if account.last_verified_at else None,
            last_error=account.last_error or None,
        )

    def _record_activity(self, action: str, zone: str, record: DNSRecord, label: str) -> None:
        self._activities.insert(
            0,
            ActivityEntry(
                id=f"account-{action}-{record.id}",
                action=action,
                domain=zone,
                record_id=record.id,
                summary=f"{label} {record.type} {record.name} → {record.content}",
                created_at=datetime.now(timezone.utc).isoformat(),
            ),
        )
