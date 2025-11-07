# ✅ قائمة التحقق الشاملة للنشر (Deployment Checklist)
## يجب تنفيذها بعد كل نشر (deployment)

---

## ⚠️ مهم جداً

**هذه الخطوات يجب تنفيذها بعد كل نشر لضمان تطبيق جميع التحديثات على البيئة المنشورة (Production).**

البيئة المؤقتة (Preview) وبيئة الإنتاج (Production) لها قواعد بيانات منفصلة!

---

## 1️⃣ قبل النشر (Pre-Deployment)

### ✅ التحقق من المتغيرات البيئية

```bash
# في ملف /app/backend/.env
MONGO_URL=mongodb+srv://YOUR_ATLAS_URI
JWT_SECRET=your-secret-key-here
BACKUP_KEY=CDI-Backup-Key-2024-Secure
GOOGLE_GEMINI_API_KEYS=key1,key2,key3
SMTP_PASSWORD=your-gmail-app-password
FRONTEND_URL=https://your-production-domain.com
```

### ✅ حفظ على GitHub

```
1. اضغط "Save to GitHub"
2. انتظر حتى يكتمل الحفظ
3. تأكد من نجاح العملية
```

---

## 2️⃣ بعد النشر مباشرة (Post-Deployment) - مهم جداً! ⚡

### الخطوة 1: تشغيل Migration Script

**يجب تشغيله فوراً بعد كل نشر!**

```bash
# SSH إلى الخادم المنشور
ssh user@your-production-server.com

# الانتقال للمجلد
cd /app/backend

# تشغيل Migration
python migration_update_users.py
```

**ماذا يفعل هذا السكريبت:**
- ✅ يضيف حقول الأمان لجميع المستخدمين
- ✅ يُحدّث/ينشئ حساب Admin بكلمة المرور الجديدة
- ✅ يُنشئ Indexes لتحسين الأداء
- ✅ يُحدّث أسماء الحقول (password → password_hash)

**معلومات تسجيل الدخول بعد Migration:**
```
Email: admin@cdi-center.sa
Password: CDI@2024#Admin
```

---

### الخطوة 2: التحقق من عمل النظام

```bash
# 1. التحقق من الخدمات
sudo supervisorctl status

# يجب أن ترى:
# backend      RUNNING
# frontend     RUNNING

# 2. التحقق من السجلات
sudo supervisorctl tail -f backend

# 3. التحقق من Metrics
curl https://your-domain.com/api/metrics | head -20
```

---

### الخطوة 3: اختبار تسجيل الدخول

```
1. افتح المتصفح
2. اذهب إلى: https://your-domain.com
3. سجّل دخول بحساب Admin:
   - Email: admin@cdi-center.sa
   - Password: CDI@2024#Admin
4. تحقق من عمل MFA (OTP عبر البريد)
5. تحقق من لوحة التحكم
```

---

## 3️⃣ إعداد النسخ الاحتياطي التلقائي

### في Cron-job.org:

```
1. تسجيل الدخول: https://cron-job.org
2. إنشاء Cron Job جديد:

Title: CDI Daily Backup
URL: https://your-production-domain.com/api/admin/backup/create
Method: POST

Headers:
X-Backup-Key: CDI-Backup-Key-2024-Secure
Content-Type: application/json

Schedule: Every day at 02:00 AM (Asia/Riyadh)

Notifications:
☑ Enable failure notifications
Email: medidocai@gmail.com
```

---

## 4️⃣ إعداد MongoDB Atlas Encryption (اختياري لكن موصى به)

### اتبع الدليل:
`/app/MONGODB_ATLAS_ENCRYPTION_GUIDE_AR.md`

**الخطوات المختصرة:**
1. تسجيل في MongoDB Atlas
2. إنشاء Cluster M10+
3. إعداد AWS KMS أو Azure Key Vault
4. تفعيل Encryption at Rest
5. تحديث MONGO_URL في .env

---

## 5️⃣ إعداد Monitoring (Prometheus + Grafana)

### الطريقة السريعة (Docker Compose):

```bash
# 1. إنشاء مجلد
mkdir -p /app/monitoring
cd /app/monitoring

# 2. إنشاء docker-compose.yml
# (انسخ المحتوى من: PROMETHEUS_GRAFANA_MONITORING_GUIDE_AR.md)

# 3. إنشاء prometheus.yml
# (انسخ المحتوى من الدليل)

# 4. تشغيل
docker-compose up -d

# 5. الوصول:
# Prometheus: http://your-server:9090
# Grafana: http://your-server:3001
# Username: admin
# Password: CDI-Grafana-2024
```

---

## 6️⃣ تحديث المستخدمين الحاليين (إذا لزم الأمر)

### إذا كنت تريد تحديث كلمات مرور مستخدمين محددين:

```python
# إنشاء سكريبت update_specific_user.py
import asyncio
import bcrypt
from motor.motor_asyncio import AsyncIOMotorClient
import os

async def update_user(email, new_password):
    mongo_url = os.environ.get('MONGO_URL')
    client = AsyncIOMotorClient(mongo_url)
    db = client['cdi_database']
    
    # تشفير كلمة المرور
    hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
    
    # تحديث المستخدم
    result = await db.users.update_one(
        {'email': email},
        {'$set': {
            'password_hash': hashed.decode('utf-8'),
            'mfa_enabled': True
        }}
    )
    
    if result.modified_count > 0:
        print(f"✅ تم تحديث: {email}")
    else:
        print(f"❌ لم يتم العثور على: {email}")
    
    client.close()

# استخدام
asyncio.run(update_user('user@example.com', 'NewPassword123!'))
```

