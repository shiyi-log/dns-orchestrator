import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

from dotenv import load_dotenv


load_dotenv()


def _as_bool(value: Optional[str], default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    godaddy_pat: Optional[str] = None
    godaddy_demo_mode: bool = True
    godaddy_api_base: str = "https://api.godaddy.com"
    request_timeout_seconds: float = 15.0
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings(
        godaddy_pat=os.getenv("GODADDY_PAT"),
        godaddy_demo_mode=_as_bool(os.getenv("GODADDY_DEMO_MODE"), True),
        godaddy_api_base=os.getenv("GODADDY_API_BASE", "https://api.godaddy.com").rstrip("/"),
        request_timeout_seconds=float(os.getenv("REQUEST_TIMEOUT_SECONDS", "15")),
        cors_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173"),
    )
