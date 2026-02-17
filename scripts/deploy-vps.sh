#!/bin/bash
set -e

# ============================================================
# Остров Везения — Скрипт деплоя на VPS
# Запуск: bash deploy-vps.sh
# Сервер: Ubuntu 22.04+, root
# ============================================================

echo "============================================"
echo "  Остров Везения — Установка на VPS"
echo "============================================"

# 1. Обновление системы
echo ""
echo ">>> [1/8] Обновление системы..."
apt-get update -qq
apt-get upgrade -y -qq

# 2. Установка Docker
echo ""
echo ">>> [2/8] Установка Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
    echo "Docker установлен."
else
    echo "Docker уже установлен."
fi

# Проверка docker compose
if ! docker compose version &> /dev/null; then
    apt-get install -y docker-compose-plugin
fi

# 3. Установка дополнительных пакетов
echo ""
echo ">>> [3/8] Установка Node.js (для билда админки)..."
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
    echo "Node.js $(node --version) установлен."
else
    echo "Node.js $(node --version) уже установлен."
fi

# 4. Клонирование репо
echo ""
echo ">>> [4/8] Клонирование репозитория..."
APP_DIR="/opt/ostrov-vezeniya"

if [ -d "$APP_DIR" ]; then
    echo "Директория $APP_DIR существует, обновляю..."
    cd "$APP_DIR"
    git pull
else
    git clone https://github.com/trapastnik/ostrov-vezenia-mvp.git "$APP_DIR"
    cd "$APP_DIR"
fi

# 5. Настройка .env
echo ""
echo ">>> [5/8] Настройка .env..."
if [ ! -f "$APP_DIR/.env" ]; then
    # Генерация секретов
    DB_PASS=$(openssl rand -hex 16)
    JWT_SECRET=$(openssl rand -hex 32)

    cat > "$APP_DIR/.env" << ENVEOF
# Database
DB_PASSWORD=${DB_PASS}
DATABASE_URL=postgresql+asyncpg://ostrov:${DB_PASS}@db:5432/ostrov

# Redis
REDIS_URL=redis://redis:6379/0

# JWT
JWT_SECRET_KEY=${JWT_SECRET}
JWT_EXPIRE_MINUTES=1440

# Pochta Russia API — ЗАПОЛНИ ВРУЧНУЮ!
POCHTA_API_TOKEN=ЗАПОЛНИ
POCHTA_LOGIN=ЗАПОЛНИ
POCHTA_PASSWORD=ЗАПОЛНИ

# Business
USD_RATE_KOPECKS=9250
DEFAULT_CUSTOMS_FEE_KOPECKS=15000
SENDER_POSTAL_CODE=238311

# CORS
CORS_ORIGINS=https://admin.ostrov-vezeniya.ru,http://admin.ostrov-vezeniya.ru
ENVEOF

    echo ""
    echo "╔══════════════════════════════════════════════╗"
    echo "║  ⚠  .env создан с рандомными секретами      ║"
    echo "║  ОБЯЗАТЕЛЬНО заполни Pochta API данные:     ║"
    echo "║    nano $APP_DIR/.env                       ║"
    echo "╚══════════════════════════════════════════════╝"
    echo ""
    echo "DB_PASSWORD: ${DB_PASS}"
    echo "JWT_SECRET:  ${JWT_SECRET}"
    echo ""
    read -p "Нажми Enter после заполнения Pochta данных (или Ctrl+C для выхода)..."
else
    echo ".env уже существует, пропускаю."
fi

# 6. Билд админки
echo ""
echo ">>> [6/8] Билд админки (Vue.js)..."
cd "$APP_DIR/admin"
npm ci --silent
npm run build
echo "Админка собрана: $APP_DIR/admin/dist/"

# 7. Запуск Docker
echo ""
echo ">>> [7/8] Запуск Docker Compose (production)..."
cd "$APP_DIR"
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

echo "Ожидание запуска БД..."
sleep 10

# 8. Инициализация БД
echo ""
echo ">>> [8/8] Инициализация БД и создание админа..."
docker compose -f docker-compose.prod.yml exec backend python init_db.py

echo ""
echo "============================================"
echo "  ✅ Установка завершена!"
echo "============================================"
echo ""
echo "  Сервисы:"
echo "    API:     http://$(hostname -I | awk '{print $1}'):80/health"
echo "    Swagger: http://$(hostname -I | awk '{print $1}'):80/docs"
echo "    Админка: http://$(hostname -I | awk '{print $1}'):80"
echo "    Эмулятор: http://$(hostname -I | awk '{print $1}'):80/shop"
echo ""
echo "  Логин: admin@ostrov.ru / admin123"
echo ""
echo "  Следующие шаги:"
echo "    1. Настрой DNS: A api.ostrov-vezeniya.ru → $(hostname -I | awk '{print $1}')"
echo "    2. Настрой DNS: A admin.ostrov-vezeniya.ru → $(hostname -I | awk '{print $1}')"
echo "    3. Получи SSL: bash scripts/setup-ssl.sh"
echo "    4. Проверь: curl http://$(hostname -I | awk '{print $1}')/health"
echo ""
