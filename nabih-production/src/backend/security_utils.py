"""
Security Utility Functions for CDI Application
"""
import random
import string
import bcrypt
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta
from typing import Optional
import os
from motor.motor_asyncio import AsyncIOMotorDatabase
from security_models import AuditLog, LoginAttempt, OTPRecord

# ========== OTP Generation ==========
def generate_otp(length: int = 6) -> str:
    """Generate a random OTP code"""
    return ''.join(random.choices(string.digits, k=length))

# ========== Email Sending ==========

async def send_welcome_email(email: str, user_name: str, role: str = "user"):
    """Send welcome email to new users"""
    try:
        smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('SMTP_PORT', 587))
        smtp_user = os.environ.get('SMTP_USER')
        smtp_password = os.environ.get('SMTP_PASSWORD')
        email_from = os.environ.get('EMAIL_FROM', smtp_user)
        
        # Determine role in Arabic
        role_ar = {
            'admin': 'مدير النظام',
            'supervisor': 'مشرف',
            'user': 'مستخدم'
        }.get(role, 'مستخدم')
        
        # Create message
        message = MIMEMultipart("alternative")
        message["From"] = email_from
        message["To"] = email
        message["Subject"] = "مرحباً بك في منصة نبيه | NABIH لتحسين التوثيق السريري"
        
        # Email body
        html_content = f"""
        <html dir="rtl">
            <body style="font-family: Arial, sans-serif; direction: rtl; text-align: right;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
                    <div style="background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        
                        <!-- Header -->
                        <div style="text-align: center; margin-bottom: 30px;">
                            <h1 style="color: #2563eb; margin: 0;">🏥 منصة نبيه | NABEEH</h1>
                            <p style="color: #64748b; margin-top: 5px;">منصة الذكاء الاصطناعي لتحسين التوثيق السريري</p>
                        </div>
                        
                        <!-- Welcome Message -->
                        <div style="margin-bottom: 30px;">
                            <h2 style="color: #1e40af; margin-bottom: 15px;">مرحباً بك، {user_name}! 👋</h2>
                            <p style="font-size: 16px; color: #333; line-height: 1.6;">
                                يسعدنا انضمامك إلى منصة الذكاء الاصطناعي لتحسين التوثيق السريري. تم إنشاء حسابك بنجاح كـ <strong>{role_ar}</strong>.
                            </p>
                        </div>
                        
                        <!-- Login Info -->
                        <div style="background-color: #eff6ff; padding: 20px; border-radius: 8px; margin-bottom: 30px;">
                            <h3 style="color: #1e40af; margin-top: 0;">معلومات تسجيل الدخول:</h3>
                            <p style="margin: 10px 0; color: #333;">
                                <strong>البريد الإلكتروني:</strong> {email}<br>
                                <strong>كلمة المرور:</strong> التي قمت بإنشائها عند التسجيل
                            </p>
                            <p style="margin: 10px 0; color: #ef4444; font-size: 14px;">
                                ⚠️ يُرجى الاحتفاظ بكلمة المرور في مكان آمن
                            </p>
                        </div>
                        
                        <!-- Features -->
                        <div style="margin-bottom: 30px;">
                            <h3 style="color: #1e40af;">ماذا يمكنك أن تفعل الآن؟</h3>
                            <ul style="color: #333; line-height: 2;">
                                <li>✅ تحليل الملاحظات السريرية بالذكاء الاصطناعي</li>
                                <li>✅ تحديد التشخيصات الموثقة والمستنتجة مع أكواد ICD-10-CM</li>
                                <li>✅ توليد استفسارات طبية احترافية للأطباء</li>
                                <li>✅ الدردشة التفاعلية مع الذكاء الاصطناعي</li>
                                <li>✅ عرض وتصدير التحليلات (PDF/Excel)</li>
                            </ul>
                        </div>
                        
                        <!-- Security Note -->
                        <div style="background-color: #fef3c7; padding: 15px; border-radius: 8px; border-right: 4px solid #f59e0b; margin-bottom: 30px;">
                            <h4 style="color: #92400e; margin-top: 0;">🔒 ملاحظة أمنية هامة:</h4>
                            <p style="color: #78350f; margin: 0; font-size: 14px;">
                                النظام محمي بالمصادقة متعددة العوامل (MFA). عند تسجيل الدخول، سيتم إرسال رمز التحقق إلى بريدك الإلكتروني.
                            </p>
                        </div>
                        
                        <!-- CTA Button -->
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{os.environ.get('FRONTEND_URL', 'https://medanalyzer-6.preview.emergentagent.com')}" 
                               style="display: inline-block; background-color: #2563eb; color: white; padding: 12px 30px; 
                                      text-decoration: none; border-radius: 6px; font-size: 16px; font-weight: bold;">
                                🚀 ابدأ الآن
                            </a>
                        </div>
                        
                        <!-- Support -->
                        <div style="border-top: 1px solid #e5e7eb; padding-top: 20px; margin-top: 30px;">
                            <h4 style="color: #1e40af; margin-top: 0;">هل تحتاج إلى مساعدة؟</h4>
                            <p style="color: #666; font-size: 14px; margin: 0;">
                                إذا كان لديك أي استفسار أو تحتاج إلى مساعدة، لا تتردد في التواصل معنا.
                            </p>
                        </div>
                        
                        <!-- Footer -->
                        <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                            <p style="color: #94a3b8; font-size: 12px; margin: 5px 0;">
                                منصة نبيه | NABIH لتحسين التوثيق السريري<br>
                                نظام CDI المدعوم بالذكاء الاصطناعي
                            </p>
                            <p style="color: #cbd5e1; font-size: 11px; margin: 10px 0;">
                                © 2024 جميع الحقوق محفوظة
                            </p>
                        </div>
                    </div>
                </div>
            </body>
        </html>
        """
        
        part = MIMEText(html_content, "html")
        message.attach(part)
        
        # Send email
        async with aiosmtplib.SMTP(hostname=smtp_host, port=smtp_port) as smtp:
            await smtp.starttls()
            await smtp.login(smtp_user, smtp_password)
            await smtp.send_message(message)
        
        return True
        
    except Exception as e:
        print(f"Error sending welcome email: {str(e)}")
        return False

