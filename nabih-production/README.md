<div dir="rtl">

# نـبـيـه | NABIH
## منصة تحسين التوثيق السريري بالذكاء الاصطناعي
### AI-Powered Clinical Documentation Improvement Platform

---

<div align="center">

![Version](https://img.shields.io/badge/version-3.0.0-blue)
![License](https://img.shields.io/badge/license-Proprietary-red)
![AI Model](https://img.shields.io/badge/AI-Qwen2.5--32B-green)
![GPU](https://img.shields.io/badge/GPU-NVIDIA%20V100-orange)

</div>

---

## 📋 نظرة عامة | Overview

**نبيه (NABIH)** هي منصة متقدمة لتحسين التوثيق السريري (CDI - Clinical Documentation Improvement) تعتمد على الذكاء الاصطناعي المتطور. تساعد المنصة أخصائيي الترميز الطبي والأطباء على تحسين جودة التوثيق الطبي وضمان دقة الترميز وفقاً لمعايير ICD-10-AM و ACS.

**NABIH** is an advanced Clinical Documentation Improvement (CDI) platform powered by cutting-edge AI. It helps medical coding specialists and physicians improve medical documentation quality and ensure accurate coding according to ICD-10-AM and ACS standards.

---

## ✨ الميزات الرئيسية | Key Features

### 🔍 تحليل ذكي للملاحظات السريرية
- استخراج التشخيصات الموثقة نصاً (Principal & Secondary)
- استنتاج التشخيصات من نتائج التحاليل والعلاجات
- التعرف على الاختصارات الطبية (DM, HTN, CKD, CHF...)
- تحديد الفجوات في التوثيق

### 📊 ترميز طبي دقيق
- أكواد ICD-10-AM لكل تشخيص
- ربط DRG للتسعير
- مراجع ACS Standards
- دعم المعايير السعودية والخليجية

### 💬 مناقشة تفاعلية
- دردشة ذكية لمناقشة الحالات
- تحليل المعلومات الجديدة (أدوية، تحاليل، ملاحظات عمليات)
- استفسارات غير موجهة للأطباء

### 🌐 دعم ثنائي اللغة
- واجهة كاملة بالعربية والإنجليزية
- تحليل الملاحظات بكلتا اللغتين
- تقارير متعددة اللغات

---

## 🏗️ البنية التقنية | Technical Architecture

```
nabih-production/
├── src/
│   ├── backend/           # FastAPI Backend
│   │   ├── server.py      # Main API server
│   │   ├── local_llm.py   # AI Engine (vLLM + Qwen)
│   │   ├── analysis_wrapper.py
│   │   ├── security_utils.py
│   │   ├── drg_lookup.py
│   │   └── acs_reference.py
│   │
│   └── frontend/          # React Frontend
│       ├── src/
│       │   ├── pages/
│       │   ├── components/
│       │   └── contexts/
│       └── package.json
│
├── config/
│   ├── nginx.conf         # Nginx configuration
│   ├── systemd.service    # Systemd service file
│   └── environment.example
│
├── docs/
│   ├── API.md
│   ├── DEPLOYMENT.md
│   └── USER_GUIDE.md
│
├── scripts/
│   ├── setup.sh
│   ├── deploy.sh
│   └── backup.sh
│
└── data/
    └── (ACS & DRG reference files)
```

---

## 🤖 نموذج الذكاء الاصطناعي | AI Model

### المواصفات
| البند | القيمة |
|-------|--------|
| **النموذج** | Qwen2.5-32B-Instruct-GPTQ-Int4 |
| **المطور** | Alibaba Cloud (Qwen Team) |
| **الحجم** | 32 Billion Parameters |
| **الكمية** | GPTQ Int4 Quantization |
| **المحرك** | vLLM Inference Engine |
| **السياق** | 8,192 tokens |

### القدرات
- فهم الملاحظات السريرية بالعربية والإنجليزية
- استخراج التشخيصات بدقة عالية
- استنتاج التشخيصات من المعطيات السريرية
- توليد استفسارات غير موجهة للأطباء
- الالتزام بمعايير التوثيق الطبي

---

## 💻 متطلبات النظام | System Requirements

### الأجهزة (Hardware)
| المتطلب | الحد الأدنى | الموصى به |
|---------|-------------|-----------|
| **GPU** | NVIDIA T4 16GB | NVIDIA V100 32GB |
| **RAM** | 32 GB | 64 GB |
| **CPU** | 8 cores | 16 cores |
| **Storage** | 100 GB SSD | 200 GB NVMe |
| **CUDA** | 11.8+ | 12.x |

### البرمجيات (Software)
- Ubuntu 22.04 LTS / 24.04 LTS
- Python 3.10+
- Node.js 18+
- MongoDB 6.0+
- Nginx 1.24+
- NVIDIA Driver 535+

---

## 🚀 التثبيت والنشر | Installation & Deployment

### 1. استنساخ المستودع
```bash
git clone https://github.com/[your-username]/nabih-platform.git
cd nabih-platform
```

### 2. إعداد البيئة
```bash
# Backend
cd src/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd ../frontend
yarn install
yarn build
```

### 3. إعداد المتغيرات البيئية
```bash
cp config/environment.example src/backend/.env
# Edit .env with your settings
```

### 4. تشغيل الخدمات
```bash
# Using systemd
sudo cp config/systemd.service /etc/systemd/system/nabih.service
sudo systemctl enable nabih
sudo systemctl start nabih

# Nginx
sudo cp config/nginx.conf /etc/nginx/sites-available/nabih
sudo ln -s /etc/nginx/sites-available/nabih /etc/nginx/sites-enabled/
sudo nginx -s reload
```

---

## 📡 واجهات API | API Endpoints

### المصادقة (Authentication)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/login-step1` | POST | Login (request OTP) |
| `/api/auth/login-step2` | POST | Verify OTP |
| `/api/auth/register` | POST | Register new user |

### الملاحظات (Notes)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/notes` | GET/POST | List/Create notes |
| `/api/notes/{id}` | GET/PUT/DELETE | Single note operations |

### التحليل (Analysis)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/analyze` | POST | Analyze clinical note |
| `/api/analysis/{id}` | GET | Get analysis result |
| `/api/chat/ask-question/{q}` | POST | Interactive chat |

---

## 🔐 الأمان | Security

- 🔒 **JWT Authentication** - Token-based security
- 📱 **MFA/OTP** - Two-factor authentication via email
- 🔑 **bcrypt** - Password hashing
- 🛡️ **HTTPS** - TLS encryption
- 🚫 **CORS** - Origin restriction
- ⏱️ **Rate Limiting** - Request throttling

---

## 📊 قواعد استنتاج التشخيصات | Diagnosis Inference Rules

| نتيجة التحليل | + العلاج | = التشخيص | ICD-10 |
|--------------|----------|-----------|--------|
| Na > 145 | تصحيح سوائل | Hypernatremia | E87.0 |
| Na < 135 | تصحيح صوديوم | Hyponatremia | E87.1 |
| K > 5.5 | علاج بوتاسيوم | Hyperkalemia | E87.5 |
| K < 3.5 | تعويض بوتاسيوم | Hypokalemia | E87.6 |
| Hb < 12 | نقل دم/حديد | Anemia | D64.9 |
| HbA1c > 8% | - | Uncontrolled DM | E11.65 |
| Cr↑ + GFR↓ | - | CKD (staged) | N18.x |
| WBC↑ + حرارة + ATB | - | Sepsis | A41.9 |

---

## 📄 الترخيص | License

هذا المشروع ملكية خاصة. جميع الحقوق محفوظة.

This project is proprietary. All rights reserved.

---

## 📞 التواصل | Contact

للاستفسارات التجارية والشراكات:
- 📧 Email: [contact@nabih.ai]
- 🌐 Website: [www.nabih.ai]

---

<div align="center">

**صُنع بـ ❤️ لتحسين الرعاية الصحية**

**Built with ❤️ to improve healthcare**

</div>

</div>
