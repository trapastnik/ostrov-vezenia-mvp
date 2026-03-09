# Security & Efficiency Audit — План работ

**Дата:** 2026-03-09
**Статус:** В работе

---

## Фаза 1 — CRITICAL (немедленно)

### 1.1 ~~Удалить .env из git-истории~~
> Требует ручного запуска `git filter-repo` — делаем в конце, чтобы не сломать текущую работу.
> **Действие:** добавить `.env` в `.gitignore` (если не добавлен), создать `.env.example`.

### 1.2 [x] Аутентификация на трекинг-эндпоинтах
- **Файл:** `backend/app/api/v1/tracking.py`
- **Проблема:** `/track/search/{query}` и `/track/{track_number}` — полностью публичные, раскрывают ПД
- **Решение:** Добавить `verify_api_key` — магазин видит только свои заказы

### 1.3 [x] Валидация webhook_url (защита от SSRF)
- **Файл:** `backend/app/schemas/shop.py`
- **Проблема:** Принимается любой URL, включая `http://localhost`, `http://169.254.169.254`
- **Решение:** Pydantic `HttpUrl` + запрет внутренних IP/localhost

### 1.4 [x] CSV-injection в экспорте ДТЭГ
- **Файл:** `backend/app/services/customs_export.py`
- **Проблема:** `item["name"]` пишется в CSV без экранирования — формула `=cmd()` исполнится в Excel
- **Решение:** Префикс `'` для ячеек, начинающихся с `=`, `+`, `-`, `@`, `\t`, `\r`

### 1.5 [x] Предсказуемые номера ДТЭГ и партий
- **Файл:** `backend/app/services/customs_declaration.py:45-47`, `backend/app/api/v1/admin_batches.py:31-35`
- **Проблема:** Номера основаны только на timestamp + слабый random
- **Решение:** Добавить `secrets.token_hex(4)` к номерам

---

## Фаза 2 — HIGH (эта неделя)

### 2.1 [x] Убрать API-ключи из ответов списка магазинов
- **Файл:** `backend/app/schemas/shop.py`, `backend/app/api/v1/admin_shops.py`
- **Проблема:** `ShopResponse` содержит `api_key` — утечка при перехвате
- **Решение:** Убрать `api_key` из `ShopResponse`, показывать только при создании

### 2.2 [x] Race condition при смене статуса (FOR UPDATE)
- **Файл:** `backend/app/services/order.py:83-84`, `backend/app/services/customs_declaration.py:173`
- **Проблема:** Два запроса одновременно могут сменить статус
- **Решение:** `select(...).with_for_update()` для блокировки строки

### 2.3 [x] CSP + HSTS заголовки в nginx
- **Файл:** `nginx/nginx.conf`, `nginx/prod.conf`
- **Проблема:** Нет Content-Security-Policy и Strict-Transport-Security
- **Решение:** Добавить заголовки безопасности

### 2.4 [x] Celery: timeout + exponential backoff + разделение ретраев
- **Файл:** `backend/app/workers/tasks_webhook.py`, `backend/app/workers/celery_app.py`
- **Проблема:** Нет timeout, фиксированный retry=60s, ретрай 4xx ошибок
- **Решение:** `time_limit`, `soft_time_limit`, backoff, не ретраить 4xx

### 2.5 [x] Настройка пула соединений БД
- **Файл:** `backend/app/core/database.py`
- **Проблема:** Default pool (5 connections), нет pool_pre_ping
- **Решение:** Настроить pool_size, max_overflow, pool_pre_ping

### 2.6 [x] Rate limiting на admin-эндпоинты
- **Файл:** `backend/app/api/v1/admin_orders.py`, `admin_batches.py`, etc.
- **Проблема:** Rate limit только на `/auth/login`, остальное без ограничений
- **Решение:** Глобальный rate limiter через middleware

---

## Фаза 3 — MEDIUM

