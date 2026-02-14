# 🔄 دليل إعداد النسخ الاحتياطي التلقائي
## باستخدام Cron-job.org

---

## 📋 معلومات الحساب

**البريد المسجل:** `medidocai@gmail.com`  
**الموقع:** https://cron-job.org  
**الغرض:** نسخ احتياطي تلقائي للبيانات

---

## 🎯 الخطوة 1: تسجيل الدخول

1. اذهب إلى: https://cron-job.org/en/members/
2. سجّل الدخول بالبريد: `medidocai@gmail.com`
3. اذهب إلى لوحة التحكم

---

## 🎯 الخطوة 2: إنشاء Cron Job للنسخ الاحتياطي اليومي

### إعدادات الـ Cron Job:

**1. معلومات أساسية:**
```
Title: CDI Daily Backup
URL: https://medical-analysis-5.preview.emergentagent.com/api/admin/backup/create
```

**2. إعدادات HTTP:**
```
Request Method: POST
Request Timeout: 120 seconds

HTTP Headers:
X-Backup-Key: CDI-Backup-Key-2024-Secure
Content-Type: application/json
```

**3. الجدول الزمني (Schedule):**

**للنسخ الاحتياطي اليومي:**
```
Schedule Type: Every day
Time: 02:00 AM (2 صباحاً بتوقيت السعودية)
Timezone: Asia/Riyadh
```

**4. إشعارات الفشل:**
```
☑ Enable failure notifications
Email: medidocai@gmail.com
Notify after: 2 consecutive failures
```

**5. الإعدادات المتقدمة:**
```
Execution History: Keep last 30 executions
Save response: Yes (for debugging)
```

---

## 🎯 الخطوة 3: إنشاء Cron Jobs إضافية (اختياري)

### نسخة احتياطية أسبوعية:

```
Title: CDI Weekly Backup
URL: https://medical-analysis-5.preview.emergentagent.com/api/admin/backup/create
Method: POST
Headers: Same as above
Schedule: Every Sunday at 03:00 AM
```

### نسخة احتياطية شهرية:

```
Title: CDI Monthly Backup
URL: https://medical-analysis-5.preview.emergentagent.com/api/admin/backup/create
Method: POST
Headers: Same as above
Schedule: First day of month at 04:00 AM
```

---

## 📊 الخطوة 4: التحقق من النسخ الاحتياطية

### من لوحة الأدمن:

1. سجّل دخول كـ Admin
2. اذهب إلى: https://medical-analysis-5.preview.emergentagent.com
3. افتح Developer Tools (F12)
4. Console اكتب:

```javascript
// عرض قائمة النسخ الاحتياطية
fetch('https://medical-analysis-5.preview.emergentagent.com/api/admin/backup/list', {
  headers: {
    'Authorization': 'Bearer ' + localStorage.getItem('token')
  }
})
.then(r => r.json())
.then(d => console.table(d.backups))
```

### اختبار يدوي:

استخدم هذا الأمر في terminal أو Postman:

```bash
curl -X POST \
  https://medical-analysis-5.preview.emergentagent.com/api/admin/backup/create \
  -H "X-Backup-Key: CDI-Backup-Key-2024-Secure" \
  -H "Content-Type: application/json"
```

**النتيجة المتوقعة:**
```json
{
  "success": true,
  "backup_file": "/app/backups/backup_20241107_020000.json",
  "timestamp": "20241107_020000",
  "collections": 10,
  "total_documents": 1234,
  "file_size_mb": 5.67
}
```

---

## 📥 تحميل النسخ الاحتياطية

### الطريقة 1: من واجهة الأدمن (قريباً)

سيتم إضافة صفحة في لوحة الأدمن لعرض وتحميل النسخ الاحتياطية.

### الطريقة 2: API مباشر

```javascript
// 1. عرض القائمة
fetch('https://medical-analysis-5.preview.emergentagent.com/api/admin/backup/list', {
  headers: { 'Authorization': 'Bearer YOUR_ADMIN_TOKEN' }
})
.then(r => r.json())
.then(data => {
  console.log('النسخ الاحتياطية المتوفرة:');
  data.backups.forEach(b => {
    console.log(`${b.filename} - ${b.size_mb}MB - ${b.created_at}`);
  });
});

// 2. تحميل نسخة محددة
window.open(
  'https://medical-analysis-5.preview.emergentagent.com/api/admin/backup/download/backup_20241107_020000.json',
  '_blank'
);
```

---

## 🔒 الأمان

### مفتاح النسخ الاحتياطي:

```
X-Backup-Key: CDI-Backup-Key-2024-Secure
```

