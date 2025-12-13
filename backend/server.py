from fastapi import FastAPI, APIRouter, HTTPException, Depends, Header, File, UploadFile, Request
from fastapi.responses import FileResponse, StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
from prometheus_fastapi_instrumentator import Instrumentator
import os
import logging
from pathlib import Path
import time
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
import random
import google.generativeai as genai
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Import coding routes
import coding_routes

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Auto-fix admin account on startup - ALWAYS runs on every startup
async def ensure_admin_account():
    """Automatically ensure admin account exists with correct credentials on startup"""
    try:
        # Get admin credentials from environment variables
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@system.com')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'ChangeMe@123456')
        
        print(f"🔍 Checking admin account...")
        
        # Delete only THIS admin email to ensure clean state (keep other users)
        deleted = await db.users.delete_many({'email': admin_email})
        if deleted.deleted_count > 0:
            print(f"🗑️  Deleted {deleted.deleted_count} old admin account(s)")
        
        # Create fresh admin account
        print(f"👤 Creating admin account: {admin_email}")
        hashed = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt())
        
        admin_user = {
            'id': str(uuid.uuid4()),
            'email': admin_email,
            'password_hash': hashed.decode('utf-8'),
            'full_name': 'مدير النظام - System Administrator',
            'phone_number': '+966500000000',
            'role': 'admin',
            'department': 'cdi',  # Admin manages both departments
            'coding_role': None,
            'daily_case_target': None,
            'mfa_enabled': True,
            'is_active': True,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'password_changed_at': datetime.now(timezone.utc).isoformat(),
            'last_login': None,
            'failed_login_attempts': 0,
            'account_locked_until': None
        }
        
        await db.users.insert_one(admin_user)
        print(f"✅ Admin account ready: {admin_email}")
        
        # Clean up old OTP and login attempts
        await db.otp_records.delete_many({})
        await db.login_attempts.delete_many({})
        print(f"🧹 Cleaned old OTP and login attempts")
        
    except Exception as e:
        print(f"❌ Error ensuring admin account: {e}")
        import traceback
        traceback.print_exc()

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Rate Limiting - TEMPORARILY DISABLED TO FIX LOGIN ISSUE
# The slowapi rate limiter was causing persistent login failures due to in-memory state
# TODO: Implement rate limiting with Redis or database-backed storage
# limiter = Limiter(key_func=get_remote_address)
# app.state.limiter = limiter
# app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Prometheus Metrics
instrumentor = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_respect_env_var=False,
    should_instrument_requests_inprogress=True,
    excluded_handlers=[".*admin.*", "/metrics"],
    inprogress_name="cdi_requests_inprogress",
    inprogress_labels=True,
)

# Custom Metrics
ACTIVE_USERS = Gauge('cdi_active_users', 'Number of active users')
AI_REQUESTS = Counter('cdi_ai_requests_total', 'Total AI requests', ['type'])
AI_RESPONSE_TIME = Histogram('cdi_ai_response_time_seconds', 'AI response time', ['type'])
DB_OPERATIONS = Counter('cdi_db_operations_total', 'Total database operations', ['operation', 'collection'])

instrumentor.instrument(app).expose(app, endpoint="/metrics")

