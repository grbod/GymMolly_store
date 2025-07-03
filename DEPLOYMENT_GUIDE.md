# GymMolly Store Deployment Guide

## Overview
This guide explains how to deploy the GymMolly store to your Vultr VPS at gymmolly.bodytools.work (155.138.211.71).

## Architecture
- **Frontend**: React app served by Nginx in Docker (port 3001)
- **Backend**: Flask API in Docker (port 5001)
- **Reverse Proxy**: VPS's existing Nginx proxies to Docker containers
- **Database**: SQLite with persistent volume
- **Domain**: gymmolly.bodytools.work

## Pre-deployment Checklist
- [ ] VPS has Docker and Docker Compose installed
- [ ] Domain A record points to 155.138.211.71
- [ ] Existing Nginx is running on the VPS
- [ ] SSH access to VPS is configured
- [ ] All environment variables in `.env.production` are correct

## Deployment Steps

### 1. Initial Deployment
```bash
# Run the deployment script
./deploy.sh
```

This script will:
- Create a deployment package
- Transfer files to VPS
- Build and start Docker containers
- Configure Nginx reverse proxy
- Initialize the database

### 2. Verify Deployment
After deployment, check:
1. Visit http://gymmolly.bodytools.work
2. Test order creation
3. Verify ShipStation integration works
4. Check email notifications are sent
5. Monitor logs: `ssh root@155.138.211.71 'cd /opt/gymmolly && docker-compose logs -f'`

### 3. Create Initial Backup
```bash
# Create a backup after successful deployment
./backup.sh
```

## Container Architecture

The production setup runs two Docker containers:
- `gymmolly_frontend`: React app on port 3001
- `gymmolly_backend`: Flask API on port 5001

The VPS's existing Nginx proxies:
- gymmolly.bodytools.work → port 3001 (frontend)
- gymmolly.bodytools.work/api → port 5001 (backend)

## File Structure on VPS
```
/opt/gymmolly/
├── backend/          # Flask application
├── frontend/         # React application
├── data/            # SQLite database (persistent)
├── uploads/         # File uploads (persistent)
├── docker-compose.yml
├── .env
└── backups/         # Backup files
```

## Maintenance Commands

### View Logs
```bash
# All containers
ssh root@155.138.211.71 'cd /opt/gymmolly && docker-compose logs -f'

# Backend only
ssh root@155.138.211.71 'cd /opt/gymmolly && docker-compose logs -f backend'

# Frontend only
ssh root@155.138.211.71 'cd /opt/gymmolly && docker-compose logs -f frontend'
```

### Restart Services
```bash
ssh root@155.138.211.71 'cd /opt/gymmolly && docker-compose restart'
```

### Update Application
1. Make changes locally
2. Run `./deploy.sh` again
3. The script will rebuild and redeploy

### Create Backup
```bash
./backup.sh
```
Backups are stored locally in `./backups/` and on VPS in `/opt/gymmolly/backups/`

### Rollback to Previous Version
```bash
# List available backups
ssh root@155.138.211.71 'ls -la /opt/gymmolly/backups/'

# Rollback to specific backup
./rollback.sh gymmolly_backup_YYYYMMDD_HHMMSS.tar.gz
```

## Troubleshooting

### Container Issues
```bash
# Check container status
ssh root@155.138.211.71 'cd /opt/gymmolly && docker-compose ps'

# Restart containers
ssh root@155.138.211.71 'cd /opt/gymmolly && docker-compose restart'

# Rebuild containers
ssh root@155.138.211.71 'cd /opt/gymmolly && docker-compose up -d --build'
```

### Nginx Issues
```bash
# Test Nginx configuration
ssh root@155.138.211.71 'nginx -t'

# Check Nginx logs
ssh root@155.138.211.71 'tail -f /var/log/nginx/gymmolly_error.log'
```

### Database Issues
```bash
# Access database
ssh root@155.138.211.71 'cd /opt/gymmolly && docker-compose exec backend python'
>>> from main import db, Orders
>>> Orders.query.all()
```

### Port Conflicts
If ports 3001 or 5001 are already in use, modify `docker-compose.production.yml` to use different ports and update the Nginx configuration accordingly.

## Security Considerations

1. **Environment Variables**: The `.env.production` file contains sensitive API keys. Ensure it's not committed to version control.

2. **Database**: SQLite database is stored in a persistent volume at `/opt/gymmolly/data/`

3. **Firewall**: Only ports 80 and 443 should be open to the public. Docker containers communicate internally.

4. **Backups**: Regular backups are crucial. Set up a cron job for automated backups:
   ```bash
   # Add to crontab on VPS
   0 2 * * * cd /opt/gymmolly && ./backup.sh
   ```

## Monitoring

1. **Application Health**: http://gymmolly.bodytools.work/api/inventory
2. **Container Status**: `docker-compose ps`
3. **Disk Usage**: Monitor `/opt/gymmolly/data/` and `/opt/gymmolly/uploads/`
4. **Logs**: Check both container logs and Nginx logs regularly

## Updates and Maintenance

1. **Regular Updates**: Keep Docker images updated
2. **Security Patches**: Apply system updates regularly
3. **Backup Before Updates**: Always backup before making changes
4. **Test Locally First**: Test all changes in local Docker environment

## Support

For issues:
1. Check logs first
2. Verify all services are running
3. Test individual components (frontend, backend, database)
4. Check network connectivity
5. Review environment variables