async def send_otp_email(email: str, otp_code: str, user_name: str = "المستخدم"):
    """Send OTP code via email"""
    try:
        smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('SMTP_PORT', 587))
        smtp_user = os.environ.get('SMTP_USER')
        smtp_password = os.environ.get('SMTP_PASSWORD')
        email_from = os.environ.get('EMAIL_FROM', smtp_user)
        
        # Create message
        message = MIMEMultipart("alternative")
        message["From"] = email_from
        message["To"] = email
        message["Subject"] = "رمز التحقق للدخول لمنصة نبيه"
        
        # Email body in Arabic and English
        html_content = f"""
        <html dir="rtl">
            <body style="font-family: Arial, sans-serif; direction: rtl; text-align: right;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
                    <div style="background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <h2 style="color: #2563eb; text-align: center;">🔒 رمز التحقق الأمني</h2>
                        <p style="font-size: 16px; color: #333;">مرحباً {user_name}،</p>
                        <p style="font-size: 16px; color: #333;">لقد طلبت رمز التحقق لتسجيل الدخول إلى حسابك في منصة نبيه | NABIH لتحسين التوثيق السريري.</p>
                        
                        <div style="background-color: #eff6ff; padding: 20px; border-radius: 8px; text-align: center; margin: 30px 0;">
                            <p style="font-size: 14px; color: #666; margin-bottom: 10px;">رمز التحقق الخاص بك:</p>
                            <h1 style="font-size: 36px; color: #2563eb; margin: 10px 0; letter-spacing: 8px;">{otp_code}</h1>
                            <p style="font-size: 14px; color: #666; margin-top: 10px;">صالح لمدة 10 دقائق</p>
                        </div>
                        
                        <div style="background-color: #fef2f2; padding: 15px; border-right: 4px solid #ef4444; border-radius: 4px; margin: 20px 0;">
                            <p style="color: #991b1b; margin: 0; font-size: 14px;">⚠️ <strong>تحذير أمني:</strong></p>
                            <p style="color: #991b1b; margin: 5px 0 0 0; font-size: 14px;">
                                لا تشارك هذا الرمز مع أي شخص. لن يطلب فريق الدعم منك هذا الرمز أبداً.
                            </p>
                        </div>
                        
                        <p style="font-size: 14px; color: #666; margin-top: 20px;">
                            إذا لم تطلب هذا الرمز، يرجى تجاهل هذا البريد الإلكتروني وتغيير كلمة المرور الخاصة بك على الفور.
                        </p>
                        
                        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
                        
                        <div style="text-align: center;">
                            <p style="font-size: 12px; color: #9ca3af;">
                                منصة نبيه | NABIH لتحسين التوثيق السريري<br>
                                NABIH - AI Clinical Documentation Improvement Platform
                            </p>
                        </div>
                    </div>
                </div>
            </body>
        </html>
        """
        
        message.attach(MIMEText(html_content, "html", "utf-8"))
        
        # Send email
        await aiosmtplib.send(
            message,
            hostname=smtp_host,
            port=smtp_port,
            username=smtp_user,
            password=smtp_password,
            start_tls=True
        )
        
        return True
    except Exception as e:
        print(f"Error sending OTP email: {str(e)}")
        return False

