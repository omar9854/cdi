#!/bin/bash
#================================================================
# سكربت تثبيت نظام نبيه - للخادم مع GPU
# Nabeeh Medical CDI Platform - GPU Server Installation
# 
# المتطلبات:
# - Ubuntu 20.04/22.04
# - NVIDIA GPU (V100/A100/RTX 3090+)
# - RAM: 64GB+ موصى به
# - التخزين: 100GB+
#
# الاستخدام:
# chmod +x INSTALL_GPU_SERVER.sh
# sudo ./INSTALL_GPU_SERVER.sh
#================================================================

set -e

# الألوان للطباعة
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[*]${NC} $1"; }
print_success() { echo -e "${GREEN}[✓]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[!]${NC} $1"; }
print_error() { echo -e "${RED}[✗]${NC} $1"; }

# متغيرات التثبيت
INSTALL_DIR="/opt/nabeeh"
BACKEND_PORT=8001
FRONTEND_PORT=3000
VLLM_PORT=8000
MODEL_NAME="Qwen/Qwen2.5-32B-Instruct"

echo ""
echo "=========================================="
echo "   🏥 تثبيت نظام نبيه للتحليل الطبي"
echo "   Nabeeh Medical CDI Platform"
echo "=========================================="
echo ""

#================================================================
# الخطوة 1: التحقق من المتطلبات
#================================================================
print_status "الخطوة 1: التحقق من المتطلبات..."

# التحقق من الجذر
if [ "$EUID" -ne 0 ]; then
    print_error "يرجى تشغيل السكربت بصلاحيات الجذر (sudo)"
    exit 1
fi

# التحقق من NVIDIA GPU
if ! command -v nvidia-smi &> /dev/null; then
    print_warning "لم يتم اكتشاف NVIDIA drivers"
    print_status "تثبيت NVIDIA drivers..."
    apt-get update
    apt-get install -y nvidia-driver-535
    print_warning "يرجى إعادة تشغيل الخادم ثم إعادة تشغيل السكربت"
    exit 1
fi

GPU_COUNT=$(nvidia-smi --query-gpu=name --format=csv,noheader | wc -l)
print_success "تم اكتشاف $GPU_COUNT GPU"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

#================================================================
# الخطوة 2: تثبيت المتطلبات الأساسية
#================================================================
print_status "الخطوة 2: تثبيت المتطلبات الأساسية..."

apt-get update
apt-get install -y \
    python3.10 \
    python3.10-venv \
    python3-pip \
    nodejs \
    npm \
    nginx \
    git \
    curl \
    wget \
    htop \
    nvtop

# تحديث Node.js إلى الإصدار 18+
if ! node -v | grep -q "v18\|v20\|v21"; then
    print_status "تحديث Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
fi

print_success "Node.js: $(node -v)"
print_success "npm: $(npm -v)"

# تثبيت yarn
npm install -g yarn
print_success "yarn: $(yarn -v)"

#================================================================
# الخطوة 3: تثبيت MongoDB
#================================================================
print_status "الخطوة 3: تثبيت MongoDB..."

if ! command -v mongod &> /dev/null; then
    wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | apt-key add -
    echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu $(lsb_release -cs)/mongodb-org/7.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-7.0.list
    apt-get update
    apt-get install -y mongodb-org
fi

systemctl start mongod
systemctl enable mongod
print_success "MongoDB تم تثبيته وتشغيله"

#================================================================
# الخطوة 4: إنشاء مجلد التثبيت
#================================================================
print_status "الخطوة 4: إعداد مجلد التثبيت..."

mkdir -p $INSTALL_DIR
cd $INSTALL_DIR

# إذا كان الكود موجوداً من قبل، احتفظ بنسخة احتياطية
if [ -d "$INSTALL_DIR/backend" ]; then
    print_warning "يوجد تثبيت سابق، إنشاء نسخة احتياطية..."
    BACKUP_DIR="$INSTALL_DIR/backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p $BACKUP_DIR
    mv $INSTALL_DIR/backend $BACKUP_DIR/ 2>/dev/null || true
    mv $INSTALL_DIR/frontend $BACKUP_DIR/ 2>/dev/null || true
    print_success "النسخة الاحتياطية في: $BACKUP_DIR"
fi

print_success "مجلد التثبيت: $INSTALL_DIR"

