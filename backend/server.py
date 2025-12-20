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
        admin_email = "almaghthawi.cdi@gmail.com"
        admin_password = "CDI@2024#Admin"
        
        print(f"🔍 Checking admin account...")
        
        # Delete ALL admin accounts first to ensure clean state
        deleted = await db.users.delete_many({'role': 'admin'})
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

# Rate Limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
SECRET_KEY = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Emergent LLM Key
# Load Gemini API Keys (multiple for rotation)
GEMINI_API_KEYS = [
    os.environ.get('GEMINI_API_KEY_1'),
    os.environ.get('GEMINI_API_KEY_2'),
    os.environ.get('GEMINI_API_KEY_3')
]
# Filter out None values
GEMINI_API_KEYS = [key for key in GEMINI_API_KEYS if key]

if not GEMINI_API_KEYS:
    raise ValueError("No Gemini API keys found in environment variables")

# Log will be done after logger is initialized
print(f"✅ Loaded {len(GEMINI_API_KEYS)} Gemini API keys for rotation")

# Helper function to get a random API key for load balancing
def get_gemini_model(model_name='gemini-flash-latest', system_instruction=None):
    """Get a Gemini model with a random API key for load balancing"""
    api_key = random.choice(GEMINI_API_KEYS)
    genai.configure(api_key=api_key)
    
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
    supervisor_id: Optional[str] = None  # ID of supervisor (if user is assigned to one)
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserRegister(BaseModel):
    email: EmailStr
    full_name: str
    phone_number: str  # رقم الجوال مطلوب
    password: str
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
    ai_provider: Optional[str] = 'azure'  # azure (default)

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
    ai_provider: Optional[str] = 'azure'  # azure (default)

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

async def analyze_with_gemini(notes_text: str, doctor_notes: List[Dict]) -> Dict:
    """Analyze clinical notes using Gemini AI - CDI Focus"""
    
    # Format doctor notes with specialties
    formatted_notes = "\n\n".join([
        f"**{note['specialty']}**:\n{note['text']}"
        for note in doctor_notes
    ])
    
    system_message = """You are a Clinical Documentation Improvement (CDI) Specialist expert.

Your role is NOT to code or assign ICD-10-CM codes directly. Your role is to:
1. Review clinical documentation for completeness and specificity
2. Identify diagnoses that SHOULD BE documented based on clinical findings
3. Identify missing or incomplete documentation
4. Provide queries to physicians to improve documentation quality
5. Ensure documentation supports the severity of illness and risk of mortality

Focus on CLINICAL DOCUMENTATION IMPROVEMENT, not medical coding.

⚠️ CRITICAL COMPLIANCE REQUIREMENT FOR PHYSICIAN QUERIES:

**Query Structure (2 Parts):**

**Part 1 - HEADER (For CDI Staff Only):**
- Include diagnosis name and ICD code
- This is for the CDI specialist's reference, NOT sent to physician directly
- Format: "استفسار يخص: [Diagnosis] ([ICD Code])"

**Part 2 - QUERY BODY (Sent to Physician):**
- Cite SPECIFIC clinical findings from the notes (symptoms, medications, lab values, vital signs)
- DO NOT mention the diagnosis name
- Ask physician to document based on clinical judgment
- Specify if principal or secondary diagnosis is needed

✅ CORRECT Complete Query Example (Arabic):
```
استفسار يخص: ارتفاع ضغط الدم (I10)

بناءً على الملاحظات الطبية:
- المريض لديه قراءات ضغط متكررة 150/95، 145/92
- تم وصف Amlodipine 5mg يومياً
- التاريخ المرضي يشير إلى ارتفاعات سابقة

بناءً على حكمك الطبي، الرجاء توثيق التشخيص الرئيسي.
```

✅ CORRECT Complete Query Example (English):
```
Query regarding: Hypertension (I10)

Based on clinical documentation:
- Patient has repeated BP readings of 150/95, 145/92
- Prescribed Amlodipine 5mg daily
- Medical history indicates previous elevations

Based on your clinical judgment, please document the principal diagnosis.
```

❌ INCORRECT (DO NOT include diagnosis in query body):
- "هل التشخيص هو ارتفاع ضغط الدم؟" ✗
- "Is this hypertension or white coat syndrome?" ✗
- "يُرجى تأكيد: ارتفاع ضغط الدم" ✗

**Key Rules:**
- Header = diagnosis name + code (for CDI staff)
- Body = clinical findings ONLY + request for documentation (for physician)
- NEVER suggest diagnosis in the body sent to physician

IMPORTANT: Provide ALL responses in BOTH Arabic and English."""

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

Please respond in the following JSON format:
{{{{
  "diagnoses_to_document": [{{
    "diagnosis_ar": "التشخيص بالعربي",
    "diagnosis_en": "Diagnosis in English", 
    "icd_code": "Code (for reference)",
    "type": "principal" or "secondary",
    "clinical_evidence": "Evidence from notes supporting this diagnosis"
  }}],
  "missing_documentation": [{{
    "item_ar": "التوثيق الناقص بالعربي",
    "item_en": "Missing item in English"
  }}],
  "gaps_ar": ["ثغرة 1", "ثغرة 2"],
  "gaps_en": ["Gap 1", "Gap 2"],
  "queries_ar": [
    "استفسار يخص: [اسم التشخيص] ([كود ICD-10])\\n\\nبناءً على الملاحظات الطبية:\\n- [معطيات محددة من الملاحظات: الأعراض]\\n- [الأدوية المصروفة]\\n- [القياسات والفحوصات]\\n\\nبناءً على حكمك الطبي، الرجاء توثيق التشخيص [الرئيسي/الثانوي]."
  ],
  "queries_en": [
    "Query regarding: [Diagnosis name] ([ICD-10 Code])\\n\\nBased on clinical documentation:\\n- [Specific findings from notes: symptoms]\\n- [Medications prescribed]\\n- [Measurements/tests]\\n\\nBased on your clinical judgment, please document the [principal/secondary] diagnosis."
  ],
  "recommendations_ar": ["توصية 1 لتحسين التوثيق", "توصية 2"],
  "recommendations_en": ["Recommendation 1 for documentation improvement", "Recommendation 2"],
  "summary_ar": "ملخص شامل لمراجعة تحسين التوثيق السريري بالعربي",
  "summary_en": "Comprehensive CDI review summary in English"
}}}}

IMPORTANT: For queries, you MUST:
1. Include the header with diagnosis name and ICD code for CDI staff reference
2. Cite ACTUAL clinical findings from the provided notes (symptoms, medications, measurements)
3. Never suggest diagnosis names in the query body itself
4. Specify if it's principal or secondary diagnosis
5. Each query should be detailed with real evidence from the notes"""

    try:
        # Use Google Gemini API with automatic key rotation
        model = get_gemini_model('gemini-2.0-flash-exp')
        
        # Combine system message and user prompt
        full_prompt = f"{system_message}\n\n{user_prompt}"
        
        # Generate response with retry logic
        max_retries = len(GEMINI_API_KEYS)
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = model.generate_content(full_prompt)
                response_text = response.text.strip()
                break  # Success, exit retry loop
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    # Try with a different key
                    logger.warning(f"Retry {attempt + 1}/{max_retries} with different API key")
                    model = get_gemini_model('gemini-2.0-flash-exp')
                else:
                    raise e
        
        # Parse JSON response
        import json
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        result = json.loads(response_text)
        return result
        
    except Exception as e:
        logging.error(f"Error analyzing with Gemini: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in analysis: {str(e)}")


async def analyze_with_ai(notes_text: str, doctor_notes: List[Dict], provider: str = 'phi3') -> Dict:
    """
    Analyze clinical notes using specified AI provider (Phi-3 or DeepSeek)
    Default: Phi-3 (local, offline, free)
    """
    
    # Format doctor notes with specialties
    formatted_notes = "\n\n".join([
        f"**{note['specialty']}**:\n{note['text']}"
        for note in doctor_notes
    ])
    
    # Enhanced system message for better accuracy with long notes and ICD codes
    system_message = """You are an Expert Clinical Documentation Improvement (CDI) Specialist with deep medical knowledge.

🎯 YOUR MISSION:
Conduct comprehensive CDI analysis to identify ALL documentation opportunities for quality improvement and proper reimbursement.

📋 CRITICAL ANALYSIS REQUIREMENTS FOR LONG CLINICAL NOTES:

1. **READ ENTIRE NOTE CAREFULLY** - Don't miss details in long documentation
2. **IDENTIFY ALL DIAGNOSES** (Principal, Secondary, AND Derived/Implied)
   - Categorize each as Principal (الرئيسي) or Secondary (الثانوي)
   - Include COMPLETE and ACCURATE ICD-10-CM codes (verify specificity)
   - Document clinical evidence supporting each diagnosis
   - Note severity, stage, type, laterality when applicable

3. **DERIVED/IMPLIED DIAGNOSES** (التشخيصات المشتقة):
   - Conditions IMPLIED by clinical data but not explicitly documented
   - Lab results showing anemia, medications for diabetes, symptoms suggesting infection
   - These require physician clarification via queries

4. **MISSING DOCUMENTATION** (التوثيق الناقص):
   - Severity indicators (mild, moderate, severe, acute, chronic)
   - Laterality (right, left, bilateral)
   - Stages of disease
   - Causal relationships (due to, secondary to)
   - Complications and manifestations
   - Type/subtype specifications

5. **DOCUMENTATION GAPS** (الفجوات والثغرات):
   - Clinical indicators present without corresponding diagnosis
   - Treatments/medications without documented indication
   - Abnormal results without interpretation
   - Historical conditions mentioned but not current status

⚠️ PHYSICIAN QUERIES - CRITICAL COMPLIANCE FORMAT:

**MANDATORY 2-PART STRUCTURE:**

**PART 1 - HEADER (CDI Staff Reference Only):**
Format: "استفسار يخص: [Diagnosis + Specification] ([ICD-10 Code])"

**PART 2 - QUERY BODY (Sent to Physician):**
MUST INCLUDE:
✓ SPECIFIC clinical findings (symptoms, vitals, lab values, medications)
✓ Request for documentation based on "clinical judgment" only
✓ Specification of what to document

MUST NOT INCLUDE:
✗ Any mention of the diagnosis name
✗ Leading questions suggesting a diagnosis

✅ CORRECT Query Example (Arabic):
```
استفسار يخص: الفشل الكلوي الحاد (N17.9)

بناءً على الملاحظات الطبية:
- الكرياتينين: 3.8 mg/dL (كان 1.2 قبل أسبوع)
- معدل الترشيح الكبيبي: 25 mL/min
- قلة البول: 400 مل خلال 24 ساعة

بناءً على حكمك الطبي، الرجاء توثيق التشخيص الرئيسي وشدة الحالة.
```

🔍 ICD-10-CM CODE ACCURACY:
- Use COMPLETE codes with all required digits
- Include 7th character extensions when required
- Specify laterality (right/left) when applicable
- Use combination codes when appropriate
- Verify code validity and specificity

CRITICAL: ALL responses MUST be in BOTH Arabic AND English."""

    user_prompt = f"""Please review the following clinical notes as a CDI Specialist.
    
IMPORTANT: This may be a LONG clinical note. Read it COMPLETELY and CAREFULLY.

{formatted_notes}

Perform a Clinical Documentation Improvement review and provide:

1. **Diagnoses That Should Be Documented**: Based on ALL clinical findings
   - Specify if "principal" (التشخيص الرئيسي) or "secondary" (التشخيص الثانوي)
   - Include ACCURATE and COMPLETE ICD-10-CM codes
   - Provide clinical evidence from notes

2. **Missing Documentation**: What specific information is missing?

3. **Documentation Gaps**: What gaps exist?

4. **Physician Queries**: Generate DETAILED queries with clinical context
   - Use the 2-part structure (Header + Body)
   - Cite specific findings from the notes
   - Request appropriate documentation level

5. **Recommendations**: Specific recommendations to improve documentation

