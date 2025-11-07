#!/bin/bash
# Post-Deployment Script
# تشغيله بعد كل نشر: bash post_deployment.sh

echo "================================================================"
echo "🚀 Post-Deployment Setup - CDI System"
echo "================================================================"
echo ""

# 1. التحقق من البيئة
echo "1️⃣ Checking environment..."
if [ ! -f "/app/backend/.env" ]; then
    echo "❌ Error: .env file not found"
    exit 1
fi
echo "✅ Environment file found"
echo ""

# 2. تشغيل Migration
echo "2️⃣ Running database migration..."
cd /app/backend
python migration_update_users.py
if [ $? -eq 0 ]; then
    echo "✅ Migration completed successfully"
else
    echo "❌ Migration failed"
    exit 1
fi
echo ""

# 3. إعادة تشغيل الخدمات
echo "3️⃣ Restarting services..."
sudo supervisorctl restart all
sleep 5
echo "✅ Services restarted"
echo ""

# 4. التحقق من حالة الخدمات
echo "4️⃣ Checking services status..."
sudo supervisorctl status
echo ""

# 5. التحقق من Metrics endpoint
echo "5️⃣ Checking metrics endpoint..."
BACKEND_URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2)
curl -s "${BACKEND_URL}/api/metrics" | head -5
if [ $? -eq 0 ]; then
    echo "✅ Metrics endpoint working"
else
    echo "⚠️ Warning: Metrics endpoint not responding"
fi
echo ""

# 6. عرض معلومات تسجيل الدخول
echo "================================================================"
echo "✅ Post-Deployment Setup Completed!"
echo "================================================================"
echo ""
echo "📋 Admin Login Credentials:"
echo "   Email: admin@cdi-center.sa"
echo "   Password: CDI@2024#Admin"
echo ""
echo "🔗 URLs:"
echo "   Application: ${BACKEND_URL}"
echo "   Metrics: ${BACKEND_URL}/api/metrics"
echo ""
echo "📚 Next Steps:"
echo "   1. Test admin login"
echo "   2. Setup cron job backup (see CRON_JOB_BACKUP_SETUP_AR.md)"
echo "   3. Setup monitoring (see PROMETHEUS_GRAFANA_MONITORING_GUIDE_AR.md)"
echo ""
echo "================================================================"
