from fastapi import FastAPI, APIRouter, HTTPException, Depends, Header
from fastapi.responses import FileResponse, StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
from emergentintegrations.llm.chat import LlmChat, UserMessage
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

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# JWT Settings
SECRET_KEY = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Emergent LLM Key
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

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
    password_hash: str
    role: str = "user"  # "admin" or "user"
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserRegister(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    admin_code: Optional[str] = None  # كود سري للأدمن

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: Dict

class DoctorNote(BaseModel):
    text: str
    specialty: str

class ClinicalNote(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    doctor_notes: List[DoctorNote]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
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

IMPORTANT: Provide ALL responses in BOTH Arabic and English."""

    user_prompt = f"""Please review the following clinical notes as a CDI Specialist:

{formatted_notes}

Perform a Clinical Documentation Improvement review and provide:

1. **Diagnoses That Should Be Documented**: Based on the clinical findings in the notes, what diagnoses should be clearly documented? (with ICD-10-CM codes for reference only)

2. **Missing Documentation**: What specific clinical information is missing or incomplete? (e.g., severity, acuity, specificity, causal relationships)

3. **Documentation Gaps**: What gaps exist in the current documentation?

4. **Physician Queries**: What specific questions should be asked to the physicians to improve documentation?

5. **Recommendations**: Specific recommendations to improve the clinical documentation quality

Please respond in the following JSON format:
{{{{
  "diagnoses_to_document": [{{
    "diagnosis_ar": "التشخيص بالعربي",
    "diagnosis_en": "Diagnosis in English", 
    "icd_code": "Code (for reference)"
  }}],
  "missing_documentation": [{{
    "item_ar": "التوثيق الناقص بالعربي",
    "item_en": "Missing item in English"
  }}],
  "gaps_ar": ["ثغرة 1", "ثغرة 2"],
  "gaps_en": ["Gap 1", "Gap 2"],
  "queries_ar": ["استفسار 1 للطبيب", "استفسار 2"],
  "queries_en": ["Query 1 for physician", "Query 2"],
  "recommendations_ar": ["توصية 1 لتحسين التوثيق", "توصية 2"],
  "recommendations_en": ["Recommendation 1 for documentation improvement", "Recommendation 2"],
  "summary_ar": "ملخص شامل لمراجعة تحسين التوثيق السريري بالعربي",
  "summary_en": "Comprehensive CDI review summary in English"
}}}}"""

    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=str(uuid.uuid4()),
            system_message=system_message
        ).with_model("gemini", "gemini-2.5-pro")
        
        message = UserMessage(text=user_prompt)
        response = await chat.send_message(message)
        
        # Parse JSON response
        import json
        response_text = response.strip()
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        result = json.loads(response_text)
        return result
        
    except Exception as e:
        logging.error(f"Error analyzing with Gemini: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in analysis: {str(e)}")

# Health check route
@api_router.get("/")
async def root():
    return {"message": "مركز الترميز الطبي وتحسين التوثيق السريري", "status": "active"}

# Get specialties
@api_router.get("/specialties")
async def get_specialties():
    return MEDICAL_SPECIALTIES

# ========== Auth Routes ==========
@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserRegister):
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check if admin code is provided and valid
    role = "user"
    if user_data.admin_code:
        if user_data.admin_code == ADMIN_SECRET_CODE:
            role = "admin"
        else:
            raise HTTPException(status_code=400, detail="Invalid admin code")
    
    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        password_hash=hash_password(user_data.password),
        role=role
    )
    
    doc = user.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.users.insert_one(doc)
    
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
            "role": user.role
        }
    }

@api_router.post("/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    
    if not user or not verify_password(credentials.password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_access_token({
        "user_id": user['id'], 
        "email": user['email'],
        "role": user.get('role', 'user')
    })
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user['id'], 
            "email": user['email'], 
            "full_name": user['full_name'],
            "role": user.get('role', 'user')
        }
    }

# ========== Admin Routes ==========
async def require_admin(user: dict = Depends(get_current_user)):
    if user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

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

# ========== Analysis Routes ==========
@api_router.post("/analyze", response_model=Analysis)
async def analyze_note(request: AnalyzeRequest, user: dict = Depends(get_current_user)):
    note = await db.clinical_notes.find_one(
        {"id": request.note_id, "user_id": user['id']},
        {"_id": 0}
    )
    
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Analyze with Gemini
    result = await analyze_with_gemini(note['title'], note['doctor_notes'])
    
    # Create analysis record
    analysis = Analysis(
        note_id=request.note_id,
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
async def chat_with_ai(request: ChatRequest, user: dict = Depends(get_current_user)):
    # Get analysis
    analysis = await db.analyses.find_one(
        {"id": request.analysis_id, "user_id": user['id']},
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
        analysis_id=request.analysis_id,
        user_id=user['id'],
        role='user',
        message=request.message
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

Answer questions professionally, provide clarifications, and help improve the documentation. Respond in the same language as the user's question. Be concise and direct."""
    
    # Use analysis_id as session for continuity
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=request.analysis_id,
            system_message=system_message
        ).with_model("gemini", "gemini-2.5-pro")
        
        message = UserMessage(text=request.message)
        response = await chat.send_message(message)
        
        # Save assistant message
        assistant_msg = ChatMessage(
            analysis_id=request.analysis_id,
            user_id=user['id'],
            role='assistant',
            message=response
        )
        assistant_doc = assistant_msg.model_dump()
        assistant_doc['created_at'] = assistant_doc['created_at'].isoformat()
        await db.chat_messages.insert_one(assistant_doc)
        
        return {"message": response}
        
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

# ========== Include Router ==========
app.include_router(api_router)

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

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()