Provide response in this EXACT JSON format:
{{{{
  "diagnoses_to_document": [
    {{
      "diagnosis_ar": "التشخيص بالعربي الكامل مع التفاصيل",
      "diagnosis_en": "Complete diagnosis in English with details",
      "icd_code": "Full ICD-10-CM code with all digits",
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
  "gaps_ar": ["فجوة توثيقية محددة 1", "ثغرة في التوثيق 2"],
  "gaps_en": ["Specific documentation gap 1", "Documentation deficiency 2"],
  "queries_ar": [
    "استفسار يخص: [التشخيص الكامل] ([ICD-10])\\n\\nبناءً على الملاحظات الطبية:\\n- [معطى سريري محدد 1]\\n- [معطى سريري محدد 2]\\n- [معطى سريري محدد 3]\\n\\nبناءً على حكمك الطبي، الرجاء توثيق التشخيص [الرئيسي/الثانوي] وشدة الحالة."
  ],
  "queries_en": [
    "Query regarding: [Full diagnosis] ([ICD-10])\\n\\nBased on clinical documentation:\\n- [Specific clinical finding 1]\\n- [Specific clinical finding 2]\\n- [Specific clinical finding 3]\\n\\nBased on your clinical judgment, please document the [principal/secondary] diagnosis and severity."
  ],
  "recommendations_ar": ["توصية محددة 1 مع خطوات عملية", "توصية 2"],
  "recommendations_en": ["Specific recommendation 1 with actionable steps", "Recommendation 2"],
  "summary_ar": "ملخص شامل ومفصل يغطي جميع النقاط الحرجة",
  "summary_en": "Comprehensive detailed summary covering all critical points"
}}}}

CRITICAL: Identify ALL diagnoses (principal, secondary, AND derived). Use COMPLETE and ACCURATE ICD-10-CM codes."""

    try:
        import requests
        import json
        
        response_text = None
        
        if provider == 'azure':
            # Use Microsoft Azure OpenAI (Fast, Reliable)
            logger.info("🔄 Using Microsoft Azure OpenAI...")
            
            try:
                from openai import AzureOpenAI
                
                azure_key = os.environ.get('AZURE_OPENAI_KEY')
                endpoint = os.environ.get('AZURE_OPENAI_ENDPOINT')
                deployment = os.environ.get('AZURE_OPENAI_DEPLOYMENT')
                api_version = os.environ.get('AZURE_OPENAI_API_VERSION', '2024-08-01-preview')
                
                if not azure_key or not endpoint or not deployment:
                    raise HTTPException(status_code=400, detail="Azure OpenAI not configured properly")
                
                client = AzureOpenAI(
                    api_key=azure_key,
                    api_version=api_version,
                    azure_endpoint=endpoint
                )
                
                messages = [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_prompt}
                ]
                
                logger.info(f"📤 Sending to Azure ({deployment})...")
                response = client.chat.completions.create(
                    model=deployment,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=4000
                )
                
                response_text = response.choices[0].message.content.strip()
                logger.info("✅ Azure OpenAI analysis successful")
                
            except Exception as e:
                logger.error(f"❌ Azure error: {str(e)}")
                raise HTTPException(status_code=500, detail=f"فشل Azure: {str(e)}")
        
        elif provider == 'gemini':
            # Use Google Gemini with API keys (12 keys with rotation)
            logger.info("🔄 Using Gemini with API keys...")
            
            try:
                model = get_gemini_model('gemini-2.0-flash-exp')
                full_prompt = f"{system_message}\n\n{user_prompt}"
                
                max_retries = len(GEMINI_API_KEYS)
                for attempt in range(max_retries):
                    try:
                        response = model.generate_content(full_prompt)
                        response_text = response.text.strip()
                        logger.info(f"✅ Gemini successful (attempt {attempt+1})")
                        break
                    except Exception as e:
                        if "429" in str(e) or "quota" in str(e).lower():
                            if attempt < max_retries - 1:
                                logger.warning(f"Key exhausted, trying next ({attempt+2}/{max_retries})")
                                model = get_gemini_model('gemini-2.0-flash-exp')
                                continue
                            else:
                                raise HTTPException(status_code=429, detail="جميع مفاتيح Gemini نفد رصيدها. All Gemini keys exhausted.")
                        else:
                            raise e
                            
            except Exception as e:
                logger.error(f"❌ Gemini error: {str(e)}")
                raise HTTPException(status_code=500, detail=f"فشل Gemini: {str(e)}")
        
        else:
            # Only Phi-3 is supported - no external API keys
            raise HTTPException(
                status_code=400,
                detail="فقط Phi-3 المحلي متاح. Only local Phi-3 analysis is available."
            )
        
        # Check if we have a response
        if not response_text:
            raise HTTPException(status_code=500, detail="No response from AI provider")
        
        # Enhanced JSON parsing with better error handling
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
            logger.info(f"✅ JSON parsing successful, found {len(result.get('diagnoses_to_document', []))} diagnoses")
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

# Get available AI providers
@api_router.get("/ai-providers")
async def get_ai_providers():
    """Get list of available AI providers - Azure & Gemini"""
    providers = [
        {
            "id": "azure",
            "name": "Microsoft Azure AI",
            "name_ar": "مايكروسوفت أزور AI",
            "description": "Microsoft Azure OpenAI - Fast, Reliable, Cloud-based",
            "description_ar": "مايكروسوفت أزور OpenAI - سريع، موثوق، سحابي",
            "status": "active",
            "is_local": False,
            "is_free": False,
            "note": "Fast (5-15 seconds)",
            "note_ar": "سريع (5-15 ثانية)"
        },
        {
            "id": "gemini",
            "name": "Google Gemini 2.0",
            "name_ar": "جوجل جيميناي 2.0",
            "description": "Google Gemini - Fast, High Accuracy",
            "description_ar": "جوجل جيميناي - سريع، دقة عالية",
            "status": "active",
            "is_local": False,
            "is_free": True,
            "note": "Fast (5-10 seconds)",
            "note_ar": "سريع (5-10 ثواني)"
        }
    ]
    
    return {"providers": providers, "default": "azure"}


# ========== Auth Routes ==========
@api_router.post("/auth/register", response_model=Token)
@limiter.limit("3/hour")
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
    
    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        phone_number=user_data.phone_number,
        password_hash=hash_password(user_data.password),
        role=role
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
    
    # Create WhatsApp welcome message link
    import urllib.parse
    welcome_message = f"""مرحباً {user.full_name}

شكراً جزيلاً على إنشاء حسابك معنا

الرجاء الضغط على تسجيل الدخول ثم بريدك الإلكتروني وكلمة المرور.

عند تسجيل الدخول على حسابك يمكنك استخدام جميع الخدمات الإلكترونية المتاحة

شكراً"""
    
    encoded_message = urllib.parse.quote(welcome_message)
    whatsapp_link = f"https://wa.me/{user.phone_number}?text={encoded_message}"
    
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
            "role": user.role
        },
        "whatsapp_welcome_link": whatsapp_link
    }

@api_router.post("/auth/login-step1")
# @limiter.limit("5/minute")  # Temporarily disabled
async def login_step1(credentials: UserLogin):
    """Step 1: Verify credentials and send OTP"""
    try:
        # Import security utils
        from security_utils import (
            check_rate_limit, record_login_attempt, 
            unlock_account_if_expired, log_audit, 
            generate_otp, send_otp_email
        )
        
        # Check if account lockout expired
        await unlock_account_if_expired(db, credentials.email)
        
        # Check rate limiting - TEMPORARILY DISABLED FOR ADMIN EMAIL
        if credentials.email != "medidocai@gmail.com":
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
        
        # Check if password is correct
        if not verify_password(credentials.password, user[password_field]):
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
                    "role": user.get('role', 'user')
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed")

@api_router.post("/auth/login-step2", response_model=Token)
# @limiter.limit("10/minute")  # Temporarily disabled
async def login_step2(credentials: OTPVerification):
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
                "role": user.get('role', 'user')
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"OTP verification error: {str(e)}")
        raise HTTPException(status_code=500, detail="Verification failed")

# Keep old endpoint for backward compatibility (deprecated)
@api_router.post("/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    """Legacy login endpoint - redirects to new MFA flow"""
    result = await login_step1(credentials)
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
    """Request password reset - sends code via WhatsApp"""
    user = await db.users.find_one({"email": request.email}, {"_id": 0})
    
    # Always return success (don't reveal if email exists)
    if not user:
        return {"message": "If the account exists, a reset code will be sent"}
    
    # Generate reset code (6 digits)
    import random
    reset_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
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
    doc['reset_code'] = reset_code
    await db.password_reset_tokens.insert_one(doc)
    
    # Send password reset email (if configured)
    try:
        await send_password_reset_email(user['email'], user['full_name'], reset_token)
    except Exception as e:
        logging.error(f"Failed to send password reset email: {str(e)}")
    
    # Create WhatsApp message with reset code
    import urllib.parse
    phone_number = user.get('phone_number', '')
    if phone_number:
        whatsapp_message = f"""مرحباً {user['full_name']}

كود استعادة كلمة المرور الخاص بك هو:

{reset_code}

هذا الكود صالح لمدة ساعة واحدة فقط.

للدعم الفني: 966502468148"""
        
        encoded_message = urllib.parse.quote(whatsapp_message)
        whatsapp_link = f"https://wa.me/{phone_number}?text={encoded_message}"
        
        return {
            "message": "Reset code sent",
            "whatsapp_link": whatsapp_link,
            "has_phone": True
        }
    
    return {"message": "If the account exists, a reset code will be sent", "has_phone": False}

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

@api_router.post("/auth/reset-password-with-code")
async def reset_password_with_code(request: PasswordResetWithCode):
    """Reset password using code from WhatsApp"""
    # Find user by email
    user = await db.users.find_one({"email": request.email}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=400, detail="Reset failed")
    
    # Find valid token with matching code
    token_doc = await db.password_reset_tokens.find_one({
        "user_id": user['id'],
        "reset_code": request.code,
        "used": False
    }, {"_id": 0})
    
    if not token_doc:
        raise HTTPException(status_code=400, detail="Invalid code")
    
    # Check if token expired
    expires_at = datetime.fromisoformat(token_doc['expires_at'])
    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(status_code=400, detail="Code has expired")
    
    # Update user password
    new_password_hash = hash_password(request.new_password)
    await db.users.update_one(
        {"id": user['id']},
        {"$set": {"password": new_password_hash}}
    )
    
    # Mark token as used
    await db.password_reset_tokens.update_one(
        {"user_id": user['id'], "reset_code": request.code},
        {"$set": {"used": True}}
    )
    
    return {"message": "Password reset successful"}

@api_router.get("/support/whatsapp")
async def get_support_whatsapp():
    """Get support WhatsApp number"""
    support_number = os.environ.get('SUPPORT_WHATSAPP', '966502468148')
    return {
        "whatsapp_number": support_number,
        "whatsapp_link": f"https://wa.me/{support_number}"
    }

# ========== Admin Routes ==========
async def require_admin(user: dict = Depends(get_current_user)):
    if user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

@api_router.get("/admin/users-statistics")
async def get_users_statistics(admin: dict = Depends(require_admin)):
    """Get detailed statistics for all users"""
    from datetime import datetime, timezone, timedelta
    
    # Get all users except admins
    users = await db.users.find(
        {"role": {"$ne": "admin"}},
        {"_id": 0, "password_hash": 0}
    ).to_list(1000)
    
    today = datetime.now(timezone.utc).date()
    yesterday = today - timedelta(days=1)
    
    user_stats = []
    for user in users:
        user_id = user['id']
        
        # Count total notes
        total_notes = await db.clinical_notes.count_documents({"user_id": user_id})
        
        # Count total analyses
        total_analyses = await db.analyses.count_documents({"user_id": user_id})
        
        # Count today's notes
        today_notes = await db.clinical_notes.count_documents({
            "user_id": user_id,
            "created_at": {
                "$gte": datetime.combine(today, datetime.min.time()).isoformat(),
                "$lt": datetime.combine(today + timedelta(days=1), datetime.min.time()).isoformat()
            }
        })
        
        # Count today's analyses
        today_analyses = await db.analyses.count_documents({
            "user_id": user_id,
            "created_at": {
                "$gte": datetime.combine(today, datetime.min.time()).isoformat(),
                "$lt": datetime.combine(today + timedelta(days=1), datetime.min.time()).isoformat()
            }
        })
        
        # Get last activity
        last_note = await db.clinical_notes.find_one(
            {"user_id": user_id},
            {"_id": 0, "created_at": 1},
            sort=[("created_at", -1)]
        )
        
        last_activity = last_note['created_at'] if last_note else user.get('created_at')
        
        user_stats.append({
            "user_id": user_id,
            "full_name": user['full_name'],
            "email": user['email'],
            "phone_number": user.get('phone_number', ''),
            "role": user.get('role', 'user'),
            "is_active": user.get('is_active', True),
            "registration_date": user.get('created_at'),
            "last_activity": last_activity,
            "total_notes": total_notes,
            "total_analyses": total_analyses,
            "today_notes": today_notes,
            "today_analyses": today_analyses,
            "is_active_today": today_notes > 0 or today_analyses > 0
        })
    
    # Sort by today's activity (most active first)
    user_stats.sort(key=lambda x: (x['today_notes'] + x['today_analyses']), reverse=True)
    
    return {
        "date": today.isoformat(),
        "total_users": len(user_stats),
        "active_today": sum(1 for u in user_stats if u['is_active_today']),
        "statistics": user_stats
    }

@api_router.get("/admin/stats")
async def get_admin_stats(admin: dict = Depends(require_admin)):
    # Count users
    total_users = await db.users.count_documents({})
    admin_users = await db.users.count_documents({"role": "admin"})
    
    # Count notes
    total_notes = await db.clinical_notes.count_documents({})
    
    # Count analyses
    total_analyses = await db.analyses.count_documents({})
    
    # Recent activity
    recent_users = await db.users.find(
        {}, {"_id": 0, "password_hash": 0}
    ).sort("created_at", -1).limit(10).to_list(10)
    
    recent_analyses = await db.analyses.find(
        {}, {"_id": 0}
    ).sort("created_at", -1).limit(10).to_list(10)
    
    return {
        "total_users": total_users,
        "admin_users": admin_users,
        "regular_users": total_users - admin_users,
        "total_notes": total_notes,
        "total_analyses": total_analyses,
        "recent_users": recent_users,
        "recent_analyses": recent_analyses
    }

@api_router.get("/admin/users")
async def get_all_users(admin: dict = Depends(require_admin)):
    users = await db.users.find(
        {}, {"_id": 0, "password_hash": 0}
    ).sort("created_at", -1).to_list(1000)
    
    for user in users:
        if isinstance(user.get('created_at'), str):
            user['created_at'] = datetime.fromisoformat(user['created_at'])
    
    return users

@api_router.put("/admin/users/{user_id}/toggle-active")
async def toggle_user_active(user_id: str, admin: dict = Depends(require_admin)):
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_status = not user.get('is_active', True)
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_active": new_status}}
    )
    
    return {"message": "User status updated", "is_active": new_status}

@api_router.get("/admin/export-statistics")
async def export_users_statistics(admin: dict = Depends(require_admin)):
    """Export user statistics to Excel file"""
    from datetime import datetime, timezone, timedelta
    
    # Get statistics
    stats_data = await get_users_statistics(admin)
    
    # Create Excel workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "إحصائيات المستخدمين"
    
    # Define headers (Arabic and English)
    headers = [
        "الاسم الكامل\nFull Name",
        "البريد الإلكتروني\nEmail",
        "رقم الجوال\nPhone",
        "تاريخ التسجيل\nRegistration Date",
        "آخر نشاط\nLast Activity",
        "إجمالي الملاحظات\nTotal Notes",
        "إجمالي التحليلات\nTotal Analyses",
        "ملاحظات اليوم\nToday's Notes",
        "تحليلات اليوم\nToday's Analyses",
        "نشط اليوم\nActive Today"
    ]
    
    # Style headers
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=12)
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment
    
    # Set column widths
    ws.column_dimensions['A'].width = 25
    ws.column_dimensions['B'].width = 30
    ws.column_dimensions['C'].width = 20
    ws.column_dimensions['D'].width = 20
    ws.column_dimensions['E'].width = 20
    ws.column_dimensions['F'].width = 18
    ws.column_dimensions['G'].width = 18
    ws.column_dimensions['H'].width = 18
    ws.column_dimensions['I'].width = 18
    ws.column_dimensions['J'].width = 15
    
    # Add data
    for row_num, user_stat in enumerate(stats_data['statistics'], 2):
        ws.cell(row=row_num, column=1, value=user_stat['full_name'])
        ws.cell(row=row_num, column=2, value=user_stat['email'])
        ws.cell(row=row_num, column=3, value=user_stat['phone_number'])
        
        # Format dates
        reg_date = user_stat.get('registration_date')
        if isinstance(reg_date, str):
            try:
                reg_date = datetime.fromisoformat(reg_date).strftime('%Y-%m-%d %H:%M')
            except:
                pass
        ws.cell(row=row_num, column=4, value=reg_date)
        
        last_activity = user_stat.get('last_activity')
        if isinstance(last_activity, str):
            try:
                last_activity = datetime.fromisoformat(last_activity).strftime('%Y-%m-%d %H:%M')
            except:
                pass
        ws.cell(row=row_num, column=5, value=last_activity)
        
        ws.cell(row=row_num, column=6, value=user_stat['total_notes'])
        ws.cell(row=row_num, column=7, value=user_stat['total_analyses'])
        ws.cell(row=row_num, column=8, value=user_stat['today_notes'])
        ws.cell(row=row_num, column=9, value=user_stat['today_analyses'])
        ws.cell(row=row_num, column=10, value='نعم / Yes' if user_stat['is_active_today'] else 'لا / No')
        
        # Apply alignment
        for col in range(1, 11):
            ws.cell(row=row_num, column=col).alignment = Alignment(horizontal="center", vertical="center")
    
    # Add summary at the bottom
    summary_row = len(stats_data['statistics']) + 3
    ws.cell(row=summary_row, column=1, value="الملخص / Summary").font = Font(bold=True, size=14)
    ws.cell(row=summary_row + 1, column=1, value=f"إجمالي المستخدمين / Total Users: {stats_data['total_users']}")
    ws.cell(row=summary_row + 2, column=1, value=f"نشط اليوم / Active Today: {stats_data['active_today']}")
    ws.cell(row=summary_row + 3, column=1, value=f"التاريخ / Date: {stats_data['date']}")
    
    # Save to BytesIO
    excel_file = io.BytesIO()
    wb.save(excel_file)
    excel_file.seek(0)
    
    # Return as downloadable file
    from fastapi.responses import StreamingResponse
    filename = f"user_statistics_{stats_data['date']}.xlsx"
    
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@api_router.delete("/admin/users/{user_id}")
async def delete_user(user_id: str, admin: dict = Depends(require_admin)):
    # Don't allow deleting yourself
    if user_id == admin['id']:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Also delete user's notes and analyses
    await db.clinical_notes.delete_many({"user_id": user_id})
    await db.analyses.delete_many({"user_id": user_id})
    await db.chat_messages.delete_many({"user_id": user_id})
    
    return {"message": "User and all data deleted successfully"}

@api_router.put("/admin/users/{user_id}")
async def update_user(user_id: str, update_data: dict, admin: dict = Depends(require_admin)):
    """Update user information"""
    allowed_fields = ['full_name', 'email', 'phone_number']
    update_dict = {k: v for k, v in update_data.items() if k in allowed_fields}
    
    if not update_dict:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": update_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User updated successfully"}

@api_router.post("/admin/suspend-user/{user_id}")
async def suspend_user(user_id: str, admin: dict = Depends(require_admin)):
    """Suspend a user account"""
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_active": False}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User suspended successfully"}

@api_router.post("/admin/activate-user/{user_id}")
async def activate_user(user_id: str, admin: dict = Depends(require_admin)):
    """Activate a user account"""
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_active": True}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User activated successfully"}

# ========== Supervisor Management Routes ==========
@api_router.post("/admin/assign-supervisor/{user_id}")
async def assign_supervisor(user_id: str, admin: dict = Depends(require_admin)):
    """Promote a user to supervisor role"""
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user is admin (use .get() to handle users without role field)
    if user.get('role') == 'admin':
        raise HTTPException(status_code=400, detail="Cannot change admin role")
    
    # Update user role to supervisor
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"role": "supervisor"}}
    )
    
    return {"message": "User promoted to supervisor successfully"}

@api_router.post("/admin/remove-supervisor/{user_id}")
async def remove_supervisor(user_id: str, admin: dict = Depends(require_admin)):
    """Demote a supervisor back to regular user"""
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user['role'] != 'supervisor':
        raise HTTPException(status_code=400, detail="User is not a supervisor")
    
    # Update user role back to user
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"role": "user"}}
    )
    
    return {"message": "Supervisor demoted to user successfully"}

@api_router.get("/admin/supervisors")
async def get_supervisors(admin: dict = Depends(require_admin)):
    """Get all supervisors"""
    supervisors = await db.users.find(
        {"role": "supervisor"},
        {"_id": 0, "password_hash": 0}
    ).to_list(1000)
    
    # Get employee count for each supervisor
    for supervisor in supervisors:
        employee_count = await db.users.count_documents({"supervisor_id": supervisor['id']})
        supervisor['employee_count'] = employee_count
    
    return supervisors

# ========== Supervisor Routes ==========
async def require_supervisor(user: dict = Depends(get_current_user)):
    if user.get('role') not in ['admin', 'supervisor']:
        raise HTTPException(status_code=403, detail="Supervisor access required")
    return user

@api_router.get("/supervisor/employees")
async def get_supervisor_employees(supervisor: dict = Depends(require_supervisor)):
    """Get all employees - both admin and supervisor see all regular employees"""
    # Both admin and supervisor see all non-admin, non-supervisor users
    employees = await db.users.find(
        {"role": {"$nin": ["admin", "supervisor"]}},
        {"_id": 0, "password_hash": 0}
    ).to_list(1000)
    
    # Add notes and analyses counts
    for employee in employees:
        notes_count = await db.clinical_notes.count_documents({"user_id": employee['id']})
        analyses_count = await db.analyses.count_documents({"user_id": employee['id']})
        employee['notes_count'] = notes_count
        employee['analyses_count'] = analyses_count
    
    return employees

@api_router.post("/admin/change-user-password/{user_id}")
async def admin_change_user_password(
    user_id: str,
    new_password: str,
    admin: dict = Depends(require_admin)
):
    """Admin can change any user's password"""
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Hash new password
    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
    
    # Update password
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"password_hash": hashed_password.decode('utf-8')}}
    )
    
    return {"message": "Password changed successfully"}