# JWT Settings
SECRET_KEY = os.environ.get('JWT_SECRET')
if not SECRET_KEY:
    raise ValueError("JWT_SECRET environment variable is required for production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Emergent LLM Key
# Load Gemini API Keys (multiple for rotation - up to 12 keys)
GEMINI_API_KEYS = [
    os.environ.get('GEMINI_API_KEY_1'),
    os.environ.get('GEMINI_API_KEY_2'),
    os.environ.get('GEMINI_API_KEY_3'),
    os.environ.get('GEMINI_API_KEY_4'),
    os.environ.get('GEMINI_API_KEY_5'),
    os.environ.get('GEMINI_API_KEY_6'),
    os.environ.get('GEMINI_API_KEY_7'),
    os.environ.get('GEMINI_API_KEY_8'),
    os.environ.get('GEMINI_API_KEY_9'),
    os.environ.get('GEMINI_API_KEY_10'),
    os.environ.get('GEMINI_API_KEY_11'),
    os.environ.get('GEMINI_API_KEY_12')
]
# Filter out None values
GEMINI_API_KEYS = [key for key in GEMINI_API_KEYS if key]

if not GEMINI_API_KEYS:
    raise ValueError("No Gemini API keys found in environment variables")

# Calculate capacity (Free tier: 20 requests/day/key)
capacity_per_key = 20  # Free tier limit
total_capacity = len(GEMINI_API_KEYS) * capacity_per_key

# Log will be done after logger is initialized
print(f"✅ Loaded {len(GEMINI_API_KEYS)} Gemini API keys for rotation (Total capacity: {total_capacity} requests/day, Free tier: 20/key/day)")

# Advanced key rotation system with usage tracking
class GeminiKeyManager:
    """Manages Gemini API keys with intelligent rotation"""
    
    def __init__(self, keys):
        self.keys = keys
        self.current_index = 0
        self.usage_count = {i: 0 for i in range(len(keys))}
        self.failed_keys = set()  # Track keys that hit quota
        
    def get_next_key(self):
        """Get next key using round-robin with skip for failed keys"""
        attempts = 0
        while attempts < len(self.keys):
            key_index = self.current_index
            self.current_index = (self.current_index + 1) % len(self.keys)
            
            # Skip if key is marked as failed
            if key_index not in self.failed_keys:
                self.usage_count[key_index] += 1
                return self.keys[key_index], key_index
            
            attempts += 1
        
        # If all keys failed, reset and try again
        logger.warning("⚠️ All Gemini keys exhausted, resetting failed keys tracker")
        self.failed_keys.clear()
        key_index = self.current_index
        self.current_index = (self.current_index + 1) % len(self.keys)
        self.usage_count[key_index] += 1
        return self.keys[key_index], key_index
    
    def mark_key_failed(self, key_index):
        """Mark a key as failed (quota exceeded)"""
        self.failed_keys.add(key_index)
        logger.warning(f"⚠️ Gemini key #{key_index + 1} marked as exhausted")
    
    def get_usage_stats(self):
        """Get usage statistics"""
        return {
            "total_keys": len(self.keys),
            "active_keys": len(self.keys) - len(self.failed_keys),
            "failed_keys": len(self.failed_keys),
            "usage_per_key": self.usage_count
        }

# Initialize key manager
gemini_key_manager = GeminiKeyManager(GEMINI_API_KEYS)

def get_gemini_model(model_name='gemini-2.5-flash', system_instruction=None):
    """Get Gemini model with intelligent key rotation"""
    api_key, key_index = gemini_key_manager.get_next_key()
    genai.configure(api_key=api_key)
    
    logger.info(f"🔑 Using Gemini key #{key_index + 1}/{len(GEMINI_API_KEYS)}")
    
    if system_instruction:
        return genai.GenerativeModel(model_name, system_instruction=system_instruction)
    else:
        return genai.GenerativeModel(model_name)

# Admin Secret Code (يمكن تغييره من .env)
ADMIN_SECRET_CODE = os.environ.get('ADMIN_SECRET_CODE', 'CDI-ADMIN-2024')

# Medical Specialties - Comprehensive List
MEDICAL_SPECIALTIES = [
    # الأقسام الطبية الرئيسية - Main Medical Departments
    {"value": "internal_medicine", "label_ar": "الطب الباطني", "label_en": "Internal Medicine"},
    {"value": "cardiology", "label_ar": "أمراض القلب", "label_en": "Cardiology"},
    {"value": "pulmonology", "label_ar": "أمراض الصدرية والجهاز التنفسي", "label_en": "Pulmonology"},
    {"value": "gastroenterology", "label_ar": "أمراض الجهاز الهضمي", "label_en": "Gastroenterology"},
    {"value": "nephrology", "label_ar": "أمراض الكلى", "label_en": "Nephrology"},
    {"value": "endocrinology", "label_ar": "الغدد الصماء والسكري", "label_en": "Endocrinology"},
    {"value": "hematology", "label_ar": "أمراض الدم", "label_en": "Hematology"},
    {"value": "oncology", "label_ar": "الأورام", "label_en": "Oncology"},
    {"value": "infectious_disease", "label_ar": "الأمراض المعدية", "label_en": "Infectious Disease"},
    {"value": "rheumatology", "label_ar": "أمراض الروماتيزم", "label_en": "Rheumatology"},
    
    # الجراحة - Surgery
    {"value": "general_surgery", "label_ar": "الجراحة العامة", "label_en": "General Surgery"},
    {"value": "orthopedics", "label_ar": "جراحة العظام", "label_en": "Orthopedics"},
    {"value": "neurosurgery", "label_ar": "جراحة المخ والأعصاب", "label_en": "Neurosurgery"},
    {"value": "cardiothoracic_surgery", "label_ar": "جراحة القلب والصدر", "label_en": "Cardiothoracic Surgery"},
    {"value": "vascular_surgery", "label_ar": "جراحة الأوعية الدموية", "label_en": "Vascular Surgery"},
    {"value": "plastic_surgery", "label_ar": "جراحة التجميل والترميم", "label_en": "Plastic Surgery"},
    {"value": "urology", "label_ar": "المسالك البولية", "label_en": "Urology"},
    
    # التخصصات الدقيقة - Specialized Departments
    {"value": "neurology", "label_ar": "الأمراض العصبية", "label_en": "Neurology"},
    {"value": "pediatrics", "label_ar": "طب الأطفال", "label_en": "Pediatrics"},
    {"value": "neonatology", "label_ar": "حديثي الولادة", "label_en": "Neonatology"},
    {"value": "obstetrics", "label_ar": "النساء والولادة", "label_en": "Obstetrics & Gynecology"},
    {"value": "psychiatry", "label_ar": "الطب النفسي", "label_en": "Psychiatry"},
    {"value": "dermatology", "label_ar": "الأمراض الجلدية", "label_en": "Dermatology"},
    {"value": "ophthalmology", "label_ar": "طب العيون", "label_en": "Ophthalmology"},
    {"value": "ent", "label_ar": "الأنف والأذن والحنجرة", "label_en": "ENT"},
    {"value": "dental", "label_ar": "طب الأسنان", "label_en": "Dentistry"},
    
    # الطوارئ والعناية المركزة - Emergency & Critical Care
    {"value": "emergency", "label_ar": "الطوارئ", "label_en": "Emergency Medicine"},
    {"value": "icu", "label_ar": "العناية المركزة", "label_en": "Intensive Care Unit"},
    {"value": "ccu", "label_ar": "العناية المركزة القلبية", "label_en": "Cardiac Care Unit"},
    {"value": "nicu", "label_ar": "العناية المركزة لحديثي الولادة", "label_en": "Neonatal ICU"},
    
    # الأقسام المساندة - Supporting Departments
    {"value": "radiology", "label_ar": "الأشعة التشخيصية", "label_en": "Radiology"},
    {"value": "nuclear_medicine", "label_ar": "الطب النووي", "label_en": "Nuclear Medicine"},
    {"value": "pathology", "label_ar": "علم الأمراض", "label_en": "Pathology"},
    {"value": "laboratory", "label_ar": "المختبر", "label_en": "Laboratory"},
    {"value": "blood_bank", "label_ar": "بنك الدم", "label_en": "Blood Bank"},
    {"value": "pharmacy", "label_ar": "الصيدلية", "label_en": "Pharmacy"},
    {"value": "nutrition", "label_ar": "التغذية العلاجية", "label_en": "Clinical Nutrition"},
    {"value": "physiotherapy", "label_ar": "العلاج الطبيعي", "label_en": "Physiotherapy"},
    {"value": "respiratory_therapy", "label_ar": "العلاج التنفسي", "label_en": "Respiratory Therapy"},
    {"value": "social_services", "label_ar": "الخدمة الاجتماعية", "label_en": "Social Services"},
    {"value": "nursing", "label_ar": "التمريض", "label_en": "Nursing"},
    {"value": "infection_control", "label_ar": "مكافحة العدوى", "label_en": "Infection Control"},
    
    # تخصصات أخرى - Other Specialties
    {"value": "anesthesiology", "label_ar": "التخدير", "label_en": "Anesthesiology"},
    {"value": "pain_management", "label_ar": "إدارة الألم", "label_en": "Pain Management"},
    {"value": "palliative_care", "label_ar": "الرعاية التلطيفية", "label_en": "Palliative Care"},
    {"value": "family_medicine", "label_ar": "طب الأسرة", "label_en": "Family Medicine"},
    {"value": "geriatrics", "label_ar": "طب المسنين", "label_en": "Geriatrics"},
    {"value": "sports_medicine", "label_ar": "الطب الرياضي", "label_en": "Sports Medicine"},
    {"value": "occupational_medicine", "label_ar": "طب الصناعات", "label_en": "Occupational Medicine"},
    
    {"value": "other", "label_ar": "أخرى", "label_en": "Other"}
]

# ========== Models ==========
class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    full_name: str
    phone_number: str  # رقم الجوال
    password_hash: str
    role: str = "user"  # "admin", "supervisor", or "user"
    department: str = "cdi"  # "cdi" or "coding"
    coding_role: Optional[str] = None  # For coding department: "coder", "auditor", or None
    daily_case_target: Optional[int] = 10  # Daily target for coders
    supervisor_id: Optional[str] = None  # ID of supervisor (if user is assigned to one)
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserRegister(BaseModel):
    email: EmailStr
    full_name: str
    phone_number: str  # رقم الجوال مطلوب
    password: str
    department: str = "cdi"  # Department selection: "cdi" or "coding"
    coding_role: Optional[str] = None  # If coding department: "coder" or "auditor"
    admin_code: Optional[str] = None  # كود سري للأدمن

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: Dict

class OTPVerification(BaseModel):
    email: EmailStr
    otp_code: str

class DoctorNote(BaseModel):
    text: str
    specialty: Optional[str] = None

class Message(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    from_user_id: str
    from_user_name: str
    to_user_id: Optional[str] = None  # None means "All"
    to_user_name: Optional[str] = None
    subject: str
    body: str
    is_draft: bool = False
    is_read: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
class MessageCreate(BaseModel):
    to_user_id: Optional[str] = None  # None for "All"
    subject: str
    body: str
    is_draft: bool = False

class ClinicalNote(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    doctor_notes: List[DoctorNote]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None

class ClinicalNoteCreate(BaseModel):
    title: str
    doctor_notes: List[DoctorNote]

class DiagnosisBilingual(BaseModel):
    diagnosis_ar: str
    diagnosis_en: str
    icd_code: str

class Analysis(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    note_id: str
    user_id: str
    diagnoses_to_document: List[DiagnosisBilingual]  # التشخيصات التي يجب توثيقها
    missing_documentation: List[Dict[str, str]]  # التوثيق الناقص
    gaps_ar: List[str]
    gaps_en: List[str]
    queries_ar: List[str]
    queries_en: List[str]
    recommendations_ar: List[str]  # توصيات لتحسين التوثيق
    recommendations_en: List[str]
    summary_ar: str
    summary_en: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AnalyzeRequest(BaseModel):
    note_id: str
    ai_provider: Optional[str] = 'gemini'  # gemini, azure, grok

class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    analysis_id: str
    user_id: str
    role: str  # 'user' or 'assistant'
    message: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChatRequest(BaseModel):
    analysis_id: str
    message: str
    ai_provider: Optional[str] = 'gemini'  # gemini, azure, grok

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str

class PasswordResetWithCode(BaseModel):
    email: EmailStr
    code: str
    new_password: str

class PasswordResetToken(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    token: str
    expires_at: datetime
    used: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ========== Helper Functions ==========
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(authorization: str = Header(None)) -> dict:
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization.replace('Bearer ', '')
    payload = decode_token(token)
    user_id = payload.get('user_id')
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

async def send_email(to_email: str, subject: str, body_html: str):
    """Send email using SMTP (Gmail)"""
    smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', 587))
    smtp_user = os.environ.get('SMTP_USER', '')
    smtp_password = os.environ.get('SMTP_PASSWORD', '')
    email_from = os.environ.get('EMAIL_FROM', 'almaghthawi.cdi@gmail.com')
    
    # If SMTP password is not set, skip email sending (for now)
    if not smtp_password:
        logging.warning(f"Email sending skipped - SMTP_PASSWORD not configured. Would have sent to: {to_email}")
        return
    
    try:
        message = MIMEMultipart('alternative')
        message['From'] = email_from
        message['To'] = to_email
        message['Subject'] = subject
        
        html_part = MIMEText(body_html, 'html', 'utf-8')
        message.attach(html_part)
        
        await aiosmtplib.send(
            message,
            hostname=smtp_host,
            port=smtp_port,
            username=smtp_user,
            password=smtp_password,
            start_tls=True
        )
        logging.info(f"Email sent successfully to {to_email}")
    except Exception as e:
        logging.error(f"Failed to send email to {to_email}: {str(e)}")
        # Don't raise exception - email failure shouldn't break registration/password reset

async def send_welcome_email(user_email: str, user_name: str):
    """Send welcome email to new users"""
    subject = "مرحباً بك في مركز الترميز الطبي | Welcome to Medical Coding Center"
    
    body_html = f"""
    <html dir="rtl">
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
            <h1 style="color: white; margin: 0; font-size: 28px;">مركز الترميز الطبي وتحسين التوثيق السريري</h1>
            <p style="color: #f0f0f0; margin-top: 10px; font-size: 14px;">Medical Coding & Clinical Documentation Improvement Center</p>
        </div>
        
        <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
            <h2 style="color: #667eea; text-align: right;">مرحباً {user_name}</h2>
            <p style="text-align: right; font-size: 16px;">
                نرحب بك في منصة مركز الترميز الطبي وتحسين التوثيق السريري. نحن سعداء بانضمامك إلينا!
            </p>
            
            <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-right: 4px solid #667eea;">
                <h3 style="color: #667eea; margin-top: 0; text-align: right;">ماذا يمكنك أن تفعل؟</h3>
                <ul style="text-align: right; color: #555;">
                    <li>إضافة وتحليل الملاحظات السريرية باستخدام الذكاء الاصطناعي</li>
                    <li>تحديد التشخيصات وتحسين التوثيق الطبي</li>
                    <li>إنشاء استفسارات للأطباء</li>
                    <li>تصدير التقارير بصيغة PDF و Excel</li>
                </ul>
            </div>
            
            <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
            
            <h2 style="color: #667eea; text-align: left;">Welcome {user_name}</h2>
            <p style="text-align: left; font-size: 16px;">
                Welcome to the Medical Coding & Clinical Documentation Improvement Center platform. We're excited to have you join us!
            </p>
            
            <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #667eea;">
                <h3 style="color: #667eea; margin-top: 0; text-align: left;">What can you do?</h3>
                <ul style="text-align: left; color: #555;">
                    <li>Add and analyze clinical notes using AI</li>
                    <li>Identify diagnoses and improve medical documentation</li>
                    <li>Generate physician queries</li>
                    <li>Export reports in PDF and Excel formats</li>
                </ul>
            </div>
            
            <div style="text-align: center; margin-top: 30px;">
                <p style="color: #999; font-size: 12px;">© 2025 جميع الحقوق محفوظة | عمر المغذوي</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    await send_email(user_email, subject, body_html)

async def send_password_reset_email(user_email: str, user_name: str, reset_token: str):
    """Send password reset email"""
    frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
    reset_link = f"{frontend_url}/reset-password?token={reset_token}"
    
    subject = "إعادة تعيين كلمة المرور | Password Reset"
    
    body_html = f"""
    <html dir="rtl">
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
            <h1 style="color: white; margin: 0; font-size: 28px;">إعادة تعيين كلمة المرور</h1>
            <p style="color: #f0f0f0; margin-top: 10px; font-size: 14px;">Password Reset Request</p>
        </div>
        
        <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
            <h2 style="color: #667eea; text-align: right;">مرحباً {user_name}</h2>
            <p style="text-align: right; font-size: 16px;">
                تلقينا طلباً لإعادة تعيين كلمة المرور الخاصة بحسابك. إذا كنت أنت من قام بهذا الطلب، يرجى النقر على الزر أدناه:
            </p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_link}" style="background: #667eea; color: white; padding: 15px 40px; text-decoration: none; border-radius: 5px; font-size: 16px; display: inline-block;">
                    إعادة تعيين كلمة المرور
                </a>
            </div>
            
            <p style="text-align: right; font-size: 14px; color: #666;">
                أو يمكنك نسخ الرابط التالي ولصقه في المتصفح:<br>
                <a href="{reset_link}" style="color: #667eea; word-break: break-all;">{reset_link}</a>
            </p>
            
            <div style="background: #fff3cd; border: 1px solid #ffc107; padding: 15px; border-radius: 5px; margin: 20px 0; text-align: right;">
                <strong>ملاحظة:</strong> هذا الرابط صالح لمدة ساعة واحدة فقط. إذا لم تطلب إعادة تعيين كلمة المرور، يرجى تجاهل هذا البريد.
            </div>
            
            <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
            
            <h2 style="color: #667eea; text-align: left;">Hello {user_name}</h2>
            <p style="text-align: left; font-size: 16px;">
                We received a request to reset your password. If this was you, please click the button below:
            </p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_link}" style="background: #667eea; color: white; padding: 15px 40px; text-decoration: none; border-radius: 5px; font-size: 16px; display: inline-block;">
                    Reset Password
                </a>
            </div>
            
            <p style="text-align: left; font-size: 14px; color: #666;">
                Or copy and paste this link into your browser:<br>
                <a href="{reset_link}" style="color: #667eea; word-break: break-all;">{reset_link}</a>
            </p>
            
            <div style="background: #fff3cd; border: 1px solid #ffc107; padding: 15px; border-radius: 5px; margin: 20px 0; text-align: left;">
                <strong>Note:</strong> This link is valid for 1 hour only. If you didn't request a password reset, please ignore this email.
            </div>
            
            <div style="text-align: center; margin-top: 30px;">
                <p style="color: #999; font-size: 12px;">© 2025 جميع الحقوق محفوظة | عمر المغذوي</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    await send_email(user_email, subject, body_html)

async def analyze_with_ai(notes_text: str, doctor_notes: List[Dict], provider: str = 'gemini') -> Dict:
    """Analyze clinical notes using specified AI provider - Enhanced CDI Focus"""
    
    # Format doctor notes with specialties
    formatted_notes = "\n\n".join([
        f"**{note['specialty']}**:\n{note['text']}"
        for note in doctor_notes
    ])
    
    system_message = """You are an Expert Clinical Documentation Improvement (CDI) Specialist with deep medical knowledge.

🎯 YOUR MISSION:
Conduct comprehensive CDI analysis to identify ALL documentation opportunities for quality improvement and proper reimbursement.

📋 ANALYSIS REQUIREMENTS:

1. **PRINCIPAL & SECONDARY DIAGNOSES** (التشخيصات الرئيسية والثانوية):
   - Identify ALL diagnoses present in clinical findings
   - Categorize each as Principal (الرئيسي) or Secondary (الثانوي)
   - Include COMPLETE ICD-10-CM codes
   - Document clinical evidence supporting each diagnosis
   - Note severity, stage, type when applicable

2. **DERIVED/IMPLIED DIAGNOSES** (التشخيصات المشتقة):
   - Identify conditions IMPLIED by clinical data but not explicitly documented
   - Example: Lab results showing anemia, medications for diabetes, symptoms suggesting infection
   - These require physician clarification via queries

3. **MISSING DOCUMENTATION** (التوثيق الناقص):
   - Severity indicators (mild, moderate, severe, acute, chronic)
   - Laterality (right, left, bilateral)
   - Stages of disease
   - Causal relationships (due to, secondary to)
   - Complications and manifestations
   - Type/subtype specifications

4. **DOCUMENTATION GAPS** (الفجوات والثغرات):
   - Clinical indicators present without corresponding diagnosis
   - Treatments/medications without documented indication
   - Abnormal results without interpretation
   - Historical conditions mentioned but not current status
   - Risk factors documented but not assessed

⚠️ PHYSICIAN QUERIES - CRITICAL COMPLIANCE FORMAT:

**MANDATORY 2-PART STRUCTURE:**

**PART 1 - HEADER (CDI Staff Reference Only):**
Format: "استفسار يخص: [Diagnosis + Specification] ([ICD-10 Code])"

Examples:
- "استفسار يخص: السكري من النوع 2 مع مضاعفات كلوية (E11.22)"
- "استفسار يخص: فشل القلب الحاد (I50.21)"

**PART 2 - QUERY BODY (Sent to Physician):**

MUST INCLUDE:
✓ SPECIFIC clinical findings (symptoms, vitals, lab values, medications)
✓ Request for documentation based on "clinical judgment" only
✓ Specification of what to document (التشخيص الرئيسي، شدة الحالة، نوع التشخيص، مرحلة المرض)

MUST NOT INCLUDE:
✗ Any mention of the diagnosis name
✗ Leading questions suggesting a diagnosis
✗ Medical coding terminology

✅ CORRECT Query Example (Arabic):
```
استفسار يخص: الفشل الكلوي الحاد (N17.9)

بناءً على الملاحظات الطبية:
- الكرياتينين: 3.8 mg/dL (كان 1.2 قبل أسبوع)
- معدل الترشيح الكبيبي: 25 mL/min
- قلة البول: 400 مل خلال 24 ساعة
- تم البدء بالسوائل الوريدية والمراقبة الدقيقة

بناءً على حكمك الطبي، الرجاء توثيق:
- التشخيص الرئيسي
- شدة الحالة (حاد/مزمن)
- المرحلة إن أمكن
```

✅ CORRECT Query Example (English):
```
Query regarding: Acute Kidney Failure (N17.9)

Based on clinical documentation:
- Creatinine: 3.8 mg/dL (was 1.2 one week ago)
- GFR: 25 mL/min
- Oliguria: 400 mL in 24 hours
- Started IV fluids and close monitoring

Based on your clinical judgment, please document:
- The principal diagnosis
- Severity (acute/chronic)
- Stage if applicable
```

🔍 QUERY SPECIFICATIONS - Request physician to document:
- "التشخيص الرئيسي" (Principal diagnosis)
- "التشخيص الثانوي" (Secondary diagnosis)  
- "شدة الحالة" (Severity: mild/moderate/severe/acute/chronic)
- "نوع التشخيص" (Type/subtype)
- "مرحلة المرض" (Stage)
- "العلاقة السببية" (Causal relationship)

CRITICAL: ALL responses MUST be in BOTH Arabic AND English."""

    user_prompt = f"""Please review the following clinical notes as a CDI Specialist:

{formatted_notes}

Perform a Clinical Documentation Improvement review and provide:

1. **Diagnoses That Should Be Documented**: Based on the clinical findings in the notes, what diagnoses should be clearly documented? (with ICD-10-CM codes for reference only)
   - For EACH diagnosis, specify if it's "principal" (التشخيص الرئيسي) or "secondary" (التشخيص الثانوي)
   - Include the clinical evidence from the notes that supports this diagnosis

2. **Missing Documentation**: What specific clinical information is missing or incomplete? (e.g., severity, acuity, specificity, causal relationships)

3. **Documentation Gaps**: What gaps exist in the current documentation?

4. **Physician Queries**: Generate DETAILED queries with clinical context. For EACH query:
   
   **CRITICAL FORMAT FOR EACH QUERY:**
   
   A. **Header (For CDI staff):**
   "استفسار يخص: [Diagnosis name in Arabic] ([ICD-10 Code])"
   "Query regarding: [Diagnosis name in English] ([ICD-10 Code])"
   
   B. **Query Body (For Physician):**
   - First, cite SPECIFIC clinical findings from the notes (symptoms, medications prescribed, lab results, vital signs)
   - Then ask physician to document based on clinical judgment
   - Specify if asking for principal diagnosis or secondary diagnosis
   
   **Example Format in Arabic:**
   ```
   استفسار يخص: ارتفاع ضغط الدم (I10)
   
   بناءً على الملاحظات الطبية:
   - [ذكر الأعراض المحددة من الملاحظات]
   - [ذكر الأدوية المصروفة من الملاحظات]
   - [ذكر القياسات أو الفحوصات من الملاحظات]
   
   بناءً على حكمك الطبي، الرجاء توثيق التشخيص [الرئيسي/الثانوي - حسب النوع].
   ```
   
   **Example Format in English:**
   ```
   Query regarding: Hypertension (I10)
   
   Based on clinical documentation:
   - [Cite specific symptoms from notes]
   - [Cite specific medications prescribed from notes]
   - [Cite specific measurements/tests from notes]
   
   Based on your clinical judgment, please document the [principal/secondary - based on type] diagnosis.
   ```
   
   **CRITICAL RULES:**
   - NEVER suggest a specific diagnosis name in the query body
   - ALWAYS include clinical evidence from the actual notes
   - ALWAYS specify if it's principal or secondary diagnosis
   - Use "التشخيص الرئيسي" for principal, omit "الرئيسي" for secondary

5. **Recommendations**: Specific recommendations to improve the clinical documentation quality

Provide response in this EXACT JSON format:
{{{{
  "diagnoses_to_document": [
    {{
      "diagnosis_ar": "التشخيص بالعربي الكامل مع التفاصيل",
      "diagnosis_en": "Complete diagnosis in English with details",
      "icd_code": "Full ICD-10-CM code",
      "type": "principal" or "secondary" or "derived",
      "severity": "Severity/Stage/Type if applicable",
      "clinical_evidence": "Specific clinical findings from notes supporting this diagnosis"
    }}
  ],
  "missing_documentation": [
    {{
      "item_ar": "التوثيق الناقص - كن محدداً",
      "item_en": "Missing documentation - be specific",
      "impact": "Impact on coding/reimbursement/quality"
    }}
  ],
  "gaps_ar": [
    "فجوة توثيقية محددة 1 - اشرح بالتفصيل",
    "ثغرة في التوثيق 2 - مع أمثلة من الملاحظات"
  ],
  "gaps_en": [
    "Specific documentation gap 1 - explain in detail",
    "Documentation deficiency 2 - with examples from notes"
  ],
  "queries_ar": [
    "استفسار يخص: [التشخيص الكامل] ([ICD-10])\\n\\nبناءً على الملاحظات الطبية:\\n- [معطى سريري محدد 1]\\n- [معطى سريري محدد 2]\\n- [معطى سريري محدد 3]\\n\\nبناءً على حكمك الطبي، الرجاء توثيق:\\n- التشخيص [الرئيسي/الثانوي]\\n- شدة الحالة\\n- المرحلة/النوع إن أمكن"
  ],
  "queries_en": [
    "Query regarding: [Full diagnosis] ([ICD-10])\\n\\nBased on clinical documentation:\\n- [Specific clinical finding 1]\\n- [Specific clinical finding 2]\\n- [Specific clinical finding 3]\\n\\nBased on your clinical judgment, please document:\\n- [Principal/Secondary] diagnosis\\n- Severity\\n- Stage/Type if applicable"
  ],
  "recommendations_ar": [
    "توصية محددة 1 مع خطوات عملية",
    "توصية 2 لتحسين جودة التوثيق"
  ],
  "recommendations_en": [
    "Specific recommendation 1 with actionable steps",
    "Recommendation 2 for documentation quality improvement"
  ],
  "summary_ar": "ملخص شامل ومفصل يغطي جميع النقاط الحرجة في التوثيق",
  "summary_en": "Comprehensive detailed summary covering all critical documentation points"
}}}}

CRITICAL REQUIREMENTS:
- Identify ALL diagnoses (principal, secondary, AND derived/implied)
- Each query MUST cite 3+ specific clinical findings
- Gaps MUST be detailed with examples
- ALL ICD-10-CM codes MUST be complete and accurate"""

    try:
        response_text = None  # Initialize to avoid UnboundLocalError
        
        # Select AI provider
        if provider == 'gemini':
            # Use Google Gemini API with intelligent key rotation
            # Combine system message and user prompt
            full_prompt = f"{system_message}\n\n{user_prompt}"
            
            # Try all available keys with intelligent rotation
            max_retries = len(GEMINI_API_KEYS)
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    # Get model with next key in rotation
                    model = get_gemini_model('gemini-2.5-flash')
                    response = model.generate_content(full_prompt)
                    response_text = response.text.strip()
                    logger.info(f"✅ Gemini analysis successful on attempt {attempt + 1}")
                    break  # Success, exit retry loop
                    
                except Exception as e:
                    last_error = e
                    error_msg = str(e)
                    
                    # Check if quota exceeded (429 error)
                    if "429" in error_msg or "quota" in error_msg.lower() or "RESOURCE_EXHAUSTED" in error_msg:
                        logger.warning(f"⚠️ Gemini key exhausted (attempt {attempt + 1}/{max_retries})")
                        
                        # Continue trying other keys
                        if attempt < max_retries - 1:
                            logger.info(f"🔄 Trying next Gemini key ({attempt + 2}/{max_retries})...")
                            continue
                        else:
                            # All Gemini keys exhausted, try fallback
                            logger.error("❌ All Gemini keys exhausted")
                            
                            # Try fallback to DeepSeek or Azure
                            deepseek_key = os.environ.get('DEEPSEEK_API_KEY')
                            azure_key = os.environ.get('AZURE_OPENAI_KEY')
                            
                            if deepseek_key:
                                logger.info("🔄 Auto-switching to DeepSeek due to Gemini quota limit")
                                provider = 'deepseek'
                                response_text = None
                                break
                            elif azure_key:
                                logger.info("🔄 Auto-switching to Azure due to Gemini quota limit")
                                provider = 'azure'
                                response_text = None
                                break
                            else:
                                raise HTTPException(
                                    status_code=429,
                                    detail=f"جميع مفاتيح Gemini ({len(GEMINI_API_KEYS)}) وصلت للحد اليومي. الرجاء استخدام DeepSeek أو Azure. All {len(GEMINI_API_KEYS)} Gemini keys reached daily quota. Please use DeepSeek or Azure."
                                )
                    else:
                        # Other errors - try next key
                        if attempt < max_retries - 1:
                            logger.warning(f"⚠️ Error with key, trying next: {error_msg[:100]}")
                            continue
                        else:
                            raise e
        
        # Process if response_text is still None (fallback triggered or direct provider selection)
        if provider == 'azure' and response_text is None:
            # Use Microsoft Azure OpenAI
            from openai import AzureOpenAI
            
            azure_key = os.environ.get('AZURE_OPENAI_KEY')
            if not azure_key:
                # Check database
                azure_settings = await db.ai_settings.find_one({"provider": "azure"})
                if azure_settings and azure_settings.get('api_keys'):
                    azure_key = random.choice(azure_settings['api_keys'])
                else:
                    raise HTTPException(status_code=400, detail="Azure OpenAI key not configured")
            
            endpoint = os.environ.get('AZURE_OPENAI_ENDPOINT', 'https://your-resource.openai.azure.com/')
            deployment = os.environ.get('AZURE_OPENAI_DEPLOYMENT', 'gpt-4')
            api_version = os.environ.get('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')
            
            client = AzureOpenAI(
                api_key=azure_key,
                api_version=api_version,
                azure_endpoint=endpoint
            )
            
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_prompt}
            ]
            
            response = client.chat.completions.create(
                model=deployment,
                messages=messages,
                temperature=0.7,
                max_tokens=4000
            )
            
            response_text = response.choices[0].message.content.strip()
        
        elif provider == 'deepseek' and response_text is None:
            # Use DeepSeek
            from openai import OpenAI
            
            # Get DeepSeek API key
            deepseek_key = os.environ.get('DEEPSEEK_API_KEY')
            if not deepseek_key:
                # Check database
                deepseek_settings = await db.ai_settings.find_one({"provider": "deepseek"})
                if deepseek_settings and deepseek_settings.get('api_keys'):
                    deepseek_key = random.choice(deepseek_settings['api_keys'])
                else:
                    raise HTTPException(status_code=400, detail="مفتاح DeepSeek غير مُعدّ. DeepSeek API key not configured")
            
            # DeepSeek uses OpenAI-compatible API
            client = OpenAI(
                api_key=deepseek_key,
                base_url="https://api.deepseek.com"
            )
            
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_prompt}
            ]
            
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                temperature=0.7,
                max_tokens=4000
            )
            
            response_text = response.choices[0].message.content.strip()
        
        elif provider == 'phi3' and response_text is None:
            # Use Microsoft Phi-3-Medium-128K via Ollama (Local/Offline)
            import requests
            
            try:
                ollama_url = "http://localhost:11434/api/generate"
                
                payload = {
                    "model": "phi3:medium-128k",
                    "prompt": f"{system_message}\n\n{user_prompt}",
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 4000
                    }
                }
                
                response = requests.post(ollama_url, json=payload, timeout=120)
                response.raise_for_status()
                
                response_text = response.json().get('response', '').strip()
                logger.info("✅ Phi-3 analysis successful (local model)")
                
            except requests.exceptions.ConnectionError:
                raise HTTPException(
                    status_code=503,
                    detail="نموذج Phi-3 غير متاح حالياً. Phi-3 model is not available. Make sure Ollama is running."
                )
            except Exception as e:
                logger.error(f"❌ Phi-3 error: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Phi-3 failed: {str(e)}")
        
        elif response_text is None:
            raise HTTPException(status_code=400, detail=f"مزود غير مدعوم أو فشل في المعالجة: {provider}. Unsupported AI provider or processing failed: {provider}")
        
        # Enhanced JSON parsing with better error handling
        import json
        import re
        
        try:
            # Remove markdown code blocks if present
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            # Remove any BOM or invisible characters
            response_text = response_text.strip().lstrip('\ufeff').lstrip('\u200b')
            
            # Try to find JSON object in the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(0)
            
            # Parse JSON
            result = json.loads(response_text)
            return result
            
        except json.JSONDecodeError as je:
            logger.error(f"JSON parsing error: {str(je)}")
            logger.error(f"Response text (first 500 chars): {response_text[:500]}")
            raise HTTPException(
                status_code=500, 
                detail=f"فشل في تحليل استجابة AI. Failed to parse AI response: {str(je)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error analyzing with AI: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in analysis: {str(e)}")

