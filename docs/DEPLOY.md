# Деплой

## Локальная разработка

### Требования
- Python 3.12+
- Node.js 18+
- npm 9+

### Запуск backend

```bash
cd backend
python -m venv venv
source venv/bin/activate          # macOS/Linux
pip install -e .

# Конфигурация
cp ../.env.example ../.env
# Заполнить: POCHTA_API_TOKEN, POCHTA_LOGIN, POCHTA_PASSWORD, JWT_SECRET_KEY

# Инициализация БД (SQLite)
python init_db.py
# Создаёт таблицы + admin@ostrov.ru / admin123

# Запуск
uvicorn app.main:app --reload --port 8000
```

### Запуск админки

```bash
cd admin
npm install
npm run dev
# http://localhost:3000 (proxy /api → localhost:8000)
```

### Эмулятор магазина

```
http://localhost:8000/shop
```

Для работы эмулятора нужен API-ключ магазина. Его можно взять из БД или создать магазин через API админки.

---

## Production (Docker Compose)

### Сервер
- **OS:** Ubuntu 22.04+
- **CPU:** 2 vCPU
- **RAM:** 4 GB
- **SSD:** 40 GB
- **Провайдер:** Reg.ru VPS

### Домены
| Домен | Назначение |
|-------|-----------|
| api.ostrov-vezeniya.ru | Backend API |
| admin.ostrov-vezeniya.ru | Админ-панель (SPA) |

### DNS
```
A  api.ostrov-vezeniya.ru    → <SERVER_IP>
A  admin.ostrov-vezeniya.ru  → <SERVER_IP>
```

### Установка

```bash
# 1. Подключиться к серверу
ssh root@<SERVER_IP>

# 2. Установить Docker
curl -fsSL https://get.docker.com | sh
apt install docker-compose-plugin

# 3. Клонировать репо
git clone https://github.com/trapastnik/ostrov-vezenia-mvp.git
cd ostrov-vezenia-mvp

# 4. Создать .env
cp .env.example .env
nano .env
```

### .env для production

```bash
# БД
DATABASE_URL=postgresql+asyncpg://ostrov:STRONG_PASSWORD@db:5432/ostrov
DB_PASSWORD=STRONG_PASSWORD

# JWT
JWT_SECRET_KEY=RANDOM_64_CHAR_STRING
JWT_EXPIRE_MINUTES=1440

# Почта России
POCHTA_API_TOKEN=<token>
POCHTA_LOGIN=<login>
POCHTA_PASSWORD=<password>

# CORS
CORS_ORIGINS=https://admin.ostrov-vezeniya.ru

# Redis (для Celery)
REDIS_URL=redis://redis:6379/0
```

### Запуск

```bash
# 5. Запустить все сервисы
docker compose up -d

# 6. Применить миграции
docker compose exec backend alembic upgrade head

# 7. Создать админ-пользователя
docker compose exec backend python -m app.scripts.create_admin

# 8. Проверить
curl https://api.ostrov-vezeniya.ru/api/v1/delivery/calculate \
  -H "X-API-Key: <key>" \
  -H "Content-Type: application/json" \
  -d '{"postal_code":"101000","weight_grams":1000,"total_amount_kopecks":100000}'
```

### docker-compose.yml (production)

```yaml
services:
  backend:
    build: ./backend
    env_file: .env
    depends_on: [db, redis]
    restart: always

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: ostrov
      POSTGRES_USER: ostrov
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

  redis:
    image: redis:7-alpine
    restart: always

  worker:
    build: ./backend
    command: celery -A app.workers.celery_app worker -l info
    env_file: .env
    depends_on: [db, redis]
    restart: always

  nginx:
    image: nginx:alpine
    ports: ["80:80", "443:443"]
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./admin/dist:/usr/share/nginx/html/admin
      - certbot_data:/etc/letsencrypt
    depends_on: [backend]
    restart: always

volumes:
  postgres_data:
  certbot_data:
```

### SSL (Let's Encrypt)

```bash
# Установить certbot
apt install certbot python3-certbot-nginx

# Получить сертификаты
certbot --nginx -d api.ostrov-vezeniya.ru -d admin.ostrov-vezeniya.ru

# Автообновление (уже настроено через systemd timer)
certbot renew --dry-run
```

### Билд админки

```bash
cd admin
npm ci
npm run build          # → admin/dist/
# Nginx раздаёт admin/dist/ как static files
```

---

## Обслуживание

### Бэкапы БД

```bash
# Ежедневный бэкап (добавить в crontab)
0 3 * * * docker compose exec -T db pg_dump -U ostrov ostrov | gzip > /backups/ostrov_$(date +\%Y\%m\%d).sql.gz

# Хранить последние 30 дней
find /backups -name "ostrov_*.sql.gz" -mtime +30 -delete
```

### Восстановление

```bash
gunzip < /backups/ostrov_20260217.sql.gz | docker compose exec -T db psql -U ostrov ostrov
```

### Логи

```bash
docker compose logs -f backend    # Логи backend
docker compose logs -f worker     # Логи Celery
docker compose logs -f nginx      # Логи Nginx
```

### Обновление

```bash
cd ostrov-vezenia-mvp
git pull
docker compose build
docker compose up -d
docker compose exec backend alembic upgrade head
```

---

## Мониторинг (будущее)

- Health-check: `GET /api/v1/health` → 200
- Метрики: Prometheus + Grafana
- Алерты: disk space, memory, API latency
- Uptime: UptimeRobot / Better Uptime
