# 📋 التوثيق الفني الشامل لنظام MediDoc AI

## مركز تحسين التوثيق السريري والترميز الطبي

---

## معلومات المشروع

| البند | القيمة |
|-------|--------|
| اسم النظام | MediDoc AI |
| الإصدار | 2.0 |
| المطور | عمر المغذوي |
| الجهة | تجمع المدينة المنورة الصحي |

---

## 📑 فهرس المحتويات

1. [نظرة عامة على النظام](#1-نظرة-عامة-على-النظام)
2. [البنية التقنية](#2-البنية-التقنية)
3. [تقنيات البرمجة](#3-تقنيات-البرمجة)
4. [قاعدة البيانات](#4-قاعدة-البيانات)
5. [واجهات API](#5-واجهات-api)
6. [متطلبات الأجهزة](#6-متطلبات-الأجهزة)
7. [التشغيل الأوفلاين](#7-التشغيل-الأوفلاين)
8. [النقل لوزارة الصحة](#8-النقل-لوزارة-الصحة)
9. [الأمان والحماية](#9-الأمان-والحماية)
10. [دليل التثبيت](#10-دليل-التثبيت)
11. [الصيانة](#11-الصيانة)

---

## 1. نظرة عامة على النظام

### 1.1 وصف النظام

نظام **MediDoc AI** هو منصة متكاملة لتحسين التوثيق السريري (CDI) والترميز الطبي، يعتمد على الذكاء الاصطناعي لتحليل الملاحظات السريرية وتقديم اقتراحات لتحسين التوثيق الطبي.

### 1.2 الميزات الرئيسية

- ✅ تحليل الملاحظات السريرية بالذكاء الاصطناعي (Gemini AI)
- ✅ اقتراح أكواد ICD-10-CM تلقائياً
- ✅ نظام محادثة ذكي للاستفسارات الطبية
- ✅ لوحة تحكم للمشرفين مع تقارير شاملة
- ✅ نظام إدارة المستخدمين والصلاحيات
- ✅ المصادقة الثنائية (MFA)
- ✅ تصدير التقارير بصيغ PDF و Excel
- ✅ دعم كامل للغة العربية (RTL)

---

## 2. البنية التقنية

### 2.1 نمط البنية

```
Three-Tier Architecture (بنية ثلاثية الطبقات)

┌─────────────────────────────────────────────────────────────┐
│                    المستخدمون (Users)                        │
│                   متصفح الويب (Browser)                      │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTPS (Port 443)
┌─────────────────────────▼───────────────────────────────────┐
│                 Nginx Reverse Proxy                         │
│                    (Load Balancer)                          │
└─────────────┬───────────────────────────────┬───────────────┘
              │                               │
┌─────────────▼─────────────┐   ┌─────────────▼─────────────┐
│     Frontend Server       │   │     Backend Server        │
│      React.js:3000        │   │     FastAPI:8001          │
│    (Presentation Layer)   │   │   (Application Layer)     │
└───────────────────────────┘   └─────────────┬─────────────┘
                                              │
                                ┌─────────────▼─────────────┐
                                │        MongoDB            │
                                │       Port: 27017         │
                                │      (Data Layer)         │
                                └─────────────┬─────────────┘
                                              │
                                ┌─────────────▼─────────────┐
                                │     External Services     │
                                │   • Google Gemini AI      │
                                │   • SMTP Email Server     │
                                └───────────────────────────┘
```

### 2.2 الطبقات

| الطبقة | التقنية | الوصف |
|--------|---------|-------|
| العرض (Presentation) | React.js 19 | واجهة المستخدم التفاعلية |
| التطبيق (Application) | FastAPI | معالجة الطلبات والمنطق |
| البيانات (Data) | MongoDB | تخزين البيانات |

---

## 3. تقنيات البرمجة

### 3.1 الواجهة الأمامية (Frontend)

| التقنية | الإصدار | الاستخدام |
|---------|---------|-----------|
| React.js | 19.0.0 | إطار واجهة المستخدم |
| React Router DOM | 7.x | التوجيه والملاحة |
| Axios | 1.x | طلبات HTTP |
| Tailwind CSS | 3.4.x | تصميم UI |
| Shadcn/UI | 0.x | مكونات جاهزة |
| Lucide React | 0.x | الأيقونات |
| Sonner | 1.x | الإشعارات |
| Recharts | 2.x | الرسوم البيانية |

### 3.2 الواجهة الخلفية (Backend)

| التقنية | الإصدار | الاستخدام |
|---------|---------|-----------|
| Python | 3.11+ | لغة البرمجة |
| FastAPI | 0.110+ | إطار API |
| Motor | 4.6+ | Async MongoDB Driver |
| PyJWT | - | JWT Tokens |
| bcrypt | 4.1+ | تشفير كلمات المرور |
| Google Generative AI | Gemini 2.0 | الذكاء الاصطناعي |
| ReportLab | 4.x | إنشاء PDF |
| OpenPyXL | 3.x | إنشاء Excel |
| aiosmtplib | 4.x | البريد الإلكتروني |
| SlowAPI | 0.1.x | تحديد المعدل |
| Prometheus | 0.x | المراقبة |

### 3.3 البنية التحتية

| التقنية | الاستخدام |
|---------|-----------|
| MongoDB 6.x/7.x | قاعدة البيانات |
| Nginx | Reverse Proxy |
| Docker | الحاويات (اختياري) |
| Supervisor | إدارة العمليات |

---

## 4. قاعدة البيانات

### 4.1 نوع قاعدة البيانات

**MongoDB** - قاعدة بيانات NoSQL

#### أسباب الاختيار:
- المرونة في تخزين البيانات غير المنظمة
- الأداء العالي مع البيانات الكبيرة
- سهولة التوسع الأفقي (Horizontal Scaling)
- دعم ممتاز للعمليات غير المتزامنة (Async)

### 4.2 المجموعات (Collections)

| المجموعة | الوصف | عدد الوثائق التقريبي |
|----------|-------|---------------------|
| users | بيانات المستخدمين | ~10+ |
| clinical_notes | الملاحظات السريرية | ~40+ |
| analyses | نتائج التحليل | ~40+ |
| user_sessions | جلسات المستخدمين | ~35+ |
| chat_messages | رسائل المحادثة | ~100+ |
| hospitals | المستشفيات | ~5+ |
| drg_prices | أسعار DRG | ~3+ |
| audit_logs | سجلات الأمان | ~10+ |
| ai_settings | إعدادات AI | ~2+ |
| otp_records | رموز OTP | متغير |

### 4.3 مخطط البيانات (Schema)

#### جدول المستخدمين (users):
```json
{
  "id": "UUID",
  "email": "string (unique, indexed)",
  "password_hash": "string (bcrypt)",
  "full_name": "string",
  "phone_number": "string",
  "role": "enum: user | admin | supervisor",
  "department": "enum: cdi | coding",
  "coding_role": "enum: coder | auditor | supervisor",
  "mfa_enabled": "boolean (default: true)",
  "is_active": "boolean",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

#### جدول الملاحظات السريرية (clinical_notes):
```json
{
  "id": "UUID",
  "user_id": "UUID (foreign key)",
  "title": "string",
  "patient_name": "string",
  "doctor_notes": [
    {
      "text": "string",
      "specialty": "string",
      "timestamp": "datetime"
    }
  ],
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

#### جدول التحليلات (analyses):
```json
{
  "id": "UUID",
  "note_id": "UUID (foreign key)",
  "user_id": "UUID (foreign key)",
  "diagnoses_to_document": [
    {
      "diagnosis_ar": "string",
      "diagnosis_en": "string",
      "icd_code": "string"
    }
  ],
  "missing_documentation": ["array of objects"],
  "cdi_opportunities": ["array of strings"],
  "queries_ar": ["array of strings"],
  "queries_en": ["array of strings"],
  "created_at": "datetime"
}
```

---

## 5. واجهات API

### 5.1 نقاط النهاية الرئيسية

| المسار | الطريقة | الوصف |
|--------|---------|-------|
| /api/auth/login-step1 | POST | تسجيل الدخول (الخطوة 1) |
| /api/auth/login-step2 | POST | التحقق من OTP |
| /api/auth/register | POST | تسجيل مستخدم جديد |
| /api/notes | GET/POST | الملاحظات السريرية |
| /api/notes/{id} | GET/PUT/DELETE | ملاحظة محددة |
| /api/analyze | POST | تحليل ملاحظة |
| /api/clinical-questions | GET | الأسئلة السريرية |
| /api/chat/ask-question/{id} | POST | سؤال جاهز |
| /api/chat/message | POST | رسالة حرة |
| /api/supervisor/stats | GET | إحصائيات المشرف |
| /api/supervisor/monthly-report | GET | تقرير شهري |
| /api/ai-settings | GET/PUT | إعدادات AI |

### 5.2 المصادقة

```
نوع المصادقة: JWT (JSON Web Tokens)
صلاحية التوكن: 7 أيام
خوارزمية التشفير: HS256

Header Format:
Authorization: Bearer {access_token}
```

### 5.3 حدود المعدل (Rate Limiting)

| النقطة | الحد |
|--------|------|
| Login | 5 طلبات/دقيقة |
| Analyze | 20 طلب/دقيقة |
| Chat | 30 رسالة/دقيقة |
| General | 100 طلب/دقيقة |

---

## 6. متطلبات الأجهزة

### 6.1 متطلبات السيرفر (Production)

| المكون | الحد الأدنى | الموصى به |
|--------|-------------|-----------|
| المعالج (CPU) | 8 Core | 16 Core |
| الذاكرة (RAM) | 16 GB | 32 GB |
| التخزين | 200 GB SSD | 500 GB SSD |
| الشبكة | 100 Mbps | 1 Gbps |

### 6.2 متطلبات البرمجيات

| البرنامج | الإصدار |
|----------|---------|
| نظام التشغيل | Ubuntu 22.04 LTS / RHEL 8+ |
| Python | 3.11+ |
| Node.js | 20.x LTS |
| MongoDB | 6.x أو 7.x |
| Nginx | 1.24+ |
| Docker (اختياري) | 20.x+ |

---

## 7. التشغيل الأوفلاين

### 7.1 التحديات الرئيسية

لتشغيل النظام بدون اتصال بالإنترنت:

1. **استبدال Gemini AI** بنموذج محلي
2. **البريد الإلكتروني** - توفير خدمة داخلية أو تعطيل MFA
3. **الاعتماديات** - تحميل جميع المكتبات مسبقاً

### 7.2 خيارات النماذج المحلية

| النموذج | الحجم | المتطلبات |
|---------|-------|-----------|
| Llama 3 | 7B-70B | GPU 24GB+ أو CPU 32GB RAM |
| Phi-3 | 3.8B | GPU 8GB+ أو CPU 16GB RAM |
| Meditron | 7B | GPU 16GB+ (متخصص طبياً) |
| Mistral | 7B | GPU 8GB+ أو CPU 16GB RAM |

### 7.3 البرمجيات المطلوبة للأوفلاين

| البرنامج | الغرض |
|----------|-------|
| Ollama | تشغيل النماذج المحلية |
| Mailhog | بديل للبريد (اختياري) |
| Docker | الحاويات |

### 7.4 خطوات التحضير للأوفلاين

```bash
# 1. تحميل اعتماديات Python
pip download -r requirements.txt -d ./offline_packages/

# 2. تحميل اعتماديات Node.js
yarn config set yarn-offline-mirror ./npm-packages-offline-cache
yarn install

# 3. تحميل نموذج AI المحلي
ollama pull phi3
# أو للنموذج الطبي:
ollama pull meditron

# 4. تصدير قاعدة البيانات
mongodump --db clinical_doc_center --out ./backup/

# 5. إنشاء صورة Docker كاملة
docker build -t medidoc-ai:offline .
docker save medidoc-ai:offline > medidoc-offline.tar
```

### 7.5 تعديلات الكود للأوفلاين

```python
# في server.py - استبدال Gemini بـ Ollama

import requests

def get_local_ai_response(prompt: str) -> str:
    """استخدام نموذج محلي بدلاً من Gemini"""
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "phi3",
            "prompt": prompt,
            "stream": False
        }
    )
    return response.json()["response"]
```

---

## 8. النقل لوزارة الصحة

### 8.1 المتطلبات الأمنية

- ✅ شهادة SSL/TLS صالحة
- ✅ تشفير البيانات (at-rest و in-transit)
- ✅ جدار حماية (Firewall)
- ✅ نظام كشف التسلل (IDS/IPS)
- ✅ سجلات أمنية (Audit Logs)
- ✅ المصادقة الثنائية (MFA)
- ✅ سياسات كلمات مرور قوية

### 8.2 المتطلبات التنظيمية

- ✅ التوافق مع نظام حماية البيانات الشخصية السعودي
- ✅ التوافق مع معايير HIPAA (إن لزم)
- ✅ سياسة الاحتفاظ بالبيانات
- ✅ خطة استعادة الكوارث (DR)
- ✅ اتفاقية مستوى الخدمة (SLA)

### 8.3 متطلبات الشبكة

| المتطلب | القيمة |
|---------|--------|
| عنوان IP | Static IP أو DNS |
| المنافذ | 443 (HTTPS), 27017 (MongoDB) |
| عرض النطاق | 50 Mbps+ |
| VPN | مطلوب للوصول الإداري |

### 8.4 الوثائق المطلوبة للنقل

1. 📄 وثيقة البنية التقنية (هذا المستند)
2. 📄 دليل التثبيت والتشغيل
3. 📄 تقرير اختبار الاختراق (Penetration Test)
4. 📄 شهادة تقييم الأمان
5. 📄 خطة النسخ الاحتياطي
6. 📄 قائمة الاعتماديات والتراخيص
7. 📄 دليل المستخدم

### 8.5 خطوات النقل

```bash
# 1. تجهيز السيرفر
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11 nodejs npm mongodb nginx docker.io

# 2. نقل الملفات
scp -r ./medidoc-ai user@server:/opt/

# 3. إعداد البيئة
cd /opt/medidoc-ai
cp .env.example .env
nano .env  # تعديل القيم

# 4. تشغيل الخدمات
docker-compose up -d

# 5. إعداد Nginx
sudo cp nginx.conf /etc/nginx/sites-available/medidoc
sudo ln -s /etc/nginx/sites-available/medidoc /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx

# 6. إعداد SSL
sudo certbot --nginx -d yourdomain.moh.gov.sa
```

---

## 9. الأمان والحماية

### 9.1 حماية البيانات

| الإجراء | التطبيق |
|---------|---------|
| تشفير كلمات المرور | bcrypt مع salt عشوائي |
| تشفير الاتصال | HTTPS مع TLS 1.3 |
| تشفير قاعدة البيانات | MongoDB encryption |
| إدارة الجلسات | JWT with expiry |
| حماية DDoS | Rate limiting |
| SQL Injection | Input sanitization |
| CSRF | CORS policy |

### 9.2 سجلات الأمان

يسجل النظام:
- محاولات تسجيل الدخول
- تغييرات بيانات المستخدمين
- الوصول للملفات الحساسة
- عمليات التحليل
- أخطاء النظام

---

## 10. دليل التثبيت

### 10.1 التثبيت باستخدام Docker

```bash
# 1. استنساخ المشروع
git clone https://github.com/your-repo/medidoc-ai.git
cd medidoc-ai

# 2. إنشاء ملف البيئة
cp .env.example .env
nano .env

# 3. بناء وتشغيل
docker-compose up -d --build

# 4. التحقق
docker-compose ps
docker-compose logs -f
```

### 10.2 التثبيت اليدوي

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8001

# Frontend
cd frontend
yarn install
yarn build
serve -s build -l 3000

# MongoDB
sudo systemctl start mongod
```

### 10.3 متغيرات البيئة

| المتغير | الوصف |
|---------|-------|
| MONGO_URL | رابط MongoDB |
| DB_NAME | اسم قاعدة البيانات |
| JWT_SECRET | مفتاح JWT |
| GEMINI_API_KEY_1..7 | مفاتيح Gemini API |
| SMTP_HOST | خادم البريد |
| SMTP_PORT | منفذ البريد |
| SMTP_USER | مستخدم البريد |
| SMTP_PASSWORD | كلمة مرور البريد |
| FRONTEND_URL | رابط الواجهة |

---

## 11. الصيانة

### 11.1 النسخ الاحتياطي

```bash
#!/bin/bash
# daily_backup.sh
DATE=$(date +%Y%m%d)
mongodump --db clinical_doc_center --out /backup/$DATE
tar -czf /backup/medidoc_$DATE.tar.gz /backup/$DATE
find /backup -name "*.tar.gz" -mtime +30 -delete
```

### 11.2 المراقبة

```
Prometheus Metrics: http://localhost:8001/metrics

المقاييس المتاحة:
- عدد الطلبات
- زمن الاستجابة
- معدل الأخطاء
- استخدام الذاكرة
```

### 11.3 تحديث النظام

```bash
# تحديث الكود
git pull origin main

# تحديث الاعتماديات
cd backend && pip install -r requirements.txt
cd frontend && yarn install

# إعادة التشغيل
docker-compose down && docker-compose up -d --build
```

---

## معلومات الاتصال

| البند | القيمة |
|-------|--------|
| المطور | عمر المغذوي |
| البريد | almaghthawi.cdi@gmail.com |
| الجهة | تجمع المدينة المنورة الصحي |

---

**© 2025 MediDoc AI - جميع الحقوق محفوظة**
