# Тест-кейси

## Identity

### TC-01 — Успішна реєстрація

**Тип:** Functional
**Передумови:** Tenant A активний; email ще не зареєстровано.

**Кроки:**

1. Надіслати запит на реєстрацію для тенанта А на електронну пошту
2. Перейти за посиланням
3. заповнити усі required поля для реєстрації
4. Перевірити створеного користувача

**Очікуваний результат:**

- повертається очікуваний POST 201 created
- створено одного користувача
- користувач прив’язаний до тенанту А
- audit event містить tenant ID

### TC-02 — Реєстрація з невалідними даними

**Тип:** Negative

**Кроки:** Надіслати запит без обов’язкового поля, з некоректним email або слабким паролем.

**Очікуваний результат:**

- повертається 400/422;
- описані validation errors;
- користувач не створений;
- жодних часткових записів немає.

### TC-03 — Повторна реєстрація того самого користувача

**Тип:** Negative / Functional
**Передумови:** Email уже існує в Tenant A.

**Кроки:** Повторити реєстрацію з тим самим нормалізованим email.

**Очікуваний результат:**

- повертається 409 або визначена бізнес-помилка;
- другий користувач не створений;
- регістр символів і пробіли не дозволяють обійти uniqueness rule.

### TC-04 — Успішний логін

**Тип:** Functional

**Кроки:** Увійти з правильними credentials у Tenant A.

**Очікуваний результат:**

- повертається access token/session;
- token містить або однозначно визначає user ID і tenant ID;
- час життя token відповідає конфігурації;
- пароль і секретні дані відсутні у response.

### TC-05 — Логін із неправильним паролем

**Тип:** Negative

**Кроки:** Виконати логін з правильним email та неправильним паролем.

**Очікуваний результат:**

- повертається 401;
- token не створюється;
- response не підтверджує, чи існує email;
- фінансові та профільні дані не розкриваються.

### TC-06 — Token Tenant A використовується в Tenant B

**Тип:** Tenant leakage / Security

**Кроки:**

1. Отримати token користувача Tenant A.
2. Викликати endpoint Tenant B з цим token.
3. Спробувати передати tenant ID через header, query і body.

**Очікуваний результат:**

- повертається 401/403/404;
- дані Tenant B не повертаються;
- tenant ID із token не можна перевизначити клієнтським параметром.

## PSP deposit callback

### TC-07 — Успішний deposit callback

**Тип:** Functional / Integration
**Передумови:** Існує pending deposit на 100.00 EUR.

**Кроки:** Надіслати валідно підписаний PSP callback зі статусом success.

**Очікуваний результат:**

- callback прийнято;
- deposit переходить у completed;
- баланс збільшується на 100.00 EUR;
- створена одна credit ledger entry;
- збережено PSP transaction ID;
- повернуто очікуваний PSP response.

### TC-08 — Callback з неправильним підписом

**Тип:** Negative / Integration

**Кроки:** Змінити signature або payload після підписання.

**Очікуваний результат:**

- повертається 401/403 або визначена provider-помилка;
- deposit і баланс не змінюються;
- ledger entry не створюється;
- подія записується в security/audit log без секретів.

### TC-09 — Невідомий PSP transaction ID

**Тип:** Negative / Integration

**Кроки:** Надіслати валідно підписаний callback з неіснуючим transaction ID.

**Очікуваний результат:**

- повертається визначений contract response;
- wallet не змінюється;
- невідома транзакція не створюється автоматично, якщо це не передбачено вимогами;
- помилка доступна в audit/monitoring.

### TC-10 — Amount або currency не відповідає deposit

**Тип:** Negative / Integration
**Передумови:** Deposit створений на 100.00 EUR.

**Кроки:** Надіслати callback на 100.00 USD або 1000.00 EUR.

**Очікуваний результат:**

- callback відхилено або переведено в manual review;
- баланс не змінюється;
- початкові amount/currency не перезаписуються безконтрольно.

### TC-11 — Failed deposit callback

**Тип:** Functional / Integration

**Кроки:** Надіслати валідний callback зі статусом failed.

