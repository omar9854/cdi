# ⚡ ملف مهم - اقرأ هذا بعد النشر!

## 🚨 مشكلة شائعة: التغييرات لا تظهر بعد النشر

### لماذا يحدث هذا؟
البيئة المؤقتة (Preview) وبيئة الإنتاج (Production) لهما قواعد بيانات منفصلة.

أي تغيير في:
- ❌ حسابات المستخدمين
- ❌ كلمات المرور
- ❌ الأدوار (Admin/Supervisor/User)
- ❌ البيانات في قاعدة البيانات

**لن ينتقل تلقائياً!**

---

## ✅ الحل البسيط (مهم جداً!)

### بعد كل نشر، شغّل هذا الأمر:

```bash
# طريقة 1: تشغيل السكريبت التلقائي
bash /app/post_deployment.sh
```

أو

```bash
# طريقة 2: تشغيل Migration يدوياً
cd /app/backend
python migration_update_users.py
```

---

## 📋 ماذا يفعل Migration Script؟

### 1. يُحدّث جميع المستخدمين:
```
✅ يضيف حقول الأمان (MFA, password policies)
✅ يُحدّث أسماء الحقول (password → password_hash)
✅ يضبط الإعدادات الافتراضية
```

### 2. يُحدّث/ينشئ حساب Admin:
```
Email: admin@cdi-center.sa
Password: CDI@2024#Admin
Role: admin
MFA: enabled
```

### 3. ينشئ Database Indexes:
```
✅ Users indexes (email, id)
✅ Clinical Notes indexes
✅ Analyses indexes
✅ Audit Logs indexes
✅ Chat Messages indexes
```

### 4. يعرض إحصائيات:
```
📊 عدد المستخدمين
📊 عدد الأدمن/المشرفين
📊 عدد الملاحظات والتحليلات
```

---

## 🎯 خطوات سريعة بعد كل نشر

### 1️⃣ SSH إلى الخادم:
```bash
ssh user@your-server.com
```

### 2️⃣ شغّل Migration:
```bash
cd /app/backend
python migration_update_users.py
```

### 3️⃣ أعد تشغيل الخدمات:
```bash
sudo supervisorctl restart all
```

### 4️⃣ اختبر تسجيل الدخول:
```
Email: admin@cdi-center.sa
Password: CDI@2024#Admin
```

---

## 🔄 إعداد تلقائي (موصى به)

### إضافة إلى CI/CD Pipeline:

إذا كان لديك GitHub Actions أو أي CI/CD:

```yaml
# .github/workflows/deploy.yml
- name: Run Post-Deployment Migration
  run: |
    ssh user@server "cd /app/backend && python migration_update_users.py"
```

---

## 📚 الملفات الهامة

| الملف | الغرض |
|-------|-------|
| `/app/post_deployment.sh` | سكريبت تلقائي شامل |
| `/app/backend/migration_update_users.py` | تحديث قاعدة البيانات |
| `/app/DEPLOYMENT_CHECKLIST_AR.md` | قائمة تحقق كاملة |
| `/app/COMPREHENSIVE_SECURITY_IT_DOCUMENTATION_AR.md` | وثيقة الأمان الشاملة |

---

## ❓ الأسئلة الشائعة

### س: هل يجب تشغيل Migration بعد كل نشر؟
**ج:** نعم! خاصة إذا كانت هناك تحديثات على:
- نماذج المستخدمين
- حقول جديدة
- indexes جديدة

### س: هل سيحذف البيانات الموجودة؟
**ج:** لا! Migration script آمن. يضيف ويحدث فقط، لا يحذف.

### س: ماذا لو نسيت تشغيله؟
**ج:** قد تجد:
- ❌ حساب Admin لا يعمل
- ❌ كلمات مرور قديمة لا تعمل
- ❌ حقول أمان مفقودة
- ❌ أداء بطيء (بدون indexes)

### س: هل يمكن تشغيله أكثر من مرة؟
**ج:** نعم! آمن 100%. يتحقق أولاً قبل التحديث.

---

## ✅ قائمة التحقق السريعة

بعد كل نشر:

- [ ] شغّلت Migration script
- [ ] أعدت تشغيل الخدمات
- [ ] اختبرت تسجيل دخول Admin
- [ ] تحققت من /api/metrics endpoint
- [ ] راجعت السجلات (logs)

---

## 🆘 مساعدة

إذا واجهت مشاكل:

1. **تحقق من السجلات:**
```bash
sudo supervisorctl tail -f backend
```

2. **أعد تشغيل Migration:**
```bash
cd /app/backend
python migration_update_users.py
```

3. **راجع الدليل الشامل:**
`/app/DEPLOYMENT_CHECKLIST_AR.md`

---

## 📞 تواصل

للمشاكل التقنية، راجع:
- `/app/COMPREHENSIVE_SECURITY_IT_DOCUMENTATION_AR.md`
- `/app/DEPLOYMENT_CHECKLIST_AR.md`

---

**تذكّر:** Migration script = تطبيق جميع التحديثات على البيئة المنشورة! 🚀

**لا تنسى تشغيله بعد كل نشر!** ✅
