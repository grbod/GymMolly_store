# GymMolly Production Deployment Guide

This guide explains how to deploy GymMolly to your Vultr server alongside your existing applications.

## Prerequisites

- Server: 155.138.211.71 (Vultr)
- Domain: gymmolly.bodytools.work
- Existing Nginx server (with timeclock.bodytools.work)
- Docker and Docker Compose installed

## Deployment Steps

### 1. Connect to Your Server

```bash
ssh root@155.138.211.71
```

### 2. Clone the Repository

```bash
cd /opt  # or your preferred directory
git clone <your-repo-url> gymmolly
cd gymmolly
```

### 3. Set Up Environment

```bash
# Copy the production environment file
cp backend/.env.production .env

# Edit if you need to change any values
# nano .env
```

### 4. Run Setup Script

```bash
# This script will:
# - Create necessary directories
# - Set proper permissions
# - Create database file
# - Optionally initialize with sample data
./deploy-setup.sh
```

### 5. Deploy with Docker Compose

```bash
# Build and start all services
docker-compose -f docker-compose.prod.yml up -d --build

# Check container health
docker-compose -f docker-compose.prod.yml ps

# Monitor logs (press Ctrl+C to exit)
docker-compose -f docker-compose.prod.yml logs -f
```

### 6. Configure Nginx

Add the server block from `nginx-server-config.conf` to your existing Nginx:

```bash
# Copy the configuration
sudo cp nginx-server-config.conf /etc/nginx/sites-available/gymmolly

# Enable the site
sudo ln -s /etc/nginx/sites-available/gymmolly /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### 8. Set Up SSL (Recommended)

```bash
# Install Certbot if not already installed
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d gymmolly.bodytools.work
```

## Important Notes

### Database
- SQLite database is stored in `./data/gymmolly.db`
- Backup regularly: `cp data/gymmolly.db data/gymmolly.db.backup`

### File Attachments
- Stored in `./uploads/` directory
- Ensure this directory is included in backups

### Container Management

```bash
# View running containers
docker-compose -f docker-compose.prod.yml ps

# Stop services
docker-compose -f docker-compose.prod.yml down

# Restart services
docker-compose -f docker-compose.prod.yml restart

# View logs
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend
```

### Updates

To deploy updates:

```bash
cd /opt/gymmolly
git pull
docker-compose -f docker-compose.prod.yml up -d --build
```

### ShipStation Webhook

Update your ShipStation webhook URL to:
- `https://gymmolly.bodytools.work/api/webhooks/shipstation`

### Monitoring

- Frontend: https://gymmolly.bodytools.work
- Backend API: https://gymmolly.bodytools.work/api/orders
- Container status: `docker ps`

## Backup Strategy

Create a backup script (`backup.sh`):

```bash
#!/bin/bash
BACKUP_DIR="/backup/gymmolly"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
cp /opt/gymmolly/data/gymmolly.db $BACKUP_DIR/gymmolly_$DATE.db

# Backup uploads
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz /opt/gymmolly/uploads/

# Keep only last 7 days of backups
find $BACKUP_DIR -mtime +7 -delete
```

Make it executable and add to cron:
```bash
chmod +x backup.sh
crontab -e
# Add: 0 2 * * * /opt/gymmolly/backup.sh
```

## Troubleshooting

### Common Issues and Solutions

1. **Backend container keeps restarting**
   - Check logs: `docker-compose -f docker-compose.prod.yml logs backend`
   - Ensure data directory exists and has proper permissions
   - Run `./deploy-setup.sh` if you haven't already

2. **Database connection errors**
   - The database file is automatically created by the setup script
   - If issues persist: `docker-compose -f docker-compose.prod.yml exec backend sqlite3 /app/data/gymmolly.db "SELECT 1;"`

3. **Port conflicts**
   - Ensure ports 3001 and 5001 are available
   - Change ports in docker-compose.prod.yml if needed

4. **Nginx 502 errors**
   - Check if containers are healthy: `docker-compose -f docker-compose.prod.yml ps`
   - Backend takes ~40 seconds to start (database initialization)
   - Monitor backend logs during startup

5. **Permission issues**
   - The setup script handles permissions automatically
   - If manual fix needed: `chmod 755 data uploads && chmod 666 data/gymmolly.db`

### Quick Health Check

```bash
# Check all services
docker-compose -f docker-compose.prod.yml ps

# Test backend API
curl http://localhost:5001/api/inventory

# Test frontend
curl http://localhost:3001
```