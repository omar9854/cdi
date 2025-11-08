# فهرس الكود المصدري الكامل
# Complete Source Code Index

**لنظام تحسين التوثيق الطبي السريري - CDI System**

**المؤلف:** عمر عواض نشي المغذوي  
**رقم الهوية:** 1059538838  
**التاريخ:** نوفمبر 2025

---

## 📋 جدول المحتويات

1. [معلومات عامة](#general-info)
2. [هيكل المشروع](#project-structure)
3. [الكود الخلفي - Backend](#backend)
4. [الكود الأمامي - Frontend](#frontend)
5. [قاعدة البيانات](#database)
6. [الوثائق](#documentation)
7. [ملفات الإعداد](#configuration)

---

<a name="general-info"></a>
## 1️⃣ معلومات عامة

### معلومات المشروع:
- **اسم المشروع:** نظام تحسين التوثيق السريري (CDI System)
- **إجمالي الملفات:** 115+ ملف
- **إجمالي الأسطر:** 15,000+ سطر برمجي
- **اللغات:** Python, JavaScript, HTML, CSS
- **المكتبات:** 50+ مكتبة

### التقنيات المستخدمة:
- **Backend:** Python 3.11, FastAPI 0.104
- **Frontend:** React 18, Tailwind CSS 3.3
- **Database:** MongoDB 7.0
- **AI Engine:** Google Gemini 2.0 Flash
- **Authentication:** JWT + MFA (OTP)

---

<a name="project-structure"></a>
## 2️⃣ هيكل المشروع الكامل

```
/app/
├── backend/                                    # النظام الخلفي
│   ├── server.py                              # [3,700 lines] الملف الرئيسي
│   ├── security_models.py                     # [200 lines] نماذج الأمان
│   ├── security_utils.py                      # [500 lines] أدوات الأمان
│   ├── security_routes.py                     # [600 lines] مسارات الأمان
│   ├── clinical_questions.py                  # [150 lines] الأسئلة السريرية
│   ├── migration_update_users.py              # [300 lines] ترحيل قاعدة البيانات
│   ├── send_password_change_emails.py         # [100 lines] إرسال البريد
│   ├── requirements.txt                       # المكتبات المطلوبة
│   └── .env                                   # متغيرات البيئة
│
├── frontend/                                   # النظام الأمامي
│   ├── public/
│   │   ├── index.html
│   │   ├── logo.jpeg
│   │   ├── download-2.png
│   │   └── login-logo.png
│   │
│   ├── src/
│   │   ├── components/                        # المكونات
│   │   │   ├── ui/                           # [20+ files] مكونات Shadcn
│   │   │   │   ├── button.jsx
│   │   │   │   ├── card.jsx
│   │   │   │   ├── input.jsx
│   │   │   │   ├── dialog.jsx
│   │   │   │   ├── select.jsx
│   │   │   │   ├── table.jsx
│   │   │   │   ├── badge.jsx
│   │   │   │   ├── tabs.jsx
│   │   │   │   ├── alert.jsx
│   │   │   │   ├── dropdown-menu.jsx
│   │   │   │   ├── popover.jsx
│   │   │   │   ├── tooltip.jsx
│   │   │   │   ├── textarea.jsx
│   │   │   │   ├── checkbox.jsx
│   │   │   │   ├── switch.jsx
│   │   │   │   ├── slider.jsx
│   │   │   │   ├── progress.jsx
│   │   │   │   ├── skeleton.jsx
│   │   │   │   └── sonner.jsx
│   │   │   │
│   │   │   ├── Navbar.jsx                    # [200 lines] شريط التنقل
│   │   │   ├── Footer.jsx                    # [100 lines] التذييل
│   │   │   ├── ChatWidget.jsx                # [400 lines] ويدجت الدردشة
│   │   │   └── WhatsAppSupport.jsx           # [150 lines] دعم واتساب
│   │   │
│   │   ├── contexts/
│   │   │   └── LanguageContext.jsx           # [100 lines] سياق اللغة
│   │   │
│   │   ├── hooks/
│   │   │   └── use-toast.js                  # [50 lines] خطاف Toast
│   │   │
│   │   ├── utils/
│   │   │   └── errorHandler.js               # [115 lines] معالج الأخطاء
│   │   │
│   │   ├── pages/                            # الصفحات الرئيسية
│   │   │   ├── Login.jsx                     # [300 lines] تسجيل الدخول
│   │   │   ├── Register.jsx                  # [400 lines] التسجيل
│   │   │   ├── MFAVerification.jsx           # [250 lines] التحقق الثنائي
│   │   │   ├── Dashboard.jsx                 # [500 lines] لوحة التحكم
│   │   │   ├── NewNote.jsx                   # [600 lines] ملاحظة جديدة
│   │   │   ├── EditNote.jsx                  # [500 lines] تعديل ملاحظة
│   │   │   ├── Analysis.jsx                  # [700 lines] عرض التحليل
│   │   │   ├── History.jsx                   # [400 lines] السجل
│   │   │   ├── Chat.jsx                      # [500 lines] الدردشة
│   │   │   ├── ChatEnhanced.jsx              # [800 lines] دردشة محسنة
│   │   │   ├── AdminDashboard.jsx            # [600 lines] لوحة الأدمن
│   │   │   ├── AdminDashboard_v2.jsx         # [800 lines] لوحة أدمن v2
│   │   │   ├── SupervisorDashboard.jsx       # [500 lines] لوحة المشرف
│   │   │   ├── SupervisorDashboardPro.jsx    # [700 lines] لوحة مشرف Pro
│   │   │   ├── Messages.jsx                  # [400 lines] الرسائل
│   │   │   ├── ForgotPassword.jsx            # [300 lines] نسيت كلمة المرور
│   │   │   ├── ResetPassword.jsx             # [300 lines] إعادة تعيين
│   │   │   └── SecurityDashboard.jsx         # [400 lines] لوحة الأمان
│   │   │
│   │   ├── App.js                            # [400 lines] التطبيق الرئيسي
│   │   ├── App.css                           # [200 lines] أنماط التطبيق
│   │   ├── index.js                          # [50 lines] نقطة الدخول
│   │   ├── index.css                         # [100 lines] الأنماط الرئيسية
│   │   └── i18n.js                           # [150 lines] إعدادات اللغة
│   │
│   ├── package.json                          # تبعيات Node.js
│   ├── tailwind.config.js                    # إعدادات Tailwind
│   ├── postcss.config.js                     # إعدادات PostCSS
│   ├── jsconfig.json                         # إعدادات JavaScript
│   ├── components.json                       # إعدادات المكونات
│   └── .env                                  # متغيرات البيئة
│
├── documentation/                            # الوثائق
│   ├── EXECUTIVE_SUMMARY_AR.md              # الملخص التنفيذي
│   ├── TECHNICAL_DOCUMENTATION_AR.md        # الوثائق التقنية
│   ├── INTELLECTUAL_PROPERTY_PATENT_AR.md   # براءة الاختراع
│   ├── CYBERSECURITY_DOCUMENTATION_AR.md    # الأمن السيبراني
│   ├── CODE_INVENTORY_AR.md                 # جرد الأكواد
│   ├── PATENT_APPLICATION_SAIP.md           # طلب براءة اختراع
│   ├── COPYRIGHT_REGISTRATION_SAIP.md       # تسجيل حقوق المؤلف
│   ├── CDI_COMPLETE_DOCUMENTATION_AND_CODE.md
│   ├── SOURCE_CODE_SAMPLES.md
│   ├── README.md
│   ├── ADMIN_CREDENTIALS.txt
│   ├── SECURITY_DOCUMENTATION.md
│   ├── DEPLOYMENT_CHECKLIST_AR.md
│   └── ... (25+ ملف وثائق)
│
└── scripts/                                 # السكربتات
    ├── update_admin_email.sh
    ├── post_deployment.sh
    └── ...
```

---

<a name="backend"></a>
## 3️⃣ الكود الخلفي - Backend

### ملفات Python الرئيسية:

#### 1. server.py (3,700 سطر)
**المحتوى:**
- إعدادات FastAPI والتطبيق الرئيسي
- اتصال MongoDB
- نظام تلقائي لإنشاء حساب الأدمن
- JWT Authentication
- MFA (Multi-Factor Authentication)
- Rate Limiting
- Prometheus Metrics
- Google Gemini AI Integration
- API Endpoints (50+ endpoint)

**الوظائف الرئيسية:**
```python
# Startup
async def ensure_admin_account()
async def startup_event()

# Authentication
@app.post("/api/auth/login-step1")
@app.post("/api/auth/login-step2")
@app.post("/api/auth/register")
@app.post("/api/auth/logout")

# Notes Management
@app.post("/api/notes/create")
@app.get("/api/notes/user")
@app.get("/api/notes/{note_id}")
@app.put("/api/notes/{note_id}")
@app.delete("/api/notes/{note_id}")

# AI Analysis
@app.post("/api/analysis/analyze")
@app.get("/api/analysis/{analysis_id}")
@app.post("/api/analysis/reanalyze")

# Chat
@app.post("/api/chat/message")
@app.get("/api/chat/history/{analysis_id}")
@app.post("/api/chat/clinical-question")

# Admin
@app.get("/api/admin/users")
@app.post("/api/admin/users/{user_id}/activate")
@app.post("/api/admin/users/{user_id}/deactivate")
@app.get("/api/admin/statistics")
@app.get("/api/admin/audit-logs")

# Supervisor
@app.get("/api/supervisor/team")
@app.get("/api/supervisor/statistics")

# Export
@app.get("/api/export/pdf/{analysis_id}")
@app.get("/api/export/excel/{analysis_id}")
```

---

#### 2. security_utils.py (500 سطر)
**المحتوى:**
- Password hashing with bcrypt
- JWT token creation and verification
- OTP generation and validation
- Email sending (SMTP)
- Rate limiting functions
- Account locking mechanisms
- Audit logging

**الوظائف الرئيسية:**
```python
def hash_password(password: str) -> str
def verify_password(password: str, hashed: str) -> bool
def create_access_token(data: dict) -> str
def decode_token(token: str) -> dict
def generate_otp() -> str
async def send_otp_email(email, name, otp)
async def send_welcome_email(email, name)
async def send_password_reset_email(email, name, token)
async def verify_otp(email, otp_code) -> bool
async def check_rate_limit(user_id) -> bool
async def log_audit(action, user_id, details)
```

---

#### 3. security_models.py (200 سطر)
**المحتوى:**
- Pydantic models for validation
- User models
- Authentication models
- Request/Response models

**النماذج الرئيسية:**
```python
class User(BaseModel)
class UserRegister(BaseModel)
class UserLogin(BaseModel)
class OTPVerification(BaseModel)
class Token(BaseModel)
class PasswordResetRequest(BaseModel)
class PasswordReset(BaseModel)
```

---

#### 4. security_routes.py (600 سطر)
**المحتوى:**
- مسارات الأمان الإضافية
- إدارة كلمات المرور
- MFA إضافي
- إعدادات الأمان

---

#### 5. clinical_questions.py (150 سطر)
**المحتوى:**
- قائمة الأسئلة السريرية المحددة
- أسئلة حسب التخصص
- قوالب الاستفسارات

---

#### 6. requirements.txt
**المكتبات المطلوبة:**
```
fastapi==0.104.1
uvicorn==0.24.0
motor==3.3.2
pymongo==4.6.0
pydantic==2.5.0
python-multipart==0.0.6
python-jose==3.3.0
passlib==1.7.4
bcrypt==4.1.1
python-dotenv==1.0.0
google-generativeai==0.3.1
aiosmtplib==3.0.1
prometheus-client==0.19.0
prometheus-fastapi-instrumentator==6.1.0
slowapi==0.1.9
reportlab==4.0.7
openpyxl==3.1.2
```

---

<a name="frontend"></a>
## 4️⃣ الكود الأمامي - Frontend

### الصفحات الرئيسية (Pages):

#### 1. Login.jsx (300 سطر)
**المحتوى:**
- واجهة تسجيل الدخول
- التحقق من البيانات
- دعم MFA
- معالجة الأخطاء
- دعم ثنائي اللغة

#### 2. MFAVerification.jsx (250 سطر)
**المحتوى:**
- إدخال OTP
- التحقق من الكود
- إعادة إرسال OTP
- العد التنازلي

#### 3. Dashboard.jsx (500 سطر)
**المحتوى:**
- إحصائيات المستخدم
- الملاحظات الأخيرة
- إجراءات سريعة
- الرسوم البيانية

#### 4. NewNote.jsx (600 سطر)
**المحتوى:**
- نموذج إنشاء ملاحظة
- معلومات المريض
- الملاحظات الطبية
- اختيار التخصص
- الحفظ والتحليل

#### 5. Analysis.jsx (700 سطر)
**المحتوى:**
- عرض نتائج التحليل
- التشخيصات وأكواد ICD-10
- الثغرات المحددة
- استفسارات الطبيب
- التوصيات
- تصدير PDF/Excel

#### 6. ChatEnhanced.jsx (800 سطر)
**المحتوى:**
- نوعان من الدردشة
- أسئلة محددة
- دردشة مفتوحة
- اختيار التخصص
- تاريخ المحادثة

#### 7. AdminDashboard.jsx (600 سطر)
**المحتوى:**
- إدارة المستخدمين
- إحصائيات النظام
- سجلات التدقيق
- تفعيل/تعطيل الحسابات

---

### المكونات (Components):

#### UI Components (20+ مكون):
```
- button.jsx          # أزرار
- card.jsx            # بطاقات
- input.jsx           # حقول إدخال
- dialog.jsx          # نوافذ منبثقة
- select.jsx          # قوائم منسدلة
- table.jsx           # جداول
- badge.jsx           # شارات
- tabs.jsx            # تبويبات
- alert.jsx           # تنبيهات
- dropdown-menu.jsx   # قوائم منسدلة
- popover.jsx         # نوافذ منبثقة صغيرة
- tooltip.jsx         # تلميحات
- textarea.jsx        # حقول نص كبيرة
- checkbox.jsx        # مربعات اختيار
- switch.jsx          # مفاتيح تبديل
- slider.jsx          # منزلقات
- progress.jsx        # أشرطة التقدم
- skeleton.jsx        # هياكل التحميل
- sonner.jsx          # إشعارات Toast
```

#### Custom Components:
```javascript
// Navbar.jsx (200 lines)
- شريط التنقل الرئيسي
- قائمة المستخدم
- تبديل اللغة
- الإشعارات

// Footer.jsx (100 lines)
- التذييل
- روابط التواصل
- معلومات الحقوق

// ChatWidget.jsx (400 lines)
- ويدجت دردشة عائم
- نافذة قابلة للتوسيع
- تكامل مع AI

// WhatsAppSupport.jsx (150 lines)
- زر واتساب عائم
- رابط مباشر للدعم
```

---

### ملفات الإعداد:

#### package.json
**التبعيات الرئيسية:**
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "axios": "^1.6.2",
    "i18next": "^23.7.6",
    "react-i18next": "^13.5.0",
    "@radix-ui/react-dialog": "^1.0.0",
    "@radix-ui/react-dropdown-menu": "^1.0.0",
    "@radix-ui/react-select": "^1.0.0",
    "tailwindcss": "^3.3.0",
    "lucide-react": "^0.294.0",
    "sonner": "^1.2.0",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.0.0",
    "tailwind-merge": "^2.0.0"
  }
}
```

---

<a name="database"></a>
## 5️⃣ قاعدة البيانات - MongoDB

### المجموعات (Collections):

#### 1. users
```javascript
{
  _id: ObjectId,
  id: "uuid-string",
  email: "user@example.com",
  password_hash: "bcrypt-hash",
  full_name: "Full Name",
  phone_number: "+966...",
  role: "admin|supervisor|user",
  mfa_enabled: true,
  is_active: true,
  created_at: ISODate,
  last_login: ISODate,
  failed_login_attempts: 0,
  account_locked_until: null,
  supervisor_id: "uuid-string"
}
```

#### 2. clinical_notes
```javascript
{
  _id: ObjectId,
  id: "uuid-string",
  user_id: "uuid-string",
  title: "Note Title",
  doctor_notes: [
    {
      text: "Clinical text...",
      specialty: "specialty-name"
    }
  ],
  created_at: ISODate,
  updated_at: ISODate
}
```

#### 3. analyses
```javascript
{
  _id: ObjectId,
  id: "uuid-string",
  note_id: "uuid-string",
  user_id: "uuid-string",
  diagnoses_to_document: [
    {
      diagnosis_ar: "Arabic name",
      diagnosis_en: "English name",
      icd_code: "ICD-10 code"
    }
  ],
  missing_documentation: [],
  gaps_ar: [],
  gaps_en: [],
  queries_ar: [],
  queries_en: [],
  recommendations_ar: [],
  recommendations_en: [],
  summary_ar: "Summary in Arabic",
  summary_en: "Summary in English",
  created_at: ISODate
}
```

#### 4. chat_messages
```javascript
{
  _id: ObjectId,
  id: "uuid-string",
  analysis_id: "uuid-string",
  user_id: "uuid-string",
  role: "user|assistant",
  message: "Message text",
  created_at: ISODate
}
```

#### 5. otp_records
```javascript
{
  _id: ObjectId,
  email: "user@example.com",
  otp_code: "123456",
  expires_at: ISODate,
  is_used: false,
  created_at: ISODate
}
```

#### 6. audit_logs
```javascript
{
  _id: ObjectId,
  user_id: "uuid-string",
  action: "action_name",
  resource: "resource_name",
  details: {},
  ip_address: "xxx.xxx.xxx.xxx",
  user_agent: "browser info",
  timestamp: ISODate,
  status: "success|failure"
}
```

#### 7. messages (رسائل داخلية)
```javascript
{
  _id: ObjectId,
  id: "uuid-string",
  from_user_id: "uuid-string",
  from_user_name: "Name",
  to_user_id: "uuid-string",
  to_user_name: "Name",
  subject: "Message subject",
  body: "Message body",
  is_draft: false,
  is_read: false,
  created_at: ISODate
}
```

---

<a name="documentation"></a>
## 6️⃣ الوثائق

### الوثائق العربية:
1. **EXECUTIVE_SUMMARY_AR.md** (297 سطر)
2. **TECHNICAL_DOCUMENTATION_AR.md** (638 سطر)
3. **INTELLECTUAL_PROPERTY_PATENT_AR.md** (422 سطر)
4. **CYBERSECURITY_DOCUMENTATION_AR.md** (522 سطر)
5. **CODE_INVENTORY_AR.md** (509 سطر)
6. **PATENT_APPLICATION_SAIP.md** (طلب براءة اختراع)
7. **COPYRIGHT_REGISTRATION_SAIP.md** (تسجيل حقوق مؤلف)

### الوثائق الإضافية:
- README.md
- ADMIN_CREDENTIALS.txt
- SECURITY_DOCUMENTATION.md
- DEPLOYMENT_CHECKLIST_AR.md
- 20+ ملف وثائق إضافي

---

<a name="configuration"></a>
## 7️⃣ ملفات الإعداد

### Backend Configuration:
```bash
# .env
MONGO_URL=mongodb://localhost:27017
DB_NAME=clinical_doc_center
JWT_SECRET=your-secret-key
GEMINI_API_KEY_1=key1
GEMINI_API_KEY_2=key2
GEMINI_API_KEY_3=key3
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=email@gmail.com
SMTP_PASSWORD=app-password
FRONTEND_URL=https://cdi-system.sa
```

### Frontend Configuration:
```bash
# .env
REACT_APP_BACKEND_URL=https://medidoc-ai.emergent.host
PORT=3000
```

---

## 📊 إحصائيات المشروع

### حجم الكود:
- **Backend:** 6,000+ سطر (Python)
- **Frontend:** 8,000+ سطر (JavaScript/React)
- **UI Components:** 1,000+ سطر (JSX/CSS)
- **Documentation:** 2,500+ سطر (Markdown)
- **الإجمالي:** 17,500+ سطر برمجي

### الملفات:
- **إجمالي الملفات:** 115+ ملف
- **ملفات Backend:** 10 ملفات
- **ملفات Frontend:** 80+ ملف
- **ملفات وثائق:** 25+ ملف

---

## 📞 معلومات المؤلف

**الاسم:** عمر عواض نشي المغذوي  
**رقم الهوية:** 1059538838  
**الجوال:** 0502468148  
**البريد الإلكتروني:** almaghthawi.cdi@gmail.com

---

## ملاحظة هامة

**جميع الملفات المذكورة في هذا الفهرس موجودة في المسار:**
```
/app/
```

**للوصول إلى الكود الكامل:**
1. جميع الملفات محفوظة على GitHub
2. يمكن تحميل الأرشيف الكامل
3. الكود متاح للمراجعة والتدقيق

---

**© 2025 عمر عواض نشي المغذوي - جميع الحقوق محفوظة**  
**© 2025 Omar Awad Nashi Al-Maghdawi - All Rights Reserved**