#================================================================
# الخطوة 5: نسخ الكود (يدوياً)
#================================================================
echo ""
print_warning "=========================================="
print_warning " الخطوة 5: نسخ الكود"
print_warning "=========================================="
echo ""
echo "الآن يجب عليك نسخ الكود إلى الخادم:"
echo ""
echo "  الخيار 1 - من جهازك:"
echo "  scp -r /path/to/backend root@YOUR_SERVER:$INSTALL_DIR/"
echo "  scp -r /path/to/frontend root@YOUR_SERVER:$INSTALL_DIR/"
echo ""
echo "  الخيار 2 - من Git:"
echo "  git clone YOUR_REPO_URL $INSTALL_DIR/app"
echo "  mv $INSTALL_DIR/app/backend $INSTALL_DIR/"
echo "  mv $INSTALL_DIR/app/frontend $INSTALL_DIR/"
echo ""

# التحقق من وجود الكود
check_code() {
    if [ -d "$INSTALL_DIR/backend" ] && [ -d "$INSTALL_DIR/frontend" ]; then
        return 0
    else
        return 1
    fi
}

if ! check_code; then
    print_warning "الكود غير موجود بعد. بعد نسخ الكود، أعد تشغيل السكربت."
    print_status "أو يمكنك متابعة التثبيت اليدوي بالأوامر التالية..."
fi

#================================================================
# الخطوة 6: إعداد Python Virtual Environment
#================================================================
print_status "الخطوة 6: إعداد بيئة Python..."

cd $INSTALL_DIR
python3.10 -m venv venv
source venv/bin/activate

# تحديث pip
pip install --upgrade pip

# تثبيت vLLM مع دعم CUDA
print_status "تثبيت vLLM (قد يستغرق وقتاً)..."
pip install vllm

# تثبيت متطلبات Backend
if [ -f "$INSTALL_DIR/backend/requirements.txt" ]; then
    pip install -r $INSTALL_DIR/backend/requirements.txt
fi

# تثبيت متطلبات إضافية
pip install \
    fastapi \
    uvicorn \
    motor \
    pymongo \
    python-jose \
    passlib \
    bcrypt \
    python-multipart \
    aiosmtplib \
    scispacy \
    spacy

# تحميل نموذج NLP (اختياري)
# python -m spacy download en_core_web_sm

print_success "بيئة Python جاهزة"

#================================================================
# الخطوة 7: تحميل نموذج Qwen
#================================================================
print_status "الخطوة 7: تحميل نموذج الذكاء الاصطناعي..."

echo ""
print_warning "سيتم تحميل نموذج Qwen2.5-32B (حوالي 60GB)"
print_warning "هذا قد يستغرق 30-60 دقيقة حسب سرعة الإنترنت"
echo ""

# تحميل النموذج مسبقاً
python3 -c "
from huggingface_hub import snapshot_download
snapshot_download('$MODEL_NAME', local_dir='/opt/nabeeh/models/$MODEL_NAME')
print('تم تحميل النموذج بنجاح')
" || print_warning "يمكنك تخطي هذه الخطوة - سيتم التحميل عند التشغيل"

#================================================================
# الخطوة 8: إعداد ملفات البيئة
#================================================================
print_status "الخطوة 8: إعداد ملفات البيئة..."

# إنشاء .env للـ Backend
cat > $INSTALL_DIR/backend/.env << 'ENVFILE'
# MongoDB
MONGO_URL="mongodb://localhost:27017"
DB_NAME="clinical_doc_center"

# Security
JWT_SECRET="CHANGE_THIS_TO_RANDOM_STRING_$(openssl rand -hex 32)"
CORS_ORIGINS="*"

# vLLM Configuration
VLLM_API_URL="http://localhost:8000/v1"
MODEL_NAME="Qwen/Qwen2.5-32B-Instruct"

# Admin Account
ADMIN_EMAIL="admin@nabeeh.local"
ADMIN_PASSWORD="CHANGE_THIS_PASSWORD"
ADMIN_SECRET_CODE="CDI-ADMIN-2024"

# Email (Optional)
EMAIL_FROM="noreply@nabeeh.local"
SMTP_HOST="smtp.gmail.com"
SMTP_PORT=587
SMTP_USER=""
SMTP_PASSWORD=""

# Misc
ENABLE_HEALTH_CHECK=true
ENVFILE

# إنشاء .env للـ Frontend
cat > $INSTALL_DIR/frontend/.env << 'ENVFILE'
REACT_APP_BACKEND_URL=
ENVFILE

print_success "ملفات البيئة جاهزة"
print_warning "تذكر تعديل كلمات المرور في: $INSTALL_DIR/backend/.env"

#================================================================
# الخطوة 9: بناء الـ Frontend
#================================================================
print_status "الخطوة 9: بناء واجهة المستخدم..."

if [ -d "$INSTALL_DIR/frontend" ]; then
    cd $INSTALL_DIR/frontend
    yarn install
    yarn build
    print_success "تم بناء الواجهة"
