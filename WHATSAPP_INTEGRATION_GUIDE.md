# دليل تكامل واتساب | WhatsApp Integration Guide

## ✅ الميزات المنفذة | Implemented Features

### 1. حقل رقم الجوال (Phone Number Field)
- **التسجيل:** تم إضافة حقل إلزامي لرقم الجوال في صفحة التسجيل
- **قاعدة البيانات:** يتم حفظ رقم الجوال مع بيانات المستخدم
- **التحقق:** التأكد من عدم تسجيل نفس الرقم مرتين

### 2. زر الدعم الفني (Technical Support Button)
- **الموقع:** زر أخضر ثابت في جميع الصفحات (أسفل اليسار في العربية / أسفل اليمين في الإنجليزية)
- **الوظيفة:** يفتح واتساب مباشرة مع رسالة ترحيبية
- **الرقم:** 966502468148
- **الرسالة الافتراضية:** "مرحباً، أحتاج إلى مساعدة في استخدام منصة مركز الترميز الطبي وتحسين التوثيق السريري"

### 3. رسائل واتساب التلقائية (Automated WhatsApp Messages)

#### أ. رسالة ترحيبية عند التسجيل
**متى؟** عند إنشاء حساب جديد  
**الطريقة:** رابط واتساب يفتح تلقائياً مع رسالة جاهزة  
**المحتوى:**
```
مرحباً [الاسم]!

تم تسجيلك بنجاح في منصة مركز الترميز الطبي وتحسين التوثيق السريري.

يمكنك الآن:
✅ إضافة ملاحظات سريرية
✅ تحليلها بالذكاء الاصطناعي
✅ تحديد التشخيصات
✅ تصدير التقارير

للدعم الفني، تواصل معنا على: 966502468148
```

#### ب. كود استعادة كلمة المرور
**متى؟** عند نسيان كلمة المرور  
**الطريقة:** إرسال كود مكون من 6 أحرف  
**التفاصيل:**
- يتم إرسال الكود عبر البريد الإلكتروني **و** واتساب
- صلاحية الكود: ساعة واحدة
- يمكن فتح واتساب مباشرة لإرسال الكود للمستخدم

---

## 🔧 التفاصيل التقنية | Technical Details

### Backend Changes

**1. Models (server.py)**
```python
class User(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    phone_number: str  # ✅ جديد
    password_hash: str
    role: str = "user"
    is_active: bool = True
    created_at: datetime

class UserRegister(BaseModel):
    email: EmailStr
    full_name: str
    phone_number: str  # ✅ جديد - مطلوب
    password: str
    admin_code: Optional[str] = None
```

**2. New Endpoints**
```python
# الحصول على معلومات الدعم الفني
GET /api/support/whatsapp
Response: {
    "whatsapp_number": "966502468148",
    "whatsapp_link": "https://wa.me/966502468148"
}

# استعادة كلمة المرور (محدث)
POST /api/auth/forgot-password
Request: { "email": "user@example.com" }
Response: {
    "message": "...",
    "whatsapp_available": true,
    "phone_number": "966XXXXXXX",
    "reset_code": "ABC123"  # كود 6 أحرف
}
```

**3. Environment Variables (.env)**
```bash
# WhatsApp Support Configuration
SUPPORT_WHATSAPP="966502468148"
```

### Frontend Changes

**1. New Component**
- `/app/frontend/src/components/WhatsAppSupport.jsx`
  - زر واتساب عائم
  - يظهر في جميع الصفحات
  - يفتح واتساب مع رسالة مخصصة
  - يتكيف مع اللغة (عربي/إنجليزي)

**2. Updated Pages**
- `Register.jsx`: إضافة حقل رقم الجوال
- `App.js`: إضافة مكون WhatsAppSupport

**3. New Translations**
```javascript
// Arabic
phoneNumber: 'رقم الجوال'
support: 'الدعم الفني'
contactSupport: 'تواصل مع الدعم'

// English
phoneNumber: 'Phone Number'
support: 'Technical Support'
contactSupport: 'Contact Support'
```

