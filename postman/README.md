# Postman

Колекція під кейси з [`../TEST-CASES.md`](../TEST-CASES.md). Перевіряє три речі:
**коди відповідей**, **JSON-схеми** та **ідемпотентність** повторних callbacks.

| Файл | Що це |
| --- | --- |
| `wallet-api.postman_collection.json` | Колекція, Postman Collection v2.1.0 |
| `staging.postman_environment.json` | Оточення зі змінними-плейсхолдерами |

> ⚠️ **Усе на плейсхолдерах.** Endpoint-и (`/api/v1/...`), поля payload,
> назва header-а підпису (`X-Signature`) і JSON-схеми вигадані. Перед першим
> прогоном замініть їх реальними контрактами — інакше все впаде на 404.

## Імпорт

1. Postman → **Import** → обидва файли.
2. Обрати оточення **Staging (placeholders)** у правому верхньому куті.
3. Заповнити `baseUrl`, `userEmail`, `userPassword`, `pspSecret`, `gspSecret`.

## Структура

| Папка | Кейси | Що перевіряє |
| --- | --- | --- |
| `1. Identity` | TC-01 … TC-06 | реєстрація, логін, uniqueness, user enumeration, tenant isolation по token |
| `2. PSP deposit callback` | TC-07 … TC-12 | підпис, невідома транзакція, amount/currency mismatch, failed, cross-tenant |
| `3. GSP bet/win callbacks` | TC-13 … TC-17 | bet, недостатній баланс, win, orphan win, cross-tenant player |
| `4. Idempotency` | TC-18 … TC-19 | повторні deposit/bet/win, контроль балансу до і після |

Запити в папці `4. Idempotency` **залежать від порядку** — виконувати через
Collection Runner, не поодинці.

## Як влаштовані перевірки

**Коди.** Кожен запит перевіряє список допустимих статусів
(`pm.expect([200, 201]).to.include(pm.response.code)`). На рівні колекції є
глобальний тест «No 5xx» — він виконується для всіх запитів.

**Схеми.** Через вбудований `pm.response.to.have.jsonSchema(...)`. Схеми
навмисно нежорсткі (`type: ['string', 'integer']`), плюс негативні перевірки —
відсутність `password`, секретів і stack trace у відповіді. Звужуйте їх, коли
буде реальний контракт.

**Ідемпотентність.** Ключовий момент — повторний запит має надіслати
**байт-у-байт те саме тіло і той самий підпис**. Тому pre-request script
першого запиту зберігає payload і HMAC у змінні:

```js
signPayload('idemDeposit', { transactionId: txId, /* ... */ }, 'pspSecret');
// → collectionVariables: idemDepositPayload, idemDepositSignature
```

а обидва запити (перший і повтор) шлють `{{idemDepositPayload}}` з header-ом
`X-Signature: {{idemDepositSignature}}`. Повтор порівнюється з першою
відповіддю за кодом і тілом, а `GET /wallet/balance` до і після підтверджує, що
баланс змінився рівно один раз.

**Підпис.** Helper `signPayload(name, payload, secretVar)` визначений у
pre-request script рівня колекції; використовує `CryptoJS.HmacSHA256`, вбудований
у Postman. Якщо у вас інший алгоритм (RSA, підпис по конкатенації полів,
timestamp у підписі) — правити треба тільки цей helper.

## Запуск через newman

```bash
npm i -g newman
newman run wallet-api.postman_collection.json \
  -e staging.postman_environment.json \
  --reporters cli,json --reporter-json-export result.json
```

## Паралельні дублікати (TC-20)

Postman і newman виконують запити послідовно, тому race condition на
паралельних callbacks вони не відтворять. Варіанти:

```bash
# 10 однакових callbacks одночасно
seq 10 | xargs -P 10 -I{} curl -s -X POST "$BASE/api/v1/callbacks/psp/deposit" \
  -H 'Content-Type: application/json' -H "X-Signature: $SIG" -d "$PAYLOAD"
```

або k6 / JMeter зі спільним `transaction_id`. Після прогону перевірити:
один рух балансу, одна ledger entry, відсутність deadlock і від'ємного балансу.
