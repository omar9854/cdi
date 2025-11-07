#!/bin/bash

# Script لتحديث إيميل الأدمن إلى medidocai@gmail.com
# يمكن تشغيله بعد Deploy مباشرة

echo "============================================================"
echo "🔧 تحديث إيميل الأدمن إلى medidocai@gmail.com"
echo "============================================================"
echo ""

# التأكد من وجود Python
if ! command -v python &> /dev/null; then
    echo "❌ Python غير موجود!"
    exit 1
fi

# الانتقال لمجلد Backend
cd /app/backend

# تشغيل migration script
echo "🚀 تشغيل Migration Script..."
echo ""

python migration_update_users.py

# التحقق من نجاح التشغيل
if [ $? -eq 0 ]; then
    echo ""
    echo "============================================================"
    echo "✅ تم التحديث بنجاح!"
    echo "============================================================"
    echo ""
    echo "📋 يمكنك الآن تسجيل الدخول باستخدام:"
    echo "   📧 Email: medidocai@gmail.com"
    echo "   🔑 Password: CDI@2024#Admin"
    echo ""
    echo "⚠️ إذا كنت قد قمت بـ Deploy للتو، انتظر دقيقة واحدة"
    echo "   حتى يتم إعادة تشغيل الخدمات."
    echo ""
else
    echo ""
    echo "❌ حدث خطأ أثناء التحديث!"
    echo "يرجى المحاولة مرة أخرى أو الاتصال بالدعم."
    echo ""
    exit 1
fi
