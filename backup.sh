#!/bin/bash

# GymMolly Store Backup Script
# Creates backups of database and uploaded files

set -e

# Configuration
VPS_IP="155.138.211.71"
VPS_USER="root"
REMOTE_DIR="/opt/gymmolly"
LOCAL_BACKUP_DIR="./backups"
BACKUP_NAME="gymmolly_backup_$(date +%Y%m%d_%H%M%S)"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Starting GymMolly backup...${NC}"

# Create local backup directory
mkdir -p ${LOCAL_BACKUP_DIR}

# Create backup on VPS
echo -e "${YELLOW}Creating backup on VPS...${NC}"
ssh ${VPS_USER}@${VPS_IP} << EOF
cd ${REMOTE_DIR}

# Create backup directory
mkdir -p backups/${BACKUP_NAME}

# Stop containers to ensure data consistency
echo "Stopping containers..."
docker-compose stop

# Backup database
echo "Backing up database..."
cp -r data/ backups/${BACKUP_NAME}/

# Backup uploads
echo "Backing up uploads..."
cp -r uploads/ backups/${BACKUP_NAME}/

# Backup current docker-compose and env files
cp docker-compose.yml backups/${BACKUP_NAME}/
cp .env backups/${BACKUP_NAME}/

# Create tarball
echo "Creating backup archive..."
cd backups
tar -czf ${BACKUP_NAME}.tar.gz ${BACKUP_NAME}/
rm -rf ${BACKUP_NAME}/

# Restart containers
echo "Restarting containers..."
cd ${REMOTE_DIR}
docker-compose start

echo "Backup created: backups/${BACKUP_NAME}.tar.gz"
EOF

# Download backup to local machine
echo -e "${YELLOW}Downloading backup to local machine...${NC}"
scp ${VPS_USER}@${VPS_IP}:${REMOTE_DIR}/backups/${BACKUP_NAME}.tar.gz ${LOCAL_BACKUP_DIR}/

echo -e "${GREEN}Backup completed successfully!${NC}"
echo -e "Local backup saved to: ${LOCAL_BACKUP_DIR}/${BACKUP_NAME}.tar.gz"

# Keep only last 5 backups locally
echo -e "${YELLOW}Cleaning up old local backups...${NC}"
cd ${LOCAL_BACKUP_DIR}
ls -t gymmolly_backup_*.tar.gz | tail -n +6 | xargs -r rm

# Clean up old backups on VPS (keep last 5)
ssh ${VPS_USER}@${VPS_IP} << EOF
cd ${REMOTE_DIR}/backups
ls -t gymmolly_backup_*.tar.gz | tail -n +6 | xargs -r rm
EOF

echo -e "${GREEN}Backup process completed!${NC}"