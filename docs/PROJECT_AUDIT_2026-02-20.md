# Комплексный аудит проекта: эффективность, надежность, безопасность

Дата аудита: 20 февраля 2026  
Проект: `ostrov-vezeniya`  
Область: `backend` (FastAPI/Celery), `admin` (Vue), `nginx`, `docker`, `plugins/bitrix`

## 1. Executive Summary

Текущая оценка:

- Безопасность: **низкая** до устранения критичных замечаний (RBAC, обработка ошибок, секреты, edge-конфиг).
- Надежность: **средне-низкая** (частичные коммиты, риск коллизий трек-номеров, широкие `except Exception`).
- Эффективность: **средняя** (есть узкие места в группировщике и batch-обработке).

Ключевой вывод: сначала нужно закрыть контроль доступа и утечки, затем стабилизировать транзакционность и уникальность идентификаторов, после этого оптимизировать throughput.

## 2. Методика и покрытие

Проверено:

- код backend API/сервисов/воркеров/моделей;
- frontend admin (auth/token handling);
- production/development docker и nginx конфигурации;
- Bitrix-плагин интеграции;
- наличие индикаторов техдолга (`except Exception`, TODO/FIXME и т.п.).

Ограничения:

- Автотесты не запускались, т.к. в окружении отсутствует `pytest` (`python3 -m pytest` -> `No module named pytest`).

## 3. Критичные находки (приоритет P0/P1/P2)

## P0

### P0-1: Неполный RBAC на admin endpoints

Риск: любой авторизованный оператор может выполнять admin-операции (просмотр/изменение заказов, партии, группы, вызовы Почты), хотя доступ должен быть ограничен ролью `admin`.

Подтверждение:

- `backend/app/api/v1/admin_orders.py:28`
- `backend/app/api/v1/admin_batches.py:28`
- `backend/app/api/v1/admin_pochta.py:96`
- `backend/app/api/v1/admin_groups.py:86`

Проблема: используется `Depends(get_current_operator)`, но не `Depends(require_admin)`.

Рекомендация:

- заменить dependency на `require_admin` во всех admin-роутах;
- добавить интеграционные тесты на 403 для non-admin роли.

### P0-2: Утечка внутренних ошибок в клиентские ответы

Риск: раскрытие деталей внутренней архитектуры, текстов исключений библиотек/провайдеров, чувствительной operational-информации.

Подтверждение:

- `backend/app/main.py:49` возвращает `{"detail": str(exc)}`
- `backend/app/api/v1/admin_pochta.py:106` и аналогичные блоки: `detail=f"Pochta API error: {e}"`

Рекомендация:

- отдавать клиенту унифицированные безопасные сообщения;
- детальные stack trace/исключения оставлять только в server logs;
- ввести correlation/request id.

## P1

### P1-1: Fallback JWT secret в runtime-конфиге

Риск: при неустановленной переменной окружения сервис стартует с предсказуемым секретом.

Подтверждение:

- `backend/app/core/config.py:8` (`JWT_SECRET_KEY = "dev-secret-change-in-production"`)

Рекомендация:

- убрать insecure default;
- fail-fast при старте, если секрет не задан или слишком слабый;
- в CI добавить check обязательных env для production.

### P1-2: Риск коллизий `internal_track_number` + неустойчивость tracking endpoint

Риск: генерация `OV-YYYYMMDD-XXXXX` может давать дубли, при дублях `scalar_one_or_none()` потенциально вызовет ошибку множества строк.

Подтверждение:

- `backend/app/models/order.py:54` (индекс есть, уникальности нет)
- `backend/app/services/grouping_optimizer.py:258` (случайный 5-значный суффикс)
- `backend/app/api/v1/tracking.py:37` (`scalar_one_or_none`)

Рекомендация:

- ввести `UNIQUE` на `internal_track_number` (с учетом nullable);
- генерировать collision-safe номер (retry loop + проверка уникальности или UUID-based scheme);
- обновить endpoint на детерминированную обработку ошибок.

### P1-3: Продовый edge-конфиг без принудительного HTTPS и с открытой docs surface

Риск: трафик без TLS, расширение поверхности атаки через публичные `/docs` и `/openapi.json`.

Подтверждение:

- `nginx/prod.conf:14` (listen 80)
- `nginx/prod.conf:39` и `nginx/prod.conf:99` (`/docs`)
- `nginx/prod.conf:43` и `nginx/prod.conf:103` (`/openapi.json`)

Рекомендация:

