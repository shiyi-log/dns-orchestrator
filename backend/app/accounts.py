from __future__ import annotations

from typing import Dict, Literal, Optional

from pydantic import BaseModel, Field, field_validator


ProviderName = Literal["godaddy", "cloudflare", "aliyun", "tencent"]
AccountStatus = Literal["unknown", "active", "error", "disabled"]


class AccountCredential(BaseModel):
    provider: ProviderName
    values: Dict[str, str] = Field(min_length=1)

    @field_validator("values")
    @classmethod
    def values_must_be_nonempty(cls, values: Dict[str, str]) -> Dict[str, str]:
        if any(not key.strip() or not value.strip() for key, value in values.items()):
            raise ValueError("credential keys and values must not be blank")
        return values


class ProviderAccountSummary(BaseModel):
    id: str
    provider: ProviderName
    display_name: str
    status: AccountStatus
    is_default: bool
    zone_count: int = Field(default=0, ge=0)
    last_verified_at: Optional[str] = None
    last_error: Optional[str] = None
