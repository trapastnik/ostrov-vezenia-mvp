# Остров Везения — Backlog

## Статусы: ✅ Сделано | 🔧 В работе | 📋 Backlog | 🔴 Блокер

## Документация

| Документ | Описание |
|----------|----------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Архитектура системы, стек, компоненты, потоки данных |
| [API.md](docs/API.md) | Контракты всех API эндпоинтов, запросы/ответы, ошибки |
| [DATABASE.md](docs/DATABASE.md) | Схема БД (5 таблиц), статусная машина заказа, индексы |
| [DEPLOY.md](docs/DEPLOY.md) | Локальная разработка, production Docker, SSL, бэкапы |

---

## Неделя 1: Backend ✅

| # | Задача | Статус | Заметки |
|---|--------|--------|---------|
| 1 | Скаффолд проекта (структура, docker-compose, pyproject.toml, Dockerfile) | ✅ | |
| 2 | Core: config.py, database.py, security.py, dependencies.py | ✅ | |
| 3 | Модели БД: shops, orders, batches, operators, order_status_history | ✅ | SQLite для dev, PostgreSQL для prod |
| 4 | Сервис Почты: async PochtaClient (портирование из pochta_api_test_full.py) | ✅ | httpx async |
| 5 | API расчёта доставки: POST /delivery/calculate | ✅ | Pochta public tariff + customs fee |
| 6 | API заказов для магазинов: создание, статус, трекинг | ✅ | X-API-Key авторизация |
| 7 | API админки: auth (JWT), заказы (список/карточка/смена статуса), магазины CRUD | ✅ | |

## Неделя 2: Админ-панель ✅

| # | Задача | Статус | Приоритет | Заметки |
|---|--------|--------|-----------|---------|
| 8 | Скаффолд: Vite + Vue 3 + TS + Tailwind v4 + Pinia + Router | ✅ | — | |
| 9 | Auth: LoginPage, Pinia store, Axios interceptors | ✅ | — | |
| 10 | Layout: Sidebar, DefaultLayout | ✅ | — | |
| 11 | Заказы: OrdersListPage (таблица, фильтры, пагинация, магазин, SKU) | ✅ | — | |
| 12 | Заказы: OrderDetailPage (товары с артикулами, получатель, стоимость, история) | ✅ | — | |
| 13 | Заказы: смена статуса (ChangeStatusModal, валидация переходов) | ✅ | — | |
| 14 | Магазины: ShopsListPage, ShopDetailPage | ✅ | — | |
| 15 | Партии: BatchesListPage | ✅ | — | |
| 16 | Dashboard: статистика (заказы, магазины, партии) | ✅ | — | |
| 17 | Эмулятор магазина: shop-emulator.html (каталог, корзина, checkout, трекинг) | ✅ | — | |

## Неделя 3: Деплой + Плагины 🔧

| # | Задача | Статус | Заметки |
|---|--------|--------|---------|
| 18 | Docker Compose production (PostgreSQL, Redis, Nginx, Celery) | ✅ | `docker-compose.prod.yml` |
| 19 | Nginx production конфиг (api + admin + SSL-ready) | ✅ | `nginx/prod.conf` |
| 20 | Скрипты деплоя (deploy-vps.sh, setup-ssl.sh, backup.sh) | ✅ | `scripts/` |
| 21 | Деплой на VPS 212.113.117.186 | ✅ | Docker, PostgreSQL, Redis, Nginx, Celery — всё работает |
| 22 | DNS: api.ostrov-vezeniya.ru + admin.ostrov-vezeniya.ru | ✅ | A-записи на 212.113.117.186 |
| 23 | SSL: Let's Encrypt (setup-ssl.sh) | ✅ | Auto-renew настроен |
| 24 | Celery + Redis: фоновые задачи | ✅ | celery_app.py работает на VPS |
| 25 | Webhook: уведомления магазину при смене статуса (HMAC-SHA256) | 📋 | webhook.py — скаффолд есть |
| 26 | Интеграционное тестирование: полный цикл расчёт → заказ → статус | 📋 | |

## Плагины магазинов

### Bitrix (1С-Битрикс) — `plugins/bitrix/ostrov.delivery/`

