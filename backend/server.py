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

# ========== Models ==========
class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    full_name: str
    password_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserRegister(BaseModel):
    email: EmailStr
    full_name: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: Dict

class ClinicalNote(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    notes_text: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ClinicalNoteCreate(BaseModel):
    title: str
    notes_text: str

class Analysis(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    note_id: str
    user_id: str
    primary_diagnoses: List[Dict[str, str]]  # [{"diagnosis": "", "icd_code": ""}]
    secondary_diagnoses: List[Dict[str, str]]
    gaps: List[str]
    queries_for_doctor: List[str]
    full_analysis: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AnalyzeRequest(BaseModel):
    note_id: str

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

async def analyze_with_gemini(notes_text: str) -> Dict:
    """Analyze clinical notes using Gemini AI"""
    
    system_message = """أنت خبير في التوثيق السريري والترميز الطبي متخصص في نظام ICD-10-CM.

مهمتك:
1. تحليل الملاحظات السريرية المقدمة
2. تحديد التشخيصات الرئيسية والثانوية
3. إيجاد أكواد ICD-10-CM المناسبة لكل تشخيص
4. تحديد الثغرات في التوثيق
5. إنشاء استفسارات محددة للطبيب

يجب أن تكون دقيقاً ومهنياً وتقدم معلومات قابلة للتطبيق."""

    user_prompt = f"""يرجى تحليل الملاحظات السريرية التالية:

{notes_text}

يرجى تقديم:
1. التشخيصات الرئيسية مع أكواد ICD-10-CM
2. التشخيصات الثانوية مع أكواد ICD-10-CM
3. الثغرات في التوثيق
4. استفسارات محددة للطبيب

الرجاء تقديم الإجابة بصيغة JSON التالية:
{{
  "primary_diagnoses": [{"diagnosis": "اسم التشخيص", "icd_code": "الكود"}],
  "secondary_diagnoses": [{"diagnosis": "اسم التشخيص", "icd_code": "الكود"}],
  "gaps": ["ثغرة 1", "ثغرة 2"],
  "queries_for_doctor": ["استفسار 1", "استفسار 2"],
  "summary": "ملخص شامل للتحليل"
}}"""

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
        # Try to extract JSON from response
        response_text = response.strip()
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        result = json.loads(response_text)
        return result
        
    except Exception as e:
        logging.error(f"Error analyzing with Gemini: {str(e)}")
        raise HTTPException(status_code=500, detail=f"خطأ في التحليل: {str(e)}")

# Health check route
@api_router.get("/")
async def root():
    return {"message": "مركز الترميز الطبي وتحسين التوثيق السريري", "status": "active"}

# ========== Auth Routes ==========
@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserRegister):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="البريد الإلكتروني مسجل مسبقاً")
    
    # Create user
    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        password_hash=hash_password(user_data.password)
    )
    
    doc = user.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.users.insert_one(doc)
    
    # Create token
    token = create_access_token({"user_id": user.id, "email": user.email})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "email": user.email, "full_name": user.full_name}
    }

@api_router.post("/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    
    if not user or not verify_password(credentials.password, user['password_hash']):
        raise HTTPException(status_code=401, detail="البريد الإلكتروني أو كلمة المرور غير صحيحة")
    
    token = create_access_token({"user_id": user['id'], "email": user['email']})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user['id'], "email": user['email'], "full_name": user['full_name']}
    }

