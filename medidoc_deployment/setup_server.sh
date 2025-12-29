#!/bin/bash
# MediDoc AI Server Setup Script
# For Ubuntu Server with NVIDIA A100 GPU

set -e

echo "=========================================="
echo "MediDoc AI Server Setup"
echo "=========================================="

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
echo "📦 Installing dependencies..."
sudo apt install -y python3.11 python3.11-venv python3-pip nginx mongodb curl git

# Install NVIDIA drivers if not present
if ! command -v nvidia-smi &> /dev/null; then
    echo "🎮 Installing NVIDIA drivers..."
    sudo apt install -y nvidia-driver-535 nvidia-cuda-toolkit
fi

# Create application directory
echo "📁 Creating application directory..."
sudo mkdir -p /opt/medidoc-ai
sudo chown $USER:$USER /opt/medidoc-ai

# Copy files
echo "📋 Copying application files..."
cp -r /app/medidoc_deployment/* /opt/medidoc-ai/backend/

# Create Python virtual environment
echo "🐍 Setting up Python environment..."
cd /opt/medidoc-ai/backend
python3.11 -m venv venv
source venv/bin/activate

# Install Python packages
echo "📦 Installing Python packages..."
pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install transformers accelerate bitsandbytes
pip install fastapi uvicorn motor python-dotenv
pip install pandas openpyxl  # For DRG file loading

# Download model (will be cached)
echo "🤖 Pre-downloading model..."
python3 -c "
from transformers import AutoTokenizer
tokenizer = AutoTokenizer.from_pretrained('Qwen/Qwen2.5-72B-Instruct', trust_remote_code=True)
print('✅ Tokenizer downloaded')
"

# Create systemd service
echo "⚙️ Creating systemd service..."
sudo tee /etc/systemd/system/medidoc-backend.service > /dev/null << EOF
[Unit]
Description=MediDoc AI Backend
After=network.target mongodb.service

[Service]
Type=simple
User=$USER
WorkingDirectory=/opt/medidoc-ai/backend
Environment="PATH=/opt/medidoc-ai/backend/venv/bin"
ExecStart=/opt/medidoc-ai/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Configure nginx
echo "🌐 Configuring Nginx..."
sudo tee /etc/nginx/sites-available/medidoc > /dev/null << EOF
server {
    listen 80;
    server_name _;

    # Frontend
    location / {
        root /opt/medidoc-ai/frontend/build;
        try_files \$uri \$uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        client_max_body_size 50M;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/medidoc /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

# Start services
echo "🚀 Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable mongodb
sudo systemctl start mongodb
sudo systemctl enable medidoc-backend
sudo systemctl start medidoc-backend

echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo "Backend: http://localhost:8001"
echo "Frontend: http://localhost"
echo ""
echo "To check status: sudo systemctl status medidoc-backend"
echo "To view logs: sudo journalctl -u medidoc-backend -f"
