from __future__ import annotations

from rest_framework import serializers

from backend.app.accounts import AccountCredential
from backend.providers.base import DNSRecordDraft


class AccountCreateSerializer(serializers.Serializer):
    provider = serializers.ChoiceField(choices=["godaddy", "cloudflare", "aliyun", "tencent"])
    display_name = serializers.CharField(min_length=1, max_length=120)
    credential = serializers.DictField(child=serializers.CharField(), write_only=True)
    api_base = serializers.URLField(required=False, allow_blank=True)

    def to_credential(self) -> AccountCredential:
        return AccountCredential(provider=self.validated_data["provider"], values=self.validated_data["credential"])


class AccountUpdateSerializer(serializers.Serializer):
    display_name = serializers.CharField(min_length=1, max_length=120, required=False)
    is_enabled = serializers.BooleanField(required=False)
    credential = serializers.DictField(child=serializers.CharField(), write_only=True, required=False)

    def credential_for(self, provider: str) -> AccountCredential | None:
        values = self.validated_data.get("credential")
        return AccountCredential(provider=provider, values=values) if values is not None else None


class AccountSummarySerializer(serializers.Serializer):
    id = serializers.CharField()
    provider = serializers.CharField()
    display_name = serializers.CharField()
    status = serializers.CharField()
    is_default = serializers.BooleanField()
    zone_count = serializers.IntegerField()
    last_verified_at = serializers.CharField(allow_null=True)
    last_error = serializers.CharField(allow_null=True)


class AccountRecordSerializer(serializers.Serializer):
    type = serializers.CharField()
    name = serializers.CharField(min_length=1, max_length=255)
    content = serializers.CharField(min_length=1, max_length=4096)
    ttl = serializers.IntegerField(min_value=60, max_value=2147483647, default=600)
    priority = serializers.IntegerField(min_value=0, max_value=65535, required=False, allow_null=True)
    provider_fields = serializers.DictField(required=False)

    def to_draft(self) -> DNSRecordDraft:
        return DNSRecordDraft(**self.validated_data)
