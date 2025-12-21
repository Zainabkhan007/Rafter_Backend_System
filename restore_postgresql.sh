#!/bin/bash
# PostgreSQL Restore Script for Rafter Backend

if [ -z "$1" ]; then
    echo "Usage: ./restore_postgresql.sh <backup_file.sql.gz>"
    echo ""
    echo "Available backups:"
    ls -lh ./backups/*.sql.gz 2>/dev/null || echo "  No backups found"
    exit 1
fi

BACKUP_FILE=$1

if [ ! -f "$BACKUP_FILE" ]; then
    echo "✗ Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "⚠️  WARNING: This will replace all data in rafter_db!"
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

# Decompress if needed
if [[ $BACKUP_FILE == *.gz ]]; then
    echo "Decompressing backup..."
    gunzip -c $BACKUP_FILE > /tmp/restore_temp.sql
    SQL_FILE="/tmp/restore_temp.sql"
else
    SQL_FILE=$BACKUP_FILE
fi

# Drop and recreate database
echo "Recreating database..."
psql postgres << EOF
DROP DATABASE IF EXISTS rafter_db;
CREATE DATABASE rafter_db;
GRANT ALL PRIVILEGES ON DATABASE rafter_db TO rafter_user;
EOF

# Restore the backup
echo "Restoring backup..."
psql -U rafter_user -h localhost rafter_db < $SQL_FILE

if [ $? -eq 0 ]; then
    echo "✓ Database restored successfully!"
    rm -f /tmp/restore_temp.sql
else
    echo "✗ Restore failed!"
    rm -f /tmp/restore_temp.sql
    exit 1
fi
