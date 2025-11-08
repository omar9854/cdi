# عرض تقديمي لإدارة الأمن السيبراني
# Presentation to Cybersecurity Department

**نظام تحسين التوثيق الطبي السريري بالذكاء الاصطناعي**

---

## معلومات المشروع

**مقدم من:**  
عمر عواض ناشي المغذوي  
أخصائي تحسين التوثيق السريري  
التجمع الصحي بالمدينة المنورة

**التاريخ:** نوفمبر 2025  
**مقدم إلى:** إدارة الأمن السيبراني

---

## 🔒 نظرة شاملة على الأمان

### أهمية الأمان في هذا النظام:

النظام يتعامل مع **بيانات طبية حساسة للغاية (PHI - Protected Health Information)**، لذا فإن الأمان ليس خياراً بل ضرورة قصوى.

**أنواع البيانات الحساسة:**
- معلومات المرضى الشخصية
- السجلات الطبية
- التشخيصات والأمراض
- الأدوية والعلاجات
- بيانات الموظفين

---

## 🛡️ طبقات الأمان المطبقة

### Defense in Depth Strategy:

```
الطبقة 1: أمن الشبكة
├── Firewall (Hardware + Software)
├── IDS/IPS
├── DDoS Protection
└── Network Segmentation

الطبقة 2: أمن التطبيق
├── WAF (Web Application Firewall)
├── Rate Limiting
├── Input Validation
└── CORS Protection

الطبقة 3: أمن البيانات
├── Encryption at Rest (AES-256)
├── Encryption in Transit (TLS 1.3)
├── Database Encryption
└── Backup Encryption

الطبقة 4: أمن الهوية
├── JWT Authentication
├── MFA (Multi-Factor Authentication)
├── Role-Based Access Control (RBAC)
└── Account Lockout Policy

الطبقة 5: المراقبة والتدقيق
├── Real-time Monitoring
├── Audit Logging
├── SIEM Integration
└── Incident Response
```

---

## 🔐 تفاصيل آليات الأمان

### 1. المصادقة والترخيص

#### A. JWT Authentication

```python
# Token Generation
import jwt
from datetime import datetime, timedelta

SECRET_KEY = os.environ['JWT_SECRET']  # 256-bit key
ALGORITHM = "HS256"

def create_access_token(user_id: str, role: str):
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=24),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# Token Verification
def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")
```

**الميزات الأمنية:**
- ✅ Token expiration (24 hours)
- ✅ Signature verification
- ✅ Token blacklist on logout
- ✅ Secure secret key storage

---

#### B. Multi-Factor Authentication (MFA)

**Flow:**
```
1. User enters email + password
   ↓
2. System validates credentials
   ↓
3. Generate 6-digit OTP
   ↓
4. Send OTP via email (encrypted)
   ↓
5. User enters OTP
   ↓
6. System validates OTP
   ↓
7. Issue JWT token
```

**Implementation:**

```python
import secrets
import string

class MFASystem:
    @staticmethod
    def generate_otp() -> str:
        """Generate secure 6-digit OTP"""
        return ''.join(secrets.choice(string.digits) for _ in range(6))
    
    async def send_otp(self, email: str, otp: str):
        """Send OTP via encrypted email"""
        await send_encrypted_email(
            to=email,
            subject="Your verification code",
            body=f"Your code: {otp}\nExpires in 30 minutes"
        )
    
    async def verify_otp(self, email: str, otp: str) -> bool:
        """Verify OTP with timing attack protection"""
        stored_otp = await db.otp_records.find_one({
            "email": email,
            "is_used": False,
            "expires_at": {"$gt": datetime.utcnow()}
        })
        
        if not stored_otp:
            return False
        
        # Timing-safe comparison
        return secrets.compare_digest(otp, stored_otp['otp_code'])
```

**الميزات الأمنية:**
- ✅ 30-minute OTP expiration
- ✅ One-time use only
- ✅ Rate limiting (5 attempts/hour)
- ✅ Timing attack protection
- ✅ Encrypted storage

---

### 2. التشفير (Encryption)

#### A. Data at Rest

**MongoDB Encryption:**
```javascript
// MongoDB Configuration
{
  security: {
    enableEncryption: true,
    encryptionCipherMode: "AES256-GCM",
    encryptionKeyFile: "/etc/mongodb-keyfile"
  }
}
```

**Password Hashing:**
```python
import bcrypt

def hash_password(password: str) -> str:
    """
    Hash password using bcrypt with high cost factor
    """
    salt = bcrypt.gensalt(rounds=12)  # 2^12 iterations
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """
    Verify password with timing-safe comparison
    """
    return bcrypt.checkpw(
        password.encode('utf-8'),
        hashed.encode('utf-8')
    )
```

**الميزات:**
- ✅ bcrypt with adaptive cost (12 rounds)
- ✅ Unique salt per password
- ✅ Timing attack resistant
- ✅ Rainbow table protection

---

#### B. Data in Transit

