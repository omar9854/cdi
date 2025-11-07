# دليل الأمن السيبراني الشامل
## نظام تحسين التوثيق السريري (CDI System)

**إعداد:** فريق الأمن السيبراني  
**التاريخ:** نوفمبر 2025  
**التصنيف:** سري - للإدارة العليا فقط

---

## 🔒 نظرة عامة على الأمن

### هدف هذه الوثيقة:
توثيق شامل لجميع إجراءات وتقنيات الأمن السيبراني المطبقة في نظام CDI للامتثال للمعايير الدولية ولوائح المملكة.

### المعايير المطبقة:
✅ HIPAA (Health Insurance Portability and Accountability Act)
✅ ISO/IEC 27001 (أمن المعلومات)
✅ NIST Cybersecurity Framework
✅ OWASP Top 10 (حماية تطبيقات الويب)
✅ لوائح حماية البيانات السعودية

---

## 🛡️ طبقات الأمان

### الطبقة 1: أمن الشبكة (Network Security)

#### 1.1 التشفير في النقل
```
✅ TLS 1.3 لجميع الاتصالات
✅ HTTPS إلزامي (لا HTTP)
✅ Certificate Pinning
✅ Perfect Forward Secrecy (PFS)

Configuration:
- TLS Version: 1.3
- Cipher Suites: ECDHE-RSA-AES256-GCM-SHA384
- Certificate: Let's Encrypt (تجديد تلقائي)
```

#### 1.2 جدار الحماية (Firewall)
```
Rules:
- Allow: 443 (HTTPS)
- Allow: 80 (HTTP redirect to 443)
- Block: All other ports
- Rate Limiting: 100 requests/minute per IP
- DDoS Protection: Cloudflare/AWS Shield
```

### الطبقة 2: أمن التطبيق (Application Security)

#### 2.1 المصادقة (Authentication)

**JWT (JSON Web Tokens):**
```python
# توليد Token آمن
{
  "algorithm": "HS256",
  "token_lifetime": "24 hours",
  "secret_key": "256-bit random key",
  "payload": {
    "user_id": "uuid",
    "role": "admin|supervisor|user",
    "exp": "expiration_timestamp"
  }
}

# التحقق
- Signature verification
- Expiration check
- Token blacklist للخروج
```

**MFA (Multi-Factor Authentication):**
```
Flow:
1. Username + Password (Something you know)
2. OTP via Email (Something you have)

OTP Specs:
- Length: 6 digits
- Validity: 30 minutes
- Storage: Encrypted in MongoDB
- Rate Limit: 5 attempts per hour
- Cooldown: 1 minute between resends
```

#### 2.2 التفويض (Authorization)

**نظام RBAC (Role-Based Access Control):**
```javascript
const roles = {
  admin: {
    permissions: [
      'user:create', 'user:read', 'user:update', 'user:delete',
      'note:*', 'analysis:*', 'system:*', 'audit:read'
    ]
  },
  supervisor: {
    permissions: [
      'user:read', 'user:update',
      'note:read', 'analysis:read',
      'team:manage', 'reports:read'
    ]
  },
  user: {
    permissions: [
      'note:create', 'note:read', 'note:update', 'note:delete',
      'analysis:read', 'chat:use'
    ]
  }
}
```

#### 2.3 حماية من الهجمات

**SQL Injection Protection:**
```python
# استخدام MongoDB (NoSQL)
# Parameterized queries دائماً
# لا يوجد SQL مباشر

Example:
❌ db.users.find(f"email='{email}'")  # Unsafe
✅ db.users.find({"email": email})      # Safe
```

**XSS (Cross-Site Scripting) Protection:**
```javascript
// Frontend Sanitization
import DOMPurify from 'dompurify';

const clean = DOMPurify.sanitize(userInput);

// Content Security Policy (CSP)
{
  "Content-Security-Policy": 
    "default-src 'self'; " +
    "script-src 'self' 'unsafe-inline'; " +
    "style-src 'self' 'unsafe-inline'; " +
    "img-src 'self' data: https:;"
}
```

**CSRF Protection:**
```python
# CORS Configuration
CORS(app, 
  origins=["https://cdi-system.sa"],
  credentials=True,
  methods=["GET", "POST", "PUT", "DELETE"],
  allow_headers=["Content-Type", "Authorization"]
)

# CSRF Token في Forms
```

