from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


ProviderName = Literal["godaddy", "cloudflare", "aliyun", "tencent"]


class Zone(BaseModel):
    id: str
    name: str
    status: str = "active"
    record_count: int = 0
    provider_fields: Dict[str, Any] = Field(default_factory=dict)


class DNSRecord(BaseModel):
    id: str
    zone: str
    type: str
    name: str
    content: str
    ttl: int = Field(ge=60)
    priority: Optional[int] = None
    status: str = "active"
    provider_fields: Dict[str, Any] = Field(default_factory=dict)


class DNSRecordDraft(BaseModel):
    type: str
    name: str
    content: str
    ttl: int = Field(default=600, ge=60)
    priority: Optional[int] = None
    provider_fields: Dict[str, Any] = Field(default_factory=dict)


class ProviderStatus(BaseModel):
    provider: ProviderName
    status: Literal["active", "error", "unsupported"]
    zone_count: int = 0
    error: Optional[str] = None


class ProviderCapabilities(BaseModel):
    provider: ProviderName
    implemented: bool
    record_types: List[str] = Field(default_factory=list)
    fields: List[str] = Field(default_factory=list)


class DNSProviderAdapter:
    provider: ProviderName

    def verify_connection(self) -> ProviderStatus:
        raise NotImplementedError

    def list_zones(self) -> list[Zone]:
        raise NotImplementedError

    def list_records(self, zone: Zone) -> list[DNSRecord]:
        raise NotImplementedError

    def create_record(self, zone: Zone, draft: DNSRecordDraft) -> DNSRecord:
        raise NotImplementedError

    def update_record(self, zone: Zone, record_id: str, draft: DNSRecordDraft) -> DNSRecord:
        raise NotImplementedError

    def delete_record(self, zone: Zone, record_id: str) -> None:
        raise NotImplementedError

    def capabilities(self) -> ProviderCapabilities:
        raise NotImplementedError
