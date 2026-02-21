# Архитектура системы

## Обзор

**Остров Везения** — сервис таможенного оформления и доставки для калининградских интернет-магазинов.

Заказчик — таможенный брокер в Калининграде. Бизнес-процесс:

```
Магазин ставит модуль → Покупатель видит доставку в checkout →
Заказ уходит к брокеру → Таможенное оформление → Почта России → Покупатель
```

---

## Стек технологий

| Компонент | Технология | Версия |
|-----------|-----------|--------|
| Backend API | Python + FastAPI (async) | 3.12 |
| ORM | SQLAlchemy (async) | 2.0 |
| БД (dev) | SQLite + aiosqlite | — |
| БД (prod) | PostgreSQL + asyncpg | 16 |
| Миграции | Alembic | — |
| Фоновые задачи | Celery + Redis | — |
| Админ-панель | Vue 3 + TypeScript + Vite | — |
| CSS | Tailwind CSS | v4 |
| State management | Pinia | — |
| HTTP (frontend) | Axios | — |
| HTTP (backend) | httpx (async) | — |
| Авторизация | JWT (админка), API-ключи (магазины) | — |
| Хеширование | bcrypt (пароли), SHA256 (API-ключи), HMAC-SHA256 (webhook) | — |
| Плагин магазина | React/TypeScript npm-пакет (Next.js) | — |
| Деплой | Docker Compose + Nginx + Let's Encrypt | — |

---

## Компоненты системы

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Интернет-магазин │────▶│   Backend API    │◀────│  Админ-панель   │
│  (Next.js плагин)│     │   (FastAPI)      │     │  (Vue.js SPA)   │
└─────────────────┘     └────────┬─────────┘     └─────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
               ┌────▼───┐  ┌────▼───┐  ┌────▼────┐
               │ Почта  │  │   БД   │  │  Redis  │
               │ России │  │ Postgres│  │ (Celery)│
               │  API   │  │        │  │         │
               └────────┘  └────────┘  └─────────┘
```

### Backend API (FastAPI)

Точка входа: `backend/app/main.py`

```
app/
├── main.py                     # FastAPI app, lifespan, CORS, static files
├── core/
│   ├── config.py               # Pydantic Settings (из .env)
│   ├── database.py             # async engine + session factory
│   ├── security.py             # JWT encode/decode, bcrypt, API key verify, HMAC
│   └── dependencies.py         # get_db, get_current_operator, get_shop_by_api_key
├── models/                     # SQLAlchemy ORM модели
│   ├── shop.py                 # Магазин (api_key, domain, customs_fee)
│   ├── order.py                # Заказ (items JSONB, status, recipient_*)
│   ├── order_status_history.py # История смен статуса
│   ├── batch.py                # Партия заказов
│   └── operator.py             # Оператор админки (admin/operator роли)
├── schemas/                    # Pydantic request/response модели
│   ├── order.py                # OrderCreate, OrderResponse, OrderDetailResponse, etc.
│   ├── delivery.py             # DeliveryCalcRequest/Response
│   ├── shop.py                 # ShopCreate, ShopResponse
│   ├── auth.py                 # LoginRequest, TokenResponse
│   └── batch.py                # BatchCreate, BatchResponse
├── api/v1/
│   ├── router.py               # Агрегирует все роутеры
│   ├── delivery.py             # POST /delivery/calculate
│   ├── orders.py               # Для магазинов: создание, статус, трекинг
│   ├── tracking.py             # GET /track/{track_number} (публичный трекинг)
│   ├── auth.py                 # POST /auth/login (rate limit 10/min)
│   ├── admin_orders.py         # Список, карточка, смена статуса
│   ├── admin_batches.py        # Создание и список партий
│   ├── admin_shops.py          # CRUD магазинов
│   ├── admin_groups.py         # Группы отправок + настройки оптимизатора
│   ├── admin_pochta.py         # Тест-интерфейс к API Почты России (тарифы, адреса, ФИО, телефон)
│   └── admin_health.py         # GET /health, GET /health/server, POST /health/run-tests
├── core/
│   ├── config.py               # Pydantic Settings (из .env); CORS_ORIGINS_STR; JWT fail-fast validator
│   ├── database.py             # async engine + session factory
│   ├── security.py             # JWT encode/decode, bcrypt, API key verify, HMAC
│   ├── dependencies.py         # get_db, get_current_operator, require_admin, verify_api_key
│   └── limiter.py              # slowapi Limiter с Redis storage + get_real_ip (X-Forwarded-For)
├── services/
│   ├── pochta.py               # PochtaClient — async обёртка API Почты России (возвращает tuple[Result, RawHttpLog])
│   ├── delivery.py             # Расчёт стоимости: тариф Почты + таможня
│   ├── order.py                # Бизнес-логика заказов, валидация переходов
│   ├── grouping_optimizer.py   # Математика оптимизации группировки (score = savings − penalty × wait_hours)
│   ├── hub_router.py           # Маршрутизация по хабам (10 хабов по первым 3 цифрам индекса)
│   └── webhook.py              # Отправка уведомлений магазину
├── workers/
│   ├── celery_app.py           # Celery конфигурация + Beat расписание
│   ├── tasks_webhook.py        # Фоновая задача отправки webhook
│   └── tasks_grouping.py       # Celery задача оптимизатора (каждые 30 мин)
└── scripts/
    └── create_admin.py         # Создание первого админ-пользователя
