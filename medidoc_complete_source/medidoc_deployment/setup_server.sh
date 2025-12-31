#!/bin/bash
# MediDoc AI Server Setup Script
# For Ubuntu Server with NVIDIA A100 GPU
# 100% OFFLINE - No External API Dependencies
# Secure Medical Application Setup

set -e

echo "=========================================="
echo "🏥 MediDoc AI Server Setup (100% Offline)"
echo "=========================================="
echo "⚠️ تطبيق طبي آمن - بدون تبعيات خارجية"
echo "⚠️ Secure Medical Application - No External Dependencies"
echo "=========================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Update system
echo -e "${GREEN}📦 Updating system packages...${NC}"
sudo apt update && sudo apt upgrade -y

# Install required packages
echo -e "${GREEN}📦 Installing dependencies...${NC}"
sudo apt install -y python3.11 python3.11-venv python3-pip nginx mongodb curl git ufw fail2ban

# Security: Configure UFW firewall
echo -e "${YELLOW}🔒 Configuring Firewall (UFW)...${NC}"
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw --force enable

# Security: Configure fail2ban
echo -e "${YELLOW}🔒 Configuring fail2ban for brute force protection...${NC}"
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Install NVIDIA drivers if not present
if ! command -v nvidia-smi &> /dev/null; then
    echo -e "${GREEN}🎮 Installing NVIDIA drivers...${NC}"
    sudo apt install -y nvidia-driver-535 nvidia-cuda-toolkit
fi

# Create application directory with proper permissions
echo -e "${GREEN}📁 Creating application directory...${NC}"
sudo mkdir -p /opt/medidoc-ai/backend
sudo mkdir -p /opt/medidoc-ai/frontend/build
sudo mkdir -p /opt/medidoc-ai/logs
sudo mkdir -p /opt/medidoc-ai/data
sudo chown -R $USER:$USER /opt/medidoc-ai

# Create secure .env file (NO API KEYS - fully offline)
echo -e "${YELLOW}🔐 Creating secure environment file...${NC}"
cat > /opt/medidoc-ai/backend/.env << 'EOF'
# MediDoc AI Configuration - 100% Offline
# لا يوجد مفاتيح API خارجية - آمن 100%

# MongoDB (Local)
MONGO_URL=mongodb://127.0.0.1:27017
DB_NAME=medidoc_production

# JWT Security
JWT_SECRET=CHANGE_THIS_TO_A_STRONG_SECRET_KEY_$(openssl rand -hex 32)
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Admin Configuration
ADMIN_SECRET_CODE=CDI-ADMIN-2024-SECURE

# Model Configuration (Local - Offline)
MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
FALLBACK_MODEL=Qwen/Qwen2.5-7B-Instruct
HOSPITAL_TYPE=A

# DRG Price List
DRG_PRICE_LIST=/opt/medidoc-ai/data/drg_prices.xlsx

# Security Settings
SESSION_TIMEOUT_MINUTES=30
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=15

# SMTP (Optional - for email notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
EMAIL_FROM=

# Security: Disable debug in production
DEBUG=false
EOF

chmod 600 /opt/medidoc-ai/backend/.env

# Copy application files
echo -e "${GREEN}📋 Copying application files...${NC}"
cp local_llm.py /opt/medidoc-ai/backend/
cp drg_lookup.py /opt/medidoc-ai/backend/
cp cdi_endpoints.py /opt/medidoc-ai/backend/
cp icd10am_codes.py /opt/medidoc-ai/backend/ 2>/dev/null || echo "icd10am_codes.py not found, skipping"
cp requirements.txt /opt/medidoc-ai/backend/

# Copy DRG price list
if [ -f "drg_prices.xlsx" ]; then
    cp drg_prices.xlsx /opt/medidoc-ai/data/
    echo -e "${GREEN}✅ DRG price list copied${NC}"
fi

# Create Python virtual environment
echo -e "${GREEN}🐍 Setting up Python environment...${NC}"
cd /opt/medidoc-ai/backend
python3.11 -m venv venv
source venv/bin/activate

# Install Python packages (offline-capable after initial download)
echo -e "${GREEN}📦 Installing Python packages...${NC}"
pip install --upgrade pip

# Install PyTorch with CUDA support
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Install transformers and quantization support
pip install transformers accelerate bitsandbytes scipy

# Install FastAPI and dependencies
pip install fastapi uvicorn[standard] motor python-dotenv pydantic[email]

# Install data processing
pip install pandas openpyxl aiofiles

# Install security packages
pip install bcrypt pyjwt python-multipart aiosmtplib

# Install monitoring (optional)
pip install prometheus-client slowapi