---

## 📱 كيفية استخدام واتساب | How to Use WhatsApp

### 1. زر الدعم الفني
```
المستخدم → يضغط على زر واتساب الأخضر
↓
يفتح واتساب تلقائياً
↓
رسالة جاهزة للإرسال إلى 966502468148
```

### 2. رسالة الترحيب (عند التسجيل)
```
المستخدم → يسجل حساب جديد
↓
Backend يحفظ البيانات بنجاح
↓
يظهر رابط واتساب في واجهة المستخدم
↓
المستخدم يضغط → يفتح واتساب → رسالة ترحيبية جاهزة
```

### 3. استعادة كلمة المرور عبر واتساب
```
المستخدم → "نسيت كلمة المرور"
↓
يدخل البريد الإلكتروني
↓
Backend يولد كود مكون من 6 أحرف
↓
يرسل الكود بالبريد الإلكتروني
↓
يعرض خيار فتح واتساب للحصول على الكود
↓
المستخدم يضغط → يفتح واتساب → الكود موجود في الرسالة
```

---

## 🎨 واجهة المستخدم | User Interface

### زر واتساب العائم
- **المظهر:** دائرة خضراء مع أيقونة رسالة
- **الموقع:** 
  - عربي: أسفل اليسار
  - إنجليزي: أسفل اليمين
- **التأثير:** يكبر عند التمرير فوقه
- **الوظيفة:** يفتح واتساب في نافذة جديدة

### حقل رقم الجوال
- **الموقع:** صفحة التسجيل (بين البريد الإلكتروني وكلمة المرور)
- **النوع:** حقل نصي مع أيقونة هاتف
- **مثال:** 966502468148
- **التحقق:** مطلوب (required)

---

## 🔗 روابط واتساب | WhatsApp Links

### صيغة الرابط الأساسية
```
https://wa.me/966502468148?text=MESSAGE_HERE
```

### أمثلة للرسائل

**1. الدعم الفني**
```javascript
const supportMessage = language === 'ar' 
  ? 'مرحباً، أحتاج إلى مساعدة في استخدام منصة مركز الترميز الطبي وتحسين التوثيق السريري'
  : 'Hello, I need help with the Medical Coding & CDI Center platform';

const link = `https://wa.me/966502468148?text=${encodeURIComponent(supportMessage)}`;
```

**2. رسالة الترحيب**
```javascript
const welcomeMessage = `مرحباً ${userName}!

تم تسجيلك بنجاح في منصة مركز الترميز الطبي وتحسين التوثيق السريري.

للدعم: 966502468148`;

const link = `https://wa.me/${phoneNumber}?text=${encodeURIComponent(welcomeMessage)}`;
```

**3. كود استعادة كلمة المرور**
```javascript
const resetMessage = `كود استعادة كلمة المرور الخاص بك: ${resetCode}

هذا الكود صالح لمدة ساعة واحدة.

للدعم: 966502468148`;

