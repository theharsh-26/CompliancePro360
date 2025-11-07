#!/bin/bash

# CompliancePro360 - Database Backup Script
# Run this script regularly to backup your database

set -e

# Configuration
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/compliancepro360_${TIMESTAMP}.sql"
RETENTION_DAYS=30

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "================================================================"
echo "  CompliancePro360 - Database Backup"
echo "================================================================"

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

# Check if containers are running
if ! docker-compose ps | grep -q "compliancepro_db.*Up"; then
    echo -e "${RED}Error: Database container is not running${NC}"
    exit 1
fi

# Perform backup
echo "Starting backup..."
docker-compose exec -T postgres pg_dump -U postgres compliancepro360 > "${BACKUP_FILE}"

if [ $? -eq 0 ]; then
    # Compress backup
    echo "Compressing backup..."
    gzip "${BACKUP_FILE}"
    BACKUP_FILE="${BACKUP_FILE}.gz"
    
    # Get file size
    SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
    
    echo -e "${GREEN}✓ Backup completed successfully${NC}"
    echo "  Location: ${BACKUP_FILE}"
    echo "  Size: ${SIZE}"
else
    echo -e "${RED}✗ Backup failed${NC}"
    exit 1
fi

# Clean old backups
echo "Cleaning old backups (older than ${RETENTION_DAYS} days)..."
find "${BACKUP_DIR}" -name "compliancepro360_*.sql.gz" -type f -mtime +${RETENTION_DAYS} -delete

# Count remaining backups
BACKUP_COUNT=$(find "${BACKUP_DIR}" -name "compliancepro360_*.sql.gz" -type f | wc -l)
echo "Total backups: ${BACKUP_COUNT}"

# Optional: Upload to S3 (uncomment and configure)
# if [ ! -z "$AWS_ACCESS_KEY_ID" ] && [ ! -z "$S3_BUCKET_NAME" ]; then
#     echo "Uploading to S3..."
#     aws s3 cp "${BACKUP_FILE}" "s3://${S3_BUCKET_NAME}/backups/"
#     echo -e "${GREEN}✓ Uploaded to S3${NC}"
# fi

echo "================================================================"
echo "  Backup Complete"
echo "================================================================"
