# منصة نبيه | NABIH Platform
## توثيق شامل للنظام

---

# 1. نظرة عامة على المنصة

## 1.1 الوصف
**منصة نبيه (NABIH)** هي منصة متقدمة لتحسين التوثيق السريري (Clinical Documentation Improvement - CDI) تعمل بالذكاء الاصطناعي. تساعد المختصين في الترميز الطبي على:
- تحليل الملاحظات السريرية
- استخراج التشخيصات الموثقة والمستنتجة
- تحديد الفجوات في التوثيق
- توليد استفسارات غير موجهة للأطباء
- ربط التشخيصات بأكواد ICD-10-AM

## 1.2 الميزات الرئيسية
| الميزة | الوصف |
|--------|--------|
| تحليل CDI بالذكاء الاصطناعي | تحليل شامل للملاحظات السريرية |
| استخراج التشخيصات | موثقة نصاً + مستنتجة من التحاليل |
| دعم الاختصارات الطبية | DM, HTN, CKD, AKI, CHF, etc. |
| استنتاج ذكي | من نتائج التحاليل + العلاج المقدم |
| أكواد ICD-10-AM | لكل تشخيص |
| تعدد اللغات | عربي / إنجليزي |
| تحقق أمني MFA | عبر البريد الإلكتروني |
| تصدير التقارير | PDF / Excel |

---

# 2. مواصفات السيرفر

## 2.1 معلومات الأجهزة
| المواصفة | القيمة |
|----------|--------|
| **مزود الخدمة** | Alibaba Cloud |
| **نوع السيرفر** | ECS GPU Instance |
| **IP العام** | 8.213.39.104 |
| **نظام التشغيل** | Ubuntu 24.04.3 LTS |
| **Kernel** | 6.8.0-87-generic |

## 2.2 المعالج (CPU)
| المواصفة | القيمة |
|----------|--------|
| **النوع** | Intel Xeon |
| **عدد الأنوية** | 8 cores |
| **الخيوط** | 16 threads |

## 2.3 الذاكرة (RAM)
| المواصفة | القيمة |
|----------|--------|
| **الإجمالي** | ~64 GB |
| **المتاح للنظام** | ~60 GB |

## 2.4 وحدة معالجة الرسومات (GPU)
| المواصفة | القيمة |
|----------|--------|
| **النوع** | NVIDIA Tesla V100 |
| **الذاكرة** | 32 GB HBM2 |
| **CUDA Version** | 12.8 |
| **Driver Version** | 570.133.20 |
| **الاستخدام** | تشغيل نموذج الذكاء الاصطناعي |

## 2.5 التخزين
| المواصفة | القيمة |
|----------|--------|
| **السعة الكلية** | 196.49 GB |
| **المستخدم** | ~37.7% |
| **المتاح** | ~122 GB |

---

# 3. البنية التقنية

## 3.1 هيكل التطبيق
```
/opt/medidoc/
├── backend/                 # الخادم الخلفي (FastAPI)
│   ├── server.py           # الملف الرئيسي للـ API
│   ├── local_llm.py        # محرك الذكاء الاصطناعي vLLM
│   ├── analysis_wrapper.py # معالج نتائج التحليل
│   ├── security_utils.py   # أدوات الأمان و OTP
│   ├── drg_lookup.py       # البحث في جداول DRG
│   ├── acs_reference.py    # مرجع معايير ACS
│   ├── venv/               # البيئة الافتراضية Python
│   ├── data/               # ملفات البيانات
│   │   ├── Full ACS 10th edition_.pdf
│   │   └── drg_prices.xlsx
│   └── .env                # متغيرات البيئة
│
└── frontend/               # الواجهة الأمامية (React)
    ├── static/
    │   ├── js/
    │   └── css/
    └── index.html
```

## 3.2 التقنيات المستخدمة

### Backend (الخادم الخلفي)
| التقنية | الإصدار | الوصف |
|---------|---------|--------|
| **Python** | 3.12+ | لغة البرمجة |
| **FastAPI** | Latest | إطار العمل للـ API |
| **vLLM** | 0.13.0 | محرك تشغيل النماذج اللغوية |
| **Uvicorn** | Latest | خادم ASGI |
| **PyMongo** | Latest | مكتبة MongoDB |
| **Pydantic** | v2 | التحقق من البيانات |
| **bcrypt** | Latest | تشفير كلمات المرور |
| **PyJWT** | Latest | JSON Web Tokens |
| **aiosmtplib** | Latest | إرسال البريد الإلكتروني |
| **pandas** | Latest | معالجة البيانات |
| **openpyxl** | Latest | قراءة ملفات Excel |

