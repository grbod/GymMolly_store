#!/bin/bash

# GymMolly Deployment Setup Script
# This script prepares the environment for Docker deployment

echo "🚀 GymMolly Deployment Setup"
echo "=========================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please copy backend/.env.production to .env first:"
    echo "  cp backend/.env.production .env"
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data uploads
echo "✅ Directories created"

# Set permissions (important for Docker volumes)
echo "🔐 Setting permissions..."
chmod 755 data uploads
echo "✅ Permissions set"

# Create empty SQLite database file
echo "🗄️  Creating database file..."
touch data/gymmolly.db
chmod 666 data/gymmolly.db
echo "✅ Database file created"

# Ask if user wants to initialize with sample data
read -p "Would you like to initialize the database with sample data? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📊 Initializing database with sample data..."
    
    # Build backend image first (needed for init)
    docker-compose -f docker-compose.prod.yml build backend
    
    # Run database initialization
    docker-compose -f docker-compose.prod.yml run --rm backend python init_db.py
    
    if [ $? -eq 0 ]; then
        echo "✅ Database initialized with sample data"
    else
        echo "⚠️  Database initialization failed, but you can continue"
        echo "   You can manually initialize later with:"
        echo "   docker-compose -f docker-compose.prod.yml exec backend python init_db.py"
    fi
else
    echo "⏭️  Skipping sample data initialization"
    echo "   You can initialize later with:"
    echo "   docker-compose -f docker-compose.prod.yml exec backend python init_db.py"
fi

echo
echo "✅ Setup complete! You can now deploy with:"
echo "   docker-compose -f docker-compose.prod.yml up -d --build"
echo
echo "After deployment:"
echo "  - Frontend will be available at: http://localhost:3001"
echo "  - Backend API will be available at: http://localhost:5001"
echo "  - To check logs: docker-compose -f docker-compose.prod.yml logs -f"