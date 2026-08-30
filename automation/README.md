# Automation — API-автотести оплати

Python + pytest + requests. Покривають платіжний потік (deposit через PSP
callback) з кейсів [`../TEST-CASES.md`](../TEST-CASES.md).

> ⚠️ **Ендпоінти — плейсхолдери.** Реального API немає, тому всі шляхи вигадані
> й зібрані в одному файлі [`api/endpoints.py`](api/endpoints.py). Тести їх не
> хардкодять — щоб підключити справжній API, правити треба тільки цей файл
> (плюс алгоритм підпису в `api/client.py`).

## Тести

| # | Тест | Кейс | Що перевіряє |
| --- | --- | --- | --- |
| 1 | `test_successful_deposit_callback_credits_balance_once` | TC-07 | валідний callback зараховує рівно 100.00 |
| 2 | `test_deposit_callback_with_invalid_signature_is_rejected` | TC-08 | payload підмінено після підписання → 4xx, баланс не змінився |
| 3 | `test_deposit_callback_with_amount_mismatch_is_rejected` | TC-10 | deposit 100.00 EUR, callback 1000.00 USD → відхилено |
| 4 | `test_duplicate_deposit_callback_is_idempotent` | TC-18 | повтор тим самим тілом → одне зарахування |
| 5 | `test_parallel_duplicate_callbacks_credit_balance_once` | TC-20 | 10 однакових callbacks одночасно → одне зарахування |

## Встановлення

```bash
cd automation
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Налаштування

Змінні беруться з оточення. Шаблон — [`.env.example`](.env.example).

```bash
cp .env.example .env
# відредагувати .env, далі:
set -a && source .env && set +a
```

Обов'язкова тільки `API_BASE_URL`. **Поки вона не задана, тести не падають, а
пропускаються** — так можна перевірити, що оточення зібралось:

```bash
pytest
# 5 skipped
```

| Змінна | Призначення |
| --- | --- |
| `API_BASE_URL` | база API; без неї — skip |
| `QA_USER_EMAIL`, `QA_USER_PASSWORD` | тестовий користувач Tenant A |
| `QA_USER_ID` | ID гравця у payload callback-а |
| `PSP_SECRET` | секрет для HMAC-підпису |
| `PSP_MERCHANT_ID` | merchant у payload |
| `CURRENCY` | валюта гаманця, дефолт `EUR` |
| `HTTP_TIMEOUT` | таймаут запиту, сек, дефолт `15` |

## Запуск

```bash
pytest                                    # усі тести
pytest -m payments                        # за маркером
pytest -m idempotency                     # тільки TC-18 і TC-20
pytest -m "not concurrency"               # без паралельного тесту
pytest tests/test_payments.py::test_duplicate_deposit_callback_is_idempotent
pytest -k signature                       # за назвою
```

Звіт у HTML:

```bash
pytest --html=report.html --self-contained-html
```

У CI:

```bash
pytest --junitxml=results.xml
```

## Структура

```
automation/
├── api/
│   ├── client.py       HTTP-клієнт, підпис, серіалізація payload
│   └── endpoints.py    ← ПЛЕЙСХОЛДЕРИ: шляхи і назва header-а підпису
├── tests/
│   └── test_payments.py
├── conftest.py         фікстури: config, api (логін), pending_deposit
├── config.py           читання оточення
├── pytest.ini          маркери, testpaths
├── requirements.txt
└── .env.example
```

## Дві деталі, які легко зламати

**Підпис рахується по сирих байтах.** `api/client.serialize()` дає канонічний
JSON (`separators=(",", ":")`, `sort_keys=True`), і саме цей рядок і
підписується, і йде в `data=`. Якщо передати dict у `json=`, requests
пересеріалізує тіло — підпис перестане збігатися, і тест 2 почне «проходити» з
хибної причини.

**Ідемпотентність — це той самий payload.** Тести 4 і 5 не генерують новий
`transactionId` для повтору: вони перевикористовують `raw_body` і `signature`
першого запиту, як це робить реальний PSP при ретраї.

## Що доробити під реальний API

- [ ] Шляхи і назва header-а підпису — `api/endpoints.py`
- [ ] Алгоритм підпису — `sign()` у `api/client.py` (зараз HMAC-SHA256 hex)
- [ ] Формат сум: тести працюють з decimal-рядками (`"100.00"`); якщо API
      використовує minor units (`10000`), правити `DEPOSIT_AMOUNT` і порівняння
- [ ] Поля payload PSP — `build_deposit_payload()`
- [ ] Підготовка даних: фікстура `pending_deposit` створює депозит через API;
      якщо так не можна — замінити на seed у БД або фікстуру з готовим ID
- [ ] Ізоляція тестів: зараз баланс перевіряється як дельта до/після, тому
      паралельний прогін (`pytest -n`) на одному користувачі дасть хибні падіння
