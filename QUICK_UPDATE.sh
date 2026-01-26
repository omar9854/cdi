#!/bin/bash
#================================================================
# سكربت التحديث السريع - لتحديث الكود فقط
# Quick Update Script - Code update only
#
# الاستخدام:
# chmod +x QUICK_UPDATE.sh
# sudo ./QUICK_UPDATE.sh
#================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[*]${NC} $1"; }
print_success() { echo -e "${GREEN}[✓]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[!]${NC} $1"; }

INSTALL_DIR="/opt/nabeeh"

echo ""
echo "=========================================="
echo "   🔄 تحديث نظام نبيه"
echo "=========================================="
echo ""

# إيقاف الخدمات
print_status "إيقاف الخدمات..."
systemctl stop nabeeh-backend nabeeh-frontend 2>/dev/null || true

# نسخة احتياطية
BACKUP_DIR="$INSTALL_DIR/backup_$(date +%Y%m%d_%H%M%S)"
print_status "إنشاء نسخة احتياطية في: $BACKUP_DIR"
mkdir -p $BACKUP_DIR
cp -r $INSTALL_DIR/backend $BACKUP_DIR/ 2>/dev/null || true
cp -r $INSTALL_DIR/frontend/src $BACKUP_DIR/ 2>/dev/null || true

# حفظ ملفات .env
cp $INSTALL_DIR/backend/.env $BACKUP_DIR/backend.env 2>/dev/null || true
cp $INSTALL_DIR/frontend/.env $BACKUP_DIR/frontend.env 2>/dev/null || true

print_success "النسخة الاحتياطية جاهزة"

echo ""
print_warning "=========================================="
print_warning " الآن قم بنسخ الكود الجديد"
print_warning "=========================================="
echo ""
echo "من جهازك، نفذ:"
echo "  scp -r ./backend/* root@YOUR_SERVER:$INSTALL_DIR/backend/"
echo "  scp -r ./frontend/* root@YOUR_SERVER:$INSTALL_DIR/frontend/"
echo ""
echo "أو إذا لديك ملف tar.gz:"
echo "  scp nabih-production-final.tar.gz root@YOUR_SERVER:/tmp/"
echo "  ssh root@YOUR_SERVER 'cd /tmp && tar -xzf nabih-production-final.tar.gz && cp -r backend/* $INSTALL_DIR/backend/ && cp -r frontend/* $INSTALL_DIR/frontend/'"
echo ""

read -p "اضغط Enter بعد نسخ الكود للمتابعة..."

# استعادة ملفات .env
print_status "استعادة إعدادات البيئة..."
cp $BACKUP_DIR/backend.env $INSTALL_DIR/backend/.env 2>/dev/null || true
cp $BACKUP_DIR/frontend.env $INSTALL_DIR/frontend/.env 2>/dev/null || true

# تفعيل البيئة الافتراضية
source $INSTALL_DIR/venv/bin/activate

# تحديث المتطلبات
print_status "تحديث متطلبات Python..."
pip install -r $INSTALL_DIR/backend/requirements.txt 2>/dev/null || true

# إعادة بناء Frontend
print_status "إعادة بناء الواجهة..."
cd $INSTALL_DIR/frontend
yarn install
yarn build

# إعادة تشغيل الخدمات
print_status "إعادة تشغيل الخدمات..."
systemctl start nabeeh-backend
systemctl start nabeeh-frontend

sleep 3

# التحقق
echo ""
echo "حالة الخدمات:"
systemctl is-active --quiet nabeeh-backend && print_success "Backend: يعمل" || print_warning "Backend: متوقف"
systemctl is-active --quiet nabeeh-frontend && print_success "Frontend: يعمل" || print_warning "Frontend: متوقف"

echo ""
print_success "التحديث اكتمل! 🎉"
echo ""
echo "للتحقق من السجلات:"
echo "  journalctl -u nabeeh-backend -f"
echo ""