| # | Задача | Статус | Приоритет | Заметки |
|---|--------|--------|-----------|---------|
| 27 | Скаффолд модуля: install, autoload, настройки, логирование | ✅ | — | Работает |
| 28 | ApiClient: HTTP-клиент к API (calculate, createOrder, getStatus) | ✅ | — | |
| 29 | OrderMapper: преобразование Bitrix → Ostrov payload | ✅ | — | |
| 30 | SaleEvents: хук OnSaleOrderSaved → автоэкспорт | ✅ | — | |
| 31 | OrderExporter: экспорт заказа + сохранение OSTROV_ORDER_ID | ✅ | — | |
| 32 | Создание property OSTROV_ORDER_ID при установке модуля | 📋 | 🔴 Высокий | Без этого ID не сохраняется |
| 33 | DeliveryCalculator: подключить к checkout (показать доставку) | 📋 | 🔴 Высокий | Класс есть, но не интегрирован |
| 34 | Трекинг статуса: отображение в ЛК покупателя | 📋 | 🟡 Средний | getOrderStatus() есть, UI нет |
| 35 | Retry/очередь при падении API | 📋 | 🟡 Средний | Сейчас заказ теряется |
| 36 | Передача SKU в маппере | 📋 | 🟡 Средний | |
| 37 | Валидация конфига при сохранении (тест-запрос) | 📋 | ⚪ Низкий | |

### Next.js — `plugins/nextjs/`

| # | Задача | Статус | Приоритет | Заметки |
|---|--------|--------|-----------|---------|
| 38 | OstrovDelivery.tsx: виджет расчёта в checkout | 📋 | 📋 | Папка пустая |
| 39 | OstrovOrderStatus.tsx: статус заказа в ЛК | 📋 | 📋 | |
| 40 | api.ts + хуки useDeliveryCalculation, useOrderStatus | 📋 | 📋 | |

---

## Тарифы и Группировка отправок ✅ (добавлено 2026-02-19)

| # | Задача | Статус | Приоритет | Заметки |
|---|--------|--------|-----------|---------|
| 54 | Сравнение публичного и контрактного тарифов Почты России | ✅ | Высокий | `compare_tariffs()` в pochta.py + эндпоинт `/admin/pochta/tariff-compare` + UI в PochtaTestPage |
| 55 | Модели БД: ShipmentGroup, GroupingSettings, TrackingEvent | ✅ | Высокий | Новые таблицы в SQLAlchemy |
| 56 | Маршрутизация по хабам: индекс → хаб (10 хабов) | ✅ | Высокий | `hub_router.py` — 10 хабов по первым 3 цифрам индекса |
| 57 | Математика оптимизации: score = savings − penalty × wait_hours | ✅ | Высокий | `grouping_optimizer.py` — условия отправки + deadline |
| 58 | Celery worker: задача оптимизатора по расписанию | ✅ | Высокий | `tasks_grouping.py` + Beat расписание каждые 30 мин |
| 59 | API групп отправок: CRUD, смена статуса, принудительная отправка | ✅ | Высокий | `admin_groups.py` |
| 60 | API настроек оптимизатора: GET/PATCH глобальных параметров | ✅ | Высокий | через `admin_groups.py` |
| 61 | Собственный трекинг: OV-YYYYMMDD-XXXXX, публичный эндпоинт | ✅ | Высокий | `tracking.py` — GET /track/{track_number} |
| 62 | Поля тарифа в заказе: internal_track_number, tariff_savings и др. | ✅ | Высокий | В модели Order |
| 63 | UI: страница "Группы отправок" (таблица + управление статусами) | ✅ | Высокий | `GroupsPage.vue` |
| 64 | UI: настройки оптимизатора с формулой | ✅ | Высокий | Вкладка в GroupsPage.vue |
| 65 | UI: карточка заказа — трекинг-номер + тариф | ✅ | Высокий | Блок в OrderDetailPage.vue |
| 66 | Протестировать реальную экономию при наличии корпоративного договора | 📋 | 🔴 Блокер | API работает полностью, savings=0 т.к. нет скидки по договору |
| 67 | Детальная страница группы отправок | 📋 | Средний | Список заказов в группе, события |

---

## Улучшения и доработки 📋

| # | Задача | Статус | Приоритет | Заметки |
|---|--------|--------|-----------|---------|
| 41 | История статусов: показывать имя оператора (changed_by) | 📋 | Средний | Данные уже в БД |
| 42 | Партии: создание партии из выбранных заказов | 📋 | Высокий | API есть, UI — только список |
| 43 | Партии: детальная страница партии | 📋 | Высокий | |
| 44 | Магазины: создание нового магазина через UI | 📋 | Средний | API CRUD есть, UI — только просмотр |
| 45 | Нормализация адреса: Pochta clean/address при создании заказа | 📋 | Средний | PochtaClient метод есть |
| 46 | Alembic миграции: autogenerate из моделей | 📋 | Низкий | Сейчас init_db.py → create_all |
| 47 | Тесты: unit (order, delivery, pochta) | 📋 | Средний | |
| 48 | Тесты: API integration (pytest + httpx) | 📋 | Средний | |
| 49 | Admin: экспорт заказов в Excel/CSV | 📋 | Низкий | |
| 50 | Admin: уведомления о новых заказах | 📋 | Низкий | |