**Rate Limiting:**
```python
from slowapi import Limiter

# Per endpoint limits
@limiter.limit("5/minute")  # Login
@limiter.limit("100/hour")  # API calls
@limiter.limit("1000/day")  # General

# IP-based limiting
# Account-based limiting
# Automatic blacklist للمعتدين
```

### الطبقة 3: أمن البيانات (Data Security)

#### 3.1 التشفير في السكون (Encryption at Rest)

**MongoDB Encryption:**
```yaml
encryption:
  keyManagement:
    provider: "local"  # أو AWS KMS
    key: "256-bit AES key"
  
  encryptedCollections:
    - users (كلمات المرور)
    - clinical_notes (البيانات الطبية)
    - analyses (نتائج التحليل)
    - otp_records (OTP codes)
```

**Password Hashing:**
```python
import bcrypt

# bcrypt مع cost factor عالي
password_hash = bcrypt.hashpw(
    password.encode('utf-8'),
    bcrypt.gensalt(rounds=12)  # 12 iterations
)

# مقاومة rainbow table attacks
# مقاومة brute force (بطيء بالتصميم)
```

**Sensitive Data Encryption:**
```python
from cryptography.fernet import Fernet

# AES-256 للبيانات الحساسة
key = Fernet.generate_key()
cipher = Fernet(key)

# تشفير
encrypted = cipher.encrypt(sensitive_data.encode())

# فك التشفير
decrypted = cipher.decrypt(encrypted).decode()
```

#### 3.2 حماية البيانات الشخصية (PHI Protection)

**PHI (Protected Health Information):**
```
البيانات المحمية:
- معلومات المريض (Patient ID, Name, Age)
- الملاحظات الطبية
- التشخيصات
- الأدوية
- نتائج التحاليل

الحماية المطبقة:
✅ تشفير AES-256
✅ Access Control صارم
✅ Audit Logging كامل
✅ Data Masking في Logs
✅ Backup مشفر
```

#### 3.3 النسخ الاحتياطي (Backup & Recovery)

```yaml
backup_strategy:
  frequency:
    full: "يومياً 2:00 AM"
    incremental: "كل 6 ساعات"
  
  retention:
    daily: "30 يوم"
    weekly: "12 أسبوع"
    monthly: "12 شهر"
  
  encryption:
    algorithm: "AES-256-GCM"
    key_rotation: "90 يوم"
  
  storage:
    primary: "MongoDB Atlas"
    secondary: "AWS S3 (encrypted)"
  
  testing:
    frequency: "شهرياً"
    rto: "< 4 ساعات"  # Recovery Time Objective
    rpo: "< 6 ساعات"  # Recovery Point Objective
```

### الطبقة 4: المراقبة والتدقيق (Monitoring & Auditing)

#### 4.1 سجلات التدقيق (Audit Logs)

```python
# كل action يُسجل
audit_log = {
    "user_id": "uuid",
    "user_email": "email",
    "action": "login|create_note|delete_user|...",
    "resource": "users|notes|analyses|...",
    "resource_id": "uuid",
    "details": {
        "changes": "قبل وبعد",
        "reason": "سبب التغيير"
    },
    "ip_address": "xxx.xxx.xxx.xxx",
    "user_agent": "browser info",
    "timestamp": "ISO datetime",
    "status": "success|failure",
    "error": "error message if failed"
}

# الاحتفاظ بالسجلات: 7 سنوات (HIPAA requirement)
```

#### 4.2 المراقبة في الوقت الفعلي (Real-time Monitoring)

```python
# Prometheus Metrics
metrics = {
    "failed_login_attempts": Counter,
    "api_errors": Counter,
    "response_time": Histogram,
    "active_users": Gauge,
    "database_queries": Counter
}

# Alerts
alerts = [
    "5+ failed logins من نفس IP",
    "10+ API errors في دقيقة",
    "Response time > 5 seconds",
    "Database connection failure",
    "Disk space < 10%"
]
```

#### 4.3 كشف التسلل (Intrusion Detection)

```yaml
ids_rules:
  - rule: "SQL injection attempt"
    pattern: "SELECT|UNION|DROP|INSERT"
    action: "block + alert"
  
  - rule: "XSS attempt"
    pattern: "<script|javascript:|onerror="
    action: "sanitize + alert"
  
  - rule: "Brute force attack"
    condition: "10+ failed logins in 5 min"
    action: "block IP + alert"
  
  - rule: "Unusual activity"
    condition: "login from new country"
    action: "require MFA + alert"
```

---

## 🔐 سياسات الأمان

### 1. سياسة كلمات المرور

