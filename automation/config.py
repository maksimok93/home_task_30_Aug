"""Конфігурація тестів. Усі значення беруться з оточення (див. .env.example)."""

import os
from dataclasses import dataclass
from typing import Optional


def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    value = os.getenv(name, default)
    return value.strip() if isinstance(value, str) else value


@dataclass(frozen=True)
class Config:
    base_url: Optional[str]
    tenant_a: str
    tenant_b: str
    user_email: str
    user_password: str
    user_id: str
    tenant_b_user_id: str
    psp_secret: str
    psp_merchant_id: str
    currency: str
    timeout: float

    @property
    def configured(self) -> bool:
        return bool(self.base_url)


def load_config() -> Config:
    return Config(
        base_url=_env("API_BASE_URL"),
        tenant_a=_env("TENANT_A", "tenant-a"),
        tenant_b=_env("TENANT_B", "tenant-b"),
        user_email=_env("QA_USER_EMAIL", "qa.user@example.com"),
        user_password=_env("QA_USER_PASSWORD", "Str0ng-P@ssw0rd"),
        user_id=_env("QA_USER_ID", "user-a-001"),
        tenant_b_user_id=_env("TENANT_B_USER_ID", "user-b-001"),
        psp_secret=_env("PSP_SECRET", "psp-shared-secret"),
        psp_merchant_id=_env("PSP_MERCHANT_ID", "merchant-a-001"),
        currency=_env("CURRENCY", "EUR"),
        timeout=float(_env("HTTP_TIMEOUT", "15")),
    )
