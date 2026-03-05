# API контракты

Базовый URL: `https://api.ostrov-vezeniya.ru/api/v1`
Локальная разработка: `http://localhost:8000/api/v1`

Все суммы — в **копейках** (1 руб = 100 коп).
Все веса — в **граммах**.

---

## Авторизация

### Магазины
```
Header: X-API-Key: <sha256-hex-string>
```
API-ключ генерируется при создании магазина и передаётся владельцу.

### Админка
```
Header: Authorization: Bearer <jwt-token>
```
JWT получается через `/auth/login`, время жизни — 60 минут.
Rate limit на `/auth/login`: 10 запросов в минуту (по IP).

---

## Для магазинов (X-API-Key)

### POST /delivery/calculate — Расчёт стоимости доставки

Запрос:
```json
{
  "postal_code": "101000",
  "weight_grams": 5000,
  "total_amount_kopecks": 500000
}
```

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| postal_code | string(5-6) | ✅ | Почтовый индекс получателя |
| weight_grams | int > 0 | ✅ | Вес посылки в граммах |
| total_amount_kopecks | int > 0 | ✅ | Сумма заказа в копейках |

Ответ (200):
```json
{
  "delivery_cost_kopecks": 178900,
  "customs_fee_kopecks": 15000,
  "total_cost_kopecks": 193900,
  "delivery_days_min": 5,
  "delivery_days_max": 10,
  "available": true,
  "rejection_reason": null
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| delivery_cost_kopecks | int | Стоимость доставки Почтой России |
| customs_fee_kopecks | int | Стоимость таможенного оформления |
| total_cost_kopecks | int | Итого (доставка + таможня) |
| delivery_days_min | int | Минимальный срок (дней) |
| delivery_days_max | int | Максимальный срок (дней) |
| available | bool | Доступна ли доставка |
| rejection_reason | string \| null | Причина отказа (лимит веса, суммы и т.д.) |

Ограничения:
- Максимальный вес: 30 000 г (30 кг)
- Максимальная сумма: ~200$ по текущему курсу

---

### POST /orders — Создание заказа

Запрос:
```json
{
  "external_order_id": "SHOP-ORD-12345",
  "recipient": {
    "name": "Иванов Пётр Сергеевич",
    "phone": "+79261234567",
    "email": "ivanov@mail.ru",
    "address": "Москва, ул. Ленина, д. 1, кв. 5",
    "postal_code": "101000"
  },
  "items": [
    {
      "name": "KALLAX Стеллаж",
      "sku": "KLX-7777-W",
      "quantity": 1,
      "price_kopecks": 499900,
      "weight_grams": 12000
    },
    {
      "name": "LACK Столик",
      "sku": "LCK-5555-W",
      "quantity": 2,
      "price_kopecks": 99900,
      "weight_grams": 3500
    }
  ]
}
```

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| external_order_id | string | ✅ | ID заказа в системе магазина |
| recipient.name | string(2+) | ✅ | ФИО получателя |
| recipient.phone | string(5+) | ✅ | Телефон |
| recipient.email | string | ❌ | Email |
| recipient.address | string(5+) | ✅ | Полный адрес |
| recipient.postal_code | string(5-6) | ✅ | Индекс |
| recipient.passport_series | string(4) | ✅ | Серия паспорта (4 цифры) |
| recipient.passport_number | string(6) | ✅ | Номер паспорта (6 цифр) |
| items[].name | string | ✅ | Название товара |
| items[].sku | string | ❌ | Артикул (SKU) магазина |
| items[].quantity | int > 0 | ✅ | Количество |
| items[].price_kopecks | int > 0 | ✅ | Цена за единицу в копейках |
| items[].weight_grams | int > 0 | ✅ | Вес единицы в граммах |

Ответ (201):
```json
{
  "id": "a1676a0c-0ab7-43a6-935a-0592b113f9d2",
  "external_order_id": "SHOP-ORD-12345",
  "status": "accepted",
  "recipient_name": "Иванов Пётр Сергеевич",
  "recipient_phone": "+79261234567",
  "recipient_email": "ivanov@mail.ru",
  "recipient_address": "Москва, ул. Ленина, д. 1, кв. 5",
  "recipient_postal_code": "101000",
  "items": [...],
  "total_amount_kopecks": 699700,
  "total_weight_grams": 19000,
  "delivery_cost_kopecks": 245600,
  "customs_fee_kopecks": 15000,
  "track_number": null,
  "batch_id": null,
  "created_at": "2026-02-17T10:30:00Z",
  "updated_at": "2026-02-17T10:30:00Z"
}
```

Ошибки:
- `409 Conflict` — заказ с таким `external_order_id` уже существует для этого магазина

---

### GET /orders/{order_id}/status — Статус заказа

Ответ (200):
```json
{
  "id": "a1676a0c-...",
  "status": "received_warehouse",
  "track_number": null,
  "updated_at": "2026-02-17T10:30:00Z"
}
```

---

### GET /orders/{order_id}/tracking — Трекинг заказа (полная история)

Ответ (200):
```json
{
  "id": "a1676a0c-...",
  "status": "received_warehouse",
  "track_number": null,
  "history": [
    {
      "old_status": null,
      "new_status": "accepted",
      "comment": null,
      "created_at": "2026-02-17T10:30:00Z"
    },
    {
      "old_status": "accepted",
      "new_status": "awaiting_pickup",
      "comment": "Курьер назначен",
      "created_at": "2026-02-17T14:00:00Z"
    }
  ]
}
```

---

## Для админки (JWT Bearer)

### POST /auth/login — Авторизация

Запрос:
```json
{
  "email": "admin@ostrov.ru",
  "password": "admin123"
}
```

Ответ (200):
```json
{
  "access_token": "eyJhbG...",
  "token_type": "bearer",
  "expires_in": 86400,
  "operator": {
    "id": "7d88e41f-...",
    "name": "Администратор",
    "role": "admin"
  }
}
```

Ошибки:
- `401 Unauthorized` — неверный email/пароль

---

### GET /admin/orders — Список заказов

Query-параметры:

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|-------------|----------|
| page | int | 1 | Номер страницы |
| per_page | int | 20 | Записей на страницу |
| status | string | — | Фильтр по статусу |
| search | string | — | Поиск по имени, номеру заказа, треку |

Ответ (200):
```json
{
  "items": [
    {
      "id": "a1676a0c-...",
      "external_order_id": "SHOP-ORD-12345",
      "shop_name": "IKEA-39 Тест",
      "status": "received_warehouse",
      "recipient_name": "Иванов Пётр Сергеевич",
      "items": [...],
      "total_amount_kopecks": 699700,
      "delivery_cost_kopecks": 245600,
      "customs_fee_kopecks": 15000,
      "track_number": null,
      "created_at": "2026-02-17T10:30:00Z",
      "updated_at": "2026-02-17T10:30:00Z"
    }
  ],
  "total": 42,
  "page": 1,
  "per_page": 20,
  "pages": 3
}
```

---

### GET /admin/orders/{order_id} — Карточка заказа

Ответ (200):
```json
{
  "id": "a1676a0c-...",
  "external_order_id": "SHOP-ORD-12345",
  "shop_name": "IKEA-39 Тест",
  "status": "received_warehouse",
  "recipient_name": "Иванов Пётр Сергеевич",
  "recipient_phone": "+79261234567",
  "recipient_email": "ivanov@mail.ru",
  "recipient_address": "Москва, ул. Ленина, д. 1, кв. 5",
  "recipient_postal_code": "101000",
  "items": [
    {"name": "KALLAX Стеллаж", "sku": "KLX-7777-W", "quantity": 1, "price_kopecks": 499900, "weight_grams": 12000}
  ],
  "total_amount_kopecks": 499900,
  "total_weight_grams": 12000,
  "delivery_cost_kopecks": 245600,
  "customs_fee_kopecks": 15000,
  "track_number": null,
  "batch_id": null,
  "created_at": "2026-02-17T10:30:00Z",
  "updated_at": "2026-02-17T10:30:00Z",
  "history": [
    {"old_status": null, "new_status": "accepted", "comment": null, "created_at": "..."},
    {"old_status": "accepted", "new_status": "awaiting_pickup", "comment": "Курьер назначен", "created_at": "..."}
  ]
}
```

---

### PATCH /admin/orders/{order_id}/status — Смена статуса

Запрос:
```json
{
  "status": "awaiting_pickup",
  "comment": "Курьер назначен на завтра"
}
```

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| status | string | ✅ | Новый статус (см. DATABASE.md → Статусная машина) |
| comment | string | ❌ | Комментарий к смене статуса |

Ответ (200): `OrderResponse`

Ошибки:
- `400 Bad Request` — недопустимый переход статуса
- `404 Not Found` — заказ не найден

---

### GET /admin/batches — Список партий

Query: `page`, `per_page`

Ответ (200):
```json
{
  "items": [
    {
      "id": "...",
      "number": "B-20260217-001",
      "status": "forming",
      "orders_count": 5,
      "total_weight_grams": 45000,
      "created_at": "2026-02-17T10:30:00Z",
      "customs_presented_at": null,
      "customs_cleared_at": null,
      "shipped_at": null
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 20,
  "pages": 1
}
```

---

### POST /admin/batches — Создание партии

Запрос:
```json
{
  "order_ids": ["a1676a0c-...", "b2787b1d-...", "c3898c2e-..."]
}
```

Ответ (201): `BatchResponse`

---

### CRUD /admin/shops — Управление магазинами

| Метод | URL | Описание |
|-------|-----|----------|
| GET | /admin/shops | Список магазинов (page, per_page) |
| GET | /admin/shops/{id} | Карточка магазина |
| POST | /admin/shops | Создание магазина |
| PATCH | /admin/shops/{id} | Обновление магазина |

**POST /admin/shops** — запрос:
```json
{
  "name": "IKEA-39",
  "domain": "ikea-39.ru",
  "webhook_url": "https://ikea-39.ru/api/ostrov-webhook",
  "customs_fee_kopecks": 15000,
  "sender_postal_code": "238311"
}
```

Ответ включает сгенерированный `api_key` — **показывается один раз**.

---

## Коды ошибок

| Код | Описание |
|-----|----------|
| 400 | Некорректный запрос (валидация, недопустимый переход статуса) |
| 401 | Не авторизован (нет/невалидный JWT или API-ключ) |
| 403 | Запрещено (нет доступа к ресурсу) |
| 404 | Ресурс не найден |
| 409 | Конфликт (дубликат external_order_id) |
| 422 | Ошибка валидации Pydantic |
| 500 | Внутренняя ошибка |

Формат ошибок:
```json
{
  "detail": "Описание ошибки"
}
```

---

### GET /admin/health — Статус системы

Ответ (200):
```json
{
  "version": "0.2.1",
  "uptime_seconds": 3600,
  "services": [
    {"name": "PostgreSQL / SQLite", "status": "ok", "latency_ms": 3},
    {"name": "Redis", "status": "ok", "latency_ms": 6},
    {"name": "Почта России API", "status": "ok", "latency_ms": 450}
  ],
  "stats": {
    "orders_total": 10, "orders_today": 0,
    "shops_total": 4, "batches_total": 0
  }
}
```

### GET /admin/health/server — Метрики VPS

```json
{
  "ram_total_mb": 1968, "ram_used_mb": 700, "ram_available_mb": 1268,
  "ram_used_pct": 35.6,
  "load_1m": 0.14, "load_5m": 0.23, "load_15m": 0.29, "cpu_count": 1,
  "disk_total_gb": 29.0, "disk_used_gb": 5.0, "disk_free_gb": 24.0, "disk_used_pct": 18.0,
  "process_pid": 8, "process_ram_mb": 95.4, "process_ram_pct": 4.85
}
```

### POST /admin/health/run-tests — Системные тесты

Запускает 5 тестов: БД, Redis SET/GET, Почта public, Почта contract, JWT.

Ответ (200):
```json
{
  "results": [
    {"name": "БД: чтение запросов", "status": "pass", "detail": "SELECT 1+1 выполнен успешно", "duration_ms": 1},
    {"name": "Redis: запись и чтение", "status": "pass", "detail": "SET/GET/DEL прошли успешно", "duration_ms": 3},
    {"name": "Почта: тарификатор (публичный)", "status": "pass", "detail": "Тариф 238311→101000 500г: 158.00 ₽", "duration_ms": 320},
    {"name": "Почта: тарификатор (контрактный)", "status": "pass", "detail": "Контрактный тариф ...", "duration_ms": 410},
    {"name": "JWT авторизация", "status": "pass", "detail": "Оператор: Администратор (admin)", "duration_ms": 0}
  ],
  "passed": 5, "failed": 0, "total": 5
}
```

---

## Таможенные декларации (ДТЭГ)

### GET /admin/customs/declarations — Список деклараций

Query: `page`, `per_page`, `status`

Ответ (200):
```json
{
  "items": [
    {
      "id": "uuid",
      "number": "DTEG-20260304-151234",
      "status": "draft",
      "orders_count": 5,
      "items_count": 12,
      "total_weight_grams": 15000,
      "total_value_kopecks": 750000,
      "total_value_usd_cents": 8108,
      "sender_name": "ООО Остров Везения",
      "sender_address": "...",
      "sender_inn": "3900000000",
      "customs_rep_name": null,
      "customs_rep_certificate": null,
      "goods_location": "Калининград, ул. ...",
      "fts_reference": null,
      "created_at": "...",
      "updated_at": "..."
    }
  ],
  "total": 1, "page": 1, "per_page": 20, "pages": 1
}
```

---

### POST /admin/customs/declarations — Создание декларации

Запрос:
```json
{
  "order_ids": ["uuid1", "uuid2", "uuid3"],
  "goods_location": "Калининград, ул. ...",
  "operator_note": "Примечание"
}
```

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| order_ids | UUID[] | ✅ | Заказы для включения (макс. 500) |
| goods_location | string | ❌ | Переопределяет значение из company_settings |
| operator_note | string | ❌ | Примечание |

Ответ (201): `CustomsDeclarationResponse`

Ошибки:
- `400` — заказ уже в другой декларации / не найден / > 500 заказов

---

### GET /admin/customs/declarations/{id} — Детальная декларация

Ответ включает `orders[]` с `items[]` и флагом `customs_ready`:

```json
{
  "...все поля CustomsDeclarationResponse...",
  "orders": [
    {
      "id": "uuid",
      "external_order_id": "SHOP-123",
      "recipient_name": "Иванов",
      "recipient_address": "...",
      "recipient_postal_code": "101000",
      "items": [
        {"name": "Товар", "tn_ved_code": "6403", "country_of_origin": "CN", "brand": "Nike", "quantity": 1, "price_kopecks": 150000, "weight_grams": 800}
      ],
      "total_amount_kopecks": 150000,
      "total_weight_grams": 800,
      "customs_ready": true
    }
  ]
}
```

---

### PATCH /admin/customs/declarations/{id}/status — Смена статуса

Запрос:
```json
{
  "status": "ready",
  "fts_reference": "10002000/040325/0012345"
}
```

Допустимые переходы: `draft→ready`, `ready→draft|submitted`, `submitted→accepted|rejected`, `rejected→draft`

---

### POST /admin/customs/declarations/{id}/validate — Проверка готовности

Ответ:
```json
{
  "valid": false,
  "errors": ["Заказ SHOP-123, товар 1 «Кроссовки»: нет кода ТН ВЭД"]
}
```

---

### DELETE /admin/customs/declarations/{id} — Удаление черновика

Только для `status=draft`. Снимает привязку заказов.

---

### GET /admin/customs/declarations/{id}/export/csv — Экспорт CSV

Возвращает CSV-файл (UTF-8 с BOM, разделитель `;`) для таможенного ПО.

### GET /admin/customs/declarations/{id}/export/pdf — Экспорт PDF

Возвращает PDF с формой ДТЭГ (шрифт DejaVuSans для кириллицы).

---

### PATCH /admin/customs/orders/{order_id}/items — Обновление таможенных полей товаров

Запрос:
```json
{
  "updates": [
    {"item_index": 0, "tn_ved_code": "6403", "country_of_origin": "CN", "brand": "Nike"},
    {"item_index": 1, "tn_ved_code": "6404", "country_of_origin": "TR"}
  ]
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| item_index | int ≥ 0 | Индекс товара в массиве items |
| tn_ved_code | string (≤10) | Код ТН ВЭД (допускается пустой) |
| country_of_origin | string (≤2) | ISO alpha-2 код страны (допускается пустой) |
| brand | string \| null | Торговая марка |

---

### GET/PATCH /admin/company/settings — Настройки компании

GET возвращает текущие настройки, PATCH обновляет:

```json
{
  "company_name": "ООО Остров Везения",
  "company_address": "...",
  "company_inn": "3900000000",
  "company_kpp": "390001001",
  "company_postal_code": "238311",
  "company_phone": "+7...",
  "customs_rep_name": "...",
  "customs_rep_certificate": "...",
  "customs_rep_inn": "...",
  "goods_location": "...",
  "usd_rate_kopecks": 9250
}
```

---

## Webhook (исходящий) — 📋 В разработке

При смене статуса заказа → POST на `webhook_url` магазина:

```
POST https://ikea-39.ru/api/ostrov-webhook
Content-Type: application/json
X-Signature: <HMAC-SHA256(body, api_key)>

{
  "event": "order.status_changed",
  "order_id": "a1676a0c-...",
  "external_order_id": "SHOP-ORD-12345",
  "old_status": "accepted",
  "new_status": "awaiting_pickup",
  "track_number": null,
  "timestamp": "2026-02-17T14:00:00Z"
}
```

Магазин верифицирует подпись:
```python
import hmac, hashlib
expected = hmac.new(api_key.encode(), body, hashlib.sha256).hexdigest()
assert expected == request.headers["X-Signature"]
```

---

## Справочник ТН ВЭД

### GET /admin/tnved/search — Поиск кодов ТН ВЭД

Query-параметры:

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|-------------|----------|
| q | string | — | Поисковый запрос (по коду или наименованию) |
| limit | int | 20 | Максимальное количество результатов |

Ответ (200):
```json
[
  {"code": "6403990000", "name": "Обувь на подошве из резины/пластмассы, прочая", "level": 10, "parent_code": "6403990000", "unit": "пар"},
  {"code": "6404110000", "name": "Спортивная обувь с подошвой из резины", "level": 10, "parent_code": "6404110000", "unit": "пар"}
]
```

---

### GET /admin/tnved/{code} — Детали кода ТН ВЭД

Возвращает код с полной иерархией (родительские коды).

Ответ (200):
```json
{
  "code": "6403990000",
  "name": "Обувь на подошве из резины/пластмассы, прочая",
  "level": 10,
  "parent_code": "640399",
  "unit": "пар",
  "note": null,
  "hierarchy": [
    {"code": "64", "name": "Обувь, гетры и аналогичные изделия", "level": 2},
    {"code": "6403", "name": "Обувь на подошве из резины, пластмассы, кожи", "level": 4},
    {"code": "640399", "name": "Прочая", "level": 6}
  ]
}
```

---

## Обновление курсов валют

### POST /admin/company/settings/update-rates — Обновить курсы из ЦБ РФ

Загружает актуальные курсы EUR и USD из API ЦБ РФ (`cbr-xml-daily.ru`) и сохраняет в `company_settings`.

Ответ (200):
```json
{
  "usd_rate_kopecks": 9250,
  "eur_rate_kopecks": 10500,
  "rates_updated_at": "2026-03-05T12:00:00Z"
}
```