```

### Админ-панель (Vue.js)

```
admin/src/
├── main.ts                     # Точка входа, Pinia + Router
├── App.vue                     # Корневой компонент
├── env.d.ts                    # declare const __APP_VERSION__: string
├── router/index.ts             # Роуты + guard авторизации
├── stores/auth.ts              # Pinia store: JWT, operator
├── api/
│   ├── client.ts               # Axios instance + interceptors (401 → logout)
│   ├── orders.ts               # fetchOrders, fetchOrder, changeOrderStatus
│   ├── shops.ts                # fetchShops, fetchShop, createShop, updateShop
│   ├── batches.ts              # fetchBatches, createBatch
│   ├── groups.ts               # fetchGroups, updateGroupStatus, fetchSettings, updateSettings
│   ├── pochta.ts               # testTariff, testAddress, testFio, testPhone (с pochta_log)
│   └── health.ts               # fetchHealth, runSystemTests, fetchServerMetrics
├── pages/
│   ├── LoginPage.vue
│   ├── DashboardPage.vue       # Статистика: заказы, магазины, партии
│   ├── OrdersListPage.vue      # Таблица с фильтрами, поиском, пагинацией
│   ├── OrderDetailPage.vue     # Карточка: товары, получатель, стоимость, история, трекинг
│   ├── BatchesListPage.vue
│   ├── ShopsListPage.vue
│   ├── ShopDetailPage.vue
│   ├── GroupsPage.vue          # Группы отправок + настройки оптимизатора
│   ├── PochtaTestPage.vue      # Тест-интерфейс API Почты (тарифы, адреса, ФИО, телефон)
│   └── SystemHealthPage.vue    # Здоровье системы: сервисы, метрики сервера, системные тесты
├── components/
│   ├── Sidebar.vue             # Навигация + версия приложения (v0.2.0)
│   ├── ApiDebugPanel.vue       # Дебаг-панель HTTP-логов (браузер↔backend, backend↔Почта)
│   ├── OrderStatusBadge.vue    # Цветные бейджи статусов
│   ├── ChangeStatusModal.vue   # Модалка смены статуса с валидацией
│   └── Pagination.vue
├── layouts/
│   └── DefaultLayout.vue       # Sidebar + content area
└── types/index.ts              # TypeScript интерфейсы, STATUS_LABELS, ALLOWED_TRANSITIONS
```

### Эмулятор магазина

`backend/static/shop-emulator.html` — standalone HTML/JS приложение для тестирования API.

Доступен по адресу `http://localhost:8000/shop`.