@api_router.post("/admin/impersonate/{user_id}")
async def impersonate_user(
    user_id: str,
    current_user: dict = Depends(require_supervisor)  # Allow both admin and supervisor
):
    """Admin/Supervisor can impersonate any user to view their account"""
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Generate a new token for the impersonated user
    access_token = create_access_token(data={
        "user_id": user['id'], 
        "email": user['email'],
        "role": user.get('role', 'user')
    })
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user['id'],
            "email": user['email'],
            "full_name": user['full_name'],
            "role": user.get('role', 'user'),
            "phone_number": user.get('phone_number', ''),
            "is_impersonating": True,
            "impersonated_by": current_user['id']
        }
    }

@api_router.get("/supervisor/employee-notes/{employee_id}")
async def get_employee_notes(employee_id: str, supervisor: dict = Depends(require_supervisor)):
    """Get all notes for a specific employee"""
    # Verify employee belongs to this supervisor (unless admin)
    if supervisor['role'] != 'admin':
        employee = await db.users.find_one({"id": employee_id}, {"_id": 0})
        if not employee or employee.get('supervisor_id') != supervisor['id']:
            raise HTTPException(status_code=403, detail="Not authorized to view this employee's notes")
    
    notes = await db.clinical_notes.find(
        {"user_id": employee_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(1000)
    
    for note in notes:
        if isinstance(note['created_at'], str):
            note['created_at'] = datetime.fromisoformat(note['created_at'])
        if 'doctor_notes' not in note:
            note['doctor_notes'] = []
    
    return notes

@api_router.get("/supervisor/employee-analyses/{employee_id}")
async def get_employee_analyses(employee_id: str, supervisor: dict = Depends(require_supervisor)):
    """Get all analyses for a specific employee"""
    # Verify employee belongs to this supervisor (unless admin)
    if supervisor['role'] != 'admin':
        employee = await db.users.find_one({"id": employee_id}, {"_id": 0})
        if not employee or employee.get('supervisor_id') != supervisor['id']:
            raise HTTPException(status_code=403, detail="Not authorized to view this employee's analyses")
    
    analyses = await db.analyses.find(
        {"user_id": employee_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(1000)
    
    for analysis in analyses:
        if isinstance(analysis['created_at'], str):
            analysis['created_at'] = datetime.fromisoformat(analysis['created_at'])
    
    return analyses

# ========== Notes Routes ==========
@api_router.post("/notes", response_model=ClinicalNote)
async def create_note(note_data: ClinicalNoteCreate, user: dict = Depends(get_current_user)):
    note = ClinicalNote(
        user_id=user['id'],
        title=note_data.title,
        doctor_notes=[dn.model_dump() for dn in note_data.doctor_notes]
    )
    
    doc = note.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.clinical_notes.insert_one(doc)
    
    return note

@api_router.get("/notes", response_model=List[ClinicalNote])
async def get_notes(user: dict = Depends(get_current_user)):
    notes = await db.clinical_notes.find(
        {"user_id": user['id']},
        {"_id": 0}
    ).sort("created_at", -1).to_list(1000)
    
    for note in notes:
        if isinstance(note['created_at'], str):
            note['created_at'] = datetime.fromisoformat(note['created_at'])
        # تأكد من وجود doctor_notes
        if 'doctor_notes' not in note:
            note['doctor_notes'] = []
    
    return notes

@api_router.get("/notes/{note_id}", response_model=ClinicalNote)
async def get_note(note_id: str, user: dict = Depends(get_current_user)):
    note = await db.clinical_notes.find_one(
        {"id": note_id, "user_id": user['id']},
        {"_id": 0}
    )
    
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    if isinstance(note['created_at'], str):
        note['created_at'] = datetime.fromisoformat(note['created_at'])
    
    return note

@api_router.put("/notes/{note_id}", response_model=ClinicalNote)
async def update_note(note_id: str, request: ClinicalNoteCreate, user: dict = Depends(get_current_user)):
    # Check if note exists and belongs to user
    existing_note = await db.clinical_notes.find_one(
        {"id": note_id, "user_id": user['id']},
        {"_id": 0}
    )
    
    if not existing_note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Update note data
    updated_data = {
        "title": request.title,
        "doctor_notes": [{"text": n.text, "specialty": n.specialty} for n in request.doctor_notes],
        "notes_text": " ".join([n.text for n in request.doctor_notes]),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.clinical_notes.update_one(
        {"id": note_id, "user_id": user['id']},
        {"$set": updated_data}
    )
    
    # Get updated note
    note = await db.clinical_notes.find_one(
        {"id": note_id, "user_id": user['id']},
        {"_id": 0}
    )
    
    if isinstance(note['created_at'], str):
        note['created_at'] = datetime.fromisoformat(note['created_at'])
    
    
    if note.get('updated_at') and isinstance(note['updated_at'], str):
        note['updated_at'] = datetime.fromisoformat(note['updated_at'])
    return note

@api_router.delete("/notes/{note_id}")
async def delete_note(note_id: str, user: dict = Depends(get_current_user)):
    # Check if note exists and belongs to user
    note = await db.clinical_notes.find_one(
        {"id": note_id, "user_id": user['id']},
        {"_id": 0}
    )
    
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Delete the note
    await db.clinical_notes.delete_one({"id": note_id, "user_id": user['id']})
    
    # Also delete all related analyses
    await db.analyses.delete_many({"note_id": note_id, "user_id": user['id']})
    
    return {"message": "Note and related analyses deleted successfully"}

# ========== Analysis Routes ==========
@api_router.post("/analyze", response_model=Analysis)
# @limiter.limit("20/hour")  # Temporarily disabled
async def analyze_note(analyze_request: AnalyzeRequest, user: dict = Depends(get_current_user)):
    # Track AI request
    start_time = time.time()
    
    note = await db.clinical_notes.find_one(
        {"id": analyze_request.note_id, "user_id": user['id']},
        {"_id": 0}
    )
    
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Track DB operation
    DB_OPERATIONS.labels(operation='read', collection='clinical_notes').inc()
    
    # Get AI provider from request (default: phi3)
    ai_provider = getattr(analyze_request, 'ai_provider', 'phi3') or 'phi3'
    logger.info(f"🤖 Analyzing with provider: {ai_provider}")
    
    # Analyze with AI (Phi-3 or DeepSeek)
    result = await analyze_with_ai(note['title'], note['doctor_notes'], provider=ai_provider)
    
    # Track AI metrics
    AI_REQUESTS.labels(type='analyze').inc()
    AI_RESPONSE_TIME.labels(type='analyze').observe(time.time() - start_time)
    
    # Create analysis record
    analysis = Analysis(
        note_id=analyze_request.note_id,
        user_id=user['id'],
        diagnoses_to_document=[DiagnosisBilingual(**d) for d in result.get('diagnoses_to_document', [])],
        missing_documentation=result.get('missing_documentation', []),
        gaps_ar=result.get('gaps_ar', []),
        gaps_en=result.get('gaps_en', []),
        queries_ar=result.get('queries_ar', []),
        queries_en=result.get('queries_en', []),
        recommendations_ar=result.get('recommendations_ar', []),
        recommendations_en=result.get('recommendations_en', []),
        summary_ar=result.get('summary_ar', ''),
        summary_en=result.get('summary_en', '')
    )
    
    doc = analysis.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    # Convert DiagnosisBilingual to dict
    doc['diagnoses_to_document'] = [d.model_dump() if hasattr(d, 'model_dump') else d for d in doc['diagnoses_to_document']]
    await db.analyses.insert_one(doc)
    
    return analysis

@api_router.post("/analysis/reanalyze/{note_id}", response_model=Analysis)
async def reanalyze_note(note_id: str, user: dict = Depends(get_current_user)):
    """Reanalyze an existing note (useful after edits)"""
    note = await db.clinical_notes.find_one(
        {"id": note_id, "user_id": user['id']},
        {"_id": 0}
    )
    
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Analyze with AI (default: phi3)
    result = await analyze_with_ai(note['title'], note.get('doctor_notes', []), provider='phi3')
    
    # Create new analysis record
    analysis = Analysis(
        note_id=note_id,
        user_id=user['id'],
        diagnoses_to_document=[DiagnosisBilingual(**d) for d in result.get('diagnoses_to_document', [])],
        missing_documentation=result.get('missing_documentation', []),
        gaps_ar=result.get('gaps_ar', []),
        gaps_en=result.get('gaps_en', []),
        queries_ar=result.get('queries_ar', []),
        queries_en=result.get('queries_en', []),
        recommendations_ar=result.get('recommendations_ar', []),
        recommendations_en=result.get('recommendations_en', []),
        summary_ar=result.get('summary_ar', ''),
        summary_en=result.get('summary_en', '')
    )
    
    doc = analysis.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['diagnoses_to_document'] = [d.model_dump() if hasattr(d, 'model_dump') else d for d in doc['diagnoses_to_document']]
    await db.analyses.insert_one(doc)
    
    # Log audit
    from security_utils import log_audit
    await log_audit(
        db,
        action="reanalyze_note",
        user_id=user['id'],
        user_email=user.get('email'),
        resource_type="note",
        resource_id=note_id,
        status="success"
    )
    
    return analysis

@api_router.get("/analyses/{note_id}", response_model=List[Analysis])
async def get_analyses(note_id: str, user: dict = Depends(get_current_user)):
    analyses = await db.analyses.find(
        {"note_id": note_id, "user_id": user['id']},
        {"_id": 0}
    ).sort("created_at", -1).to_list(1000)
    
    for analysis in analyses:
        if isinstance(analysis['created_at'], str):
            analysis['created_at'] = datetime.fromisoformat(analysis['created_at'])
    
    return analyses

@api_router.get("/analysis/{analysis_id}", response_model=Analysis)
async def get_analysis_by_id(analysis_id: str, user: dict = Depends(get_current_user)):
    """Get specific analysis by analysis ID"""
    analysis = await db.analyses.find_one(
        {"id": analysis_id, "user_id": user['id']},
        {"_id": 0}
    )
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    if isinstance(analysis['created_at'], str):
        analysis['created_at'] = datetime.fromisoformat(analysis['created_at'])
    
    return analysis

@api_router.get("/history", response_model=List[Dict])
async def get_history(user: dict = Depends(get_current_user)):
    analyses = await db.analyses.find(
        {"user_id": user['id']},
        {"_id": 0}
    ).sort("created_at", -1).to_list(1000)
    
    result = []
    for analysis in analyses:
        note = await db.clinical_notes.find_one(
            {"id": analysis['note_id']},
            {"_id": 0, "title": 1}
        )
        
        if isinstance(analysis['created_at'], str):
            analysis['created_at'] = datetime.fromisoformat(analysis['created_at'])
        
        result.append({
            **analysis,
            "note_title": note.get('title', '') if note else ''
        })
    
    return result

# ========== Chat Routes ==========
@api_router.post("/chat")
# @limiter.limit("30/minute")  # Temporarily disabled
async def chat_with_ai(chat_request: ChatRequest, user: dict = Depends(get_current_user)):
    # Get analysis
    analysis = await db.analyses.find_one(
        {"id": chat_request.analysis_id, "user_id": user['id']},
        {"_id": 0}
    )
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    # Get note
    note = await db.clinical_notes.find_one(
        {"id": analysis['note_id']},
        {"_id": 0}
    )
    
    # Save user message
    user_msg = ChatMessage(
        analysis_id=chat_request.analysis_id,
        user_id=user['id'],
        role='user',
        message=chat_request.message
    )
    user_doc = user_msg.model_dump()
    user_doc['created_at'] = user_doc['created_at'].isoformat()
    await db.chat_messages.insert_one(user_doc)
    
    # Build context
    import json
    context = f"""Clinical Note: {note['title']}

Analysis Summary (Arabic): {analysis.get('summary_ar', '')}
Analysis Summary (English): {analysis.get('summary_en', '')}

Diagnoses to Document: {json.dumps(analysis.get('diagnoses_to_document', []), ensure_ascii=False)}
Missing Documentation: {json.dumps(analysis.get('missing_documentation', []), ensure_ascii=False)}"""
    
    system_message = f"""You are a Clinical Documentation Improvement (CDI) specialist. You have reviewed a clinical case and now the user wants to discuss the analysis with you.

Context:
{context}

Answer questions professionally, provide clarifications, and help improve the documentation. Respond in the same language as the user's question. 

IMPORTANT: Be VERY concise and direct. Give precise answers without unnecessary details. Focus only on the specific question asked. Maximum 3-4 sentences unless more detail is specifically requested."""
    
    # Use analysis_id as session for continuity
    try:
        # Get AI provider from request (default: azure)
        ai_provider = getattr(chat_request, 'ai_provider', 'azure') or 'azure'
        
        # Get chat history for context
        previous_messages = await db.chat_messages.find(
            {"analysis_id": chat_request.analysis_id}
        ).sort("created_at", 1).to_list(100)
        
        response_text = None
        
        if ai_provider == 'azure':
            # Use Azure for chat
            try:
                from openai import AzureOpenAI
                
                azure_key = os.environ.get('AZURE_OPENAI_KEY')
                endpoint = os.environ.get('AZURE_OPENAI_ENDPOINT')
                deployment = os.environ.get('AZURE_OPENAI_DEPLOYMENT')
                api_version = os.environ.get('AZURE_OPENAI_API_VERSION', '2024-08-01-preview')
                
                client = AzureOpenAI(
                    api_key=azure_key,
                    api_version=api_version,
                    azure_endpoint=endpoint
                )
                
                messages = [{"role": "system", "content": system_message}]
                for msg in previous_messages:
                    if 'role' in msg and msg['role'] in ['user', 'assistant']:
                        messages.append({"role": msg['role'], "content": msg['message']})
                messages.append({"role": "user", "content": chat_request.message})
                
                response = client.chat.completions.create(
                    model=deployment,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=500
                )
                response_text = response.choices[0].message.content.strip()
                logger.info("✅ Azure chat successful")
                
            except Exception as e:
                logger.error(f"❌ Azure chat error: {str(e)}")
                raise HTTPException(status_code=500, detail=f"فشلت الدردشة: {str(e)}")
        
        elif ai_provider == 'gemini':
            # Use Gemini for chat
            try:
                model = get_gemini_model('gemini-2.0-flash-exp', system_instruction=system_message)
                
                chat_history = []
                for msg in previous_messages:
                    if 'role' in msg:
                        chat_history.append({
                            'role': 'user' if msg['role'] == 'user' else 'model',
                            'parts': [msg['message']]
                        })
                
                chat = model.start_chat(history=chat_history)
                response = chat.send_message(chat_request.message)
                response_text = response.text
                logger.info("✅ Gemini chat successful")
                
            except Exception as e:
                logger.error(f"❌ Gemini chat error: {str(e)}")
                raise HTTPException(status_code=500, detail=f"فشلت الدردشة: {str(e)}")
        
        if not response_text:
            raise HTTPException(status_code=500, detail="No response from AI provider")
        
        # Save assistant message
        assistant_msg = ChatMessage(
            analysis_id=chat_request.analysis_id,
            user_id=user['id'],
            role='assistant',
            message=response_text
        )
        assistant_doc = assistant_msg.model_dump()
        assistant_doc['created_at'] = assistant_doc['created_at'].isoformat()
        await db.chat_messages.insert_one(assistant_doc)
        
        return {"message": response_text}
        
    except Exception as e:
        logging.error(f"Error in chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in chat: {str(e)}")

@api_router.get("/chat/{analysis_id}")
async def get_chat_history(analysis_id: str, user: dict = Depends(get_current_user)):
    messages = await db.chat_messages.find(
        {"analysis_id": analysis_id, "user_id": user['id']},
        {"_id": 0}
    ).sort("created_at", 1).to_list(1000)
    
    for msg in messages:
        if isinstance(msg['created_at'], str):
            msg['created_at'] = datetime.fromisoformat(msg['created_at'])
    
    return messages

@api_router.post("/chat/{analysis_id}")
@limiter.limit("30/minute")
async def chat_with_ai_by_path(request: Request, analysis_id: str, question: dict, user: dict = Depends(get_current_user)):
    """Alternative chat endpoint for ChatEnhanced.jsx - expects {question: str} in body"""
    try:
        # Get analysis
        analysis = await db.analyses.find_one(
            {"id": analysis_id, "user_id": user['id']},
            {"_id": 0}
        )
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Get note
        note = await db.clinical_notes.find_one(
            {"id": analysis['note_id']},
            {"_id": 0}
        )
        
        user_question = question.get('question', '')
        if not user_question:
            raise HTTPException(status_code=400, detail="Question is required")
        
        # Save user message
        user_msg = ChatMessage(
            analysis_id=analysis_id,
            user_id=user['id'],
            role='user',
            message=user_question
        )
        user_doc = user_msg.model_dump()
        user_doc['created_at'] = user_doc['created_at'].isoformat()
        await db.chat_messages.insert_one(user_doc)
        
        # Build context
        import json
        
        # Format doctor notes
        doctor_notes_text = "\n\n".join([
            f"**{dn.get('specialty', 'عام')}**:\n{dn.get('text', '')}"
            for dn in note.get('doctor_notes', [])
        ])
        
        context = f"""Clinical Note: {note['title']}

Clinical Notes:
{doctor_notes_text}

Analysis Summary (Arabic): {analysis.get('summary_ar', '')}
Analysis Summary (English): {analysis.get('summary_en', '')}

Diagnoses to Document: {json.dumps(analysis.get('diagnoses_to_document', []), ensure_ascii=False)}
Missing Documentation: {json.dumps(analysis.get('missing_documentation', []), ensure_ascii=False)}"""
        
        system_message = f"""You are a Clinical Documentation Improvement (CDI) specialist. You have reviewed a clinical case and now the user wants to discuss the analysis with you.

Context:
{context}

Answer questions professionally, provide clarifications, and help improve the documentation. Respond in the same language as the user's question. 

IMPORTANT: Be VERY concise and direct. Give precise answers without unnecessary details. Focus only on the specific question asked. Maximum 3-4 sentences unless more detail is specifically requested."""
        
        # Use analysis_id as session for continuity
        try:
            # Use Google Gemini API with automatic key rotation
            model = get_gemini_model('gemini-flash-latest', system_instruction=system_message)
            
            # Get chat history for context
            chat_history = []
            previous_messages = await db.chat_messages.find(
                {"analysis_id": analysis_id}
            ).sort("created_at", 1).to_list(100)
            
            # Build chat history
            for msg in previous_messages:
                # Handle both open chat messages (with 'role') and predefined questions (with 'question'/'answer')
                if 'role' in msg:
                    if msg['role'] == 'user':
                        chat_history.append({'role': 'user', 'parts': [msg['message']]})
                    else:
                        chat_history.append({'role': 'model', 'parts': [msg['message']]})
                elif 'question' in msg and 'answer' in msg:
                    # Predefined question format
                    chat_history.append({'role': 'user', 'parts': [msg['question']]})
                    chat_history.append({'role': 'model', 'parts': [msg['answer']]})
            
            # Start chat with history and retry logic
            max_retries = len(GEMINI_API_KEYS)
            response_text = None
            
            for attempt in range(max_retries):
                try:
                    chat = model.start_chat(history=chat_history)
                    response = chat.send_message(user_question)
                    response_text = response.text
                    break  # Success, exit retry loop
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Chat retry {attempt + 1}/{max_retries} with different API key")
                        model = get_gemini_model('gemini-flash-latest', system_instruction=system_message)
                    else:
                        raise e
            
            # Save assistant message
            assistant_msg = ChatMessage(
                analysis_id=analysis_id,
                user_id=user['id'],
                role='assistant',
                message=response_text
            )
            assistant_doc = assistant_msg.model_dump()
            assistant_doc['created_at'] = assistant_doc['created_at'].isoformat()
            await db.chat_messages.insert_one(assistant_doc)
            
            # Return format expected by ChatEnhanced.jsx
            return {
                "question": user_question,
                "answer": response_text
            }
            
        except Exception as e:
            logging.error(f"Error in chat: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error in chat: {str(e)}")
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error processing chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ========== Export Routes ==========
@api_router.get("/export/pdf/{analysis_id}")
async def export_pdf(analysis_id: str, user: dict = Depends(get_current_user)):
    analysis = await db.analyses.find_one(
        {"id": analysis_id, "user_id": user['id']},
        {"_id": 0}
    )
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    note = await db.clinical_notes.find_one(
        {"id": analysis['note_id']},
        {"_id": 0}
    )
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1e40af'),
        alignment=TA_CENTER,
        spaceAfter=30
    )
    
    elements.append(Paragraph("Clinical Analysis Report / تقرير التحليل السريري", title_style))
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph(f"<b>Note Title:</b> {note.get('title', '')}", styles['Normal']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Diagnoses to Document
    elements.append(Paragraph("<b>Diagnoses to Document / التشخيصات المطلوب توثيقها:</b>", styles['Heading2']))
    for diag in analysis.get('diagnoses_to_document', []):
        elements.append(Paragraph(f"• {diag.get('diagnosis_en', '')} / {diag.get('diagnosis_ar', '')} - {diag.get('icd_code', '')}", styles['Normal']))
    elements.append(Spacer(1, 0.2*inch))
    
    doc.build(elements)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=analysis_{analysis_id}.pdf"}
    )

@api_router.get("/download/security-documentation")
async def download_security_documentation():
    """Download comprehensive security documentation"""
    import os
    
    file_path = "/app/COMPREHENSIVE_SECURITY_IT_DOCUMENTATION_AR.md"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Documentation file not found")
    
    return FileResponse(
        path=file_path,
        filename="COMPREHENSIVE_SECURITY_IT_DOCUMENTATION_AR.md",
        media_type="text/markdown"
    )

@api_router.post("/admin/backup/create")
async def create_backup(backup_key: str = Header(None, alias="X-Backup-Key")):
    """
    Create database backup (for cron jobs)
    Requires X-Backup-Key header for security
    """
    import subprocess
    import json
    
    # Verify backup key
    BACKUP_KEY = os.environ.get('BACKUP_KEY', 'change-this-backup-key-in-production')
    if backup_key != BACKUP_KEY:
        raise HTTPException(status_code=403, detail="Invalid backup key")
    
    try:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_dir = "/app/backups"
        os.makedirs(backup_dir, exist_ok=True)
        
        backup_file = f"{backup_dir}/backup_{timestamp}.json"
        
        # Export all collections
        collections_to_backup = [
            "users",
            "clinical_notes", 
            "analyses",
            "chat_messages",
            "audit_logs",
            "login_attempts",
            "otp_records",
            "user_sessions",
            "password_history",
            "messages"
        ]
        
        backup_data = {}
        for collection_name in collections_to_backup:
            collection = db[collection_name]
            documents = await collection.find({}, {"_id": 0}).to_list(None)
            
            # Convert datetime objects to ISO strings
            for doc in documents:
                for key, value in doc.items():
                    if isinstance(value, datetime):
                        doc[key] = value.isoformat()
            
            backup_data[collection_name] = documents
        
        # Save to file
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        # Get file size
        file_size = os.path.getsize(backup_file)
        
        # Log backup creation
        await db.audit_logs.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": "system",
            "email": "system",
            "action": "backup_created",
            "resource_type": "system",
            "resource_id": backup_file,
            "ip_address": "cron-job",
            "user_agent": "automated-backup",
            "status": "success",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": {
                "collections_backed_up": len(collections_to_backup),
                "total_documents": sum(len(docs) for docs in backup_data.values()),
                "file_size_mb": round(file_size / (1024 * 1024), 2)
            }
        })
        
        return {
            "success": True,
            "backup_file": backup_file,
            "timestamp": timestamp,
            "collections": len(collections_to_backup),
            "total_documents": sum(len(docs) for docs in backup_data.values()),
            "file_size_mb": round(file_size / (1024 * 1024), 2)
        }
        
    except Exception as e:
        logging.error(f"Backup creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")

@api_router.get("/admin/backup/list")
async def list_backups(user: dict = Depends(get_current_user)):
    """List all available backups (Admin only)"""
    if user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        backup_dir = "/app/backups"
        if not os.path.exists(backup_dir):
            return {"backups": []}
        
        backups = []
        for filename in sorted(os.listdir(backup_dir), reverse=True):
            if filename.startswith("backup_") and filename.endswith(".json"):
                filepath = os.path.join(backup_dir, filename)
                file_size = os.path.getsize(filepath)
                file_time = os.path.getmtime(filepath)
                
                backups.append({
                    "filename": filename,
                    "size_mb": round(file_size / (1024 * 1024), 2),
                    "created_at": datetime.fromtimestamp(file_time).isoformat(),
                    "download_url": f"/api/admin/backup/download/{filename}"
                })
        
        return {"backups": backups}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/admin/backup/download/{filename}")
async def download_backup(filename: str, user: dict = Depends(get_current_user)):
    """Download specific backup file (Admin only)"""
    if user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Security: only allow backup files
    if not filename.startswith("backup_") or not filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Invalid backup filename")
    
    filepath = f"/app/backups/{filename}"
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Backup file not found")
    
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/json"
    )

