from __future__ import annotations

import uuid

from django.db import models
from django.db.models import Q


class Workspace(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def get_default(cls) -> "Workspace":
        workspace, _ = cls.objects.get_or_create(name="Default Workspace")
        return workspace


class ProviderAccount(models.Model):
    PROVIDER_CHOICES = (
        ("godaddy", "GoDaddy"),
        ("cloudflare", "Cloudflare"),
        ("aliyun", "Aliyun DNS"),
        ("tencent", "Tencent Cloud DNS"),
    )
    STATUS_CHOICES = (
        ("unknown", "Unknown"),
        ("active", "Active"),
        ("error", "Error"),
        ("disabled", "Disabled"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="provider_accounts")
    provider = models.CharField(max_length=32, choices=PROVIDER_CHOICES)
    display_name = models.CharField(max_length=120)
    api_base = models.URLField(max_length=300, blank=True)
    credential_ciphertext = models.TextField()
    is_default = models.BooleanField(default=False)
    is_enabled = models.BooleanField(default=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="unknown")
    last_zone_count = models.PositiveIntegerField(default=0)
    last_verified_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("workspace",),
                condition=Q(is_default=True),
                name="one_default_provider_account_per_workspace",
            )
        ]
