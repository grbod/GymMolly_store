#!/bin/bash

# GymMolly Nginx Setup Script
# This script configures Nginx to route gymmolly.bodytools.work to the Docker containers

echo "Setting up Nginx configuration for GymMolly..."

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Check if nginx-server-config.conf exists
if [ ! -f "nginx-server-config.conf" ]; then
    echo "Error: nginx-server-config.conf not found in current directory"
    echo "Make sure you're running this from /opt/gymmolly/"
    exit 1
fi

# Copy the configuration to sites-available
echo "Copying Nginx configuration..."
cp nginx-server-config.conf /etc/nginx/sites-available/gymmolly

# Create symbolic link to enable the site
echo "Enabling the site..."
ln -sf /etc/nginx/sites-available/gymmolly /etc/nginx/sites-enabled/

# Test Nginx configuration
echo "Testing Nginx configuration..."
nginx -t

if [ $? -eq 0 ]; then
    echo "Nginx configuration is valid!"
    
    # Reload Nginx
    echo "Reloading Nginx..."
    systemctl reload nginx
    
    if [ $? -eq 0 ]; then
        echo "✅ Nginx successfully configured!"
        echo ""
        echo "GymMolly should now be available at:"
        echo "http://gymmolly.bodytools.work"
        echo ""
        echo "To set up SSL with Let's Encrypt, run:"
        echo "certbot --nginx -d gymmolly.bodytools.work"
    else
        echo "❌ Failed to reload Nginx"
        exit 1
    fi
else
    echo "❌ Nginx configuration test failed!"
    echo "Please check the configuration file and try again"
    exit 1
fi