else
    print_warning "مجلد frontend غير موجود - تخطي"
fi

#================================================================
# الخطوة 10: إعداد Systemd Services
#================================================================
print_status "الخطوة 10: إعداد خدمات النظام..."

# خدمة vLLM
cat > /etc/systemd/system/nabeeh-vllm.service << 'SERVICE'
[Unit]
Description=Nabeeh vLLM Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/nabeeh
Environment="PATH=/opt/nabeeh/venv/bin"
ExecStart=/opt/nabeeh/venv/bin/python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-32B-Instruct \
    --tensor-parallel-size 4 \
    --gpu-memory-utilization 0.90 \
    --max-model-len 8192 \
    --port 8000 \
    --host 0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE

# خدمة Backend
cat > /etc/systemd/system/nabeeh-backend.service << 'SERVICE'
[Unit]
Description=Nabeeh Backend API
After=network.target nabeeh-vllm.service mongod.service
Requires=mongod.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/nabeeh/backend
Environment="PATH=/opt/nabeeh/venv/bin"
ExecStart=/opt/nabeeh/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --workers 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE

# خدمة Frontend (serve static files)
cat > /etc/systemd/system/nabeeh-frontend.service << 'SERVICE'
[Unit]
Description=Nabeeh Frontend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/nabeeh/frontend
ExecStart=/usr/bin/npx serve -s build -l 3000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
print_success "خدمات النظام جاهزة"

#================================================================
# الخطوة 11: إعداد Nginx
#================================================================
print_status "الخطوة 11: إعداد Nginx..."

cat > /etc/nginx/sites-available/nabeeh << 'NGINX'
server {
    listen 80;
    server_name _;
    
    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    # Backend API
    location /api {
        proxy_pass http://localhost:8001/api;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        
        # للملفات الكبيرة
        client_max_body_size 50M;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/nabeeh /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx
print_success "Nginx جاهز"

#================================================================
# الخطوة 12: تشغيل الخدمات
#================================================================
print_status "الخطوة 12: تشغيل الخدمات..."

# تشغيل vLLM أولاً (يحتاج وقت للتحميل)
print_status "تشغيل vLLM (قد يستغرق 2-5 دقائق للتحميل)..."
systemctl enable nabeeh-vllm
systemctl start nabeeh-vllm

# انتظار vLLM
print_status "انتظار تحميل النموذج..."
sleep 30

# تشغيل Backend
systemctl enable nabeeh-backend
systemctl start nabeeh-backend

# تشغيل Frontend
systemctl enable nabeeh-frontend
systemctl start nabeeh-frontend

#================================================================
# الخطوة 13: التحقق من الحالة
#================================================================
print_status "الخطوة 13: التحقق من الحالة..."

sleep 5

echo ""
echo "حالة الخدمات:"
echo "=============="
systemctl is-active --quiet nabeeh-vllm && print_success "vLLM: يعمل" || print_error "vLLM: متوقف"
systemctl is-active --quiet nabeeh-backend && print_success "Backend: يعمل" || print_error "Backend: متوقف"
systemctl is-active --quiet nabeeh-frontend && print_success "Frontend: يعمل" || print_error "Frontend: متوقف"
systemctl is-active --quiet mongod && print_success "MongoDB: يعمل" || print_error "MongoDB: متوقف"
systemctl is-active --quiet nginx && print_success "Nginx: يعمل" || print_error "Nginx: متوقف"

#================================================================
# ملخص التثبيت
#================================================================
echo ""
echo "=========================================="
echo "   ✅ اكتمل التثبيت!"
echo "=========================================="
echo ""
echo "📍 الروابط:"
echo "   الموقع: http://YOUR_SERVER_IP"
echo "   API: http://YOUR_SERVER_IP/api"
echo ""
echo "📁 المجلدات:"
echo "   التثبيت: $INSTALL_DIR"
echo "   Backend: $INSTALL_DIR/backend"
echo "   Frontend: $INSTALL_DIR/frontend"
echo ""
echo "🔧 الأوامر المفيدة:"
echo "   حالة الخدمات: systemctl status nabeeh-*"
echo "   سجلات vLLM: journalctl -u nabeeh-vllm -f"
echo "   سجلات Backend: journalctl -u nabeeh-backend -f"
echo "   إعادة تشغيل: systemctl restart nabeeh-backend"
echo ""
echo "⚠️ لا تنسَ:"
echo "   1. تعديل كلمات المرور في: $INSTALL_DIR/backend/.env"
echo "   2. إعداد SSL certificate للإنتاج"
echo "   3. تكوين جدار الحماية (firewall)"
echo ""
print_success "التثبيت اكتمل بنجاح! 🎉"
