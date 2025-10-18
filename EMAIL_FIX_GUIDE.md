# دليل إعداد البريد الإلكتروني | Email Setup Guide

## ⚠️ المشكلة الحالية | Current Issue

**رسائل البريد الإلكتروني لا ترسل حالياً!**

السبب: `SMTP_PASSWORD` غير محدد في ملف `.env`

---

## 🔧 الحل السريع | Quick Fix

### الخطوة 1: الحصول على App Password من Gmail

1. **اذهب إلى حساب Google:**
   - افتح: https://myaccount.google.com/

2. **فعّل التحقق بخطوتين (2-Step Verification):**
   - اذهب إلى: Security → 2-Step Verification
   - اتبع الخطوات لتفعيله (إذا لم يكن مفعلاً)

3. **إنشاء App Password:**
   - اذهب إلى: Security → 2-Step Verification → App passwords
   - اختر: Mail
   - اختر: Other (custom name)
   - اكتب: "CDI Platform"
   - اضغط "Generate"
   
4. **انسخ الكود المكون من 16 حرف:**
   - مثال: `abcd efgh ijkl mnop`
   - **مهم:** احذف المسافات، الكود النهائي: `abcdefghijklmnop`

---

### الخطوة 2: تحديث ملف .env

افتح الملف: `/app/backend/.env`

ابحث عن السطر:
```
SMTP_PASSWORD=""
```

غيّره إلى:
```
SMTP_PASSWORD="abcdefghijklmnop"
```
(استخدم الكود الذي حصلت عليه من Gmail)

---

### الخطوة 3: إعادة تشغيل Backend

```bash
sudo supervisorctl restart backend
```

---

## ✅ بعد التفعيل

سيعمل النظام على إرسال:

### 1. رسالة ترحيبية عبر البريد (عند التسجيل)
- **الموضوع:** "مرحباً بك في مركز الترميز الطبي"
- **المحتوى:** رسالة ترحيبية بالعربية والإنجليزية

### 2. رسالة استعادة كلمة المرور
- **الموضوع:** "إعادة تعيين كلمة المرور"
- **المحتوى:** رابط لإعادة تعيين كلمة المرور (صالح لمدة ساعة)

---

## 📧 تفاصيل إعدادات البريد الحالية

```env
EMAIL_FROM="almaghthawi.cdi@gmail.com"
SMTP_HOST="smtp.gmail.com"
SMTP_PORT=587
SMTP_USER="almaghthawi.cdi@gmail.com"
SMTP_PASSWORD=""  # ⚠️ هذا هو السطر الذي يجب تعبئته
```

---

## 🔍 كيف تتحقق أن البريد يعمل؟

### 1. افحص Logs:

```bash
tail -f /var/log/supervisor/backend.err.log
```

**قبل التفعيل (خطأ):**
```
WARNING - Email sending skipped - SMTP_PASSWORD not configured
```

**بعد التفعيل (نجاح):**
```
INFO - Email sent successfully to user@example.com
```

### 2. جرب التسجيل:
- سجل حساب جديد
- تحقق من صندوق الوارد للبريد المسجل
- يجب أن تصل رسالة ترحيبية

### 3. جرب استعادة كلمة المرور:
- اذهب إلى "نسيت كلمة المرور"
- أدخل البريد الإلكتروني
- تحقق من صندوق الوارد
- يجب أن يصل رابط إعادة التعيين

---

## 🌐 بدائل أخرى (إذا لم يعمل Gmail)

### 1. استخدام SendGrid (موصى به للإنتاج)

```bash
pip install sendgrid
```

تحديث `.env`:
```env
EMAIL_PROVIDER="sendgrid"
SENDGRID_API_KEY="your-api-key-here"
EMAIL_FROM="almaghthawi.cdi@gmail.com"
```

### 2. استخدام AWS SES

```bash
pip install boto3
```

تحديث `.env`:
```env
EMAIL_PROVIDER="ses"
AWS_ACCESS_KEY_ID="your-key"
AWS_SECRET_ACCESS_KEY="your-secret"
AWS_REGION="us-east-1"
EMAIL_FROM="almaghthawi.cdi@gmail.com"
```

---

## 📋 ملخص سريع

| الميزة | الحالة | الحل |
|-------|--------|------|
| رسالة الترحيب (واتساب) | ✅ تعمل | لا يحتاج أي إعداد |
| رسالة الترحيب (بريد) | ❌ لا تعمل | ⚠️ تحتاج App Password |
| استعادة كلمة المرور (بريد) | ❌ لا تعمل | ⚠️ تحتاج App Password |
| زر الدعم الفني (واتساب) | ✅ تعمل | لا يحتاج أي إعداد |

---

## 🚨 تنبيه مهم

**حالياً:**
- ✅ واتساب يعمل بشكل كامل (رسالة ترحيب + دعم فني)
- ❌ البريد الإلكتروني لا يعمل (يحتاج App Password)

**بعد إضافة App Password:**
- ✅ كل شيء سيعمل!

---

## 📞 للدعم

إذا واجهت أي مشكلة:
- تواصل عبر واتساب: 966502468148
- راجع logs: `/var/log/supervisor/backend.err.log`

---

© 2025 جميع الحقوق محفوظة | عمر المغذوي