# ========== Notes Routes ==========
@api_router.post("/notes", response_model=ClinicalNote)
async def create_note(note_data: ClinicalNoteCreate, user: dict = Depends(get_current_user)):
    note = ClinicalNote(
        user_id=user['id'],
        title=note_data.title,
        notes_text=note_data.notes_text
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
        raise HTTPException(status_code=404, detail="الملاحظة غير موجودة")
    
    if isinstance(note['created_at'], str):
        note['created_at'] = datetime.fromisoformat(note['created_at'])
    
    return note

# ========== Analysis Routes ==========
@api_router.post("/analyze", response_model=Analysis)
async def analyze_note(request: AnalyzeRequest, user: dict = Depends(get_current_user)):
    # Get the note
    note = await db.clinical_notes.find_one(
        {"id": request.note_id, "user_id": user['id']},
        {"_id": 0}
    )
    
    if not note:
        raise HTTPException(status_code=404, detail="الملاحظة غير موجودة")
    
    # Analyze with Gemini
    result = await analyze_with_gemini(note['notes_text'])
    
    # Create analysis record
    analysis = Analysis(
        note_id=request.note_id,
        user_id=user['id'],
        primary_diagnoses=result.get('primary_diagnoses', []),
        secondary_diagnoses=result.get('secondary_diagnoses', []),
        gaps=result.get('gaps', []),
        queries_for_doctor=result.get('queries_for_doctor', []),
        full_analysis=result.get('summary', '')
    )
    
    doc = analysis.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
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
    # Get all analyses with note info
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

# ========== Export Routes ==========
@api_router.get("/export/pdf/{analysis_id}")
async def export_pdf(analysis_id: str, user: dict = Depends(get_current_user)):
    analysis = await db.analyses.find_one(
        {"id": analysis_id, "user_id": user['id']},
        {"_id": 0}
    )
    
    if not analysis:
        raise HTTPException(status_code=404, detail="التحليل غير موجود")
    
    note = await db.clinical_notes.find_one(
        {"id": analysis['note_id']},
        {"_id": 0}
    )
    
    # Create PDF in memory
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Container for elements
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1e40af'),
        alignment=TA_CENTER,
        spaceAfter=30
    )
    
    elements.append(Paragraph("تقرير التحليل السريري", title_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Note title
    elements.append(Paragraph(f"<b>عنوان الملاحظة:</b> {note.get('title', '')}", styles['Normal']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Primary Diagnoses
    elements.append(Paragraph("<b>التشخيصات الرئيسية:</b>", styles['Heading2']))
    for diag in analysis.get('primary_diagnoses', []):
        elements.append(Paragraph(f"• {diag.get('diagnosis', '')} - {diag.get('icd_code', '')}", styles['Normal']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Secondary Diagnoses
    elements.append(Paragraph("<b>التشخيصات الثانوية:</b>", styles['Heading2']))
    for diag in analysis.get('secondary_diagnoses', []):
        elements.append(Paragraph(f"• {diag.get('diagnosis', '')} - {diag.get('icd_code', '')}", styles['Normal']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Gaps
    elements.append(Paragraph("<b>الثغرات في التوثيق:</b>", styles['Heading2']))
    for gap in analysis.get('gaps', []):
        elements.append(Paragraph(f"• {gap}", styles['Normal']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Queries
    elements.append(Paragraph("<b>استفسارات للطبيب:</b>", styles['Heading2']))
    for query in analysis.get('queries_for_doctor', []):
        elements.append(Paragraph(f"• {query}", styles['Normal']))
    
    doc.build(elements)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=analysis_{analysis_id}.pdf"}
    )

@api_router.get("/export/excel/{analysis_id}")
async def export_excel(analysis_id: str, user: dict = Depends(get_current_user)):
    user = await get_current_user(authorization)
    
    analysis = await db.analyses.find_one(
        {"id": analysis_id, "user_id": user['id']},
        {"_id": 0}
    )
    
    if not analysis:
        raise HTTPException(status_code=404, detail="التحليل غير موجود")
    
    note = await db.clinical_notes.find_one(
        {"id": analysis['note_id']},
        {"_id": 0}
    )
    
    # Create workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "تحليل سريري"
    
    # Headers
    header_fill = PatternFill(start_color="1e40af", end_color="1e40af", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    
    ws['A1'] = 'عنوان الملاحظة'
    ws['B1'] = note.get('title', '')
    ws['A1'].fill = header_fill
    ws['A1'].font = header_font
    
    # Primary Diagnoses
    row = 3
    ws[f'A{row}'] = 'التشخيصات الرئيسية'
    ws[f'A{row}'].fill = header_fill
    ws[f'A{row}'].font = header_font
    row += 1
    
    ws[f'A{row}'] = 'التشخيص'
    ws[f'B{row}'] = 'كود ICD-10'
    ws[f'A{row}'].fill = PatternFill(start_color="3b82f6", end_color="3b82f6", fill_type="solid")
    ws[f'B{row}'].fill = PatternFill(start_color="3b82f6", end_color="3b82f6", fill_type="solid")
    row += 1
    
    for diag in analysis.get('primary_diagnoses', []):
        ws[f'A{row}'] = diag.get('diagnosis', '')
        ws[f'B{row}'] = diag.get('icd_code', '')
        row += 1
    
    # Secondary Diagnoses
    row += 1
    ws[f'A{row}'] = 'التشخيصات الثانوية'
    ws[f'A{row}'].fill = header_fill
    ws[f'A{row}'].font = header_font
    row += 1
    
    ws[f'A{row}'] = 'التشخيص'
    ws[f'B{row}'] = 'كود ICD-10'
    ws[f'A{row}'].fill = PatternFill(start_color="3b82f6", end_color="3b82f6", fill_type="solid")
    ws[f'B{row}'].fill = PatternFill(start_color="3b82f6", end_color="3b82f6", fill_type="solid")
    row += 1
    
    for diag in analysis.get('secondary_diagnoses', []):
        ws[f'A{row}'] = diag.get('diagnosis', '')
        ws[f'B{row}'] = diag.get('icd_code', '')
        row += 1
    
    # Gaps
    row += 1
    ws[f'A{row}'] = 'الثغرات'
    ws[f'A{row}'].fill = header_fill
    ws[f'A{row}'].font = header_font
    row += 1
    
    for gap in analysis.get('gaps', []):
        ws[f'A{row}'] = gap
        row += 1
    
    # Queries
    row += 1
    ws[f'A{row}'] = 'استفسارات للطبيب'
    ws[f'A{row}'].fill = header_fill
    ws[f'A{row}'].font = header_font
    row += 1
    
    for query in analysis.get('queries_for_doctor', []):
        ws[f'A{row}'] = query
        row += 1
    
    # Adjust column widths
    ws.column_dimensions['A'].width = 50
    ws.column_dimensions['B'].width = 20
    
    # Save to buffer
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