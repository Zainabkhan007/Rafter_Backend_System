#!/bin/bash
# PostgreSQL Backup Script for Rafter Backend

BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/rafter_db_backup_$TIMESTAMP.sql"

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Backup the database
echo "Creating backup..."
pg_dump -U rafter_user -h localhost rafter_db > $BACKUP_FILE

if [ $? -eq 0 ]; then
    echo "✓ Backup created successfully: $BACKUP_FILE"

    # Compress the backup
    gzip $BACKUP_FILE
    echo "✓ Backup compressed: ${BACKUP_FILE}.gz"

    # Delete backups older than 30 days
    find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
    echo "✓ Cleaned up old backups (>30 days)"
else
    echo "✗ Backup failed!"
    exit 1
fi