# Health check route
@api_router.get("/")
async def root():
    return {"message": "مركز الترميز الطبي وتحسين التوثيق السريري", "status": "active"}

@api_router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    from fastapi.responses import Response
    return Response(generate_latest(REGISTRY), media_type="text/plain")

# Get specialties
@api_router.get("/specialties")
async def get_specialties():
    return MEDICAL_SPECIALTIES

# ========== Auth Routes ==========
@api_router.post("/auth/register", response_model=Token)
# @limiter.limit("3/hour")  # Temporarily disabled
async def register(request: Request, user_data: UserRegister):
    import re
    from security_utils import log_audit, send_welcome_email
    
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Registration failed")
    
    # Check if phone number already registered
    existing_phone = await db.users.find_one({"phone_number": user_data.phone_number})
    if existing_phone:
        raise HTTPException(status_code=400, detail="Registration failed")
    
    # Validate password strength
    password = user_data.password
    if len(password) < 12:
        raise HTTPException(status_code=400, detail="Password must be at least 12 characters long")
    if not re.search(r'[A-Z]', password):
        raise HTTPException(status_code=400, detail="Password must contain at least one uppercase letter")
    if not re.search(r'[a-z]', password):
        raise HTTPException(status_code=400, detail="Password must contain at least one lowercase letter")
    if not re.search(r'[0-9]', password):
        raise HTTPException(status_code=400, detail="Password must contain at least one digit")
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise HTTPException(status_code=400, detail="Password must contain at least one special character")
    
    # Check for common weak passwords
    weak_passwords = ['Password123!', 'Welcome123!', 'Admin123!', 'User123456!']
    if password in weak_passwords:
        raise HTTPException(status_code=400, detail="This password is too common. Please choose a stronger password")
    
    # Check if admin code is provided and valid
    role = "user"
    if user_data.admin_code:
        if user_data.admin_code == ADMIN_SECRET_CODE:
            role = "admin"
        else:
            raise HTTPException(status_code=400, detail="Invalid admin code")
    
    # Set password expiration (90 days from now)
    password_expires_at = datetime.now(timezone.utc) + timedelta(days=90)
    
    # Validate department and coding_role
    department = user_data.department if user_data.department in ['cdi', 'coding'] else 'cdi'
    coding_role = None
    daily_case_target = None
    
    if department == 'coding':
        if user_data.coding_role not in ['coder', 'auditor']:
            raise HTTPException(status_code=400, detail="Invalid coding role. Must be 'coder' or 'auditor'")
        coding_role = user_data.coding_role
        
        if coding_role == 'coder':
            daily_case_target = 10  # Default target for new coders
    
    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        phone_number=user_data.phone_number,
        password_hash=hash_password(user_data.password),
        role=role,
        department=department,
        coding_role=coding_role,
        daily_case_target=daily_case_target
    )
    
    doc = user.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    # Add security fields
    doc['mfa_enabled'] = True  # Enable MFA by default for security
    doc['password_last_changed'] = datetime.now(timezone.utc).isoformat()
    doc['password_expires_at'] = password_expires_at.isoformat()
    doc['account_locked'] = False
    doc['locked_until'] = None
    doc['failed_login_attempts'] = 0
    
    await db.users.insert_one(doc)
    
    # Log registration in audit logs
    await log_audit(
        db,
        action="user_registered",
        user_id=user.id,
        user_email=user.email,
        status="success",
        details={"role": role}
    )
    
    # Send welcome email (async, non-blocking)
    try:
        await send_welcome_email(user.email, user.full_name, role)
    except Exception as e:
        logging.error(f"Failed to send welcome email: {str(e)}")
    
    token = create_access_token({
        "user_id": user.id, 
        "email": user.email,
        "role": user.role
    })
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id, 
            "email": user.email, 
            "full_name": user.full_name,
            "phone_number": user.phone_number,
            "role": user.role,
            "department": user.department,
            "coding_role": user.coding_role
        }
    }

