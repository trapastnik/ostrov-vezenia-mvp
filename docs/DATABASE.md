# Схема базы данных

ORM: SQLAlchemy 2.0 (async)
Dev: SQLite + aiosqlite
Prod: PostgreSQL 16 + asyncpg
Миграции: Alembic (пока через `init_db.py` → `create_all`)

---

## ER-диаграмма

```
┌───────────┐       ┌────────────┐       ┌──────────────────────┐
│  shops    │ 1───N │  orders    │ 1───N │ order_status_history │
│           │       │            │       │                      │
│ id (PK)   │       │ id (PK)    │       │ id (PK)              │
│ name      │       │ shop_id(FK)│       │ order_id (FK)        │
│ domain    │       │ batch_id   │───┐   │ old_status           │
│ api_key   │       │ status     │   │   │ new_status           │
│ webhook_url│      │ items(JSON)│   │   │ comment              │
│ customs_fee│      │ customs_   │──┐│   │ changed_by (FK)──────┤──┐
└───────────┘       │ decl_id   │  ││   │ created_at           │  │
                    └────────────┘  ││   └──────────────────────┘  │
                                    ││                              │
                    ┌────────────┐  ││   ┌──────────────┐          │
                    │  batches   │◀─┘│   │  operators   │◀─────────┘
                    │ id (PK)    │   │   │ id (PK)      │
                    │ number     │   │   │ name         │
                    │ status     │   │   │ email        │
                    │ orders_cnt │   │   │ password_hash│
                    │ total_wt   │   │   │ role         │
                    └────────────┘   │   └──────────────┘
                                     │
           ┌─────────────────────┐   │   ┌──────────────────┐
           │ customs_declarations│◀──┘   │ company_settings │
           │                     │       │                  │
           │ id (PK)             │       │ id (PK)          │
           │ number (UNIQUE)     │       │ scope (UNIQUE)   │
           │ status              │       │ company_name     │
           │ orders_count        │       │ company_inn      │
           │ items_count         │       │ customs_rep_name │
           │ total_weight_grams  │       │ usd_rate_kopecks │
           │ total_value_kopecks │       └──────────────────┘
           │ sender_name         │
           │ fts_reference       │
           └─────────────────────┘
```

---

## Таблицы

### shops — Магазины

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| id | UUID | PK | |
| name | VARCHAR(255) | NOT NULL | Название магазина |
| domain | VARCHAR(255) | UNIQUE, NOT NULL | Домен (ikea-39.ru) |
| api_key | VARCHAR(64) | UNIQUE, NOT NULL | SHA256 hex для авторизации |
| webhook_url | VARCHAR(512) | NULL | URL для webhook-уведомлений |
| customs_fee_kopecks | INTEGER | NOT NULL, default 15000 | Стоимость таможенного оформления (150 руб) |
| sender_postal_code | VARCHAR(6) | NOT NULL, default '238311' | Индекс склада отправки (Калининград) |
| is_active | BOOLEAN | NOT NULL, default true | Активен ли магазин |
| created_at | TIMESTAMP TZ | NOT NULL | |
| updated_at | TIMESTAMP TZ | NOT NULL | |

---

### orders — Заказы

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| id | UUID | PK | |
| shop_id | UUID | FK shops.id, NOT NULL | Магазин |
| external_order_id | VARCHAR(100) | NOT NULL | ID заказа в системе магазина |
| status | VARCHAR(30) | NOT NULL, default 'accepted' | Текущий статус |
| recipient_name | VARCHAR(255) | NOT NULL | ФИО получателя |
| recipient_phone | VARCHAR(20) | NOT NULL | Телефон |
| recipient_email | VARCHAR(255) | NULL | Email |
| recipient_address | TEXT | NOT NULL | Полный адрес |
| recipient_postal_code | VARCHAR(6) | NOT NULL | Почтовый индекс |
| items | JSON/JSONB | NOT NULL | Массив товаров (см. ниже) |
| total_amount_kopecks | INTEGER | NOT NULL | Сумма товаров |
| total_weight_grams | INTEGER | NOT NULL | Общий вес |
| delivery_cost_kopecks | INTEGER | NOT NULL | Стоимость доставки |
| customs_fee_kopecks | INTEGER | NOT NULL | Стоимость таможни |
| track_number | VARCHAR(30) | NULL | Трек-номер Почты России |
| internal_track_number | VARCHAR(30) | NULL, INDEX | Внутренний трек OV-XXXXXX |
| batch_id | UUID | FK batches.id, NULL | Партия |
| shipment_group_id | UUID | FK shipment_groups.id, NULL | Группа отправки |
| customs_declaration_id | UUID | FK customs_declarations.id, NULL | ПТД-ЭГ декларация |
| public_tariff_kopecks | INTEGER | NULL | Публичный тариф |
| contract_tariff_kopecks | INTEGER | NULL | Контрактный тариф |
| tariff_savings_kopecks | INTEGER | NULL | Экономия |
| tariff_savings_percent | FLOAT | NULL | % экономии |
| created_at | TIMESTAMP TZ | NOT NULL | |
| updated_at | TIMESTAMP TZ | NOT NULL | |