### Frontend (الواجهة الأمامية)
| التقنية | الإصدار | الوصف |
|---------|---------|--------|
| **React** | 18.x | مكتبة واجهة المستخدم |
| **Tailwind CSS** | 3.x | إطار CSS |
| **Shadcn/UI** | Latest | مكونات UI |
| **Axios** | Latest | طلبات HTTP |
| **Lucide React** | Latest | الأيقونات |
| **i18next** | Latest | تعدد اللغات |

### قاعدة البيانات
| التقنية | الإصدار | الوصف |
|---------|---------|--------|
| **MongoDB** | 7.x | قاعدة بيانات NoSQL |
| **Database Name** | clinical_doc_center | |

### خادم الويب
| التقنية | الإصدار | الوصف |
|---------|---------|--------|
| **Nginx** | Latest | خادم الويب والـ Reverse Proxy |

---

# 4. نموذج الذكاء الاصطناعي

## 4.1 المواصفات
| المواصفة | القيمة |
|----------|--------|
| **اسم النموذج** | Qwen2.5-32B-Instruct-GPTQ-Int4 |
| **المطور** | Alibaba (Qwen) |
| **الحجم** | 32 Billion Parameters |
| **الكمية (Quantization)** | GPTQ Int4 |
| **الذاكرة المطلوبة** | ~18 GB GPU |
| **السياق الأقصى** | 8,192 tokens |
| **درجة الحرارة** | 0.0 (حتمي) |

## 4.2 قدرات النموذج
- فهم الملاحظات السريرية بالعربية والإنجليزية
- استخراج التشخيصات من النص
- التعرف على الاختصارات الطبية
- استنتاج التشخيصات من نتائج التحاليل
- توليد استفسارات للأطباء بصيغة غير موجهة
- الالتزام بمعايير ACS و ICD-10-AM

## 4.3 قواعد الاستنتاج
| نتيجة التحليل | + العلاج | = التشخيص | الكود |
|--------------|----------|-----------|-------|
| Na > 145 | تصحيح سوائل | Hypernatremia | E87.0 |
| Na < 135 | تصحيح صوديوم | Hyponatremia | E87.1 |
| K > 5.5 | كايكسالات/غسيل | Hyperkalemia | E87.5 |
| K < 3.5 | بوتاسيوم | Hypokalemia | E87.6 |
| Hb < 12 | نقل دم/حديد | Anemia | D64.9 |
| HbA1c > 8% | - | Uncontrolled DM | E11.65 |
| Cr↑ + GFR↓ | - | CKD | N18.x |
| WBC↑ + حرارة | مضاد حيوي | Sepsis | A41.9 |

---

# 5. واجهات برمجة التطبيقات (APIs)

## 5.1 نقاط النهاية الرئيسية
| المسار | الطريقة | الوصف |
|--------|---------|--------|
| `/api/auth/login-step1` | POST | الخطوة الأولى لتسجيل الدخول |
| `/api/auth/login-step2` | POST | التحقق من OTP |
| `/api/auth/register` | POST | تسجيل مستخدم جديد |
| `/api/notes` | GET/POST | إدارة الملاحظات |
| `/api/notes/{id}` | GET/PUT/DELETE | ملاحظة محددة |
| `/api/analyze` | POST | تحليل ملاحظة |
| `/api/analysis/{id}` | GET | نتيجة تحليل |
| `/api/chat/ask-question/{q}` | POST | أسئلة سريعة |
| `/api/users` | GET | قائمة المستخدمين (Admin) |

## 5.2 المصادقة
- **نوع المصادقة:** JWT (JSON Web Token)
- **التحقق الثنائي:** MFA عبر OTP بالبريد الإلكتروني
- **مدة صلاحية Token:** 24 ساعة
- **مدة صلاحية OTP:** 30 دقيقة

---

# 6. قاعدة البيانات

## 6.1 المجموعات (Collections)
| المجموعة | الوصف |
|----------|--------|
| `users` | بيانات المستخدمين |
| `clinical_notes` | الملاحظات السريرية |
| `analyses` | نتائج التحليل |
| `otp_records` | سجلات OTP |
| `user_sessions` | جلسات المستخدمين |
| `chat_messages` | رسائل الدردشة |
| `audit_logs` | سجلات المراجعة |
| `login_attempts` | محاولات تسجيل الدخول |

## 6.2 نموذج المستخدم
```json
{
  "id": "UUID",
  "email": "string",
  "password_hash": "string",
  "full_name": "string",
  "phone_number": "string",
  "role": "admin | user | supervisor",
  "mfa_enabled": true,
  "is_active": true,
  "created_at": "datetime",
  "last_login": "datetime"
}
```

## 6.3 نموذج الملاحظة السريرية
```json
{
  "id": "UUID",
  "user_id": "UUID",
  "title": "string",
  "content": "string",
  "doctor_notes": [
    {
      "specialty": "string",
      "text": "string"
    }
  ],
  "analysis_result_id": "UUID",
  "created_at": "datetime"
}
```