@api_router.post("/auth/login-step1")
# @limiter.limit("50/minute")  # Temporarily disabled for testing
async def login_step1(request: Request, credentials: UserLogin):
    """Step 1: Verify credentials and send OTP"""
    print(f"🔑 LOGIN REQUEST: {credentials.email}")
    try:
        # Import security utils
        from security_utils import (
            check_rate_limit, record_login_attempt, 
            unlock_account_if_expired, log_audit, 
            generate_otp, send_otp_email
        )
        
        # Skip rate limiting and unlock for test accounts
        test_accounts = ["medidocai@gmail.com", "almaghthawi.cdi@gmail.com", "supervisor@hospital.sa", "coder@hospital.sa", "auditor@hospital.sa"]
        if credentials.email in test_accounts:
            # Force unlock test accounts
            await db.users.update_one(
                {"email": credentials.email},
                {"$set": {"account_locked": False, "locked_until": None, "failed_login_attempts": 0}}
            )
        else:
            # Check if account lockout expired
            await unlock_account_if_expired(db, credentials.email)
            # Check rate limiting
            is_allowed, remaining = await check_rate_limit(db, credentials.email)
            if not is_allowed:
                raise HTTPException(
                    status_code=429, 
                    detail="Account temporarily locked due to multiple failed login attempts. Please try again later."
                )
        
        # Find user
        user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
        
        print(f"LOGIN DEBUG: Found user={user is not None}, Email={credentials.email}")
        
        # Check if user exists
        if not user:
            print("LOGIN DEBUG: User not found")
            await record_login_attempt(db, credentials.email, False)
            await log_audit(
                db,
                action="login_failed",
                user_email=credentials.email,
                status="failure",
                details={"reason": "User not found"}
            )
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        print(f"LOGIN DEBUG: User fields: {list(user.keys())}")
        
        # Check if password field exists (support both 'password' and 'password_hash')
        password_field = 'password' if 'password' in user else 'password_hash'
        if password_field not in user:
            print("LOGIN DEBUG: Password field missing!")
            raise HTTPException(status_code=500, detail="User account error - please contact support")
        
        print(f"LOGIN DEBUG: Verifying password using field: {password_field}...")
        print(f"LOGIN DEBUG: Password length: {len(credentials.password)}, Hash length: {len(user[password_field])}")
        
        # Check if password is correct
        try:
            password_valid = verify_password(credentials.password, user[password_field])
            print(f"LOGIN DEBUG: Password verification result: {password_valid}")
        except Exception as e:
            print(f"LOGIN DEBUG: Password verification error: {e}")
            password_valid = False
        
        if not password_valid:
            print("LOGIN DEBUG: Password verification failed")
            # Record failed attempt
            await record_login_attempt(db, credentials.email, False)
            await log_audit(
                db,
                action="login_failed",
                user_email=credentials.email,
                status="failure",
                details={"reason": "Invalid credentials", "remaining_attempts": remaining - 1}
            )
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Check if account is locked
        if user.get('account_locked'):
            raise HTTPException(status_code=403, detail="Account is locked. Please contact support.")
        
        # Check if MFA is enabled (default: true for security)
        mfa_enabled = user.get('mfa_enabled', True)
        
        if mfa_enabled:
            # Generate and send OTP
            otp_code = generate_otp()
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)  # Increased from 15 to 30 minutes
            
            # Save OTP to database
            otp_doc = {
                "id": str(uuid.uuid4()),
                "user_id": user['id'],
                "email": credentials.email,
                "otp_code": otp_code,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": expires_at.isoformat(),
                "is_used": False,
                "attempts": 0
            }
            print(f"DEBUG: Saving OTP for {credentials.email}, code: {otp_code}, expires: {expires_at.isoformat()}")
            result = await db.otp_records.insert_one(otp_doc)
            print(f"DEBUG: OTP saved with ID: {result.inserted_id}")
            
            # Send OTP via email
            user_name = user.get('full_name', 'المستخدم')
            await send_otp_email(credentials.email, otp_code, user_name)
            
            # Log audit
            await log_audit(
                db,
                action="login_otp_sent",
                user_id=user['id'],
                user_email=credentials.email,
                status="success"
            )
            
            return {
                "requires_mfa": True,
                "message": "OTP sent to your email",
                "email": credentials.email
            }
        else:
            # MFA disabled, login directly (not recommended)
            await record_login_attempt(db, credentials.email, True)
            
            token = create_access_token({
                "user_id": user['id'], 
                "email": user['email'],
                "role": user.get('role', 'user')
            })
            
            # Log successful login
            await log_audit(
                db,
                action="login_success",
                user_id=user['id'],
                user_email=credentials.email,
                status="success"
            )
            
            return {
                "requires_mfa": False,
                "access_token": token,
                "token_type": "bearer",
                "user": {
                    "id": user['id'], 
                    "email": user['email'], 
                    "full_name": user['full_name'],
                    "phone_number": user.get('phone_number', ''),
                    "role": user.get('role', 'user'),
                    "department": user.get('department', 'cdi'),
                    "coding_role": user.get('coding_role')
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed")

@api_router.post("/auth/login-step2", response_model=Token)
# @limiter.limit("10/minute")  # Temporarily disabled
async def login_step2(request: Request, credentials: OTPVerification):
    """Step 2: Verify OTP and complete login"""
    try:
        from security_utils import log_audit, record_login_attempt
        
        # Find OTP record
        print(f"DEBUG: Looking for OTP - email={credentials.email}, code={credentials.otp_code}")
        otp_record = await db.otp_records.find_one({
            "email": credentials.email,
            "otp_code": credentials.otp_code,
            "is_used": False
        }, {"_id": 0})
        print(f"DEBUG: OTP found={otp_record is not None}")
        
        if not otp_record:
            await log_audit(
                db,
                action="login_otp_failed",
                user_email=credentials.email,
                status="failure",
                details={"reason": "Invalid OTP"}
            )
            raise HTTPException(status_code=400, detail="Invalid OTP code")
        
        # Check expiration
        expires_at = datetime.fromisoformat(otp_record['expires_at'])
        if datetime.now(timezone.utc) > expires_at:
            await log_audit(
                db,
                action="login_otp_failed",
                user_email=credentials.email,
                status="failure",
                details={"reason": "OTP expired"}
            )
            raise HTTPException(status_code=400, detail="OTP code has expired")
        
        # Mark OTP as used
        await db.otp_records.update_one(
            {"id": otp_record['id']},
            {"$set": {"is_used": True}}
        )
        
        # Get user
        user = await db.users.find_one({"id": otp_record['user_id']}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Record successful login
        await record_login_attempt(db, credentials.email, True)
        
        # Create session
        token = create_access_token({
            "user_id": user['id'], 
            "email": user['email'],
            "role": user.get('role', 'user')
        })
        
        # Save session to database
        session_expires = datetime.now(timezone.utc) + timedelta(days=7)
        session_doc = {
            "id": str(uuid.uuid4()),
            "user_id": user['id'],
            "token": token,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_activity": datetime.now(timezone.utc).isoformat(),
            "expires_at": session_expires.isoformat(),
            "is_active": True
        }
        await db.user_sessions.insert_one(session_doc)
        
        # Log successful login
        await log_audit(
            db,
            action="login_success",
            user_id=user['id'],
            user_email=credentials.email,
            status="success",
            details={"method": "mfa"}
        )
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user['id'], 
                "email": user['email'], 
                "full_name": user['full_name'],
                "phone_number": user.get('phone_number', ''),
                "role": user.get('role', 'user'),
                "department": user.get('department', 'cdi'),
                "coding_role": user.get('coding_role')
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"OTP verification error: {str(e)}")
        raise HTTPException(status_code=500, detail="Verification failed")

# Keep old endpoint for backward compatibility (deprecated)
@api_router.post("/auth/login", response_model=Token)
async def login(request: Request, credentials: UserLogin):
    """Legacy login endpoint - redirects to new MFA flow"""
    result = await login_step1(request, credentials)
    if result.get('requires_mfa'):
        raise HTTPException(
            status_code=202,
            detail={
                "message": "MFA required",
                "email": result['email'],
                "requires_mfa": True
            }
        )
    return result

@api_router.get("/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current logged in user info"""
    return {
        "id": current_user['id'],
        "email": current_user['email'],
        "full_name": current_user['full_name'],
        "phone_number": current_user.get('phone_number', ''),
        "role": current_user.get('role', 'user')
    }

@api_router.post("/auth/forgot-password")
async def forgot_password(request: PasswordResetRequest):
    """Request password reset - sends link via Email only"""
    user = await db.users.find_one({"email": request.email}, {"_id": 0})
    
    # Always return success (don't reveal if email exists)
    if not user:
        return {"message": "If the account exists, a reset link will be sent to email"}
    
    # Generate reset token
    reset_token = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    
    # Store reset token
    token_doc = PasswordResetToken(
        user_id=user['id'],
        token=reset_token,
        expires_at=expires_at
    )
    
    doc = token_doc.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['expires_at'] = doc['expires_at'].isoformat()
    await db.password_reset_tokens.insert_one(doc)
    
    # Send password reset email
    try:
        await send_password_reset_email(user['email'], user['full_name'], reset_token)
        logging.info(f"Password reset email sent to user {user['email']}")
    except Exception as e:
        logging.error(f"Failed to send password reset email: {str(e)}")
    
    return {
        "message": "تم إرسال رابط إعادة تعيين كلمة المرور إلى بريدك الإلكتروني",
        "message_en": "Password reset link sent to your email"
    }

@api_router.post("/auth/reset-password")
async def reset_password(request: PasswordReset):
    """Reset password using token from email"""
    # Find valid token
    token_doc = await db.password_reset_tokens.find_one({
        "token": request.token,
        "used": False
    }, {"_id": 0})
    
    if not token_doc:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    # Check if token expired
    expires_at = datetime.fromisoformat(token_doc['expires_at'])
    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(status_code=400, detail="Reset token has expired")
    
    # Update user password
    new_password_hash = hash_password(request.new_password)
    await db.users.update_one(
        {"id": token_doc['user_id']},
        {"$set": {"password": new_password_hash}}
    )
    
    # Mark token as used
    await db.password_reset_tokens.update_one(
        {"token": request.token},
        {"$set": {"used": True}}
    )
    
    return {"message": "Password reset successful"}

# ========== Admin Routes ==========
async def require_admin(user: dict = Depends(get_current_user)):
    if user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

@api_router.get("/admin/users-statistics")
async def get_users_statistics(admin: dict = Depends(require_admin)):
    """Get detailed statistics for all users - Optimized with aggregation"""
    from datetime import datetime, timezone, timedelta
    
    today = datetime.now(timezone.utc).date()
    today_start = datetime.combine(today, datetime.min.time()).isoformat()
    today_end = datetime.combine(today + timedelta(days=1), datetime.min.time()).isoformat()
    
    # Optimized aggregation pipeline - single query instead of N+1
    pipeline = [
        {"$match": {"role": {"$ne": "admin"}}},
        {
            "$lookup": {
                "from": "clinical_notes",
                "localField": "id",
                "foreignField": "user_id",
                "as": "notes"
            }
        },
        {
            "$lookup": {
                "from": "analyses",
                "localField": "id",
                "foreignField": "user_id",
                "as": "analyses"
            }
        },
        {
            "$addFields": {
                "total_notes": {"$size": "$notes"},
                "total_analyses": {"$size": "$analyses"},
                "today_notes": {
                    "$size": {
                        "$filter": {
                            "input": "$notes",
                            "cond": {
                                "$and": [
                                    {"$gte": ["$$this.created_at", today_start]},
                                    {"$lt": ["$$this.created_at", today_end]}
                                ]
                            }
                        }
                    }
                },
                "today_analyses": {
                    "$size": {
    