**Очікуваний результат:**

- deposit переходить у failed;
- баланс не збільшується;
- credit ledger entry відсутня;
- причина відмови збережена без чутливих даних.

### TC-12 — PSP callback Tenant A для транзакції Tenant B

**Тип:** Tenant leakage / Integration

**Кроки:**

1. Створити deposit у Tenant B.
2. Надіслати callback через endpoint/configuration Tenant A.
3. Використати transaction ID або user ID з Tenant B.

**Очікуваний результат:**

- callback відхилено;
- дані Tenant B не розкриваються;
- баланс і транзакція Tenant B не змінюються;
- пошук транзакції обмежений Tenant A.

## GSP bet/win callbacks

### TC-13 — Успішний bet callback

**Тип:** Functional / Integration
**Передумови:** Баланс користувача — 100.00 EUR.

**Кроки:** Надіслати валідний bet callback на 20.00 EUR.

**Очікуваний результат:**

- bet прийнято;
- баланс стає 80.00 EUR;
- створена одна debit ledger entry;
- збережені GSP transaction ID, game ID і round ID.

### TC-14 — Bet при недостатньому балансі

**Тип:** Negative / Integration
**Передумови:** Баланс — 10.00 EUR.

**Кроки:** Надіслати bet callback на 20.00 EUR.

**Очікуваний результат:**

- повертається provider-specific insufficient funds;
- баланс залишається 10.00 EUR;
- debit ledger entry не створюється;
- баланс не може стати від’ємним.

### TC-15 — Успішний win callback

**Тип:** Functional / Integration
**Передумови:** Bet на 20.00 EUR успішно оброблений; баланс — 80.00 EUR.

**Кроки:** Надіслати win callback на 50.00 EUR для того самого round.

**Очікуваний результат:**

- win прийнято;
- баланс стає 130.00 EUR;
- створена одна credit ledger entry;
- win пов’язаний із правильним bet/round.

### TC-16 — Win для невідомого bet або round

**Тип:** Negative / Integration

**Кроки:** Надіслати win із неіснуючим bet ID/round ID.

**Очікуваний результат:**

- спрацьовує визначена політика: rejection або pending reconciliation;
- callback не зараховується довільному користувачу;
- якщо credit не дозволений вимогами — баланс не змінюється;
- подія доступна для reconciliation.

### TC-17 — GSP callback Tenant A містить користувача Tenant B

**Тип:** Tenant leakage / Integration

**Кроки:** Через GSP configuration Tenant A передати player ID, bet ID або round ID Tenant B.

**Очікуваний результат:**

- callback відхилено;
- баланс Tenant B не змінюється;
- response не розкриває дані користувача Tenant B;
- provider/player mapping перевіряється разом із tenant ID.

## Idempotency

### TC-18 — Повторний PSP deposit callback

**Тип:** Functional / Integration / Idempotency

**Кроки:** Двічі послідовно надіслати ідентичний успішний deposit callback.

**Очікуваний результат:**

- перший callback зараховує кошти;
- другий повертає той самий успішний або idempotent response;
- баланс змінюється лише один раз;
- існує одна фінансова ledger entry;
- повтор зафіксований у callback/audit history.

### TC-19 — Повторні bet і win callbacks

**Тип:** Functional / Integration / Idempotency

**Кроки:**

1. Двічі надіслати callback одного bet transaction ID.
2. Двічі надіслати callback одного win transaction ID.

**Очікуваний результат:**

- bet списується один раз;
- win зараховується один раз;
- повтори не створюють нових ledger entries;
- idempotency застосовується окремо до типу операції та provider transaction ID.

### TC-20 — Паралельні дублікати callback

**Тип:** Integration / Negative / Idempotency

**Кроки:** Одночасно надіслати 10–20 однакових PSP deposit або GSP bet/win callbacks.

**Очікуваний результат:**

- тільки один request виконує фінансову операцію;
- решта отримують узгоджений idempotent response;
- баланс змінюється один раз;
- створюється одна ledger entry;
- немає deadlock, negative balance або частково записаних даних;
- database unique constraint або atomic lock захищає від race condition.
