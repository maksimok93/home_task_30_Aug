# Баг-репорти

> **Зразки.** Дефекти складені на основі кейсів із [TEST-CASES.md](TEST-CASES.md).
> Значення оточення, білдів, ID запитів і логів — плейсхолдери, які треба
> замінити фактичними даними з реального прогону.

## Зведення

| ID | Заголовок | Severity | Priority | Компонент | Кейс |
| --- | --- | --- | --- | --- | --- |
| BUG-001 | Повторний PSP deposit callback зараховує кошти двічі | Critical | P1 | Wallet / PSP | TC-18 |
| BUG-002 | Token Tenant A надає доступ до даних Tenant B | Critical | P1 | Auth / Multi-tenancy | TC-06 |
| BUG-003 | Паралельні bet callbacks доводять баланс до від’ємного | Critical | P1 | Wallet / GSP | TC-14, TC-20 |
| BUG-004 | Login response дозволяє user enumeration | Major | P2 | Auth | TC-05 |
| BUG-005 | Невідомий PSP transaction ID спричиняє 500 | Minor | P3 | PSP callback | TC-09 |

---

## BUG-001 — Повторний PSP deposit callback зараховує кошти двічі

| | |
| --- | --- |
| **Severity** | Critical |
| **Priority** | P1 |
| **Компонент** | Wallet / PSP callback |
| **Оточення** | Staging, API build `1.4.2`, Tenant A |
| **Пов’язаний кейс** | TC-18 (Idempotency) |
| **Статус** | Open |

**Передумови:** користувач Tenant A з балансом 0.00 EUR; створено pending deposit на 100.00 EUR.

**Кроки відтворення:**

1. Надіслати валідно підписаний PSP callback зі статусом `success` на 100.00 EUR.
2. Дочекатися відповіді `200 OK`.
3. Надіслати той самий callback повторно з ідентичним payload і signature.

**Фактичний результат:**

- обидва callbacks обробляються як нові;
- баланс стає 200.00 EUR;
- у ledger дві credit entries з тим самим PSP transaction ID;
- deposit двічі переходить у `completed`.

**Очікуваний результат:**

- другий callback повертає той самий успішний або idempotent response;
- баланс змінюється один раз — 100.00 EUR;
- існує рівно одна credit ledger entry;
- повтор зафіксований у callback/audit history.

**Додатково:** відсутній unique constraint на `(provider, transaction_id)` — перевірити на рівні БД, а не лише в коді.

---

## BUG-002 — Token Tenant A надає доступ до даних Tenant B

| | |
| --- | --- |
| **Severity** | Critical |
| **Priority** | P1 |
| **Компонент** | Auth / Multi-tenancy |
| **Оточення** | Staging, API build `1.4.2`, Tenant A і Tenant B |
| **Пов’язаний кейс** | TC-06 (Tenant leakage / Security) |
| **Статус** | Open |

**Передумови:** активні користувачі в Tenant A і Tenant B; у Tenant B є транзакції.

**Кроки відтворення:**

1. Залогінитися користувачем Tenant A, отримати access token.
2. Викликати endpoint Tenant B (`GET /api/transactions`) з цим token.
3. Додатково передати `X-Tenant-Id: B` у header.

**Фактичний результат:**

- повертається `200 OK` зі списком транзакцій Tenant B;
- tenant ID береться з header і перевизначає значення з token.

**Очікуваний результат:**

- повертається `401/403/404`;
- дані Tenant B не повертаються;
- tenant ID із token не можна перевизначити клієнтським параметром.

---

## BUG-003 — Паралельні bet callbacks доводять баланс до від’ємного

| | |
| --- | --- |
| **Severity** | Critical |
| **Priority** | P1 |
| **Компонент** | Wallet / GSP callback |
| **Оточення** | Staging, API build `1.4.2`, Tenant A |
| **Пов’язаний кейс** | TC-14, TC-20 (Concurrency / Idempotency) |
| **Статус** | Open |

**Передумови:** баланс користувача — 10.00 EUR.

**Кроки відтворення:**

1. Підготувати 10 однакових bet callbacks на 5.00 EUR (різні transaction ID).
2. Надіслати їх одночасно в 10 паралельних потоках.
3. Перевірити баланс і ledger.

**Фактичний результат:**

- прийнято 6+ bets замість 2;
- баланс стає `-20.00 EUR`;
- перевірка достатності балансу виконується поза транзакцією.

**Очікуваний результат:**

- прийнято рівно 2 bets, баланс — 0.00 EUR;
- решта отримують provider-specific insufficient funds;
- баланс не може стати від’ємним;
- немає deadlock і частково записаних даних.

---

## BUG-004 — Login response дозволяє user enumeration

| | |
| --- | --- |
| **Severity** | Major |
| **Priority** | P2 |
| **Компонент** | Auth |
| **Оточення** | Staging, API build `1.4.2`, Tenant A |
| **Пов’язаний кейс** | TC-05 (Negative) |
| **Статус** | Open |

**Передумови:** у Tenant A зареєстрований `user@example.com`.

**Кроки відтворення:**

1. Виконати логін з `user@example.com` і неправильним паролем.
2. Виконати логін з неіснуючим `nobody@example.com` і будь-яким паролем.
3. Порівняти статус-коди, тіла відповідей і час обробки.

**Фактичний результат:**

- для існуючого email — `401` з `"Invalid password"`;
- для неіснуючого — `404` з `"User not found"`;
- відповіді дозволяють визначити, чи існує акаунт.

**Очікуваний результат:**

- в обох випадках `401` з однаковим generic-повідомленням;
- response не підтверджує, чи існує email;
- token не створюється.

---

## BUG-005 — Невідомий PSP transaction ID спричиняє 500

| | |
| --- | --- |
| **Severity** | Minor |
| **Priority** | P3 |
| **Компонент** | PSP callback |
| **Оточення** | Staging, API build `1.4.2`, Tenant A |
| **Пов’язаний кейс** | TC-09 (Negative / Integration) |
| **Статус** | Open |

**Передумови:** немає.

**Кроки відтворення:**

1. Надіслати валідно підписаний PSP callback з неіснуючим `transaction_id`.
2. Перевірити response і логи.

**Фактичний результат:**

- повертається `500 Internal Server Error` з stack trace у тілі відповіді;
- PSP трактує це як тимчасову помилку і ретраїть callback.

**Очікуваний результат:**

- повертається визначений contract response (наприклад `404` або provider-specific код);
- wallet не змінюється;
- помилка доступна в audit/monitoring без stack trace у відповіді.