async def send_security_alert_email(email: str, alert_type: str, details: str):
    """Send security alert email"""
    try:
        smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('SMTP_PORT', 587))
        smtp_user = os.environ.get('SMTP_USER')
        smtp_password = os.environ.get('SMTP_PASSWORD')
        email_from = os.environ.get('EMAIL_FROM', smtp_user)
        
        alert_titles = {
            'multiple_failed_logins': 'محاولات تسجيل دخول فاشلة متعددة',
            'account_locked': 'تم قفل الحساب',
            'password_changed': 'تم تغيير كلمة المرور',
            'new_device_login': 'تسجيل دخول من جهاز جديد'
        }
        
        message = MIMEMultipart("alternative")
        message["From"] = email_from
        message["To"] = email
        message["Subject"] = f"🔔 تنبيه أمني - {alert_titles.get(alert_type, 'تنبيه')}"
        
        html_content = f"""
        <html dir="rtl">
            <body style="font-family: Arial, sans-serif; direction: rtl;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background-color: #fef2f2; padding: 20px; border-radius: 10px; border: 2px solid #ef4444;">
                        <h2 style="color: #dc2626;">🔔 تنبيه أمني</h2>
                        <h3 style="color: #991b1b;">{alert_titles.get(alert_type, 'تنبيه')}</h3>
                        <p style="font-size: 16px; color: #333;">{details}</p>
                        <p style="font-size: 14px; color: #666; margin-top: 20px;">
                            الوقت: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
                        </p>
                        <p style="font-size: 14px; color: #991b1b; margin-top: 20px;">
                            إذا لم تقم بهذا الإجراء، يرجى تغيير كلمة المرور فوراً والاتصال بالدعم الفني.
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        message.attach(MIMEText(html_content, "html", "utf-8"))
        
        await aiosmtplib.send(
            message,
            hostname=smtp_host,
            port=smtp_port,
            username=smtp_user,
            password=smtp_password,
            start_tls=True
        )
        
        return True
    except Exception as e:
        print(f"Error sending security alert: {str(e)}")
        return False

# ========== Audit Logging ==========
async def log_audit(
    db: AsyncIOMotorDatabase,
    action: str,
    user_id: Optional[str] = None,
    user_email: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    status: str = "success",
    details: Optional[dict] = None
):
    """Log an audit event"""
    try:
        audit_log = AuditLog(
            user_id=user_id,
            user_email=user_email,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            details=details
        )
        
        doc = audit_log.model_dump()
        doc['timestamp'] = doc['timestamp'].isoformat()
        
        await db.audit_logs.insert_one(doc)
        return True
    except Exception as e:
        print(f"Error logging audit: {str(e)}")
        return False

# ========== Rate Limiting ==========
async def check_rate_limit(
    db: AsyncIOMotorDatabase,
    email: str,
    ip_address: Optional[str] = None,
    max_attempts: int = 5,
    time_window_minutes: int = 15
) -> tuple[bool, int]:
    """
    Check if user has exceeded login attempts
    Returns: (is_allowed, remaining_attempts)
    """
    try:
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=time_window_minutes)
        
        # Count failed attempts in time window
        failed_attempts = await db.login_attempts.count_documents({
            "email": email,
            "success": False,
            "timestamp": {"$gte": cutoff_time.isoformat()}
        })
        
        remaining = max_attempts - failed_attempts
        is_allowed = remaining > 0
        
        return is_allowed, max(0, remaining)
    except Exception as e:
        print(f"Error checking rate limit: {str(e)}")
        return True, max_attempts

async def record_login_attempt(
    db: AsyncIOMotorDatabase,
    email: str,
    success: bool,
    ip_address: Optional[str] = None
):
    """Record a login attempt"""
    try:
        attempt = LoginAttempt(
            email=email,
            ip_address=ip_address,
            success=success
        )
        
        doc = attempt.model_dump()
        doc['timestamp'] = doc['timestamp'].isoformat()
        
        await db.login_attempts.insert_one(doc)
        
        # If failed, check if account should be locked
        if not success:
            is_allowed, remaining = await check_rate_limit(db, email)
            if not is_allowed:
                # Lock account for 30 minutes
                await lock_account(db, email, duration_minutes=30)
                
        return True
    except Exception as e:
        print(f"Error recording login attempt: {str(e)}")
        return False

async def lock_account(
    db: AsyncIOMotorDatabase,
    email: str,
    duration_minutes: int = 30
):
    """Lock user account temporarily"""
    try:
        user = await db.users.find_one({"email": email})
        if not user:
            return False
        
        unlock_time = datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)
        
        await db.users.update_one(
            {"email": email},
            {
                "$set": {
                    "account_locked": True,
                    "locked_until": unlock_time.isoformat()
                }
            }
        )
        
        # Send security alert
        await send_security_alert_email(
            email,
            'account_locked',
            f'تم قفل حسابك مؤقتاً بسبب محاولات تسجيل دخول فاشلة متعددة. سيتم فتح الحساب تلقائياً بعد {duration_minutes} دقيقة.'
        )
        
        return True
    except Exception as e:
        print(f"Error locking account: {str(e)}")
        return False

async def unlock_account_if_expired(db: AsyncIOMotorDatabase, email: str) -> bool:
    """Check and unlock account if lock period has expired"""
    try:
        user = await db.users.find_one({"email": email})
        if not user or not user.get('account_locked'):
            return True
        
        locked_until = user.get('locked_until')
        if locked_until:
            unlock_time = datetime.fromisoformat(locked_until)
            if datetime.now(timezone.utc) >= unlock_time:
                await db.users.update_one(
                    {"email": email},
                    {
                        "$set": {
                            "account_locked": False,
                            "locked_until": None
                        }
                    }
                )
                return True
        
        return False
    except Exception as e:
        print(f"Error unlocking account: {str(e)}")
        return False

# ========== Password Validation ==========
def check_password_history(new_password_hash: str, password_history: list) -> bool:
    """Check if password was used before (last 5 passwords)"""
    for old_hash in password_history[-5:]:
        if bcrypt.checkpw(new_password_hash.encode('utf-8'), old_hash.encode('utf-8')):
            return False  # Password was used before
    return True  # Password is new

def is_password_expired(last_changed: datetime, expiry_days: int = 90) -> bool:
    """Check if password has expired"""
    expiry_date = last_changed + timedelta(days=expiry_days)
    return datetime.now(timezone.utc) >= expiry_date
