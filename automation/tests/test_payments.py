"""API-автотести оплати (deposit через PSP callback).

Покриття — кейси з ../TEST-CASES.md:
    TC-07  успішний deposit callback
    TC-08  callback з неправильним підписом
    TC-10  amount/currency не відповідає deposit
    TC-18  повторний callback (ідемпотентність)
    TC-20  паралельні дублікати callback

Ендпоінти — плейсхолдери, див. api/endpoints.py.
"""

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import pytest

DEPOSIT_AMOUNT = "100.00"
PARALLEL_REQUESTS = 10


def _callback(api, config, transaction_id, amount=DEPOSIT_AMOUNT, currency=None, status="success"):
    """Готує підписаний callback і повертає (raw_body, signature)."""
    payload = api.build_deposit_payload(
        transaction_id=transaction_id,
        user_id=config.user_id,
        merchant_id=config.psp_merchant_id,
        amount=amount,
        currency=currency or config.currency,
        status=status,
    )
    return api.signed_body(payload, config.psp_secret)


@pytest.mark.payments
def test_successful_deposit_callback_credits_balance_once(api, config, pending_deposit):
    """TC-07: валідний callback зараховує рівно суму депозиту."""
    balance_before = Decimal(str(api.balance_amount()))

    raw_body, signature = _callback(api, config, pending_deposit)
    response = api.send_deposit_callback(raw_body, signature)

    assert response.status_code in (200, 201), (
        "Очікували 200/201, отримали {}: {}".format(response.status_code, response.text[:200])
    )
    body = response.json()
    assert "status" in body, "У відповіді немає поля 'status': {}".format(body)

    balance_after = Decimal(str(api.balance_amount()))
    assert balance_after - balance_before == Decimal(DEPOSIT_AMOUNT), (
        "Баланс змінився на {}, очікували +{}".format(balance_after - balance_before, DEPOSIT_AMOUNT)
    )


@pytest.mark.payments
def test_deposit_callback_with_invalid_signature_is_rejected(api, config, pending_deposit):
    """TC-08: payload підмінено після підписання — callback має бути відхилений."""
    raw_body, signature = _callback(api, config, pending_deposit)
    tampered_body = raw_body.replace('"{}"'.format(DEPOSIT_AMOUNT), '"9999.00"')
    assert tampered_body != raw_body, "Payload не змінився — перевірте формат серіалізації"

    balance_before = Decimal(str(api.balance_amount()))
    response = api.send_deposit_callback(tampered_body, signature)

    assert response.status_code in (400, 401, 403), (
        "Підпис не перевіряється: отримали {}".format(response.status_code)
    )
    assert Decimal(str(api.balance_amount())) == balance_before, "Баланс змінився попри невалідний підпис"

    lowered = response.text.lower()
    for leak in ("traceback", "stack", config.psp_secret.lower()):
        assert leak not in lowered, "Відповідь розкриває внутрішні дані: {}".format(leak)


@pytest.mark.payments
def test_deposit_callback_with_amount_mismatch_is_rejected(api, config, pending_deposit):
    """TC-10: deposit на 100.00 EUR, callback на 1000.00 USD."""
    balance_before = Decimal(str(api.balance_amount()))

    raw_body, signature = _callback(api, config, pending_deposit, amount="1000.00", currency="USD")
    response = api.send_deposit_callback(raw_body, signature)

    assert response.status_code >= 400, (
        "Невідповідність amount/currency прийнято зі статусом {}".format(response.status_code)
    )
    assert Decimal(str(api.balance_amount())) == balance_before, (
        "Баланс змінився за callback-ом з невідповідними amount/currency"
    )


@pytest.mark.payments
@pytest.mark.idempotency
def test_duplicate_deposit_callback_is_idempotent(api, config, pending_deposit):
    """TC-18: повтор із тим самим тілом і підписом не зараховує кошти вдруге."""
    balance_before = Decimal(str(api.balance_amount()))
    raw_body, signature = _callback(api, config, pending_deposit)

    first = api.send_deposit_callback(raw_body, signature)
    assert first.status_code in (200, 201), "Перший callback не пройшов: {}".format(first.status_code)

    # Байт-у-байт той самий payload і підпис — саме так ретраїть реальний PSP.
    second = api.send_deposit_callback(raw_body, signature)

    assert second.status_code < 500, "Повтор впав із 5xx: {}".format(second.status_code)
    assert second.status_code == first.status_code, (
        "Повтор дав інший статус: {} проти {}".format(second.status_code, first.status_code)
    )

    balance_after = Decimal(str(api.balance_amount()))
    assert balance_after - balance_before == Decimal(DEPOSIT_AMOUNT), (
        "Баланс змінився на {}, очікували одноразове +{}".format(
            balance_after - balance_before, DEPOSIT_AMOUNT
        )
    )


@pytest.mark.payments
@pytest.mark.idempotency
@pytest.mark.concurrency
def test_parallel_duplicate_callbacks_credit_balance_once(api, config, pending_deposit):
    """TC-20: N однакових callbacks одночасно — рівно одне зарахування."""
    balance_before = Decimal(str(api.balance_amount()))
    raw_body, signature = _callback(api, config, pending_deposit)

    with ThreadPoolExecutor(max_workers=PARALLEL_REQUESTS) as pool:
        responses = list(
            pool.map(lambda _: api.send_deposit_callback(raw_body, signature), range(PARALLEL_REQUESTS))
        )

    codes = [r.status_code for r in responses]
    assert all(code < 500 for code in codes), "Race condition дала 5xx: {}".format(codes)

    balance_after = Decimal(str(api.balance_amount()))
    assert balance_after - balance_before == Decimal(DEPOSIT_AMOUNT), (
        "{} паралельних callbacks змінили баланс на {}, очікували +{}".format(
            PARALLEL_REQUESTS, balance_after - balance_before, DEPOSIT_AMOUNT
        )
    )
    assert balance_after >= 0, "Баланс став від'ємним"