@api_router.get("/export/excel/{analysis_id}")
async def export_excel(analysis_id: str, user: dict = Depends(get_current_user)):
    analysis = await db.analyses.find_one(
        {"id": analysis_id, "user_id": user['id']},
        {"_id": 0}
    )
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    note = await db.clinical_notes.find_one(
        {"id": analysis['note_id']},
        {"_id": 0}
    )
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Clinical Analysis"
    
    header_fill = PatternFill(start_color="1e40af", end_color="1e40af", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    
    ws['A1'] = 'Note Title'
    ws['B1'] = note.get('title', '')
    ws['A1'].fill = header_fill
    ws['A1'].font = header_font
    
    row = 3
    ws[f'A{row}'] = 'Diagnoses to Document'
    ws[f'A{row}'].fill = header_fill
    ws[f'A{row}'].font = header_font
    row += 1
    
    ws[f'A{row}'] = 'Diagnosis (EN)'
    ws[f'B{row}'] = 'Diagnosis (AR)'
    ws[f'C{row}'] = 'ICD-10 Code'
    row += 1
    
    for diag in analysis.get('diagnoses_to_document', []):
        ws[f'A{row}'] = diag.get('diagnosis_en', '')
        ws[f'B{row}'] = diag.get('diagnosis_ar', '')
        ws[f'C{row}'] = diag.get('icd_code', '')
        row += 1
    
    ws.column_dimensions['A'].width = 40
    ws.column_dimensions['B'].width = 40
    ws.column_dimensions['C'].width = 15
    
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=analysis_{analysis_id}.xlsx"}
    )

