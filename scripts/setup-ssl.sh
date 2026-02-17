#!/bin/bash
set -e

# ============================================================
# Установка SSL (Let's Encrypt) для Остров Везения
# Запуск: bash scripts/setup-ssl.sh
# Предварительно: DNS A-записи должны указывать на этот сервер
# ============================================================

APP_DIR="/opt/ostrov-vezeniya"
cd "$APP_DIR"

echo ">>> Установка Certbot..."
apt-get install -y certbot

echo ""
echo ">>> Получение SSL-сертификатов..."
echo "Убедись что DNS настроен:"
echo "  A api.ostrov-vezeniya.ru → $(hostname -I | awk '{print $1}')"
echo "  A admin.ostrov-vezeniya.ru → $(hostname -I | awk '{print $1}')"
echo ""
read -p "DNS настроен? (y/N): " confirm
if [ "$confirm" != "y" ]; then
    echo "Отменено."
    exit 1
fi

# Получаем сертификат через webroot (nginx уже слушает :80)
certbot certonly --webroot \
    -w /var/lib/docker/volumes/ostrov-vezeniya_certbot_www/_data \
    -d api.ostrov-vezeniya.ru \
    -d admin.ostrov-vezeniya.ru \
    --non-interactive \
    --agree-tos \
    --email admin@ostrov-vezeniya.ru

echo ""
echo ">>> Переключение nginx на HTTPS..."

# Обновляем nginx конфиг для SSL
cat > "$APP_DIR/nginx/prod.conf" << 'NGINXEOF'
upstream backend {
    server backend:8000;
}

# Redirect HTTP → HTTPS
server {
    listen 80;
    server_name api.ostrov-vezeniya.ru admin.ostrov-vezeniya.ru;
    location /.well-known/acme-challenge/ { root /var/www/certbot; }
    location / { return 301 https://$host$request_uri; }
}

# API (HTTPS)
server {
    listen 443 ssl;
    server_name api.ostrov-vezeniya.ru;

    ssl_certificate /etc/letsencrypt/live/api.ostrov-vezeniya.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.ostrov-vezeniya.ru/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_read_timeout 30s;
        client_max_body_size 10m;
    }

    location /health { proxy_pass http://backend; }
    location /docs { proxy_pass http://backend; }
    location /openapi.json { proxy_pass http://backend; }
    location /shop { proxy_pass http://backend; }
}

# Admin (HTTPS)
server {
    listen 443 ssl;
    server_name admin.ostrov-vezeniya.ru;

    ssl_certificate /etc/letsencrypt/live/api.ostrov-vezeniya.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.ostrov-vezeniya.ru/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_read_timeout 30s;
    }

    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
}

# По IP
server {
    listen 80 default_server;
    server_name _;
    location / {
        return 200 '{"service":"ostrov-vezeniya","status":"ok"}';
        add_header Content-Type application/json;
    }
}
NGINXEOF

# Перезапуск nginx
docker compose -f docker-compose.prod.yml restart nginx

echo ""
echo ">>> Настройка автообновления сертификатов..."
# Certbot timer уже настроен при установке через apt
systemctl enable certbot.timer
systemctl start certbot.timer

echo ""
echo "✅ SSL установлен!"
echo "  https://api.ostrov-vezeniya.ru/health"
echo "  https://admin.ostrov-vezeniya.ru"
echo ""
