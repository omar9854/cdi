"""
Medical Coding System Models
ICD-10-AM Australian Coding Standards for Saudi Arabia
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
import uuid

# ========== Hospital Management ==========
class Hospital(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    code: str
    location: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class HospitalCreate(BaseModel):
    name: str
    code: str
    location: str

# ========== ICD-10-AM Codes ==========
class ICDCode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str  # e.g., "E11.9"
    description_ar: str
    description_en: str
    category: str  # e.g., "Endocrine"
    is_principal: bool = True  # Can be used as principal diagnosis
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ICDCodeCreate(BaseModel):
    code: str
    description_ar: str
    description_en: str
    category: str
    is_principal: bool = True

# ========== DRG Pricing ==========
class DRGPrice(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    drg_code: str  # e.g., "DRG-123"
    description_ar: str
    description_en: str
    weight: float  # Relative weight
    base_price: float  # Base price in SAR
    year: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DRGPriceCreate(BaseModel):
    drg_code: str
    description_ar: str
    description_en: str
    weight: float
    base_price: float
    year: int

# ========== Medical Case for Coding ==========
class DiagnosisCode(BaseModel):
    code: str
    description: str
    is_principal: bool = False
    is_complication: bool = False  # CC or MCC

class MedicalCase(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    case_number: str
    patient_id: str  # Anonymous patient identifier
    hospital_id: str
    admission_date: str
    discharge_date: str
    age: int
    gender: str
    
    # Assignment
    assigned_to: Optional[str] = None  # Coder user_id
    assigned_at: Optional[datetime] = None
    
    # Clinical Info
    chief_complaint: str
    clinical_summary: str
    procedures: List[str] = []
    
    # Coding Results
    principal_diagnosis: Optional[DiagnosisCode] = None
    secondary_diagnoses: List[DiagnosisCode] = []
    drg_code: Optional[str] = None
    drg_description: Optional[str] = None
    financial_value: Optional[float] = None
    
    # Timing
    coding_started_at: Optional[datetime] = None
    coding_completed_at: Optional[datetime] = None
    coding_duration_minutes: Optional[int] = None
    
    # Status
    status: str = "pending"  # pending, in_progress, completed, audited
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str  # Supervisor user_id

class MedicalCaseCreate(BaseModel):
    case_number: str
    patient_id: str
    hospital_id: str
    admission_date: str
    discharge_date: str
    age: int
    gender: str
    chief_complaint: str
    clinical_summary: str
    procedures: List[str] = []

class CodingSubmission(BaseModel):
    case_id: str
    principal_diagnosis: DiagnosisCode
    secondary_diagnoses: List[DiagnosisCode]
    drg_code: str
    drg_description: str
    financial_value: float

# ========== Audit System ==========
class AuditError(BaseModel):
    error_type: str  # undercoding, overcoding, poa_error, cc_mcc_error
    description: str
    icd_code: Optional[str] = None
    financial_impact: float = 0.0
    severity: str  # low, medium, high, critical

class AuditRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    case_id: str
    auditor_id: str
    coder_id: str
    
    # Original coding
    original_principal: str
    original_secondary: List[str]
    original_drg: str
    original_value: float
    
    # Audit findings
    errors: List[AuditError]
    total_errors: int
    has_critical_errors: bool = False
    
    # Corrected coding
    corrected_principal: Optional[str] = None
    corrected_secondary: Optional[List[str]] = None
    corrected_drg: Optional[str] = None
    corrected_value: Optional[float] = None
    
    # Financial impact
    financial_impact: float  # Difference in SAR
    impact_percentage: float
    
    # Recommendations
    recommendations: str
    risk_level: str  # low, medium, high, critical
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AuditSubmission(BaseModel):
    case_id: str
    errors: List[AuditError]
    corrected_principal: Optional[str] = None
    corrected_secondary: Optional[List[str]] = None
    corrected_drg: Optional[str] = None
    corrected_value: Optional[float] = None
    recommendations: str
    risk_level: str

# ========== Statistics Models ==========
class CoderStats(BaseModel):
    user_id: str
    full_name: str
    total_cases: int
    completed_today: int
    avg_coding_time: float
    daily_target: int
    completion_rate: float

class AuditorStats(BaseModel):
    user_id: str
    full_name: str
    total_audits: int
    total_errors_found: int
    avg_error_rate: float
    financial_impact_total: float

class DepartmentKPIs(BaseModel):
    total_cases: int
    completed_cases: int
    pending_cases: int
    in_progress_cases: int
    audited_cases: int
    
    total_coders: int
    active_coders_today: int
    
    total_auditors: int
    
    avg_coding_time: float
    total_financial_value: float
    
    error_rate: float
    financial_accuracy: float