**Constraints:**
- `UNIQUE(shop_id, external_order_id)` — один заказ на магазин

**Индексы:**
- `ix_orders_status` — фильтр по статусу
- `ix_orders_batch_id` — заказы в партии
- `ix_orders_created_at` — сортировка
- `ix_orders_customs_declaration_id` — заказы в декларации

**Формат items (JSON):**
```json
[
  {
    "name": "KALLAX Стеллаж",
    "sku": "KLX-7777-W",
    "quantity": 1,
    "price_kopecks": 499900,
    "weight_grams": 12000,
    "tn_ved_code": "9403",
    "country_of_origin": "CN",
    "brand": "IKEA"
  }
]
```

Поля `tn_ved_code`, `country_of_origin`, `brand` добавляются при заполнении таможенных данных через ПТД-ЭГ.

---

### order_status_history — История смен статуса

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| id | UUID | PK | |
| order_id | UUID | FK orders.id, NOT NULL | Заказ |
| old_status | VARCHAR(30) | NULL | Предыдущий статус (null при создании) |
| new_status | VARCHAR(30) | NOT NULL | Новый статус |
| comment | TEXT | NULL | Комментарий оператора |
| changed_by | UUID | FK operators.id, NULL | Кто сменил (null = система) |
| created_at | TIMESTAMP TZ | NOT NULL | |

**Индексы:**
- `ix_history_order_created` — (order_id, created_at) для быстрой выборки истории

---

### batches — Партии

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| id | UUID | PK | |
| number | VARCHAR(20) | UNIQUE, NOT NULL | Номер партии (B-20260217-001) |
| status | VARCHAR(30) | NOT NULL, default 'forming' | Статус партии |
| orders_count | INTEGER | NOT NULL, default 0 | Количество заказов |
| total_weight_grams | INTEGER | NOT NULL, default 0 | Общий вес |
| customs_presented_at | TIMESTAMP TZ | NULL | Дата подачи на таможню |
| customs_cleared_at | TIMESTAMP TZ | NULL | Дата растаможки |
| shipped_at | TIMESTAMP TZ | NULL | Дата передачи перевозчику |
| created_at | TIMESTAMP TZ | NOT NULL | |
| updated_at | TIMESTAMP TZ | NOT NULL | |

**Статусы партии:** `forming` → `customs_presented` → `customs_cleared` → `shipped`

---

### operators — Операторы (пользователи админки)

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| id | UUID | PK | |
| name | VARCHAR(255) | NOT NULL | Имя |
| email | VARCHAR(255) | UNIQUE, NOT NULL | Email (логин) |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt hash |
| role | VARCHAR(20) | NOT NULL, default 'operator' | admin / operator |
| is_active | BOOLEAN | NOT NULL, default true | |
| created_at | TIMESTAMP TZ | NOT NULL | |
| updated_at | TIMESTAMP TZ | NOT NULL | |

---

### customs_declarations — Таможенные декларации (ПТД-ЭГ)

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| id | UUID | PK | |
| number | VARCHAR(30) | UNIQUE, NOT NULL | Номер (PTD-YYYYMMDD-HHMMSS) |
| status | VARCHAR(30) | NOT NULL, default 'draft' | draft / ready / submitted / accepted / rejected |
| orders_count | INTEGER | NOT NULL | Количество заказов |
| items_count | INTEGER | NOT NULL | Количество товарных позиций |
| total_weight_grams | INTEGER | NOT NULL | Общий вес |
| total_value_kopecks | INTEGER | NOT NULL | Стоимость (руб) |
| total_value_usd_cents | INTEGER | NOT NULL | Стоимость (USD) |
| goods_location | VARCHAR(500) | NULL | Место нахождения товаров |
| sender_name | VARCHAR(255) | NOT NULL | Снапшот: название компании |
| sender_address | TEXT | NOT NULL | Снапшот: адрес компании |
| sender_inn | VARCHAR(12) | NOT NULL | Снапшот: ИНН |
| customs_rep_name | VARCHAR(255) | NULL | Таможенный представитель |
| customs_rep_certificate | VARCHAR(100) | NULL | Свидетельство представителя |
| operator_note | VARCHAR(500) | NULL | Примечание оператора |
| fts_reference | VARCHAR(100) | NULL | Регистрационный номер ФТС |
| submitted_at | TIMESTAMP TZ | NULL | Дата подачи |
| accepted_at | TIMESTAMP TZ | NULL | Дата принятия |
| created_at | TIMESTAMP TZ | NOT NULL | |
| updated_at | TIMESTAMP TZ | NOT NULL | |

**Статусы:** `draft` → `ready` → `submitted` → `accepted` / `rejected` (→ `draft`)

---