---

## 7️⃣ تفعيل HTTPS/SSL (إذا لم يكن مفعلاً)

### استخدام Let's Encrypt (مجاني):

```bash
# تثبيت Certbot
sudo apt update
sudo apt install certbot python3-certbot-nginx

# الحصول على شهادة
sudo certbot --nginx -d your-domain.com

# تجديد تلقائي
sudo certbot renew --dry-run
```

---

## 8️⃣ إعداد Firewall

```bash
# تفعيل UFW
sudo ufw enable

# السماح بالمنافذ الضرورية
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS

# التحقق
sudo ufw status
```

---

## 9️⃣ التحقق النهائي - قائمة شاملة

### الأمان:
- [ ] Migration script تم تشغيله
- [ ] حساب Admin يعمل بكلمة المرور الجديدة
- [ ] MFA مفعّل لجميع المستخدمين
- [ ] Rate Limiting يعمل
- [ ] HTTPS/SSL مفعّل
- [ ] Firewall مُعدّ

### النسخ الاحتياطي:
- [ ] Cron job للنسخ الاحتياطي مُعدّ
- [ ] تم اختبار النسخ الاحتياطي يدوياً
- [ ] تم التحقق من إشعارات البريد

### المراقبة:
- [ ] Prometheus يجمع المقاييس
- [ ] Grafana يعرض Dashboards
- [ ] Alerts مُعدّة
- [ ] إشعارات البريد تعمل

### الأداء:
- [ ] Database Indexes منشأة
- [ ] /api/metrics endpoint يعمل
- [ ] Response times مقبولة (<2s)

### الوظائف:
- [ ] تسجيل الدخول يعمل
- [ ] MFA يعمل
- [ ] إنشاء ملاحظات يعمل
- [ ] AI Analysis يعمل
- [ ] Chat يعمل
- [ ] الاستفسارات الطبية متوافقة (بدون تشخيصات محددة)

---

## 🔄 عند كل نشر جديد (Every Deployment)

```bash
# 1. حفظ على GitHub
git push origin main

# 2. نشر (Deploy)
[استخدام منصة النشر الخاصة بك]

# 3. SSH إلى الخادم
ssh user@production-server

# 4. تشغيل Migration
cd /app/backend
python migration_update_users.py

# 5. إعادة تشغيل الخدمات
sudo supervisorctl restart all

# 6. التحقق
sudo supervisorctl status
curl https://your-domain.com/api/metrics | grep cdi_active_users

# 7. اختبار تسجيل الدخول
# افتح المتصفح وسجل دخول
```

---

## 📞 استكشاف الأخطاء

### المشكلة: حساب Admin لا يعمل بعد النشر

**الحل:**
```bash
# تشغيل Migration مرة أخرى
python migration_update_users.py
```

### المشكلة: كلمات مرور المستخدمين القديمة لا تعمل

**الحل:**
Migration script يُحدّث جميع المستخدمين تلقائياً. إذا كانت المشكلة مستمرة:
```bash
# إعادة تعيين كلمة مرور من لوحة Admin
# أو تشغيل update_specific_user.py
```

### المشكلة: Metrics لا تعمل

**الحل:**
```bash
# التحقق من السجلات
sudo supervisorctl tail -f backend

# إعادة تشغيل
sudo supervisorctl restart backend

# التحقق من endpoint
curl https://your-domain.com/api/metrics
```

### المشكلة: النسخ الاحتياطي لا يعمل

**الحل:**
```bash
# اختبار يدوي
curl -X POST https://your-domain.com/api/admin/backup/create \
  -H "X-Backup-Key: CDI-Backup-Key-2024-Secure"

# التحقق من Cron-job.org execution history
```

---

## 📚 الملفات المرجعية

1. **الأمان الشامل:**
   `/app/COMPREHENSIVE_SECURITY_IT_DOCUMENTATION_AR.md`

2. **تشفير MongoDB:**
   `/app/MONGODB_ATLAS_ENCRYPTION_GUIDE_AR.md`

3. **المراقبة:**
   `/app/PROMETHEUS_GRAFANA_MONITORING_GUIDE_AR.md`

4. **النسخ الاحتياطي:**
   `/app/CRON_JOB_BACKUP_SETUP_AR.md`

---

## ✅ الخلاصة

**الخطوات الإلزامية بعد كل نشر:**
1. ✅ تشغيل `migration_update_users.py`
2. ✅ اختبار تسجيل الدخول
3. ✅ التحقق من الخدمات

**الخطوات الموصى بها (مرة واحدة):**
4. ✅ إعداد النسخ الاحتياطي التلقائي
5. ✅ إعداد MongoDB Encryption
6. ✅ إعداد Monitoring
7. ✅ إعداد HTTPS/SSL

---

**تاريخ الإنشاء:** 2024-11-07  
**آخر تحديث:** 2024-11-07  
**الحالة:** جاهز للتطبيق ✅

**ملاحظة مهمة:** احفظ نسخة من هذا الملف ورجع إليه بعد كل نشر!