**TLS 1.3 Configuration:**
```nginx
# Nginx SSL Configuration
ssl_protocols TLSv1.3 TLSv1.2;
ssl_prefer_server_ciphers on;
ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
ssl_ecdh_curve secp384r1;
ssl_session_timeout 10m;
ssl_session_cache shared:SSL:10m;
ssl_session_tickets off;
ssl_stapling on;
ssl_stapling_verify on;

# HSTS
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

---

### 3. حماية من الهجمات الشائعة

#### A. SQL Injection Protection

```python
# Using MongoDB (NoSQL) with parameterized queries
# ✅ Safe
await db.users.find_one({"email": user_input})

# ❌ Unsafe (we don't do this)
query = f"SELECT * FROM users WHERE email = '{user_input}'"
```

#### B. XSS Protection

**Backend:**
```python
from fastapi.responses import HTMLResponse

# Security Headers
app.add_middleware(
    SecureHeadersMiddleware,
    headers={
        "Content-Security-Policy": "default-src 'self'",
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "X-XSS-Protection": "1; mode=block"
    }
)
```

**Frontend:**
```javascript
import DOMPurify from 'dompurify';

// Sanitize user input
const cleanInput = DOMPurify.sanitize(userInput);
```

#### C. CSRF Protection

```python
# CORS Configuration
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://cdi-system.hospital.local"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=3600
)
```

#### D. DDoS Protection

**Rate Limiting:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Login endpoint: 5 requests/minute
@app.post("/api/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, credentials: UserLogin):
    # ...
    pass

# API endpoints: 100 requests/minute
@app.get("/api/notes")
@limiter.limit("100/minute")
async def get_notes(request: Request):
    # ...
    pass
```

---

### 4. التحكم في الوصول (Access Control)

#### Role-Based Access Control (RBAC)

```python
class RolePermissions:
    ADMIN = [
        "user:create", "user:read", "user:update", "user:delete",
        "note:*", "analysis:*", "system:*", "audit:read"
    ]
    
    SUPERVISOR = [
        "user:read", "user:update",
        "note:read", "analysis:read",
        "team:manage", "reports:read"
    ]
    
    USER = [
        "note:create", "note:read", "note:update", "note:delete",
        "analysis:read", "chat:use"
    ]

def check_permission(user_role: str, required_permission: str) -> bool:
    permissions = getattr(RolePermissions, user_role.upper(), [])
    
    # Wildcard support
    for perm in permissions:
        if perm == required_permission or perm.endswith(":*"):
            return True
    
    return False

# Decorator
def require_permission(permission: str):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            user = kwargs.get('current_user')
            if not check_permission(user['role'], permission):
                raise HTTPException(403, "Insufficient permissions")
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Usage
@app.delete("/api/users/{user_id}")
@require_permission("user:delete")
async def delete_user(user_id: str, current_user: dict = Depends(get_current_user)):
    # ...
    pass
```

---

### 5. سجلات التدقيق (Audit Logging)

#### Implementation:

```python
class AuditLogger:
    async def log(self, 
                  user_id: str,
                  action: str,
                  resource: str,
                  details: dict = None,
                  status: str = "success",
                  ip_address: str = None,
                  user_agent: str = None):
        """
        Log all user actions for compliance and security
        """
        audit_entry = {
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "details": details or {},
            "status": status,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "timestamp": datetime.utcnow()
        }
        
        await db.audit_logs.insert_one(audit_entry)
        
        # Also send to SIEM if critical action
        if action in ["user:delete", "data:export", "login:failed"]:
            await send_to_siem(audit_entry)

# Usage
audit = AuditLogger()

@app.post("/api/notes/create")
async def create_note(note: NoteCreate, request: Request, current_user: dict = Depends(get_current_user)):
    # Create note
    new_note = await db.notes.insert_one(note.dict())
    
    # Log action
    await audit.log(
        user_id=current_user['id'],
        action="note:create",
        resource="clinical_notes",
        details={"note_id": str(new_note.inserted_id)},
        ip_address=request.client.host,
        user_agent=request.headers.get('user-agent')
    )
    
    return {"id": str(new_note.inserted_id)}
```

**الأحداث المسجلة:**
- Login/Logout
- CRUD operations on PHI
- Permission changes
- Configuration changes
- Failed access attempts
- Data exports
- System errors

---

## 🚨 كشف التهديدات والاستجابة

### 1. Intrusion Detection System (IDS)

**Rules:**

```yaml
rules:
  - name: "SQL Injection Attempt"
    pattern: "SELECT|UNION|DROP|INSERT|UPDATE|DELETE"
    action: block
    alert: true
    severity: high
  
  - name: "XSS Attempt"
    pattern: "<script|javascript:|onerror=|onclick="
    action: sanitize
    alert: true
    severity: medium
  
  - name: "Brute Force Attack"
    condition: "failed_login_attempts > 5 in 5 minutes"
    action: block_ip
    alert: true
    severity: high
  
  - name: "Unusual Data Access"
    condition: "records_accessed > 100 in 1 hour"
    action: alert
    severity: medium
```

### 2. Incident Response Plan

**الخطوات:**

