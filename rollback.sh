#!/bin/bash

# GymMolly Store Rollback Script
# Restores from a backup

set -e

# Configuration
VPS_IP="155.138.211.71"
VPS_USER="root"
REMOTE_DIR="/opt/gymmolly"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if backup file is provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: No backup file specified${NC}"
    echo "Usage: ./rollback.sh <backup_filename>"
    echo ""
    echo "Available backups on VPS:"
    ssh ${VPS_USER}@${VPS_IP} "ls -la ${REMOTE_DIR}/backups/*.tar.gz 2>/dev/null || echo 'No backups found'"
    exit 1
fi

BACKUP_FILE=$1

echo -e "${YELLOW}WARNING: This will restore from backup and overwrite current data!${NC}"
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Rollback cancelled"
    exit 0
fi

echo -e "${GREEN}Starting rollback process...${NC}"

# Perform rollback on VPS
ssh ${VPS_USER}@${VPS_IP} << EOF
cd ${REMOTE_DIR}

# Check if backup exists
if [ ! -f "backups/${BACKUP_FILE}" ]; then
    echo -e "${RED}Error: Backup file not found: backups/${BACKUP_FILE}${NC}"
    exit 1
fi

# Stop containers
echo "Stopping containers..."
docker-compose down

# Create rollback directory
ROLLBACK_DIR="rollback_$(date +%Y%m%d_%H%M%S)"
mkdir -p \${ROLLBACK_DIR}

# Backup current state before rollback
echo "Backing up current state..."
cp -r data/ \${ROLLBACK_DIR}/ 2>/dev/null || true
cp -r uploads/ \${ROLLBACK_DIR}/ 2>/dev/null || true
cp docker-compose.yml \${ROLLBACK_DIR}/ 2>/dev/null || true
cp .env \${ROLLBACK_DIR}/ 2>/dev/null || true

# Extract backup
echo "Extracting backup..."
cd backups
tar -xzf ${BACKUP_FILE}
BACKUP_DIR=\$(basename ${BACKUP_FILE} .tar.gz)

# Restore files
echo "Restoring files..."
cd ${REMOTE_DIR}
rm -rf data/ uploads/
cp -r backups/\${BACKUP_DIR}/data/ ./
cp -r backups/\${BACKUP_DIR}/uploads/ ./
cp backups/\${BACKUP_DIR}/docker-compose.yml ./
cp backups/\${BACKUP_DIR}/.env ./

# Clean up extracted backup
rm -rf backups/\${BACKUP_DIR}/

# Rebuild and start containers
echo "Rebuilding and starting containers..."
docker-compose build --no-cache
docker-compose up -d

# Wait for services
sleep 10

# Verify containers are running
docker-compose ps

echo -e "${GREEN}Rollback completed successfully!${NC}"
echo "Previous state backed up to: \${ROLLBACK_DIR}/"
EOF

echo -e "${GREEN}Rollback process completed!${NC}"
echo -e "${YELLOW}Please verify your application at: http://gymmolly.bodytools.work${NC}"