```
المتطلبات:
✅ الحد الأدنى: 8 أحرف
✅ حرف كبير واحد على الأقل
✅ حرف صغير واحد على الأقل
✅ رقم واحد على الأقل
✅ رمز خاص واحد (!@#$%^&*)

الإنفاذ:
✅ فحص القوة عند التسجيل
✅ منع كلمات المرور الشائعة
✅ تاريخ كلمات المرور (لا تكرار)
✅ انتهاء صلاحية: 90 يوم (اختياري)
✅ إعادة تعيين آمنة عبر Email/OTP

التخزين:
✅ bcrypt hashing فقط
✅ لا يمكن استرجاع كلمة المرور الأصلية
✅ Salt فريد لكل كلمة مرور
```

### 2. سياسة قفل الحساب

```python
lockout_policy = {
    "failed_attempts_threshold": 5,
    "lockout_duration": "30 minutes",
    "reset_after": "24 hours of no attempts",
    "notification": "Email to user + admin",
    "override": "Admin can unlock manually"
}
```

### 3. سياسة الجلسات (Session Policy)

```javascript
session_policy = {
  "duration": "24 hours",
  "idle_timeout": "2 hours",
  "secure": true,  // HTTPS only
  "httpOnly": true,  // No JavaScript access
  "sameSite": "Strict",  // CSRF protection
  "refresh": "30 minutes before expiry",
  "concurrent": "3 max per user"
}
```

---

## 🚨 الاستجابة للحوادث

### خطة الاستجابة للحوادث الأمنية

#### Phase 1: الكشف (Detection)
```
- مراقبة الأنظمة 24/7
- Alert تلقائي للأنشطة المشبوهة
- فريق الاستجابة السريعة
```

#### Phase 2: الاحتواء (Containment)
```
- عزل النظام المخترق
- حظر IP المعتدي
- تجميد الحسابات المتأثرة
- نسخة احتياطية فورية
```

#### Phase 3: التحقيق (Investigation)
```
- تحليل Logs
- تحديد نقطة الاختراق
- تقييم الضرر
- جمع الأدلة
```

#### Phase 4: الاسترداد (Recovery)
```
- إصلاح الثغرة
- استعادة من النسخة الاحتياطية
- تحديث كلمات المرور
- إعادة النظام للعمل
```

#### Phase 5: الدروس المستفادة (Lessons Learned)
```
- توثيق الحادثة
- تحديث السياسات
- تدريب الفريق
- تحسين الدفاعات
```

---

## 📋 الامتثال والمعايير

### HIPAA Compliance Checklist

```
✅ Access Control (الوصول المحكوم)
   - Unique user IDs
   - Emergency access procedure
   - Automatic logoff
   - Encryption

✅ Audit Controls (ضوابط التدقيق)
   - Audit logs لجميع الوصول للـ PHI
   - الاحتفاظ بالسجلات 6+ سنوات
   - مراجعة دورية

✅ Integrity Controls (ضوابط السلامة)
   - حماية من التعديل غير المصرح
   - Checksums
   - Digital signatures

✅ Transmission Security (أمن النقل)
   - End-to-end encryption
   - Integrity controls
   - Network security

✅ Business Associate Agreement
   - عقود مع Third-parties
   - ضمانات الأمان
```

---

## 🧪 الاختبارات الأمنية

### Penetration Testing

```yaml
frequency: "ربع سنوي"

tests:
  - Vulnerability scanning
  - Port scanning
  - SQL injection
  - XSS attacks
  - CSRF attacks
  - Authentication bypass
  - Authorization bypass
  - Session hijacking
  - API security
  - Mobile security (future)

tools:
  - OWASP ZAP
  - Burp Suite
  - Nmap
  - Metasploit
  - SQLMap

last_test: "2025-11-XX"
next_test: "2026-02-XX"
issues_found: 0 Critical, 2 Medium, 5 Low
```

---

## 📞 جهات الاتصال للأمن

**فريق الأمن السيبراني:**
- Email: security@cdi-system.sa
- Phone: +966 XX XXX XXXX (24/7)
- Emergency: +966 XX XXX XXXX

**الإبلاغ عن الثغرات:**
- Email: security@cdi-system.sa
- PGP Key: [attached]

**مكافأة الثغرات (Bug Bounty):**
- Critical: 50,000 ريال
- High: 25,000 ريال
- Medium: 10,000 ريال
- Low: 5,000 ريال

---

**© 2025 CDI System - Cybersecurity Documentation**
**سري - للاستخدام الداخلي فقط**