const link = `https://wa.me/${phoneNumber}?text=${encodeURIComponent(resetMessage)}`;
```

---

## ⚠️ ملاحظات مهمة | Important Notes

### 1. بدون API حالياً
- **الحالة:** نستخدم روابط wa.me البسيطة
- **السبب:** لا تحتاج API key أو تكوين معقد
- **القيد:** المستخدم يحتاج الضغط على "إرسال" يدوياً

### 2. للترقية إلى WhatsApp Business API

إذا أردت إرسال رسائل تلقائية بالكامل (بدون تدخل المستخدم):

**الخيارات:**
1. **Twilio WhatsApp API**
   - احترافي ومستقر
   - يحتاج: Twilio Account + API Key
   - التكلفة: حسب عدد الرسائل
   
2. **WhatsApp Business API**
   - رسمي من Meta
   - يحتاج: حساب Business معتمد
   - عملية الموافقة قد تأخذ وقت

3. **Baileys (من Playbook)**
   - مجاني
   - يستخدم WhatsApp Web
   - معقد التنصيب (Node.js service)
   - قد يتم حظره من واتساب

**التوصية:** ابدأ بالروابط البسيطة (الحالي)، ثم انتقل إلى Twilio لاحقاً إذا احتجت.

### 3. الأمان
- ✅ أرقام الجوال محفوظة بشكل آمن في قاعدة البيانات
- ✅ لا يتم عرض الأرقام للمستخدمين الآخرين
- ✅ كود استعادة كلمة المرور يُستخدم مرة واحدة فقط
- ✅ صلاحية الكود: ساعة واحدة

---

## 📊 اختبار الميزات | Testing Features

### 1. اختبار زر الدعم الفني
```
1. افتح أي صفحة في التطبيق
2. ابحث عن الزر الأخضر في الزاوية السفلية
3. اضغط عليه
4. يجب أن يفتح واتساب مع رسالة جاهزة إلى 966502468148
```

### 2. اختبار التسجيل برقم الجوال
```
1. اذهب إلى صفحة التسجيل
2. املأ: الاسم، البريد، رقم الجوال، كلمة المرور
3. اضغط "إنشاء حساب جديد"
4. تحقق من أن التسجيل تم بنجاح
5. تحقق من حفظ الرقم في قاعدة البيانات
```

### 3. اختبار استعادة كلمة المرور
```
1. اذهب إلى "نسيت كلمة المرور"
2. أدخل البريد الإلكتروني
3. تحقق من استلام البريد مع رابط إعادة التعيين
4. تحقق من ظهور خيار واتساب (إذا كان الرقم مسجل)
```

---

## 📁 الملفات المعدلة | Modified Files

### Backend
- ✏️ `/app/backend/server.py`
  - إضافة حقل phone_number في User model
  - تحديث endpoint التسجيل
  - تحديث endpoint تسجيل الدخول
  - تحديث endpoint forgot-password
  - إضافة endpoint support/whatsapp
- ✏️ `/app/backend/.env`
  - إضافة SUPPORT_WHATSAPP=966502468148

### Frontend
- ✏️ `/app/frontend/src/pages/Register.jsx`
  - إضافة حقل رقم الجوال
- ✏️ `/app/frontend/src/App.js`
  - إضافة مكون WhatsAppSupport
- ✏️ `/app/frontend/src/contexts/LanguageContext.jsx`
  - إضافة ترجمات جديدة
- ➕ `/app/frontend/src/components/WhatsAppSupport.jsx`
  - مكون جديد لزر واتساب

---

## 🚀 الخطوات التالية | Next Steps

### إذا أردت ترقية النظام:

1. **احصل على Twilio Account**
   - سجل في https://www.twilio.com
   - احصل على رقم واتساب مخصص
   - احصل على Account SID & Auth Token

2. **قم بتثبيت Twilio SDK**
   ```bash
   pip install twilio
   ```

3. **أضف إلى .env**
   ```bash
   TWILIO_ACCOUNT_SID=your_account_sid
   TWILIO_AUTH_TOKEN=your_auth_token
   TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
   ```

4. **حدث Backend لإرسال رسائل تلقائية**

---

## ✅ الملخص | Summary

تم تنفيذ نظام واتساب كامل يتضمن:

1. ✅ حقل رقم الجوال في التسجيل
2. ✅ زر دعم فني ثابت في جميع الصفحات (966502468148)
3. ✅ رسائل واتساب الترحيبية (عبر روابط wa.me)
4. ✅ كود استعادة كلمة المرور عبر واتساب

**النظام جاهز للاستخدام الفوري!** 🎉

للترقية إلى إرسال تلقائي بالكامل، اتبع خطوات Twilio أعلاه.

---

© 2025 جميع الحقوق محفوظة | عمر المغذوي  
رقم الدعم الفني: 966502468148