**⚠️ هام جداً:**
- ✅ احفظ هذا المفتاح في مكان آمن
- ✅ لا تشاركه مع أحد
- ✅ غيّره كل 3-6 أشهر
- ✅ استخدمه فقط في Cron-job.org

### تغيير المفتاح:

إذا أردت تغيير المفتاح:

1. افتح ملف: `/app/backend/.env`
2. غيّر السطر: `BACKUP_KEY=المفتاح_الجديد`
3. أعد تشغيل Backend
4. حدّث المفتاح في Cron-job.org

---

## 📂 محتويات النسخة الاحتياطية

كل نسخة احتياطية تحتوي على:

```json
{
  "users": [...],              // جميع المستخدمين
  "clinical_notes": [...],     // جميع الملاحظات السريرية
  "analyses": [...],           // جميع التحليلات
  "chat_messages": [...],      // رسائل الدردشة مع AI
  "audit_logs": [...],         // سجلات التدقيق
  "login_attempts": [...],     // محاولات تسجيل الدخول
  "otp_records": [...],        // سجلات OTP
  "user_sessions": [...],      // الجلسات النشطة
  "password_history": [...],   // تاريخ كلمات المرور
  "messages": [...]            // الرسائل الداخلية
}
```

**الحجم المتوقع:** 5-50 MB (حسب حجم البيانات)

---

## 📅 جدول النسخ الاحتياطي الموصى به

| النوع | التكرار | الوقت | الاحتفاظ |
|-------|---------|-------|---------|
| **يومي** | كل يوم | 2:00 ص | 30 يوم |
| **أسبوعي** | كل أحد | 3:00 ص | 3 أشهر |
| **شهري** | أول الشهر | 4:00 ص | 1 سنة |

---

## 🔄 استعادة النسخة الاحتياطية

### في حالة الطوارئ:

**الخطوة 1: تحميل النسخة الاحتياطية**
```bash
# من API
curl -H "Authorization: Bearer ADMIN_TOKEN" \
  https://medical-analysis-5.preview.emergentagent.com/api/admin/backup/download/backup_YYYYMMDD_HHMMSS.json \
  -o backup.json
```

**الخطوة 2: الاستعادة**

سيتم إنشاء endpoint للاستعادة التلقائية لاحقاً. حالياً، يمكن الاستعادة يدوياً:

```python
# استعادة يدوية (على الخادم)
import json
from motor.motor_asyncio import AsyncIOMotorClient

# قراءة النسخة الاحتياطية
with open('backup.json', 'r') as f:
    backup_data = json.load(f)

# الاتصال بقاعدة البيانات
client = AsyncIOMotorClient("mongodb://...")
db = client['cdi_database']

# استعادة كل مجموعة
for collection_name, documents in backup_data.items():
    collection = db[collection_name]
    if documents:
        await collection.insert_many(documents)
```

---

## ✅ قائمة التحقق النهائية

قبل النشر، تأكد من:

- [ ] تسجيل الدخول إلى Cron-job.org
- [ ] إنشاء Cron Job يومي (2 صباحاً)
- [ ] إضافة X-Backup-Key الصحيح
- [ ] تفعيل إشعارات الفشل
- [ ] اختبار النسخ الاحتياطي يدوياً مرة واحدة
- [ ] التحقق من نجاح أول نسخة تلقائية
- [ ] حفظ معلومات تسجيل الدخول في مكان آمن
- [ ] توثيق موقع النسخ الاحتياطية

---

## 📞 الدعم

في حالة المشاكل:

1. **تحقق من Execution History في Cron-job.org**
2. **تحقق من Audit Logs في قاعدة البيانات**
3. **تحقق من مجلد `/app/backups/`**
4. **تحقق من صحة X-Backup-Key**

---

## 🔐 ملاحظات أمنية إضافية

### تشفير النسخ الاحتياطية (موصى به للإنتاج):

```bash
# بعد إنشاء النسخة الاحتياطية، قم بتشفيرها
openssl enc -aes-256-cbc -salt -in backup.json -out backup.json.enc -k "كلمة_مرور_قوية"

# لفك التشفير عند الحاجة
openssl enc -aes-256-cbc -d -in backup.json.enc -out backup.json -k "كلمة_مرور_قوية"
```

### رفع إلى Cloud Storage (موصى به):

بعد إنشاء النسخة الاحتياطية، يمكنك رفعها إلى:
- AWS S3
- Google Cloud Storage  
- Azure Blob Storage
- Dropbox / Google Drive

---

**تم إنشاء هذا الدليل:** 2024-11-07  
**آخر تحديث:** 2024-11-07  
**الحالة:** جاهز للتطبيق ✅

