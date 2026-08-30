import pytest

from api.client import ApiClient
from config import load_config


def pytest_configure(config):
    config.addinivalue_line("markers", "payments: тести платіжних потоків")
    config.addinivalue_line("markers", "idempotency: перевірки повторних callbacks")
    config.addinivalue_line("markers", "concurrency: паралельні запити")


@pytest.fixture(scope="session")
def config():
    cfg = load_config()
    if not cfg.configured:
        pytest.skip(
            "API_BASE_URL не заданий — тести пропущено. "
            "Див. automation/README.md, розділ «Налаштування»."
        )
    return cfg


@pytest.fixture(scope="session")
def api(config):
    client = ApiClient(config.base_url, timeout=config.timeout)
    response = client.login(config.user_email, config.user_password, config.tenant_a)
    assert response.ok, "Логін тестового користувача не вдався: {} {}".format(
        response.status_code, response.text[:200]
    )
    return client


@pytest.fixture
def pending_deposit(api, config):
    """Створює pending deposit на 100.00 і повертає його transaction ID."""
    response = api.create_deposit("100.00", config.currency)
    assert response.ok, "Не вдалося створити deposit: {}".format(response.status_code)
    body = response.json()
    return body.get("transactionId") or body.get("id")
