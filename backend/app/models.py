from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


RecordType = Literal["A", "AAAA", "CNAME", "MX", "TXT", "NS", "SRV", "CAA"]
RecordStatus = Literal["active", "pending", "error"]


class DomainSummary(BaseModel):
    domain: str
    status: str = "active"
    expires_at: Optional[str] = None
    auto_renew: Optional[bool] = None
    record_count: int = 0


class RecordCreate(BaseModel):
    type: RecordType
    name: str = Field(min_length=1, max_length=255)
    data: str = Field(min_length=1, max_length=4096)
    ttl: int = Field(default=600, ge=60, le=2147483647)
    priority: Optional[int] = Field(default=None, ge=0, le=65535)
    weight: Optional[int] = Field(default=None, ge=0, le=65535)
    port: Optional[int] = Field(default=None, ge=0, le=65535)
    service: Optional[str] = None
    protocol: Optional[str] = None
    flags: Optional[int] = Field(default=None, ge=0, le=255)
    tag: Optional[str] = None

    @field_validator("name", "data")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class RecordUpdate(RecordCreate):
    pass


class DNSRecord(RecordCreate):
    id: str
    status: RecordStatus = "active"


class ActivityEntry(BaseModel):
    id: str
    action: Literal["create", "update", "delete"]
    domain: str
    record_id: Optional[str] = None
    summary: str
    status: Literal["success", "error"] = "success"
    created_at: str