- включить `80 -> 443` redirect;
- закрыть docs/openapi в production (IP allowlist, basic auth или отключение);
- добавить security headers (`HSTS`, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`).

### P1-4: Небезопасные дефолтные учетные данные в init-скрипте

Риск: случайный запуск скрипта вне локальной среды создаст предсказуемый admin-аккаунт.

Подтверждение:

- `backend/init_db.py:24` (`admin@ostrov.ru`)
- `backend/init_db.py:25` (`admin123`)

Рекомендация:

- убрать hardcoded пароль;
- требовать ввод/переменные окружения;
- ограничить скрипт только dev-профилем.

## P2

### P2-1: CORS чрезмерно открыт

Риск: избыточно широкая политика повышает вероятность кросс-доменных злоупотреблений и ошибок конфигурирования.

Подтверждение:

- `backend/app/main.py:37` (`allow_origins=["*"]`)
- `backend/app/main.py:38` (`allow_credentials=True`)

Рекомендация:

- whitelist origin’ов из env;
- разделение dev/prod политики CORS.

### P2-2: Частичные коммиты в batch-операции

Риск: при ошибке в середине цикла возможна частично примененная операция (часть заказов обновлена, часть нет).

Подтверждение:

- `backend/app/api/v1/admin_batches.py:73` вызывает `change_order_status` в цикле
- `backend/app/services/order.py:77` внутри `change_order_status` выполняется `commit()`

Рекомендация:

- вынести commit на уровень use-case (`create_batch`);
- применять изменения в одной транзакции (`session.begin()`).

### P2-3: Узкое место производительности в Grouping Optimizer

Риск: последовательные внешние вызовы тарифов и неэффективный расчет моды индекса масштабируются плохо при росте заказов.

Подтверждение:

- `backend/app/services/grouping_optimizer.py:211` (последовательные запросы)
- `backend/app/services/grouping_optimizer.py:207` (nested counting)

Рекомендация:

- ввести concurrency с ограничением (semaphore);
- заменить расчет моды на `collections.Counter`;
- добавить кэширование тарифов по ключу `(from, to, weight)`.

## 4. Дополнительные наблюдения

- `admin` хранит JWT в `localStorage` (`admin/src/stores/auth.ts:7`), что увеличивает риск при XSS. На текущем этапе это приемлемо для internal панели, но лучше рассмотреть httpOnly cookie + CSRF защиту при выходе в более широкую эксплуатацию.
- В коде встречаются общие `except Exception` без типизации, что ухудшает диагностику и повышает шанс скрытой деградации (`backend/app/services/delivery.py:56`, `backend/app/services/webhook.py:21`, `backend/app/services/grouping_optimizer.py:150`).
- Bitrix options по умолчанию используют `http://localhost:8000` (`plugins/bitrix/ostrov.delivery/options.php:13`) — норм для dev, но в prod нужно enforce HTTPS.

## 5. Приоритетный план исправлений

## Фаза 1 (срочно, 1-2 дня)

1. Закрыть RBAC на всех admin endpoints (`require_admin`).
2. Убрать утечки исключений из API-ответов.
3. Удалить fallback JWT secret, добавить fail-fast.
4. Отключить/ограничить `/docs` и `/openapi.json` в production.

## Фаза 2 (высокий приоритет, 2-4 дня)

1. Исправить транзакционность batch-операций (single transaction).
2. Ввести уникальность `internal_track_number` и collision-safe генерацию.
3. Ужесточить CORS на whitelist.
4. Убрать hardcoded admin credentials из init-скрипта.

## Фаза 3 (производительность и устойчивость, 3-5 дней)

1. Оптимизировать grouping optimizer (concurrency + caching + Counter).
2. Типизировать обработку исключений по доменным ошибкам.
3. Добавить smoke/integration тесты на auth/RBAC/critical flows.

## 6. KPI после исправлений (рекомендуемые целевые метрики)

- 100% admin endpoints защищены role-check (`admin` only).
- 0 случаев возврата raw exception текста клиенту.
- 0 коллизий `internal_track_number` (DB-enforced uniqueness).
- 0 partial commit инцидентов на batch flow.
- В production весь трафик только через HTTPS, docs surface закрыта.

## 7. Чеклист верификации после remediation

- [ ] non-admin получает 403 на все `admin/*` маршруты.
- [ ] при внутренних ошибках клиент получает generic error, детали только в логах.
- [ ] сервис не стартует без корректного `JWT_SECRET_KEY`.
- [ ] tracking стабильно работает при высоком параллелизме.
- [ ] batch create либо применяет все изменения, либо не применяет ничего.
- [ ] `nginx` редиректит HTTP -> HTTPS; `/docs` и `/openapi.json` ограничены.
- [ ] pytest/integration suite исполняется в CI.