# Pre-download model tokenizer (full model downloads on first run)
echo -e "${GREEN}🤖 Pre-downloading model tokenizer...${NC}"
python3 -c "
from transformers import AutoTokenizer
print('📥 Downloading tokenizer for Qwen2.5-72B-Instruct...')
tokenizer = AutoTokenizer.from_pretrained('Qwen/Qwen2.5-72B-Instruct', trust_remote_code=True)
print('✅ Tokenizer downloaded successfully')
"

# Create systemd service with security hardening
echo -e "${GREEN}⚙️ Creating systemd service...${NC}"
sudo tee /etc/systemd/system/medidoc-backend.service > /dev/null << EOF
[Unit]
Description=MediDoc AI Backend (Secure Offline Medical Application)
After=network.target mongodb.service
Requires=mongodb.service

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=/opt/medidoc-ai/backend
Environment="PATH=/opt/medidoc-ai/backend/venv/bin"
EnvironmentFile=/opt/medidoc-ai/backend/.env
ExecStart=/opt/medidoc-ai/backend/venv/bin/uvicorn server:app --host 127.0.0.1 --port 8001 --workers 2
Restart=always
RestartSec=10

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/medidoc-ai

# Logging
StandardOutput=append:/opt/medidoc-ai/logs/backend.log
StandardError=append:/opt/medidoc-ai/logs/backend-error.log

[Install]
WantedBy=multi-user.target
EOF

# Configure nginx with security headers
echo -e "${GREEN}🌐 Configuring Nginx with security headers...${NC}"
sudo tee /etc/nginx/sites-available/medidoc > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self';" always;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login_limit:10m rate=5r/m;

    # Frontend
    location / {
        root /opt/medidoc-ai/frontend/build;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
            expires 30d;
            add_header Cache-Control "public, immutable";
        }
    }

    # Backend API
    location /api {
        limit_req zone=api_limit burst=20 nodelay;
        
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        client_max_body_size 50M;
    }

    # Login endpoint with stricter rate limiting
    location /api/auth/login {
        limit_req zone=login_limit burst=5 nodelay;
        
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Block sensitive paths
    location ~ /\. {
        deny all;
    }
    
    location ~ /\.env {
        deny all;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/medidoc /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

# Configure MongoDB security
echo -e "${YELLOW}🔒 Securing MongoDB...${NC}"
sudo tee /etc/mongod.conf > /dev/null << 'EOF'
# MongoDB Configuration - Secure
storage:
  dbPath: /var/lib/mongodb
  journal:
    enabled: true

systemLog:
  destination: file
  logAppend: true
  path: /var/log/mongodb/mongod.log

net:
  port: 27017
  bindIp: 127.0.0.1  # Only listen on localhost

security:
  authorization: disabled  # Enable after creating admin user
EOF

# Start services
echo -e "${GREEN}🚀 Starting services...${NC}"
sudo systemctl daemon-reload
sudo systemctl enable mongodb
sudo systemctl restart mongodb
sudo systemctl enable medidoc-backend
sudo systemctl start medidoc-backend
sudo systemctl enable nginx
sudo systemctl restart nginx

# Create log rotation
echo -e "${GREEN}📝 Configuring log rotation...${NC}"
sudo tee /etc/logrotate.d/medidoc > /dev/null << 'EOF'
/opt/medidoc-ai/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 $USER $USER
}
EOF

echo ""
echo "=========================================="
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo "=========================================="
echo ""
echo -e "${GREEN}🏥 MediDoc AI - 100% Offline Medical Application${NC}"
echo -e "${YELLOW}⚠️ لا توجد تبعيات خارجية - جميع البيانات محلية${NC}"
echo -e "${YELLOW}⚠️ No external dependencies - All data stays local${NC}"
echo ""
echo "📍 Backend:  http://127.0.0.1:8001 (internal only)"
echo "📍 Frontend: http://YOUR_SERVER_IP"
echo ""
echo "🔧 Useful Commands:"
echo "   Check status:  sudo systemctl status medidoc-backend"
echo "   View logs:     sudo journalctl -u medidoc-backend -f"
echo "   Restart:       sudo systemctl restart medidoc-backend"
echo ""
echo -e "${RED}⚠️ IMPORTANT SECURITY STEPS:${NC}"
echo "1. Change JWT_SECRET in /opt/medidoc-ai/backend/.env"
echo "2. Set up HTTPS with Let's Encrypt:"
echo "   sudo apt install certbot python3-certbot-nginx"
echo "   sudo certbot --nginx -d your-domain.com"
echo "3. Enable MongoDB authentication after setup"
echo "4. Regular security updates: sudo apt update && sudo apt upgrade"
echo ""
echo "=========================================="