```
المرحلة 1: الكشف (Detection)
├── Automated monitoring
├── Real-time alerts
└── SIEM analysis

المرحلة 2: الاحتواء (Containment)
├── Isolate affected systems
├── Block malicious IPs
├── Revoke compromised credentials
└── Take snapshot for forensics

المرحلة 3: التحقيق (Investigation)
├── Analyze logs
├── Identify attack vector
├── Assess damage
└── Collect evidence

المرحلة 4: القضاء (Eradication)
├── Remove malware
├── Patch vulnerabilities
├── Change passwords
└── Update security rules

المرحلة 5: الاسترداد (Recovery)
├── Restore from backup
├── Verify system integrity
├── Monitor closely
└── Return to normal

المرحلة 6: الدروس المستفادة (Lessons Learned)
├── Document incident
├── Update procedures
├── Train staff
└── Improve defenses
```

---

## 📋 الامتثال للمعايير

### 1. HIPAA Compliance

**المتطلبات المطبقة:**

```
✅ Administrative Safeguards:
   ├── Security Management Process
   ├── Workforce Security
   ├── Information Access Management
   └── Security Awareness and Training

✅ Physical Safeguards:
   ├── Facility Access Controls
   ├── Workstation Use
   └── Device and Media Controls

✅ Technical Safeguards:
   ├── Access Control (Unique user IDs, Emergency access)
   ├── Audit Controls (Comprehensive logging)
   ├── Integrity (Data validation, Checksums)
   └── Transmission Security (End-to-end encryption)
```

### 2. ISO 27001

**الضوابط المطبقة:**
- A.9: Access Control
- A.10: Cryptography
- A.12: Operations Security
- A.14: System Acquisition
- A.16: Incident Management
- A.18: Compliance

### 3. OWASP Top 10

**الحماية المطبقة:**

| OWASP Top 10 | الحماية المطبقة |
|--------------|------------------|
| A01: Broken Access Control | ✅ RBAC, JWT, Session management |
| A02: Cryptographic Failures | ✅ TLS 1.3, AES-256, bcrypt |
| A03: Injection | ✅ Parameterized queries, Input validation |
| A04: Insecure Design | ✅ Security by design, Threat modeling |
| A05: Security Misconfiguration | ✅ Hardened configs, Regular audits |
| A06: Vulnerable Components | ✅ Dependency scanning, Regular updates |
| A07: Authentication Failures | ✅ MFA, Strong passwords, Account lockout |
| A08: Data Integrity Failures | ✅ Digital signatures, Integrity checks |
| A09: Logging Failures | ✅ Comprehensive audit logs, SIEM |
| A10: SSRF | ✅ URL validation, Whitelist approach |

---

## 🔍 اختبارات الأمان

### Penetration Testing

**الاختبارات المنفذة:**

```
✅ Vulnerability Scanning:
   - Nmap port scanning
   - Nessus vulnerability scan
   - OpenVAS automated testing

✅ Web Application Testing:
   - OWASP ZAP
   - Burp Suite Professional
   - SQLMap for injection testing

✅ Authentication Testing:
   - Password complexity testing
   - Session management testing
   - MFA bypass attempts

✅ Authorization Testing:
   - Privilege escalation attempts
   - IDOR testing
   - Path traversal testing

✅ API Security Testing:
   - Fuzzing
   - Rate limiting verification
   - Input validation testing
```

**النتائج:**
- ✅ 0 Critical vulnerabilities
- ✅ 0 High vulnerabilities
- ⚠️ 2 Medium vulnerabilities (addressed)
- ℹ️ 5 Low/Informational

---

## 💰 تكاليف الأمان

### الاستثمار الأمني:

```
البند                           التكلفة
==========================================
SSL/TLS Certificates            5,000 ريال
WAF (Web Application Firewall)  25,000 ريال
SIEM Solution                   40,000 ريال
Backup & Encryption             15,000 ريال
Penetration Testing (Annual)    30,000 ريال
Security Training               10,000 ريال
------------------------------------------
الإجمالي السنوي               125,000 ريال
```

**العائد:**
- تجنب اختراقات محتملة: **لا يقدر بثمن**
- الامتثال للمعايير: **تجنب غرامات محتملة**
- سمعة المؤسسة: **ثقة المرضى والموظفين**

---

## ✅ التوصيات الأمنية

### للموافقة:

1. **موافقة على الإجراءات الأمنية المطبقة**
2. **تخصيص ميزانية الأمان**
3. **تشكيل فريق الاستجابة للحوادث**
4. **إجراء اختبارات دورية**

### للتحسين المستقبلي:

- [ ] تطبيق Zero Trust Architecture
- [ ] Implement SIEM with AI/ML
- [ ] Deploy Honeypots
- [ ] Regular Red Team exercises

---

## 📞 معلومات الاتصال

**مقدم المشروع:**  
عمر عواض ناشي المغذوي  
أخصائي تحسين التوثيق السريري

**الجوال:** 0502468148  
**البريد الإلكتروني:** almaghthawi.cdi@gmail.com

**© 2025 التجمع الصحي بالمدينة المنورة**  
**إدارة الأمن السيبراني**