@api_router.post("/supervisor/upload-cdi-data")
async def upload_cdi_data(
    file: UploadFile = File(...),
    supervisor: dict = Depends(require_supervisor)
):
    """Upload and analyze monthly CDI Excel data with comprehensive professional indicators"""
    import pandas as pd
    from collections import Counter
    
    # Validate file type
    if not (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are allowed")
    
    try:
        # Read Excel file
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        # Normalize column names
        df.columns = df.columns.str.lower().str.strip()
        
        # Function to find column by keywords
        def find_column(keywords):
            for keyword in keywords:
                matches = [c for c in df.columns if keyword.lower() in c.lower()]
                if matches:
                    return matches[0]
            return None
        
        # Find all columns flexibly
        cds_col = find_column(['cds', 'specialist', 'doctor', 'physician'])
        hospital_col = find_column(['hospital', 'facility', 'مستشفى', 'مستشفيات'])
        admission_col = find_column(['admission', 'admit', 'date', 'تاريخ'])
        
        # Principal Diagnosis columns
        pdx_before_col = find_column(['pdx before', 'principal before', 'primary before', 'pdxbefore'])
        pdx_after_col = find_column(['pdx after', 'principal after', 'primary after', 'pdxafter', 'pdx/after cdi', 'pdx /after cdi', 'pdx after cdi'])
        pdx_due_to_cdi_col = find_column(['pdx due to cdi', 'pdx added'])
        
        # Additional Diagnosis columns - SEPARATED for accuracy
        adx_due_to_cdi_col = find_column(['adx due to cdi', 'adx added', 'secondary due to cdi'])
        adx_after_col = find_column(['adx after', 'adx/after cdi', 'adx after cdi', 'secondary after', 'additional after', 'all adx'])
        
        # DRG columns
        drg_before_col = find_column(['drg before', 'before drg', 'drgbefore', 'previous drg'])
        drg_after_col = find_column(['drg after', 'after drg', 'drgafter', 'current drg', 'new drg'])
        drg_change_col = find_column(['drg change', 'change', 'drgchange', 'impact'])
        
        # Specialty column
        specialty_col = find_column(['specialty', 'speciality', 'تخصص', 'department', 'dept', 'service'])
        
        # Query and Review columns
        query_col = find_column(['numbers of query', 'query', 'queries', 'استفسار', 'استفسارات', 'number of query'])
        review_col = find_column(['numbers of review', 'review', 'reviews', 'مراجعة', 'مراجعات', 'number of review'])
        response_col = find_column(['numbers of response', 'numbers of respons', 'response', 'responses', 'رد', 'ردود', 'number of response'])
        
        # Check critical columns
        if not hospital_col:
            raise HTTPException(status_code=400, detail="تعذر العثور على عمود المستشفى. يرجى التأكد من وجود عمود 'Hospital Name' أو مشابه.")
        
        # Basic Statistics
        total_records = len(df)
        hospitals = df[hospital_col].dropna().unique()
        total_hospitals = len(hospitals)
        
        # DRG Analysis
        drg_changes_count = 0
        if drg_change_col:
            # Check for Yes/No values, or numeric values, or compare before/after
            df['has_drg_change'] = df[drg_change_col].notna() & (
                (df[drg_change_col].astype(str).str.strip().str.lower().isin(['yes', 'نعم', 'true', '1'])) |
                ((df[drg_change_col] != 0) & (df[drg_change_col].astype(str).str.lower() != 'no'))
            )
            drg_changes_count = int(df['has_drg_change'].sum())
        elif drg_before_col and drg_after_col:
            df['has_drg_change'] = (df[drg_before_col] != df[drg_after_col]) & df[drg_before_col].notna() & df[drg_after_col].notna()
            drg_changes_count = int(df['has_drg_change'].sum())
        else:
            df['has_drg_change'] = False
        
        # PDX Analysis (Principal Diagnosis after CDI)
        pdx_changes = 0
        pdx_added = 0
        if pdx_after_col:
            # PDX Added: count all non-empty values in PDX/After CDI column
            pdx_added_series = df[pdx_after_col].dropna()
            pdx_added_series = pdx_added_series[pdx_added_series.astype(str).str.strip() != '']
            pdx_added = len(pdx_added_series)
            
            # PDX Changes: only if we have before column
            if pdx_before_col:
                df['pdx_changed'] = (df[pdx_before_col] != df[pdx_after_col]) & df[pdx_before_col].notna() & df[pdx_after_col].notna()
                pdx_changes = int(df['pdx_changed'].sum())
        
        # ADX Analysis (Additional Diagnosis due to CDI)
        adx_added = 0
        if adx_due_to_cdi_col:
            df['has_adx'] = df[adx_due_to_cdi_col].notna() & (df[adx_due_to_cdi_col].astype(str).str.strip() != '')
            adx_added = int(df['has_adx'].sum())
        
        # Calculate documentation metrics - with empty string filtering
        total_pdx_after = int((df[pdx_after_col].notna() & (df[pdx_after_col].astype(str).str.strip() != '')).sum()) if pdx_after_col else 0
        total_adx = int((df[adx_due_to_cdi_col].notna() & (df[adx_due_to_cdi_col].astype(str).str.strip() != '')).sum()) if adx_due_to_cdi_col else 0
        
        # Calculate Query and Review metrics
        total_queries = 0
        if query_col:
            # Sum numeric values in query column
            query_series = pd.to_numeric(df[query_col], errors='coerce').fillna(0)
            total_queries = int(query_series.sum())
        
        total_reviews = 0
        if review_col:
            # Sum numeric values in review column
            review_series = pd.to_numeric(df[review_col], errors='coerce').fillna(0)
            total_reviews = int(review_series.sum())
        
        total_responses = 0
        if response_col:
            # Sum numeric values in response column
            response_series = pd.to_numeric(df[response_col], errors='coerce').fillna(0)
            total_responses = int(response_series.sum())
        
        # Hospital-Level Comprehensive Analysis
        # Hospital-Level PRECISE Analysis
        hospitals_data = []
        for hospital in hospitals:
            if pd.notna(hospital) and str(hospital).strip():
                # Get exact match for this hospital
                hospital_df = df[df[hospital_col] == hospital].copy()
                total_cases_hospital = len(hospital_df)
                
                # PDX/After CDI Analysis - PRECISE counting
                pdx_diagnoses = []
                pdx_diagnoses_full = []
                if pdx_after_col and pdx_after_col in hospital_df.columns:
                    # Only count non-null, non-empty values
                    pdx_list = hospital_df[pdx_after_col].dropna()
                    pdx_list = pdx_list[pdx_list.astype(str).str.strip() != '']
                    
                    if len(pdx_list) > 0:
                        pdx_counter = Counter(pdx_list)
                        # Top 10 for display
                        pdx_diagnoses = [
                            {"diagnosis": str(diag).strip(), "count": int(count)} 
                            for diag, count in pdx_counter.most_common(10)
                        ]
                        # All diagnoses for comprehensive report
                        pdx_diagnoses_full = [
                            {"diagnosis": str(diag).strip(), "count": int(count)} 
                            for diag, count in pdx_counter.most_common()
                        ]
                
                # PDX due to CDI Analysis - Only added PDX diagnoses
                pdx_due_to_cdi_diagnoses = []
                pdx_due_to_cdi_diagnoses_full = []
                
                # First, try to find a dedicated PDX due to CDI column
                if pdx_due_to_cdi_col and pdx_due_to_cdi_col in hospital_df.columns:
                    pdx_due_list = hospital_df[pdx_due_to_cdi_col].dropna()
                    pdx_due_list = pdx_due_list[pdx_due_list.astype(str).str.strip() != '']
                    
                    if len(pdx_due_list) > 0:
                        pdx_due_counter = Counter(pdx_due_list)
                        pdx_due_to_cdi_diagnoses = [
                            {"diagnosis": str(diag).strip(), "count": int(count)} 
                            for diag, count in pdx_due_counter.most_common(10)
                        ]
                        pdx_due_to_cdi_diagnoses_full = [
                            {"diagnosis": str(diag).strip(), "count": int(count)} 
                            for diag, count in pdx_due_counter.most_common()
                        ]
                # Fallback: use pdx_added flag if no dedicated column
                elif pdx_after_col and pdx_after_col in hospital_df.columns and 'pdx_added' in hospital_df.columns:
                    pdx_added_df = hospital_df[hospital_df['pdx_added'] == True]
                    pdx_added_list = pdx_added_df[pdx_after_col].dropna()
                    pdx_added_list = pdx_added_list[pdx_added_list.astype(str).str.strip() != '']
                    
                    if len(pdx_added_list) > 0:
                        pdx_added_counter = Counter(pdx_added_list)
                        pdx_due_to_cdi_diagnoses = [
                            {"diagnosis": str(diag).strip(), "count": int(count)} 
                            for diag, count in pdx_added_counter.most_common(10)
                        ]
                        pdx_due_to_cdi_diagnoses_full = [
                            {"diagnosis": str(diag).strip(), "count": int(count)} 
                            for diag, count in pdx_added_counter.most_common()
                        ]
                
                # ADX due to CDI Analysis - PRECISE counting
                adx_diagnoses = []
                adx_diagnoses_full = []
                if adx_due_to_cdi_col and adx_due_to_cdi_col in hospital_df.columns:
                    # Only count non-null, non-empty values
                    adx_list = hospital_df[adx_due_to_cdi_col].dropna()
                    adx_list = adx_list[adx_list.astype(str).str.strip() != '']
                    
                    if len(adx_list) > 0:
                        adx_counter = Counter(adx_list)
                        # Top 10 for display
                        adx_diagnoses = [
                            {"diagnosis": str(diag).strip(), "count": int(count)} 
                            for diag, count in adx_counter.most_common(10)
                        ]
                        # All diagnoses for comprehensive report
                        adx_diagnoses_full = [
                            {"diagnosis": str(diag).strip(), "count": int(count)} 
                            for diag, count in adx_counter.most_common()
                        ]
                
                # ADX/After CDI Analysis - ALL secondary diagnoses after CDI
                adx_after_diagnoses = []
                adx_after_diagnoses_full = []
                if adx_after_col and adx_after_col in hospital_df.columns:
                    # Count all ADX after CDI
                    adx_after_list = hospital_df[adx_after_col].dropna()
                    adx_after_list = adx_after_list[adx_after_list.astype(str).str.strip() != '']
                    
                    if len(adx_after_list) > 0:
                        adx_after_counter = Counter(adx_after_list)
                        # Top 10 for display
                        adx_after_diagnoses = [
                            {"diagnosis": str(diag).strip(), "count": int(count)} 
                            for diag, count in adx_after_counter.most_common(10)
                        ]
                        # All diagnoses for comprehensive report
                        adx_after_diagnoses_full = [
                            {"diagnosis": str(diag).strip(), "count": int(count)} 
                            for diag, count in adx_after_counter.most_common()
                        ]
                elif adx_due_to_cdi_col and adx_due_to_cdi_col in hospital_df.columns:
                    # Fallback: if no separate ADX/After column, use ADX due to CDI
                    adx_after_diagnoses = adx_diagnoses
                    adx_after_diagnoses_full = adx_diagnoses_full
                
                # Calculate metrics with validation
                drg_changes_hospital = 0
                if 'has_drg_change' in hospital_df.columns:
                    drg_changes_hospital = int(hospital_df['has_drg_change'].sum())
                
                pdx_changes_hospital = 0
                if 'pdx_changed' in hospital_df.columns:
                    pdx_changes_hospital = int(hospital_df['pdx_changed'].sum())
                
                # PDX Added: count non-empty values from PDX/After CDI column
                pdx_added_hospital = 0
                if pdx_after_col and pdx_after_col in hospital_df.columns:
                    pdx_added_list = hospital_df[pdx_after_col].dropna()
                    pdx_added_list = pdx_added_list[pdx_added_list.astype(str).str.strip() != '']
                    pdx_added_hospital = len(pdx_added_list)
                
                adx_added_hospital = 0
                if 'has_adx' in hospital_df.columns:
                    adx_added_hospital = int(hospital_df['has_adx'].sum())
                
                # Calculate impact rate
                drg_impact_rate_hospital = 0.0
                if total_cases_hospital > 0 and 'has_drg_change' in hospital_df.columns:
                    drg_impact_rate_hospital = round((drg_changes_hospital / total_cases_hospital * 100), 2)
                
                # Calculate queries and reviews for this hospital
                queries_hospital = 0
                if query_col and query_col in hospital_df.columns:
                    query_series_hospital = pd.to_numeric(hospital_df[query_col], errors='coerce').fillna(0)
                    queries_hospital = int(query_series_hospital.sum())
                
                reviews_hospital = 0
                if review_col and review_col in hospital_df.columns:
                    review_series_hospital = pd.to_numeric(hospital_df[review_col], errors='coerce').fillna(0)
                    reviews_hospital = int(review_series_hospital.sum())
                
                responses_hospital = 0
                if response_col and response_col in hospital_df.columns:
                    response_series_hospital = pd.to_numeric(hospital_df[response_col], errors='coerce').fillna(0)
                    responses_hospital = int(response_series_hospital.sum())
                
                hospital_data = {
                    'hospital_name': str(hospital).strip(),
                    'total_cases': total_cases_hospital,
                    'drg_changes': drg_changes_hospital,
                    'pdx_changes': pdx_changes_hospital,
                    'pdx_added': pdx_added_hospital,
                    'adx_added': adx_added_hospital,
                    'top_pdx_diagnoses': pdx_diagnoses,
                    'top_pdx_due_to_cdi_diagnoses': pdx_due_to_cdi_diagnoses,
                    'top_adx_diagnoses': adx_diagnoses,
                    'top_adx_after_diagnoses': adx_after_diagnoses,
                    'all_pdx_diagnoses': pdx_diagnoses_full,
                    'all_pdx_due_to_cdi_diagnoses': pdx_due_to_cdi_diagnoses_full,
                    'all_adx_diagnoses': adx_diagnoses_full,
                    'all_adx_after_diagnoses': adx_after_diagnoses_full,
                    'drg_impact_rate': drg_impact_rate_hospital,
                    'pdx_diagnoses_count': len(pdx_diagnoses_full),
                    'pdx_due_to_cdi_count': len(pdx_due_to_cdi_diagnoses_full),
                    'adx_diagnoses_count': len(adx_diagnoses_full),
                    'total_queries': queries_hospital,
                    'total_reviews': reviews_hospital,
                    'total_responses': responses_hospital
                }
                hospitals_data.append(hospital_data)
        
        # Sort by DRG impact
        hospitals_data.sort(key=lambda x: x['drg_changes'], reverse=True)
        
        # Overall Top Diagnoses (PDX/After CDI)
        top_pdx_overall = []
        if pdx_after_col:
            pdx_all = df[pdx_after_col].dropna()
            if len(pdx_all) > 0:
                pdx_counter = Counter(pdx_all)
                top_pdx_overall = [
                    {"diagnosis": str(diag), "count": count, "percentage": round(count/len(pdx_all)*100, 2)} 
                    for diag, count in pdx_counter.most_common(15)
                ]
        
        # Overall Top PDX due to CDI (only added)
        top_pdx_due_to_cdi_overall = []
        if pdx_after_col and 'pdx_added' in df.columns:
            pdx_added_all_df = df[df['pdx_added'] == True]
            pdx_added_all = pdx_added_all_df[pdx_after_col].dropna()
            if len(pdx_added_all) > 0:
                pdx_added_counter = Counter(pdx_added_all)
                top_pdx_due_to_cdi_overall = [
                    {"diagnosis": str(diag), "count": count, "percentage": round(count/len(pdx_added_all)*100, 2)} 
                    for diag, count in pdx_added_counter.most_common(15)
                ]
        
        # Overall Top ADX Diagnoses
        top_adx_overall = []
        if adx_due_to_cdi_col:
            adx_all = df[adx_due_to_cdi_col].dropna()
            if len(adx_all) > 0:
                adx_counter = Counter(adx_all)
                top_adx_overall = [
                    {"diagnosis": str(diag), "count": count, "percentage": round(count/len(adx_all)*100, 2)} 
                    for diag, count in adx_counter.most_common(15)
                ]
        
        # Specialty Analysis
        specialty_data = []
        if specialty_col:
            specialties = df[specialty_col].dropna().unique()
            for specialty in specialties:
                if str(specialty).strip():
                    specialty_df = df[df[specialty_col] == specialty]
                    
                    # Calculate PDX count from PDX/After CDI column directly
                    pdx_count_specialty = 0
                    if pdx_after_col and pdx_after_col in specialty_df.columns:
                        pdx_list = specialty_df[pdx_after_col].dropna()
                        pdx_list = pdx_list[pdx_list.astype(str).str.strip() != '']
                        pdx_count_specialty = len(pdx_list)
                    
                    specialty_data.append({
                        'specialty': str(specialty),
                        'total_cases': len(specialty_df),
                        'drg_changes': int(specialty_df['has_drg_change'].sum()) if 'has_drg_change' in specialty_df.columns else 0,
                        'pdx_changes': pdx_count_specialty,
                        'adx_added': int(specialty_df['has_adx'].sum()) if 'has_adx' in specialty_df.columns else 0,
                        'impact_rate': round((specialty_df['has_drg_change'].sum() / len(specialty_df) * 100), 2) if len(specialty_df) > 0 and 'has_drg_change' in specialty_df.columns else 0
                    })
            
            specialty_data.sort(key=lambda x: x['drg_changes'], reverse=True)
        
        # CDS Performance with Status Analysis - PRECISE CALCULATION
        cds_performance = []
        status_col = find_column(['status', 'حالة', 'state', 'condition'])
        
        if cds_col:
            cds_specialists = df[cds_col].dropna().unique()
            for cds in cds_specialists:
                if str(cds).strip():
                    # Get all rows for this CDS specialist (exact match)
                    cds_df = df[df[cds_col] == cds].copy()
                    total_cases_cds = len(cds_df)
                    
                    # PRECISE Status Analysis with validation
                    status_done = 0
                    status_to_start = 0
                    status_working = 0
                    status_empty = 0
                    
                    if status_col and status_col in cds_df.columns:
                        for idx, status_val in cds_df[status_col].items():
                            # Check if value exists and is not null/empty
                            if pd.notna(status_val):
                                status_str = str(status_val).strip().lower()
                                
                                # Empty string check
                                if not status_str or status_str == '' or status_str == 'nan':
                                    status_empty += 1
                                # Done status (exact matching)
                                elif status_str in ['done', 'تم', 'منتهي', 'complete', 'completed', 'finished']:
                                    status_done += 1
                                # To Start status
                                elif status_str in ['to start', 'للبدء', 'لم يبدأ', 'not started', 'pending']:
                                    status_to_start += 1
                                # Working status
                                elif status_str in ['working', 'working on it', 'جاري', 'قيد العمل', 'in progress', 'ongoing']:
                                    status_working += 1
                                # Any other text is considered as not categorized (empty)
                                else:
                                    status_empty += 1
                            else:
                                # Null/NaN values
                                status_empty += 1
                    else:
                        # No status column means all are empty
                        status_empty = total_cases_cds
                    
                    # VALIDATION: Total should match
                    status_total = status_done + status_to_start + status_working + status_empty
                    if status_total != total_cases_cds:
                        logger.warning(f"CDS {cds}: Status count mismatch. Total cases: {total_cases_cds}, Status sum: {status_total}")
                    
                    # Calculate DRG impact with validation
                    drg_impact_cds = 0
                    if 'has_drg_change' in cds_df.columns:
                        drg_impact_cds = int(cds_df['has_drg_change'].sum())
                    
                    # Calculate PDX queries from PDX/After CDI column directly
                    pdx_queries_cds = 0
                    if pdx_after_col and pdx_after_col in cds_df.columns:
                        pdx_list_cds = cds_df[pdx_after_col].dropna()
                        pdx_list_cds = pdx_list_cds[pdx_list_cds.astype(str).str.strip() != '']
                        pdx_queries_cds = len(pdx_list_cds)
                    
                    # Calculate ADX queries with validation
                    adx_queries_cds = 0
                    if 'has_adx' in cds_df.columns:
                        adx_queries_cds = int(cds_df['has_adx'].sum())
                    
                    # Calculate total queries from Numbers of Query column
                    total_queries_cds = 0
                    if query_col and query_col in cds_df.columns:
                        query_series_cds = pd.to_numeric(cds_df[query_col], errors='coerce').fillna(0)
                        total_queries_cds = int(query_series_cds.sum())
                    
                    # Calculate success rate with validation
                    success_rate_cds = 0.0
                    if total_cases_cds > 0 and 'has_drg_change' in cds_df.columns:
                        success_rate_cds = round((drg_impact_cds / total_cases_cds * 100), 2)
                    
                    cds_performance.append({
                        'cds_name': str(cds),
                        'total_cases': total_cases_cds,
                        'drg_impact': drg_impact_cds,
                        'pdx_queries': pdx_queries_cds,
                        'adx_queries': adx_queries_cds,
                        'total_queries': total_queries_cds,
                        'success_rate': success_rate_cds,
                        'status_done': status_done,
                        'status_to_start': status_to_start,
                        'status_working': status_working,
                        'status_empty': status_empty,
                        # Add validation field
                        'status_total': status_total,
                        'validation_passed': (status_total == total_cases_cds)
                    })
            
            cds_performance.sort(key=lambda x: x['drg_impact'], reverse=True)
        
        # Calculate rates
        drg_impact_rate = round((drg_changes_count / total_records * 100), 2) if total_records > 0 else 0
        pdx_change_rate = round((pdx_changes / total_records * 100), 2) if total_records > 0 else 0
        adx_rate = round((adx_added / total_records * 100), 2) if total_records > 0 else 0
        
        return {
            # Summary Statistics
            'summary': {
                'total_records': int(total_records),
                'total_hospitals': int(total_hospitals),
                'total_specialties': len(specialty_data) if specialty_data else 0,
                'total_cds': len(cds_performance) if cds_performance else 0,
                'analysis_date': datetime.now(timezone.utc).isoformat()
            },
            
            # DRG Metrics
            'drg_metrics': {
                'total_changes': int(drg_changes_count),
                'change_rate': drg_impact_rate,
                'no_change': int(total_records - drg_changes_count)
            },
            
            # PDX Metrics (Principal Diagnosis)
            'pdx_metrics': {
                'total_after_cdi': int(total_pdx_after),
                'changes': int(pdx_changes),
                'newly_added': int(pdx_added),
                'change_rate': pdx_change_rate
            },
            
            # ADX Metrics (Additional Diagnosis)
            'adx_metrics': {
                'total_added': int(adx_added),
                'addition_rate': adx_rate
            },
            
            # Query and Review Metrics
            'query_metrics': {
                'total_queries': int(total_queries)
            },
            
            'review_metrics': {
                'total_reviews': int(total_reviews)
            },
            
            'response_metrics': {
                'total_responses': int(total_responses)
            },
            
            # Top Diagnoses Overall
            'top_diagnoses': {
                'pdx_after_cdi': top_pdx_overall,
                'pdx_due_to_cdi': top_pdx_due_to_cdi_overall,
                'adx_due_to_cdi': top_adx_overall
            },
            
            # Detailed Breakdowns
            'hospitals_analysis': hospitals_data,
            'specialty_analysis': specialty_data[:20],
            'cds_performance': cds_performance[:20],
            
            # Data Availability Flags
            'data_flags': {
                'has_pdx_data': bool(pdx_after_col),
                'has_adx_data': bool(adx_due_to_cdi_col),
                'has_specialty_data': bool(specialty_col),
                'has_cds_data': bool(cds_col),
                'has_drg_data': bool(drg_change_col or (drg_before_col and drg_after_col)),
                'has_status_data': bool(status_col)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing Excel file: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"خطأ في معالجة الملف: {str(e)}")



def calculate_financial_impact(drg_changes: int, avg_case_value_sar: float = 25000.0) -> dict:
    """
    Calculate financial impact of DRG changes in Saudi Riyals
    
    Args:
        drg_changes: Number of DRG changes/upgrades
        avg_case_value_sar: Average additional reimbursement per DRG upgrade (default: 25,000 SAR)
    
    Returns:
        dict with financial metrics
    """
    total_impact_sar = drg_changes * avg_case_value_sar
    monthly_impact = total_impact_sar
    annual_projection = monthly_impact * 12
    
    return {
        "drg_changes": drg_changes,
        "avg_case_value_sar": avg_case_value_sar,
        "total_impact_sar": round(total_impact_sar, 2),
        "monthly_impact_sar": round(monthly_impact, 2),
        "annual_projection_sar": round(annual_projection, 2),
        "total_impact_formatted": f"{total_impact_sar:,.2f} ريال",
        "monthly_impact_formatted": f"{monthly_impact:,.2f} ريال",
        "annual_projection_formatted": f"{annual_projection:,.2f} ريال"
    }


@api_router.post("/supervisor/generate-excel-report")
async def generate_excel_report(
    analysis_data: dict,
    supervisor: dict = Depends(require_supervisor)
):
    """Generate comprehensive Excel report with recommendations"""
    try:
        wb = Workbook()
        
        # Summary Sheet
        ws_summary = wb.active
        ws_summary.title = "ملخص التحليل"
        
        # Header styling
        header_fill = PatternFill(start_color="1F4788", end_color="1F4788", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True, size=12)
        
        # Title
        ws_summary['A1'] = 'تقرير تحليل CDI الشامل'
        ws_summary['A1'].font = Font(bold=True, size=16)
        ws_summary.merge_cells('A1:D1')
        
        # Summary data
        ws_summary['A3'] = 'المؤشر'
        ws_summary['B3'] = 'القيمة'
        ws_summary['A3'].fill = header_fill
        ws_summary['A3'].font = header_font
        ws_summary['B3'].fill = header_fill
        ws_summary['B3'].font = header_font
        
        summary = analysis_data.get('summary', {})
        row = 4
        ws_summary[f'A{row}'] = 'إجمالي الحالات'
        ws_summary[f'B{row}'] = summary.get('total_records', 0)
        row += 1
        ws_summary[f'A{row}'] = 'عدد المستشفيات'
        ws_summary[f'B{row}'] = summary.get('total_hospitals', 0)
        row += 1
        
        # DRG Metrics
        drg = analysis_data.get('drg_metrics', {})
        ws_summary[f'A{row}'] = 'تغييرات DRG'
        ws_summary[f'B{row}'] = drg.get('total_changes', 0)
        row += 1
        ws_summary[f'A{row}'] = 'معدل تغيير DRG'
        ws_summary[f'B{row}'] = f"{drg.get('change_rate', 0)}%"
        row += 1
        
        # PDX Metrics
        pdx = analysis_data.get('pdx_metrics', {})
        ws_summary[f'A{row}'] = 'PDX/After CDI'
        ws_summary[f'B{row}'] = pdx.get('total_after_cdi', 0)
        row += 1
        ws_summary[f'A{row}'] = 'PDX المتغيرة'
        ws_summary[f'B{row}'] = pdx.get('changes', 0)
        row += 1
        
        # ADX Metrics
        adx = analysis_data.get('adx_metrics', {})
        ws_summary[f'A{row}'] = 'ADX due to CDI'
        ws_summary[f'B{row}'] = adx.get('total_added', 0)
        row += 2
        
        # Financial Impact Section
        financial_fill = PatternFill(start_color="2ECC71", end_color="2ECC71", fill_type="solid")
        ws_summary[f'A{row}'] = 'الأثر المالي (Financial Impact)'
        ws_summary[f'A{row}'].font = Font(bold=True, size=14, color="FFFFFF")
        ws_summary[f'A{row}'].fill = financial_fill
        ws_summary.merge_cells(f'A{row}:B{row}')
        row += 1
        
        # Calculate financial impact
        drg_changes_count = drg.get('total_changes', 0)
        financial_impact = calculate_financial_impact(drg_changes_count)
        
        ws_summary[f'A{row}'] = 'عدد تغييرات DRG'
        ws_summary[f'B{row}'] = financial_impact['drg_changes']
        row += 1
        ws_summary[f'A{row}'] = 'متوسط القيمة لكل حالة'
        ws_summary[f'B{row}'] = f"{financial_impact['avg_case_value_sar']:,.0f} ريال"
        row += 1
        ws_summary[f'A{row}'] = 'الأثر المالي الشهري'
        ws_summary[f'B{row}'] = financial_impact['monthly_impact_formatted']
        ws_summary[f'B{row}'].font = Font(bold=True, size=12, color="2ECC71")
        row += 1
        ws_summary[f'A{row}'] = 'التوقعات السنوية'
        ws_summary[f'B{row}'] = financial_impact['annual_projection_formatted']
        ws_summary[f'B{row}'].font = Font(bold=True, size=13, color="2ECC71")
        row += 2
        
        # Hospitals Analysis Sheet
        ws_hospitals = wb.create_sheet(title="تحليل المستشفيات")
        headers = ['المستشفى', 'الحالات', 'DRG Changes', 'PDX Changes', 'PDX Added', 'ADX Added', 'معدل التأثير %']
        for col_idx, header in enumerate(headers, 1):
            cell = ws_hospitals.cell(row=1, column=col_idx)
            cell.value = header
            cell.fill = header_fill
            cell.font = header_font
        
        hospitals = analysis_data.get('hospitals_analysis', [])
        for row_idx, hospital in enumerate(hospitals, 2):
            ws_hospitals.cell(row=row_idx, column=1).value = hospital.get('hospital_name', '')
            ws_hospitals.cell(row=row_idx, column=2).value = hospital.get('total_cases', 0)
            ws_hospitals.cell(row=row_idx, column=3).value = hospital.get('drg_changes', 0)
            ws_hospitals.cell(row=row_idx, column=4).value = hospital.get('pdx_changes', 0)
            ws_hospitals.cell(row=row_idx, column=5).value = hospital.get('pdx_added', 0)
            ws_hospitals.cell(row=row_idx, column=6).value = hospital.get('adx_added', 0)
            ws_hospitals.cell(row=row_idx, column=7).value = hospital.get('drg_impact_rate', 0)
        
        # Financial Impact by Hospital Sheet
        ws_financial = wb.create_sheet(title="الأثر المالي التفصيلي")
        financial_headers = ['المستشفى', 'تغييرات DRG', 'الأثر المالي الشهري (ريال)', 'التوقعات السنوية (ريال)']
        for col_idx, header in enumerate(financial_headers, 1):
            cell = ws_financial.cell(row=1, column=col_idx)
            cell.value = header
            cell.fill = PatternFill(start_color="2ECC71", end_color="2ECC71", fill_type="solid")
            cell.font = Font(color="FFFFFF", bold=True)
        
        total_financial_impact = 0
        for row_idx, hospital in enumerate(hospitals, 2):
            hosp_drg_changes = hospital.get('drg_changes', 0)
            hosp_impact = calculate_financial_impact(hosp_drg_changes)
            
            ws_financial.cell(row=row_idx, column=1).value = hospital.get('hospital_name', '')
            ws_financial.cell(row=row_idx, column=2).value = hosp_drg_changes
            ws_financial.cell(row=row_idx, column=3).value = hosp_impact['monthly_impact_sar']
            ws_financial.cell(row=row_idx, column=3).number_format = '#,##0.00'
            ws_financial.cell(row=row_idx, column=4).value = hosp_impact['annual_projection_sar']
            ws_financial.cell(row=row_idx, column=4).number_format = '#,##0.00'
            total_financial_impact += hosp_impact['monthly_impact_sar']
        
        # Add total row
        total_row = len(hospitals) + 2
        ws_financial.cell(row=total_row, column=1).value = "الإجمالي"
        ws_financial.cell(row=total_row, column=1).font = Font(bold=True)
        ws_financial.cell(row=total_row, column=3).value = total_financial_impact
        ws_financial.cell(row=total_row, column=3).font = Font(bold=True, color="2ECC71")
        ws_financial.cell(row=total_row, column=3).number_format = '#,##0.00'
        ws_financial.cell(row=total_row, column=4).value = total_financial_impact * 12
        ws_financial.cell(row=total_row, column=4).font = Font(bold=True, color="2ECC71")
        ws_financial.cell(row=total_row, column=4).number_format = '#,##0.00'
        
        # Top PDX Diagnoses Sheet
        if analysis_data.get('top_diagnoses', {}).get('pdx_after_cdi'):
            ws_pdx = wb.create_sheet(title="Top PDX Diagnoses")
            ws_pdx['A1'] = 'التشخيص'
            ws_pdx['B1'] = 'العدد'
            ws_pdx['C1'] = 'النسبة %'
            for col in ['A1', 'B1', 'C1']:
                ws_pdx[col].fill = header_fill
                ws_pdx[col].font = header_font
            
            for row_idx, diag in enumerate(analysis_data['top_diagnoses']['pdx_after_cdi'], 2):
                ws_pdx.cell(row=row_idx, column=1).value = diag.get('diagnosis', '')
                ws_pdx.cell(row=row_idx, column=2).value = diag.get('count', 0)
                ws_pdx.cell(row=row_idx, column=3).value = diag.get('percentage', 0)
        
        # Recommendations Sheet
        ws_recommendations = wb.create_sheet(title="التوصيات")
        ws_recommendations['A1'] = 'التوصيات والتوجيهات للتحسين'
        ws_recommendations['A1'].font = Font(bold=True, size=14)
        ws_recommendations.merge_cells('A1:B1')
        
        recommendations = generate_recommendations(analysis_data)
        row_idx = 3
        for rec in recommendations:
            ws_recommendations.cell(row=row_idx, column=1).value = rec['category']
            ws_recommendations.cell(row=row_idx, column=1).font = Font(bold=True)
            ws_recommendations.cell(row=row_idx, column=1).fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")
            row_idx += 1
            ws_recommendations.cell(row=row_idx, column=1).value = rec['recommendation']
            ws_recommendations.cell(row=row_idx, column=1).alignment = Alignment(wrap_text=True)
            ws_recommendations.row_dimensions[row_idx].height = 40
            row_idx += 2
        
        # Adjust column widths
        for ws in wb.worksheets:
            for column in ws.columns:
                max_length = 0
                column_letter = None
                for cell in column:
                    try:
                        if hasattr(cell, 'column_letter'):
                            column_letter = cell.column_letter
                        if cell.value and len(str(cell.value)) > max_length:
                            max_length = len(cell.value)
                    except:
                        pass
                if column_letter:
                    adjusted_width = min(max_length + 2, 50)
                    ws.column_dimensions[column_letter].width = adjusted_width
        
        # Save to BytesIO
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=CDI_Report_{datetime.now().strftime('%Y%m%d')}.xlsx"}
        )
    
    except Exception as e:
        logger.error(f"Error generating Excel report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")


@api_router.get("/supervisor/dashboard-stats")
async def get_dashboard_statistics(supervisor: dict = Depends(require_supervisor)):
    """
    Get visual dashboard statistics with KPIs and charts data
    Returns comprehensive monthly statistics for visual dashboard
    """
    try:
        # Get the latest uploaded analysis data from session/database
        # For now, we'll return structure - implement actual data fetching later
        
        # Mock data structure for dashboard
        current_month = datetime.now().strftime("%B %Y")
        
        dashboard_data = {
            "period": current_month,
            "kpis": {
                "total_cases": 0,
                "drg_changes": 0,
                "drg_impact_rate": 0.0,
                "financial_impact_sar": 0.0,
                "annual_projection_sar": 0.0,
                "pdx_changes": 0,
                "adx_added": 0,
                "queries_generated": 0
            },
            "charts": {
                "drg_trend": {
                    "labels": [],
                    "values": []
                },
                "hospital_comparison": {
                    "hospitals": [],
                    "drg_changes": [],
                    "financial_impact": []
                },
                "specialty_distribution": {
                    "specialties": [],
                    "cases": []
                },
                "cds_performance": {
                    "specialists": [],
                    "drg_impact": [],
                    "success_rate": []
                }
            },
            "top_performers": [],
            "improvement_areas": []
        }
        
        return dashboard_data
    
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/supervisor/export-dashboard-image")
async def export_dashboard_image(
    chart_data: dict,
    supervisor: dict = Depends(require_supervisor)
):
    """
    Export dashboard charts as images (PNG)
    Receives chart configuration and returns image
    """
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from io import BytesIO
        
        chart_type = chart_data.get('type', 'bar')
        title = chart_data.get('title', 'Chart')
        labels = chart_data.get('labels', [])
        values = chart_data.get('values', [])
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        if chart_type == 'bar':
            ax.bar(labels, values, color='#3B82F6')
        elif chart_type == 'line':
            ax.plot(labels, values, marker='o', color='#10B981', linewidth=2)
        elif chart_type == 'pie':
            ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
            ax.axis('equal')
        
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # Save to buffer
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        
        return StreamingResponse(
            buffer,
            media_type="image/png",
            headers={"Content-Disposition": f"attachment; filename={title.replace(' ', '_')}.png"}
        )
    
    except Exception as e:
        logger.error(f"Error exporting chart image: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



def generate_recommendations(analysis_data):
    """Generate smart recommendations based on analysis data"""
    recommendations = []
    
    drg_metrics = analysis_data.get('drg_metrics', {})
    pdx_metrics = analysis_data.get('pdx_metrics', {})
    adx_metrics = analysis_data.get('adx_metrics', {})
    hospitals = analysis_data.get('hospitals_analysis', [])
    
    # DRG Impact Analysis
    drg_rate = drg_metrics.get('change_rate', 0)
    if drg_rate < 20:
        recommendations.append({
            'category': '⚠️ معدل تأثير DRG منخفض',
            'recommendation': f'معدل تغيير DRG الحالي {drg_rate}% أقل من المتوقع. يُنصح بتكثيف جهود CDI والتركيز على المراجعة الدقيقة للملفات قبل الترميز النهائي.'
        })
    elif drg_rate > 60:
        recommendations.append({
            'category': '✅ معدل تأثير DRG ممتاز',
            'recommendation': f'معدل تغيير DRG الحالي {drg_rate}% يعتبر ممتازاً. استمروا في تطبيق نفس المعايير والممارسات الحالية.'
        })
    
    # PDX Documentation Analysis
    pdx_rate = pdx_metrics.get('change_rate', 0)
    if pdx_rate > 30:
        recommendations.append({
            'category': '📋 تحسين التوثيق الرئيسي مطلوب',
            'recommendation': f'نسبة {pdx_rate}% من التشخيصات الرئيسية تم تعديلها. يجب تدريب الأطباء على توثيق التشخيص الرئيسي بدقة منذ البداية.'
        })
    
    # Hospital-Specific Recommendations
    if hospitals:
        # Find hospitals with low performance
        low_performers = [h for h in hospitals if h.get('drg_impact_rate', 0) < 20]
        if low_performers:
            hospital_names = ', '.join([h['hospital_name'] for h in low_performers[:3]])
            recommendations.append({
                'category': '🏥 مستشفيات تحتاج تحسين',
                'recommendation': f'المستشفيات التالية تحتاج إلى تحسين في التوثيق: {hospital_names}. يُنصح بعقد ورش عمل تدريبية وزيادة التواصل مع فريق التوثيق.'
            })
        
        # Find hospitals with high undocumented cases
        high_undoc = sorted(hospitals, key=lambda x: x.get('pdx_added', 0) + x.get('adx_added', 0), reverse=True)[:3]
        if high_undoc and (high_undoc[0].get('pdx_added', 0) + high_undoc[0].get('adx_added', 0)) > 50:
            recommendations.append({
                'category': '📝 نقص في التوثيق',
                'recommendation': f'المستشفى {high_undoc[0]["hospital_name"]} يحتاج إلى تحسين كبير في توثيق التشخيصات. تم إضافة {high_undoc[0].get("pdx_added", 0)} تشخيص رئيسي و {high_undoc[0].get("adx_added", 0)} تشخيص إضافي بعد مراجعة CDI.'
            })
    
    # Top Diagnoses Recommendations
    top_pdx = analysis_data.get('top_diagnoses', {}).get('pdx_after_cdi', [])
    if top_pdx:
        top_3 = ', '.join([d['diagnosis'] for d in top_pdx[:3]])
        recommendations.append({
            'category': '🎯 التشخيصات الأكثر شيوعاً',
            'recommendation': f'التشخيصات الأكثر شيوعاً بعد CDI: {top_3}. يُنصح بإنشاء بروتوكولات توثيق محددة لهذه الحالات لتقليل الحاجة للتعديل مستقبلاً.'
        })
    
    # Specialty Recommendations
    specialties = analysis_data.get('specialty_analysis', [])
    if specialties:
        low_spec = [s for s in specialties if s.get('impact_rate', 0) < 15]
        if low_spec:
            spec_names = ', '.join([s['specialty'] for s in low_spec[:2]])
            recommendations.append({
                'category': '🔬 تخصصات تحتاج دعم',
                'recommendation': f'التخصصات التالية تحتاج إلى دعم إضافي في التوثيق: {spec_names}. يُفضل تعيين CDS متخصص لهذه الأقسام.'
            })
    
    # General Best Practices
    recommendations.append({
        'category': '💡 أفضل الممارسات',
        'recommendation': 'استمروا في المراجعة الدورية للملفات، وتحديث البروتوكولات بناءً على أحدث إرشادات ICD-10، وعقد اجتماعات دورية بين فريق CDI والأطباء.'
    })
    
    return recommendations


# ========== Messaging System ==========

@api_router.post("/messages/send")
async def send_message(
    message: MessageCreate,
    current_user: dict = Depends(get_current_user)
):
    """Send a message to a user or all users"""
    logger.info(f"User {current_user['id']} sending message to {message.to_user_id}")
    
    # Get recipient name if specific user
    to_user_name = None
    to_user_id_final = None
    
    if message.to_user_id and message.to_user_id != "ALL":
        recipient = await db.users.find_one({"id": message.to_user_id}, {"_id": 0, "full_name": 1})
        if not recipient:
            logger.error(f"Recipient {message.to_user_id} not found")
            raise HTTPException(status_code=404, detail="Recipient not found")
        to_user_name = recipient['full_name']
        to_user_id_final = message.to_user_id
        logger.info(f"Sending to specific user: {to_user_name} ({to_user_id_final})")
    else:
        to_user_name = "الكل"
        to_user_id_final = "ALL"
        logger.info("Sending to ALL users")
    
    # Create message document
    message_doc = {
        "id": str(uuid.uuid4()),
        "from_user_id": current_user['id'],
        "from_user_name": current_user['full_name'],
        "to_user_id": to_user_id_final,
        "to_user_name": to_user_name,
        "subject": message.subject,
        "message": message.body,  # Store as 'message' for frontend compatibility
        "is_draft": message.is_draft,
        "is_read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.messages.insert_one(message_doc)
    logger.info(f"Message saved with id: {message_doc['id']}")
    
    return {"message": "Message sent successfully", "id": message_doc['id']}

@api_router.get("/messages/inbox")
async def get_inbox(current_user: dict = Depends(get_current_user)):
    """Get inbox messages for current user - includes sent and received"""
    # Messages sent TO this user, TO all users, OR FROM this user (ascending order - oldest first)
    messages = await db.messages.find({
        "$or": [
            {"to_user_id": current_user['id']},  # Messages to me
            {"to_user_id": "ALL"},                # Public messages
            {"from_user_id": current_user['id']}  # Messages I sent
        ],
        "is_draft": False
    }, {"_id": 0}).sort("created_at", 1).to_list(1000)
    
    logger.info(f"Retrieved {len(messages)} messages for user {current_user['id']}")
    return {"messages": messages}

@api_router.get("/messages/sent")
async def get_sent_messages(current_user: dict = Depends(get_current_user)):
    """Get sent messages for current user"""
    messages = await db.messages.find({
        "from_user_id": current_user['id'],
        "is_draft": False
    }, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    # Convert datetime
    for msg in messages:
        if isinstance(msg.get('created_at'), str):
            msg['created_at'] = datetime.fromisoformat(msg['created_at'])
    
    return messages

@api_router.get("/messages/drafts")
async def get_draft_messages(current_user: dict = Depends(get_current_user)):
    """Get draft messages for current user"""
    messages = await db.messages.find({
        "from_user_id": current_user['id'],
        "is_draft": True
    }, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    # Convert datetime
    for msg in messages:
        if isinstance(msg.get('created_at'), str):
            msg['created_at'] = datetime.fromisoformat(msg['created_at'])
    
    return messages

@api_router.post("/messages/{message_id}/read")
async def mark_message_as_read(
    message_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Mark message as read"""
    await db.messages.update_one(
        {"id": message_id, "to_user_id": current_user['id']},
        {"$set": {"is_read": True}}
    )
    return {"message": "Marked as read"}

@api_router.delete("/messages/{message_id}")
async def delete_message(
    message_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a message"""
    result = await db.messages.delete_one({
        "id": message_id,
        "$or": [
            {"from_user_id": current_user['id']},
            {"to_user_id": current_user['id']}
        ]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Message not found")
    
    return {"message": "Message deleted"}

@api_router.get("/messages/unread-count")
async def get_unread_count(current_user: dict = Depends(get_current_user)):
    """Get count of unread messages"""
    count = await db.messages.count_documents({
        "$or": [
            {"to_user_id": current_user['id']},
            {"to_user_id": None}
        ],
        "is_draft": False,
        "is_read": False
    })
    return {"count": count}


# ========== Supervisor Impersonation ==========

@api_router.post("/supervisor/impersonate/{user_id}")
async def impersonate_user(
    user_id: str,
    supervisor: dict = Depends(require_supervisor)
):
    """Supervisor can impersonate (login as) any user"""
    # Get target user
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Don't allow impersonating admin
    if user.get('role') == 'admin':
        raise HTTPException(status_code=403, detail="Cannot impersonate admin")
    
    # Create access token for the target user
    access_token = create_access_token({
        "user_id": user['id'], 
        "email": user['email'],
        "role": user.get('role', 'user')
    })
    
    # Add impersonation info
    user['is_impersonated'] = True
    user['impersonated_by'] = supervisor['id']
    user['impersonated_by_name'] = supervisor['full_name']
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
        "original_supervisor": {
            "id": supervisor['id'],
            "name": supervisor['full_name'],
            "email": supervisor['email']
        }
    }

# ========== Clinical Questions Routes ==========
# Import clinical questions
try:
    from clinical_questions import get_questions, get_question_by_id, get_categories
    print("✅ Clinical questions loaded successfully")
except Exception as e:
    print(f"⚠️ Warning: Could not load clinical questions: {str(e)}")

@api_router.get("/clinical-questions")
async def get_clinical_questions(language: str = "ar", user: dict = Depends(get_current_user)):
    """Get all predefined clinical questions"""
    try:
        questions = get_questions(language)
        return {"questions": questions}
    except Exception as e:
        print(f"Error getting questions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get questions")

@api_router.get("/clinical-questions/categories")
async def get_question_categories(language: str = "ar", user: dict = Depends(get_current_user)):
    """Get question categories"""
    try:
        categories = get_categories(language)
        return {"categories": categories}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get categories")

@api_router.post("/chat/ask-question/{question_id}")
@limiter.limit("20/minute")
async def ask_predefined_question(
    request: Request,
    question_id: str,
    analysis_id: str,
    language: str = "ar",
    user: dict = Depends(get_current_user)
):
    """Ask a predefined clinical question about an analysis"""
    try:
        # Get the question
        question = get_question_by_id(question_id, language)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        
        # Get the analysis
        analysis = await db.analyses.find_one(
            {"id": analysis_id, "user_id": user['id']},
            {"_id": 0}
        )
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Get the note
        note = await db.clinical_notes.find_one(
            {"id": analysis['note_id'], "user_id": user['id']},
            {"_id": 0}
        )
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
        
        # Build context for AI
        # Format doctor notes
        doctor_notes_text = "\n\n".join([
            f"**{dn.get('specialty', 'عام')}**:\n{dn.get('text', '')}"
            for dn in note.get('doctor_notes', [])
        ])
        
        # Format missing documentation
        missing_docs = analysis.get('missing_documentation', [])
        if missing_docs and isinstance(missing_docs[0], dict):
            missing_docs_text = ', '.join([d.get('item_ar', '') for d in missing_docs])
        else:
            missing_docs_text = ', '.join(missing_docs) if missing_docs else 'لا يوجد'
        
        context = f"""
التحليل السريري:
العنوان: {note.get('title', 'N/A')}

الملاحظات السريرية:
{doctor_notes_text}

التشخيصات المحددة للتوثيق:
{', '.join([d.get('diagnosis_ar', '') for d in analysis.get('diagnoses_to_document', [])])}

التوثيق الناقص:
{missing_docs_text}

الثغرات في التوثيق:
{', '.join(analysis.get('gaps_ar', []))}

الاستفسارات للطبيب:
{', '.join(analysis.get('queries_ar', []))}
"""
        
        # Ask AI with the question's prompt
        full_prompt = f"{context}\n\n{question['prompt']}"
        
        # Use Gemini to answer
        system_message = """You are a Clinical Documentation Improvement (CDI) specialist expert. 
Answer the question based on the clinical context provided. 

CRITICAL: Be VERY concise and precise. Give direct answers without unnecessary details or lengthy explanations.
Use bullet points when listing items. Focus ONLY on what was specifically asked.
Maximum 5-7 bullet points or 4-5 short paragraphs unless the question explicitly asks for comprehensive detail.
Respond in Arabic if the question is in Arabic, or in English if the question is in English."""
        
        try:
            model = get_gemini_model('gemini-flash-latest', system_instruction=system_message)
            response = model.generate_content(full_prompt)
            result = response.text
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to generate AI response")
        
        # Save to chat history
        chat_message = {
            "id": str(uuid.uuid4()),
            "analysis_id": analysis_id,
            "user_id": user['id'],
            "question": question['question'],
            "question_id": question_id,
            "answer": result,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.chat_messages.insert_one(chat_message)
        
        return {
            "question": question['question'],
            "answer": result,
            "category": question['category']
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error asking question: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process question")

# ========== Include Routers ==========
app.include_router(api_router)

# Import and include security router
try:
    from security_routes import security_router
    app.include_router(security_router, prefix="/api")
    print("✅ Security routes loaded successfully")
except Exception as e:
    print(f"⚠️ Warning: Could not load security routes: {str(e)}")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_monitoring():
    """Start monitoring tasks and ensure admin account"""
    import asyncio
    
    # CRITICAL: Ensure admin account exists with correct credentials
    await ensure_admin_account()
    
    async def update_active_users():
        while True:
            try:
                # Count active sessions (last 30 minutes)
                cutoff = datetime.now(timezone.utc) - timedelta(minutes=30)
                active_count = await db.user_sessions.count_documents({
                    "last_activity": {"$gte": cutoff.isoformat()},
                    "is_active": True
                })
                ACTIVE_USERS.set(active_count)
            except Exception as e:
                logging.error(f"Error updating active users metric: {e}")
            
            await asyncio.sleep(60)  # Update every minute
    
    # Start background task
    asyncio.create_task(update_active_users())
    logging.info("✅ Monitoring tasks started")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()