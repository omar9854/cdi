# 🚨 CRITICAL FIX: تحديث رابط Production

## ❌ المشكلة

بعد النشر، المستخدمين لا يستطيعون تسجيل الدخول:
1. يدخلون البريد وكلمة المرور ✅
2. يستلمون OTP ✅
3. يدخلون OTP ❌ → صفحة فارغة
4. لا يصلون للـ Dashboard ❌

## 🔍 السبب الجذري

ملف `/app/frontend/.env` مازال يحتوي على رابط Preview:
```
REACT_APP_BACKEND_URL=https://nabeeh-medical.preview.emergentagent.com
```

هذا يعني:
- Frontend في Production يحاول الاتصال بـ Backend في Preview
- الطلبات تفشل (404 أو CORS error)
- الصفحة تصبح فارغة

---

## ✅ الحل (مهم جداً!)

### الخطوة 1: تحديد رابط Production الصحيح

**أحتاج منك رابط Backend في Production!**

مثال:
```
https://your-domain.com
أو
https://medidoc-ai.production.emergentagent.com
أو
https://api.your-domain.com
```

### الخطوة 2: تحديث الملف

بعد معرفة الرابط، حدّث `/app/frontend/.env`:

```bash
# افتح الملف
nano /app/frontend/.env

# غيّر السطر الأول إلى:
REACT_APP_BACKEND_URL=https://YOUR-PRODUCTION-URL
```

### الخطوة 3: إعادة تشغيل Frontend

```bash
sudo supervisorctl restart frontend
```

### الخطوة 4: اختبار

```
1. افتح الموقع
2. سجّل دخول
3. أدخل OTP
4. يجب أن تصل للـ Dashboard ✅
```

---

## 🔄 خيارات لتحديث الرابط

### الخيار 1: إذا كان لديك SSH للخادم

```bash
# 1. SSH إلى الخادم
ssh user@production-server

# 2. حدّث .env
sed -i 's|medidoc-ai-1.preview.emergentagent.com|YOUR-PRODUCTION-DOMAIN|g' /app/frontend/.env

# 3. أعد تشغيل
sudo supervisorctl restart frontend
```

### الخيار 2: إذا لم يكن لديك SSH

```
1. احفظ التغييرات على GitHub (بعد تحديث .env هنا)
2. أعد النشر
3. شغّل migration مرة أخرى
```

### الخيار 3: تحديث من منصة النشر

بعض منصات النشر تسمح بتحديث Environment Variables:
```
1. اذهب لإعدادات المشروع
2. Environment Variables
3. حدّث REACT_APP_BACKEND_URL
4. أعد النشر
```

---

## 📋 التحقق من نجاح الإصلاح

### اختبار سريع:

```bash
# 1. افتح console في المتصفح (F12)
# 2. في Console اكتب:
console.log(process.env.REACT_APP_BACKEND_URL)

# يجب أن يُظهر رابط Production، ليس Preview
```

### اختبار شامل:

```
1. افتح الموقع
2. افتح Network tab في DevTools (F12)
3. سجّل دخول
4. أدخل OTP
5. راقب الطلبات - يجب أن تذهب لـ Production URL
6. يجب أن تصل للـ Dashboard
```

---

## ⚠️ ملاحظات مهمة

### لا تنسى تحديث Backend URL أيضاً:

في `/app/backend/.env`:
```bash
FRONTEND_URL=https://YOUR-PRODUCTION-FRONTEND-URL
```

### إذا كان لديك أكثر من بيئة:

يُفضل إنشاء:
- `.env.preview` (للـ Preview)
- `.env.production` (للـ Production)

---

## 🚨 حل سريع مؤقت (للطوارئ)

إذا كنت بحاجة لحل فوري:

### في الكود مباشرة (غير موصى به للإنتاج):

```javascript
// في /app/frontend/src/pages/MFAVerification.jsx
// أضف في بداية الملف:
const API = "https://YOUR-PRODUCTION-URL";

// بدلاً من:
// const API = process.env.REACT_APP_BACKEND_URL;
```

**⚠️ هذا حل مؤقت فقط! استخدم .env للحل الدائم**

---

## 📞 ما أحتاجه منك

**أخبرني برابط Production الصحيح وسأحدث الملفات فوراً!**

الرابط يجب أن يكون مثل:
```
https://your-domain.com
أو
https://api.your-domain.com
أو
https://medidoc-ai.production.com
```

---

**تاريخ الإنشاء:** 2024-11-07  
**الأولوية:** 🚨 **CRITICAL**  
**الحالة:** في انتظار رابط Production
