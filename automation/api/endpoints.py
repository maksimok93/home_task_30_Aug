"""Ендпоінти — ПЛЕЙСХОЛДЕРИ.

Реального API немає, тому шляхи вигадані. Це єдине місце, яке треба
відредагувати, коли з'явиться справжній контракт: тести їх не хардкодять.
"""

LOGIN = "/api/v1/auth/login"
BALANCE = "/api/v1/wallet/balance"

# PSP (payment service provider)
DEPOSIT_CREATE = "/api/v1/payments/deposits"
DEPOSIT_CALLBACK = "/api/v1/callbacks/psp/deposit"

# Назва header-а з підписом callback-а — теж плейсхолдер.
SIGNATURE_HEADER = "X-Signature"
