#!/bin/bash

# Smart Crédit - Backup Script
# Create daily backup of database and media files

BACKUP_DIR="/backups/smart-credit"
REPO_DIR="/var/www/smart-credit"
DB_NAME="smart_credit_db"
DB_USER="smart_credit_user"

# Create backup directory if not exists
mkdir -p $BACKUP_DIR

# Date
DATE=$(date +"%Y%m%d_%H%M%S")

echo "→ Starting backup at $DATE"

# 1. Database backup
echo "→ Backing up database..."
pg_dump -U $DB_USER $DB_NAME | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

# 2. Media files backup
echo "→ Backing up media files..."
tar -czf "$BACKUP_DIR/media_$DATE.tar.gz" $REPO_DIR/media/

# 3. Cleanup old backups (keep last 30 days)
echo "→ Cleaning old backups..."
find $BACKUP_DIR -type f -mtime +30 -delete

echo "✓ Backup complete"
echo "  Database: $BACKUP_DIR/db_$DATE.sql.gz"
echo "  Media: $BACKUP_DIR/media_$DATE.tar.gz"
