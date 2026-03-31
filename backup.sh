#!/bin/bash
# Database backup script for EventAxis

BACKUP_DIR="/opt/eventaxis/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Database backup
docker exec eventaxis_db pg_dump -U ${POSTGRES_USER:-eventaxis_user} ${POSTGRES_DB:-eventaxis} > $BACKUP_DIR/db_$DATE.sql

# Compress
gzip $BACKUP_DIR/db_$DATE.sql

# Keep only last 7 days
find $BACKUP_DIR -type f -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR/db_$DATE.sql.gz"