### company_settings — Настройки компании (синглтон)

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| id | UUID | PK | |
| scope | VARCHAR(30) | UNIQUE, default 'global' | Всегда 'global' |
| company_name | VARCHAR(255) | NOT NULL | Наименование компании |
| company_address | TEXT | NOT NULL | Адрес |
| company_inn | VARCHAR(12) | NOT NULL | ИНН |
| company_kpp | VARCHAR(9) | NOT NULL | КПП |
| company_postal_code | VARCHAR(6) | NOT NULL, default '238311' | Индекс |
| company_phone | VARCHAR(20) | NOT NULL | Телефон |
| customs_rep_name | VARCHAR(255) | NOT NULL | Таможенный представитель |
| customs_rep_certificate | VARCHAR(100) | NOT NULL | Свидетельство |
| customs_rep_inn | VARCHAR(12) | NOT NULL | ИНН представителя |
| goods_location | VARCHAR(500) | NOT NULL | Место нахождения товаров по умолчанию |
| usd_rate_kopecks | INTEGER | NOT NULL, default 9250 | Курс USD (копеек за 1 USD) |
| created_at | TIMESTAMP TZ | NOT NULL | |
| updated_at | TIMESTAMP TZ | NOT NULL | |

Автоматически создаётся при первом обращении через `get_company_settings()`.

---

## Статусная машина заказа

### Диаграмма переходов

```
                    ┌──────────┐
                    │ accepted │ ─── Заказ принят
                    └────┬─────┘
                         │
                    ┌────▼──────────┐
                    │awaiting_pickup│ ─── Ожидает забора курьером
                    └────┬──────────┘
                         │
                    ┌────▼───────────────┐
                    │ received_warehouse │ ─── Получен на складе
                    └────┬───────────────┘
                         │
                    ┌────▼────────────┐
                    │ batch_forming   │ ─── Формируется партия
                    └────┬────────────┘
                         │
                    ┌────▼──────────────────┐
                    │ customs_presented     │ ─── Подан на таможню
                    └────┬─────────────────┘
                         │
                    ┌────▼──────────────────┐
                    │ customs_cleared       │ ─── Растаможен
                    └────┬─────────────────┘
                         │
                    ┌────▼──────────────────┐
                    │ awaiting_carrier      │ ─── Ожидает перевозчика
                    └────┬─────────────────┘
                         │
                    ┌────▼─────────┐
                    │   shipped    │ ─── Отправлен
                    └────┬─────────┘
                         │
                    ┌────▼──────────┐
                    │  in_transit   │ ─── В пути
                    └────┬──────────┘
                         │
                    ┌────▼──────────┐
                    │  delivered    │ ─── Доставлен ✅
                    └───────────────┘

    Из любого статуса до shipped:
    ──────▶ cancelled (Отменён)

    Из customs_presented и далее:
    ──────▶ problem (Проблема) ──────▶ обратно в любой статус
```

### Допустимые переходы (код)

```typescript
const ALLOWED_TRANSITIONS: Record<string, string[]> = {
  accepted:           ['awaiting_pickup', 'cancelled'],
  awaiting_pickup:    ['received_warehouse', 'cancelled'],
  received_warehouse: ['batch_forming', 'cancelled'],
  batch_forming:      ['customs_presented', 'cancelled'],
  customs_presented:  ['customs_cleared', 'problem', 'cancelled'],
  customs_cleared:    ['awaiting_carrier', 'problem', 'cancelled'],
  awaiting_carrier:   ['shipped', 'problem', 'cancelled'],
  shipped:            ['in_transit', 'problem'],
  in_transit:         ['delivered', 'problem'],
  delivered:          [],
  cancelled:          [],
  problem:            ['accepted', 'awaiting_pickup', 'received_warehouse',
                       'batch_forming', 'customs_presented', 'customs_cleared',
                       'awaiting_carrier', 'shipped', 'in_transit', 'cancelled'],
}
```

### Метки статусов (UI)

| Код | Название | Цвет |
|-----|----------|------|
| accepted | Принят | 🔵 синий |
| awaiting_pickup | Ожидает забора | 🟡 жёлтый |
| received_warehouse | На складе | 🟣 фиолетовый |
| batch_forming | Формирование партии | ⚪ серый |
| customs_presented | На таможне | 🟠 оранжевый |
| customs_cleared | Растаможен | 🟢 зелёный |
| awaiting_carrier | Ожидает отправки | 🟡 жёлтый |
| shipped | Отправлен | 🔵 синий |
| in_transit | В пути | 🔵 синий |
| delivered | Доставлен | 🟢 зелёный |
| cancelled | Отменён | 🔴 красный |
| problem | Проблема | 🔴 красный |

---

## Миграции

**Текущее состояние:** таблицы создаются через `init_db.py` (`Base.metadata.create_all`).

**TODO:** перейти на Alembic autogenerate для production:
```bash
alembic revision --autogenerate -m "initial"
alembic upgrade head
```
