"""Тонкий HTTP-клієнт над реальними ендпоінтами.

Ключова деталь для підпису: callback надсилається як сирі байти того самого
payload, який підписували. Якщо віддати dict у `json=`, requests пересеріалізує
тіло і підпис перестане збігатися.
"""

import hashlib
import hmac
import json
import time
import uuid
from typing import Any, Dict, Optional, Tuple

import requests

from api import endpoints


def sign(payload: str, secret: str) -> str:
    """HMAC-SHA256 у hex. Замініть на алгоритм вашого PSP."""
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


def serialize(payload: Dict[str, Any]) -> str:
    """Канонічна серіалізація — саме ці байти підписуються і надсилаються."""
    return json.dumps(payload, separators=(",", ":"), sort_keys=True)


def unique_id(prefix: str) -> str:
    return "{}-{}-{}".format(prefix, int(time.time() * 1000), uuid.uuid4().hex[:8])


class ApiClient:
    def __init__(self, base_url: str, timeout: float = 15.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.token: Optional[str] = None

    def _url(self, path: str) -> str:
        return self.base_url + path

    def _auth_headers(self) -> Dict[str, str]:
        return {"Authorization": "Bearer {}".format(self.token)} if self.token else {}

    def login(self, email: str, password: str, tenant_id: str) -> requests.Response:
        response = self.session.post(
            self._url(endpoints.LOGIN),
            json={"email": email, "password": password, "tenantId": tenant_id},
            timeout=self.timeout,
        )
        if response.ok:
            self.token = response.json().get("token")
        return response

    def get_balance(self) -> requests.Response:
        return self.session.get(
            self._url(endpoints.BALANCE),
            headers=self._auth_headers(),
            timeout=self.timeout,
        )

    def balance_amount(self) -> float:
        response = self.get_balance()
        response.raise_for_status()
        return float(response.json()["balance"])

    def create_deposit(self, amount: str, currency: str) -> requests.Response:
        return self.session.post(
            self._url(endpoints.DEPOSIT_CREATE),
            headers=self._auth_headers(),
            json={"amount": amount, "currency": currency},
            timeout=self.timeout,
        )

    def build_deposit_payload(
        self,
        transaction_id: str,
        user_id: str,
        merchant_id: str,
        amount: str,
        currency: str,
        status: str = "success",
    ) -> Dict[str, Any]:
        return {
            "transactionId": transaction_id,
            "merchantId": merchant_id,
            "userId": user_id,
            "amount": amount,
            "currency": currency,
            "status": status,
        }

    def signed_body(self, payload: Dict[str, Any], secret: str) -> Tuple[str, str]:
        """Повертає (raw_body, signature) — обидва треба перевикористати у повторі."""
        raw = serialize(payload)
        return raw, sign(raw, secret)

    def send_deposit_callback(self, raw_body: str, signature: str) -> requests.Response:
        return self.session.post(
            self._url(endpoints.DEPOSIT_CALLBACK),
            data=raw_body.encode(),
            headers={
                "Content-Type": "application/json",
                endpoints.SIGNATURE_HEADER: signature,
            },
            timeout=self.timeout,
        )