---

# 7. الأمان

## 7.1 إجراءات الأمان
| الإجراء | الوصف |
|---------|--------|
| **تشفير كلمات المرور** | bcrypt مع salt |
| **JWT** | توقيع HS256 |
| **MFA** | OTP عبر البريد |
| **HTTPS** | تشفير الاتصال |
| **CORS** | تقييد المصادر |
| **Rate Limiting** | حماية من الهجمات |

## 7.2 إعدادات SMTP
| الإعداد | القيمة |
|---------|--------|
| **SMTP Host** | smtp.gmail.com |
| **SMTP Port** | 587 |
| **TLS** | نعم |

---

# 8. الخدمات والعمليات

## 8.1 خدمات Systemd
| الخدمة | الملف | الوصف |
|--------|-------|--------|
| `medidoc-backend` | `/etc/systemd/system/medidoc-backend.service` | الخادم الخلفي |
| `nginx` | Built-in | خادم الويب |
| `mongod` | Built-in | قاعدة البيانات |

## 8.2 أوامر الإدارة
```bash
# إعادة تشغيل الخلفية
systemctl restart medidoc-backend

# فحص الحالة
systemctl status medidoc-backend

# عرض السجلات
journalctl -u medidoc-backend -n 100

# إعادة تشغيل Nginx
nginx -s reload
```

---

# 9. هيكل الملفات

## 9.1 ملفات الإعدادات
| الملف | الموقع | الوصف |
|-------|--------|--------|
| `.env` | `/opt/medidoc/backend/` | متغيرات البيئة |
| `nginx config` | `/etc/nginx/sites-available/medidoc` | إعدادات Nginx |
| `systemd service` | `/etc/systemd/system/medidoc-backend.service` | خدمة الخلفية |

## 9.2 محتوى ملف .env
```env
MONGO_URL="mongodb://localhost:27017"
DB_NAME="clinical_doc_center"
CORS_ORIGINS="*"
SECRET_KEY="[secure-key]"
LOCAL_MODEL="Qwen/Qwen2.5-32B-Instruct"
TENSOR_PARALLEL_SIZE=1
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=[email]
SMTP_PASSWORD=[app-password]
EMAIL_FROM=[email]
```

---

# 10. صفحات التطبيق

## 10.1 صفحات الواجهة
| الصفحة | المسار | الوصف |
|--------|--------|--------|
| تسجيل الدخول | `/login` | صفحة الدخول |
| التسجيل | `/register` | إنشاء حساب جديد |
| التحقق MFA | `/mfa-verify` | إدخال رمز OTP |
| لوحة التحكم | `/dashboard` | الصفحة الرئيسية |
| ملاحظة جديدة | `/new-note` | إنشاء ملاحظة |
| التحليل | `/analysis/{id}` | عرض نتائج التحليل |
| الدردشة | `/chat` | أسئلة سريعة |
| الإعدادات | `/settings` | إعدادات الحساب |

---

# 11. المكتبات والاعتماديات

## 11.1 Python (requirements.txt)
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
python-multipart>=0.0.6
pydantic>=2.5.0
motor>=3.3.0
pymongo>=4.6.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
bcrypt>=4.1.0
aiosmtplib>=3.0.0
email-validator>=2.1.0
pandas>=2.1.0
openpyxl>=3.1.0
vllm>=0.13.0
torch>=2.0.0
transformers>=4.35.0
accelerate>=0.25.0
```

## 11.2 Node.js (package.json)
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "axios": "^1.6.0",
    "tailwindcss": "^3.3.0",
    "@radix-ui/react-*": "latest",
    "lucide-react": "latest",
    "i18next": "latest",
    "react-i18next": "latest"
  }
}
```

---

# 12. معلومات الاتصال والدعم

## 12.1 الوصول
| العنصر | القيمة |
|--------|--------|
| **URL التطبيق** | http://8.213.39.104 |
| **SSH** | root@8.213.39.104 |
| **قاعدة البيانات** | mongodb://localhost:27017 |

## 12.2 الحسابات
| الحساب | البريد | الدور |
|--------|--------|-------|
| مدير النظام | almaghthawi.cdi@gmail.com | admin |

---

# 13. الملخص

منصة **نبيه (NABIH)** هي حل متكامل لتحسين التوثيق السريري، مبني على:
- **بنية حديثة:** FastAPI + React + MongoDB
- **ذكاء اصطناعي متقدم:** Qwen2.5-32B على GPU V100
- **أمان عالي:** MFA + JWT + تشفير
- **دعم ثنائي اللغة:** عربي/إنجليزي
- **معايير طبية:** ICD-10-AM + ACS Standards

---

**تاريخ التوثيق:** يناير 2026  
**الإصدار:** 1.0

