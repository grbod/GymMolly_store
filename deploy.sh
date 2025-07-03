#!/bin/bash

# GymMolly Store Deployment Script
# This script deploys the GymMolly store to a Vultr VPS

set -e  # Exit on error

# Configuration
VPS_IP="155.138.211.71"
VPS_USER="root"  # Change if using different user
PROJECT_NAME="gymmolly"
REMOTE_DIR="/opt/gymmolly"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting GymMolly Store deployment...${NC}"

# Step 1: Create deployment package
echo -e "${YELLOW}Step 1: Creating deployment package...${NC}"
rm -rf deploy_package/
mkdir -p deploy_package

# Copy necessary files
cp -r backend/ deploy_package/
cp -r frontend/ deploy_package/
cp docker-compose.production.yml deploy_package/docker-compose.yml
cp .env.production deploy_package/.env
cp -r nginx-vps-config/ deploy_package/

# Create necessary directories
mkdir -p deploy_package/data
mkdir -p deploy_package/uploads

echo -e "${GREEN}Deployment package created${NC}"

# Step 2: Transfer files to VPS
echo -e "${YELLOW}Step 2: Transferring files to VPS...${NC}"
ssh ${VPS_USER}@${VPS_IP} "mkdir -p ${REMOTE_DIR}"
rsync -avz --progress deploy_package/ ${VPS_USER}@${VPS_IP}:${REMOTE_DIR}/

echo -e "${GREEN}Files transferred successfully${NC}"

# Step 3: Setup on VPS
echo -e "${YELLOW}Step 3: Setting up on VPS...${NC}"

ssh ${VPS_USER}@${VPS_IP} << 'EOF'
cd /opt/gymmolly

# Install Docker and Docker Compose if not already installed
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Installing Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Stop existing containers if any
docker-compose down || true

# Build and start containers
echo "Building and starting containers..."
docker-compose build --no-cache
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 10

# Check if containers are running
docker-compose ps

# Setup Nginx configuration
echo "Setting up Nginx configuration..."
cp nginx-vps-config/gymmolly.conf /etc/nginx/sites-available/
ln -sf /etc/nginx/sites-available/gymmolly.conf /etc/nginx/sites-enabled/

# Test Nginx configuration
nginx -t

# Reload Nginx
systemctl reload nginx

echo "Deployment completed on VPS!"
EOF

# Step 4: Initialize database
echo -e "${YELLOW}Step 4: Initializing database...${NC}"
ssh ${VPS_USER}@${VPS_IP} << 'EOF'
cd /opt/gymmolly
docker-compose exec backend python init_db.py
EOF

# Step 5: Verify deployment
echo -e "${YELLOW}Step 5: Verifying deployment...${NC}"
echo "Checking backend health..."
curl -s http://gymmolly.bodytools.work/api/inventory > /dev/null && echo -e "${GREEN}Backend is responding${NC}" || echo -e "${RED}Backend check failed${NC}"

echo -e "${GREEN}Deployment completed!${NC}"
echo -e "${GREEN}Your application should be available at: http://gymmolly.bodytools.work${NC}"

# Cleanup
rm -rf deploy_package/

echo -e "${YELLOW}Post-deployment checklist:${NC}"
echo "1. Check application at http://gymmolly.bodytools.work"
echo "2. Test order creation functionality"
echo "3. Verify ShipStation integration"
echo "4. Check email notifications"
echo "5. Monitor logs: ssh ${VPS_USER}@${VPS_IP} 'cd /opt/gymmolly && docker-compose logs -f'"