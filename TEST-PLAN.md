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
