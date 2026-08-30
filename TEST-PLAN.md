Мета

Перевірити критичні інтеграційні потоки:

- реєстрацію та логін;
- deposit callback від PSP;
- bet/win callbacks від GSP;
- повторну обробку callbacks;
- ізоляцію даних між тенантами;
- коректність фінансових операцій і балансу

Scope:

authentication та authorization;
визначення tenant за token/header/domain/provider configuration;
перевірка callback signature;
відповідність callback правильному tenant;
atomic wallet operations;
idempotency;
послідовність bet → win;
audit logs та HTTP responses.

In-scope

Identity

- реєстрація користувача (логін, валідація обов’язкових полів, унікальність користувача всередині системи)
- tenant binding
- невалідні credentials
- недійсний, прострочений та токен іншого тенанту

PSP deposit callback

успішний deposit callback;
перевірка підпису;
перевірка merchant/provider configuration;
пошук користувача і транзакції;
статуси success/failed;
відповідність amount/currency;
оновлення wallet/ledger;
повторні та паралельні callbacks;
rollback у разі внутрішньої помилки;
tenant isolation.

GSP bet/win callbacks

успішний bet;
недостатній баланс;
успішний win;
зв’язок win з bet/round;
порядок callbacks;
перевірка signature і provider configuration;
повторні та паралельні callbacks;
tenant isolation;
точність фінансових розрахунків.

Out-of-scope

- UI/UX, верстка та адаптивність
- тестування реальних платіжних карток
- повна перевірка систем PSP/GSP
- penetration testing і DDoS
- security testing логін форми
- навантажувальне тестування
- KYC/AML та responsible-gaming правила
- бонуси, jackpot, cashout/refund/rollback, якщо вони не входять в окремі вимоги
- перевірка математичної моделі гри або RTP

# Ризик-матриця

| Ризик | Ймовірність | Вплив | Рівень | Основна перевірка |
| --- | --- | --- | --- | --- |
| Подвійне зарахування deposit | High | Critical | High | Повторні та паралельні PSP callbacks |
| Подвійне списання bet | High | Critical | High | Idempotency та concurrency |
| Подвійне зарахування win | High | Critical | High | Унікальність provider transaction ID |
| Доступ до даних іншого tenant | Medium | Critical | High | Token/header/object tenant isolation |
| Callback із валідним підписом одного tenant прийнято іншим | Medium | Critical | High | Tenant-specific secrets і merchant mapping |
| Прийняття callback з неправильним підписом | Medium | Critical | High | Signature verification |
| Часткове оновлення: ledger створено, баланс не змінено | Medium | Critical | High | Atomicity та rollback |
| Race condition при паралельних callbacks | Medium | Critical | High | Concurrent requests |
| Bet при недостатньому балансі | Medium | High | High | Balance validation та locking |
| Неправильний amount або currency | Medium | High | High | Перевірка даних callback |
| Win прив’язано до неправильного bet/round | Medium | High | High | Provider reference validation |
| Win отримано раніше за bet | Medium | High | Medium | Defined out-of-order policy |
| Повторна реєстрація користувача | Medium | Medium | Medium | Uniqueness rules |
| User enumeration через login errors | Medium | Medium | Medium | Однакові помилки та статуси |
| Прострочений token залишається активним | Low | High | Medium | Token expiration |
| Некоректний callback формат спричиняє 500 | Medium | Medium | Medium | Schema validation |
| Відсутність correlation/audit data | Medium | Medium | Medium | Logging та observability |
| Чутливі дані потрапляють у логи | Low | High | Medium | Log inspection |
| Незначна затримка callback | Medium | Low | Low | Retry behavior |
| Некритична різниця в тексті validation error | Medium | Low | Low | Contract validation |