---

## Баги и технический долг 🔧

| # | Задача | Статус | Заметки |
|---|--------|--------|---------|
| 51 | Backend: убрать inline import HTTPException в admin_orders.py | 📋 | Мелочь |
| 52 | Эмулятор: заказы из test_emulator.py без SKU (артикул = "—") | 📋 | Косметика |
| 53 | CORS: заменить allow_origins=["*"] на конкретные домены в prod | ✅ | CORS_ORIGINS_STR в config.py, whitelist по доменам |

---

## Аудит безопасности 2026-02-21 ✅

Проведён аудит, закрыты критичные и высокоприоритетные уязвимости.

| # | Задача | Статус | Приоритет | Заметки |
|---|--------|--------|-----------|---------|
| 68 | CORS: whitelist вместо `*` | ✅ | CRITICAL | `CORS_ORIGINS_STR` в config.py, `allow_credentials=False` |
| 69 | JWT: fail-fast валидация — не стартует без сильного секрета | ✅ | CRITICAL | `@field_validator` в config.py, min 32 символа |
| 70 | JWT: TTL 1440 → 60 минут | ✅ | CRITICAL | `JWT_EXPIRE_MINUTES=60` |
| 71 | Error handler: `str(exc)` → `"Internal server error"` | ✅ | CRITICAL | Детали только в логах, клиент видит generic |
| 72 | `/docs` и `/openapi.json` закрыты снаружи | ✅ | CRITICAL | `allow 127.0.0.1; deny all;` во всех nginx блоках |
| 73 | Rate limiting на `/auth/login` | ✅ | HIGH | slowapi 10/min, Redis storage, X-Forwarded-For |
| 74 | Security headers в nginx | ✅ | HIGH | X-Frame-Options, X-Content-Type-Options, X-XSS-Protection, Referrer-Policy |
| 75 | Валидация входных данных в admin_pochta.py | ✅ | MEDIUM | `pattern=r"^\d{6}$"` для индексов, `gt=0, le=30000` для веса |
| 76 | Docker: non-root пользователь | ✅ | MEDIUM | `appuser` в Dockerfile |
| 77 | Безопасные ошибки в admin_pochta.py | ✅ | HIGH | `"Pochta API unavailable"` + `logger.error(exc_info=True)` |
| 78 | Фикс tuple распаковки в delivery.py и grouping_optimizer.py | ✅ | Баг | После переработки pochta.py (tuple return) не были обновлены |
| 79 | Rate limiter: Redis storage вместо MemoryStorage | ✅ | HIGH | Multi-worker uvicorn требует общего хранилища |
| 80 | localStorage JWT → httpOnly cookies | 📋 | MEDIUM | Архитектурное изменение, отдельная задача |
| 81 | API ключи: хранить хеш вместо plaintext | 📋 | MEDIUM | Требует миграции БД |
| 82 | Refresh tokens для JWT | 📋 | MEDIUM | Отдельная задача |
| 83 | Audit log: логировать операции создания/изменения/удаления | 📋 | LOW | Отдельная таблица AuditLog |

---

## Мониторинг / System Health (добавлено 2026-02-21) ✅

| # | Задача | Статус | Заметки |
|---|--------|--------|---------|
| 84 | Страница «Здоровье системы» в админке (`/system-health`) | ✅ | Vue-страница с баннером статуса, сервисами, статистикой |
| 85 | Backend: `GET /admin/health` — статус сервисов + статистика БД | ✅ | DB, Redis, Почта API latency; заказы/магазины/партии |
| 86 | Backend: `POST /admin/health/run-tests` — 5 системных тестов | ✅ | БД, Redis SET/GET, Pochta public+contract, JWT |
| 87 | Backend: `GET /admin/health/server` — метрики VPS через /proc | ✅ | RAM (total/used + % нашего процесса), CPU load avg (1/5/15м), диск |
| 88 | Frontend: секция «Ресурсы сервера» с прогресс-барами | ✅ | Цветовая индикация green/yellow/red, вклад backend в RAM |
| 89 | Фикс роута `/health` → `/system-health` (конфликт с nginx) | ✅ | nginx перехватывал /health и проксировал на backend |
| 90 | Версионность: v0.2.0 в pyproject.toml + package.json | ✅ | importlib.metadata в backend; Vite define в frontend; git tag v0.2.0 |
| 91 | Sidebar: версия `v0.2.0` внизу + ссылка «Здоровье системы» (admin only) | ✅ | |

---

## Последнее обновление: 2026-03-04

### Итого
- **Сделано**: 60 задач
- **В работе**: 0
- **Backlog**: 29 задач
- **Репозиторий**: https://github.com/trapastnik/ostrov-vezenia-mvp
- **VPS**: 212.113.117.186