### 3.1 [x] Шифрование паспортных данных в БД
- **Файлы:** `backend/app/core/encryption.py` (новый), `backend/app/models/order.py`, `backend/app/core/config.py`
- **Решение:** Fernet (AES-128-CBC + HMAC-SHA256) через `EncryptedString` TypeDecorator. Ключ из `PII_ENCRYPTION_KEY` в `.env`. Graceful degradation — без ключа данные хранятся открыто. Обратная совместимость с legacy данными.

### 3.2 [x] Маскировка паспортов в API-ответах
- **Файл:** `backend/app/schemas/order.py`
- **Решение:** `_mask_passport()` + `@model_validator(mode="after")` на `OrderResponse` и `OrderDetailResponse`. `1234` → `**34`, `567890` → `****90`.

### 3.3 [ ] Хеширование API-ключей магазинов (bcrypt)
> **Отложено** — требует Alembic миграции (3.4) для изменения схемы столбца `api_key` и перехода на хеш-сравнение.

### 3.4 [ ] Alembic вместо create_all + ALTER
> **Отложено** — крупная инфраструктурная задача, требует отдельного спринта.

### 3.5 [x] Аудит-лог действий администраторов
- **Файлы:** `backend/app/models/audit_log.py` (новый), `backend/app/services/audit.py` (новый), `backend/app/api/v1/admin_orders.py`, `backend/app/api/v1/admin_shops.py`
- **Решение:** Модель `AuditLog` (operator_id, action, resource_type, resource_id, details JSON, ip_address). `log_action()` пишет в ту же транзакцию. Подключен к CRUD магазинов и смене статусов заказов.

### 3.6 [ ] JWT → httpOnly cookies
> **Отложено** — требует изменений на фронтенде (удаление localStorage, обработка cookies), отдельный спринт.

### 3.7 [x] Механизм ротации API-ключей
- **Файл:** `backend/app/api/v1/admin_shops.py`
- **Решение:** Эндпоинт `POST /admin/shops/{shop_id}/rotate-key`. Генерирует новый ключ, пишет аудит-лог, возвращает `ShopCreateResponse` (ключ показывается один раз).

### 3.8 [x] CHECK constraints на статусы в БД
- **Файлы:** `backend/app/models/order.py`, `batch.py`, `customs_declaration.py`, `shipment_group.py`
- **Решение:** `CheckConstraint` на поле `status` для всех моделей — Orders (12 статусов), Batches (4), CustomsDeclarations (5), ShipmentGroups (6). Гарантирует целостность на уровне БД.

### 3.9 [x] Индекс на shop_id в orders
- **Файл:** `backend/app/models/order.py`
- **Решение:** `Index("ix_orders_shop_id", "shop_id")` в `__table_args__`.

### 3.10 [x] Кеширование курсов ЦБ РФ (Redis)
- **Файл:** `backend/app/services/cbr_rates.py`
- **Решение:** Redis кеш с TTL 1 час (`cbr:rates:daily` ключ). Graceful degradation — при недоступности Redis идёт напрямую в ЦБ.

### 3.11 [x] Экранирование HTML в PDF (operator_note)
- **Файл:** `backend/app/services/customs_export.py`
- **Решение:** `_esc()` helper через `html.escape()`. Применён ко всем пользовательским данным в ReportLab `Paragraph()`.

---

## Прогресс

| Фаза | Задач | Сделано | Статус |
|-------|-------|---------|--------|
| 1. Critical | 5 | 4 | ✅ Done (1.1 — вручную) |
| 2. High | 6 | 6 | ✅ Done |
| 3. Medium | 11 | 8 | ✅ Done (3 отложены) |

### Отложенные задачи (отдельный спринт)
- **3.3** Хеширование API-ключей — зависит от 3.4
- **3.4** Alembic миграции — крупная инфраструктурная задача
- **3.6** JWT → httpOnly cookies — требует изменений фронтенда
