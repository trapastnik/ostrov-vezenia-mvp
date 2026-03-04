# Остров Везения

Логистическо-таможенный сервис для e-commerce Калининграда. Помогает интернет-магазинам доставлять товары через таможню с интеграцией Почты России.

## Стек

- **Backend:** FastAPI + SQLAlchemy async + Celery + Redis
- **БД:** PostgreSQL (prod) / SQLite (dev)
- **Админ-панель:** Vue 3 + TypeScript + Vite + Tailwind CSS v4
- **Плагины:** Bitrix (PHP), Next.js (в разработке)
- **Деплой:** Docker Compose + Nginx + Let's Encrypt

## Быстрый старт

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -e .
cp ../.env.example ../.env   # заполнить секреты
python init_db.py             # создать таблицы + admin user
uvicorn app.main:app --reload --port 8000

# Админ-панель
cd admin
npm install
npm run dev

# Эмулятор магазина
open http://localhost:8000/shop

# Docker (всё вместе)
docker-compose up
```

## Структура

```
ostrov-vezeniya/
├── backend/          # FastAPI API + Celery workers
├── admin/            # Vue 3 SPA админ-панель
├── plugins/
│   ├── bitrix/       # 1С-Битрикс модуль
│   └── nextjs/       # React/Next.js компоненты (в разработке)
├── nginx/            # Конфигурация reverse proxy
├── scripts/          # Скрипты деплоя, бэкапов, SSL
└── docs/             # Документация
```

## Документация

| Документ | Описание |
|----------|----------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Архитектура, стек, компоненты, потоки данных |
| [API.md](docs/API.md) | Контракты API эндпоинтов |
| [DATABASE.md](docs/DATABASE.md) | Схема БД, статусная машина заказа |
| [DEPLOY.md](docs/DEPLOY.md) | Деплой, SSL, бэкапы, мониторинг |
| [ISSUES.md](docs/ISSUES.md) | Известные проблемы |
| [BACKLOG.md](BACKLOG.md) | Backlog задач |

## API

| Эндпоинт | Назначение |
|----------|------------|
| `POST /delivery/calculate` | Расчёт стоимости доставки + таможня |
| `POST /orders/` | Создание заказа (X-API-Key) |
| `GET /orders/{id}/status` | Статус заказа |
| `GET /track/{track_number}` | Публичный трекинг |
| `POST /auth/login` | JWT авторизация админки |
| `GET /admin/orders` | Список заказов (фильтры, пагинация) |
| `* /admin/shops` | CRUD магазинов |
| `* /admin/batches` | Управление партиями |
| `* /admin/groups` | Группы отправок + оптимизатор |
| `GET /health` | Здоровье системы |

## Версии

- Backend: v0.2.1
- Admin: v0.2.0
