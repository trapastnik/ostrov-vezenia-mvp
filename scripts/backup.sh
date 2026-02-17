#!/bin/bash
# Бэкап БД. Добавить в crontab: 0 3 * * * /opt/ostrov-vezeniya/scripts/backup.sh

BACKUP_DIR="/opt/backups/ostrov"
mkdir -p "$BACKUP_DIR"

cd /opt/ostrov-vezeniya
docker compose -f docker-compose.prod.yml exec -T db pg_dump -U ostrov ostrov | gzip > "$BACKUP_DIR/ostrov_$(date +%Y%m%d_%H%M).sql.gz"

# Удалить бэкапы старше 30 дней
find "$BACKUP_DIR" -name "ostrov_*.sql.gz" -mtime +30 -delete

echo "Backup done: $BACKUP_DIR/ostrov_$(date +%Y%m%d_%H%M).sql.gz"
