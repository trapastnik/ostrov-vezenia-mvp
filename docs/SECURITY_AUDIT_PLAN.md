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

## Фаза 3 — MEDIUM (следующий спринт)

### 3.1 [ ] Шифрование паспортных данных в БД
### 3.2 [ ] Маскировка паспортов в API-ответах
### 3.3 [ ] Хеширование API-ключей магазинов (bcrypt)
### 3.4 [ ] Alembic вместо create_all + ALTER
### 3.5 [ ] Аудит-лог действий администраторов
### 3.6 [ ] JWT → httpOnly cookies
### 3.7 [ ] Механизм ротации API-ключей
### 3.8 [ ] CHECK constraints на статусы в БД
### 3.9 [ ] Индекс на shop_id в orders
### 3.10 [ ] Кеширование курсов ЦБ РФ (Redis)
### 3.11 [ ] Экранирование HTML в PDF (operator_note)

---

## Прогресс

| Фаза | Задач | Сделано | Статус |
|-------|-------|---------|--------|
| 1. Critical | 5 | 4 | Done (1.1 — вручную) |
| 2. High | 6 | 6 | Done |
| 3. Medium | 11 | 0 | Следующий спринт |