Функции:
- Каталог товаров IKEA (12 позиций с SKU)
- Корзина с подсчётом
- Расчёт доставки через API Почты России
- Оформление заказа
- Трекинг заказа по ID
- Список заказов

---

## Авторизация

### Магазины → API (X-API-Key)
```
Запрос: X-API-Key: <sha256-hex>
Проверка: dependencies.py → get_shop_by_api_key() → SHA256 hash lookup в shops
```

### Админка → API (JWT Bearer)
```
POST /api/v1/auth/login { email, password }
→ bcrypt.verify(password, hash)
→ JWT { sub: operator_id, role, exp }

Все admin/* эндпоинты: Authorization: Bearer <jwt>
→ dependencies.py → get_current_operator()
```

### Webhook (HMAC-SHA256)
```
При смене статуса → POST webhook_url
Headers: X-Signature: HMAC-SHA256(body, api_key)
Магазин верифицирует подпись
```

---

## Потоки данных

### 1. Расчёт доставки
```
Магазин → POST /delivery/calculate { postal_code, weight, amount }
         → PochtaClient.calculate_tariff() → Pochta API (tariff.pochta.ru)
         → + customs_fee из настроек магазина
         → { delivery_cost, customs_fee, total, days_min, days_max }
```

### 2. Создание заказа
```
Магазин → POST /orders { external_order_id, recipient, items }
         → Валидация данных
         → Расчёт delivery_cost + customs_fee
         → Сохранение в БД (status: accepted)
         → Запись в order_status_history
         → { id, status, costs }
```

### 3. Обработка заказа (админка)
```
Оператор → Список заказов → Открыть карточку → Сменить статус
           → PATCH /admin/orders/{id}/status { status, comment }
           → Валидация перехода (ALLOWED_TRANSITIONS)
           → Обновление order.status
           → Запись в order_status_history (changed_by = operator.id)
           → [Будущее] Webhook → магазин
```

### 4. Формирование партии
```
Оператор → Выбрать заказы → Создать партию
           → POST /admin/batches { order_ids }
           → Batch(status: forming, orders_count, total_weight)
           → orders.batch_id = batch.id, orders.status = batch_forming
```

---

## Конфигурация

Все настройки через переменные окружения (`.env`):

| Переменная | Описание | Пример |
|-----------|----------|--------|
| DATABASE_URL | Строка подключения к БД | postgresql+asyncpg://... |
| REDIS_URL | URL Redis (Celery + rate limiter) | redis://redis:6379/0 |
| JWT_SECRET_KEY | Секрет JWT (≥32 символов, fail-fast) | openssl rand -hex 32 |
| JWT_EXPIRE_MINUTES | Время жизни JWT | 60 (1 час) |
| POCHTA_API_TOKEN | Токен API Почты России | NgZG... |
| POCHTA_LOGIN | Логин Почты России | email |
| POCHTA_PASSWORD | Пароль Почты России | password |
| CORS_ORIGINS_STR | Разрешённые origins (через запятую) | https://admin.ostrov-vezeniya.ru |

---

## Локальная разработка

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -e .
cp ../.env.example ../.env  # заполнить секреты
python init_db.py            # создать таблицы + admin user
uvicorn app.main:app --reload --port 8000

# Админка
cd admin
npm install
npm run dev                  # http://localhost:3000 (proxy → 8000)

# Эмулятор магазина
open http://localhost:8000/shop
```

---

## Production деплой

См. [DEPLOY.md](DEPLOY.md)

```
Docker Compose:
  backend   → FastAPI (uvicorn, port 8000)
  db        → PostgreSQL 16
  redis     → Redis 7
  worker    → Celery worker
  nginx     → Reverse proxy + SSL + static admin

Домены:
  api.ostrov-vezeniya.ru   → backend
  admin.ostrov-vezeniya.ru → admin SPA
```
