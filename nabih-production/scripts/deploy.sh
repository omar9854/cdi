#!/bin/bash
# Nabih Platform - Deployment Script
# Usage: ./deploy.sh [production|staging]

set -e

ENVIRONMENT=${1:-production}
DEPLOY_DIR="/opt/nabih"
BACKUP_DIR="/opt/nabih-backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "🚀 Deploying Nabih Platform - $ENVIRONMENT"
echo "============================================"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root"
    exit 1
fi

# Create backup
echo "📦 Creating backup..."
mkdir -p $BACKUP_DIR
if [ -d "$DEPLOY_DIR" ]; then
    tar -czf "$BACKUP_DIR/nabih_backup_$TIMESTAMP.tar.gz" -C /opt nabih
    echo "✅ Backup created: nabih_backup_$TIMESTAMP.tar.gz"
fi

# Stop services
echo "⏹️ Stopping services..."
systemctl stop nabih 2>/dev/null || true

# Create deploy directory
mkdir -p $DEPLOY_DIR/{backend,frontend}

# Deploy backend
echo "📂 Deploying backend..."
cp -r src/backend/* $DEPLOY_DIR/backend/

# Setup Python virtual environment
if [ ! -d "$DEPLOY_DIR/backend/venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv $DEPLOY_DIR/backend/venv
fi

# Install dependencies
echo "📚 Installing Python dependencies..."
source $DEPLOY_DIR/backend/venv/bin/activate
pip install --upgrade pip
pip install -r $DEPLOY_DIR/backend/requirements.txt

# Deploy frontend
echo "📂 Deploying frontend..."
cd src/frontend
yarn install
yarn build
cp -r build/* $DEPLOY_DIR/frontend/

# Setup environment file
if [ ! -f "$DEPLOY_DIR/backend/.env" ]; then
    echo "⚙️ Creating environment file..."
    cp config/environment.example $DEPLOY_DIR/backend/.env
    echo "⚠️ Please edit $DEPLOY_DIR/backend/.env with your settings"
fi

# Install systemd service
echo "🔧 Installing systemd service..."
cp config/nabih.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable nabih

# Install nginx config
echo "🔧 Installing nginx configuration..."
cp config/nginx.conf /etc/nginx/sites-available/nabih
ln -sf /etc/nginx/sites-available/nabih /etc/nginx/sites-enabled/
nginx -t && nginx -s reload

# Start services
echo "▶️ Starting services..."
systemctl start nabih

# Verify deployment
sleep 5
if systemctl is-active --quiet nabih; then
    echo ""
    echo "✅ Deployment successful!"
    echo "============================================"
    echo "📊 Service status:"
    systemctl status nabih --no-pager | head -10
else
    echo "❌ Deployment failed! Check logs:"
    journalctl -u nabih -n 50
    exit 1
fi

echo ""
echo "🎉 Nabih Platform deployed successfully!"
echo "   Access at: http://$(hostname -I | awk '{print $1}')"
