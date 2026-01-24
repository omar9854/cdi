#!/bin/bash
# Nabih Platform - Initial Setup Script
# Run this on a fresh Ubuntu 22.04/24.04 server

set -e

echo "🔧 Nabih Platform - Initial Setup"
echo "=================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root"
    exit 1
fi

# Update system
echo "📦 Updating system packages..."
apt-get update
apt-get upgrade -y

# Install dependencies
echo "📚 Installing dependencies..."
apt-get install -y \
    python3 python3-pip python3-venv \
    nodejs npm \
    nginx \
    mongodb-org \
    git curl wget \
    build-essential

# Install Yarn
npm install -g yarn

# Check for NVIDIA GPU
echo "🎮 Checking GPU..."
if command -v nvidia-smi &> /dev/null; then
    echo "✅ NVIDIA GPU detected:"
    nvidia-smi --query-gpu=name,memory.total --format=csv
else
    echo "⚠️ No NVIDIA GPU detected. AI features will not work."
fi

# Install CUDA (if GPU available)
if command -v nvidia-smi &> /dev/null; then
    echo "📦 Installing CUDA toolkit..."
    # Add NVIDIA repository and install CUDA
    # This is distribution-specific
fi

# Start MongoDB
echo "🗄️ Starting MongoDB..."
systemctl enable mongod
systemctl start mongod

# Start Nginx
echo "🌐 Starting Nginx..."
systemctl enable nginx
systemctl start nginx

# Create application directory
mkdir -p /opt/nabih/{backend,frontend}

echo ""
echo "✅ Initial setup complete!"
echo ""
echo "Next steps:"
echo "1. Clone the repository to /opt/nabih"
echo "2. Run ./scripts/deploy.sh"
echo "3. Edit /opt/nabih/backend/.env with your settings"
