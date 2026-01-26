"""
Medical Coding System Routes
Comprehensive endpoints for supervisor, coder, and auditor workflows
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List, Optional
import pandas as pd
import io
from datetime import datetime, timezone, timedelta
import random
import logging

from coding_models import (
    Hospital, HospitalCreate,
    ICDCode, ICDCodeCreate,
    DRGPrice, DRGPriceCreate,
    MedicalCase, MedicalCaseCreate, CodingSubmission,
    AuditRecord, AuditSubmission, AuditError,
    CoderStats, AuditorStats, DepartmentKPIs
)

router = APIRouter(prefix="/coding", tags=["Medical Coding"])

# Database will be injected from main server.py
db = None

def set_db(database):
    global db
    db = database

# ========== Helper Functions ==========
async def get_current_user(token: str):
    """Get current user from token - will be implemented in server.py"""
    pass

async def require_coding_supervisor(user: dict):
    """Require user to be supervisor in coding department"""
    if user.get('department') != 'coding' or user.get('role') not in ['admin', 'supervisor']:
        raise HTTPException(status_code=403, detail="Coding supervisor access required")
    return user

async def require_coder(user: dict):
    """Require user to be coder in coding department"""
    if user.get('department') != 'coding' or user.get('coding_role') != 'coder':
        raise HTTPException(status_code=403, detail="Medical coder access required")
    return user

async def require_auditor(user: dict):
    """Require user to be auditor in coding department"""
    if user.get('department') != 'coding' or user.get('coding_role') != 'auditor':
        raise HTTPException(status_code=403, detail="Medical auditor access required")
    return user

# ========== Hospital Management (Supervisor) ==========
@router.get("/hospitals")
async def get_hospitals():
    """Get all hospitals"""
    hospitals = await db.hospitals.find({}, {"_id": 0}).to_list(1000)
    return {"hospitals": hospitals}

@router.post("/hospitals")
async def create_hospital(hospital: HospitalCreate):
    """Create new hospital"""
    # Check if code already exists
    existing = await db.hospitals.find_one({"code": hospital.code}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Hospital code already exists")
    
    hospital_doc = Hospital(**hospital.dict())
    doc = hospital_doc.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.hospitals.insert_one(doc)
    # Remove _id field for response
    doc.pop('_id', None)
    return {"message": "Hospital created successfully", "hospital": doc}

@router.put("/hospitals/{hospital_id}")
async def update_hospital(hospital_id: str, hospital: HospitalCreate):
    """Update hospital"""
    result = await db.hospitals.update_one(
        {"id": hospital_id},
        {"$set": hospital.dict()}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Hospital not found")
    
    return {"message": "Hospital updated successfully"}

@router.delete("/hospitals/{hospital_id}")
async def delete_hospital(hospital_id: str):
    """Delete hospital (soft delete by setting is_active=False)"""
    result = await db.hospitals.update_one(
        {"id": hospital_id},
        {"$set": {"is_active": False}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Hospital not found")
    
    return {"message": "Hospital deactivated successfully"}

@router.post("/hospitals/{hospital_id}/activate")
async def activate_hospital(hospital_id: str):
    """Reactivate a deactivated hospital"""
    result = await db.hospitals.update_one(
        {"id": hospital_id},
        {"$set": {"is_active": True}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Hospital not found")
    
    return {"message": "Hospital activated successfully"}

# ========== ICD-10-AM Code Management ==========
@router.get("/icd-codes")
async def get_icd_codes(search: Optional[str] = None, limit: int = 50):
    """Search ICD-10-AM codes"""
    query = {}
    if search:
        # Search in code, Arabic description, or English description
        query = {
            "$or": [
                {"code": {"$regex": search, "$options": "i"}},
                {"description_ar": {"$regex": search, "$options": "i"}},
                {"description_en": {"$regex": search, "$options": "i"}}
            ]
        }
    
    codes = await db.icd_codes.find(query, {"_id": 0}).limit(limit).to_list(limit)
    return {"codes": codes, "count": len(codes)}

@router.post("/icd-codes/upload")
async def upload_icd_codes(file: UploadFile = File(...)):
    """Upload ICD-10-AM codes from Excel file
    
    Expected columns: code, description_ar, description_en, category, is_principal
    """
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        required_cols = ['code', 'description_ar', 'description_en', 'category']
        if not all(col in df.columns for col in required_cols):
            raise HTTPException(
                status_code=400,
                detail=f"Excel must contain columns: {', '.join(required_cols)}"
            )
        
        # Add is_principal column if not exists
        if 'is_principal' not in df.columns:
            df['is_principal'] = True
        
        # Insert codes
        codes_added = 0
        for _, row in df.iterrows():
            code_doc = ICDCode(
                code=str(row['code']),
                description_ar=str(row['description_ar']),
                description_en=str(row['description_en']),
                category=str(row['category']),
                is_principal=bool(row['is_principal'])
            )
            
            doc = code_doc.model_dump()
            doc['created_at'] = doc['created_at'].isoformat()
            
            # Check if code already exists
            existing = await db.icd_codes.find_one({"code": doc['code']}, {"_id": 0})
            if not existing:
                await db.icd_codes.insert_one(doc)
                codes_added += 1
        
        return {
            "message": f"Successfully uploaded {codes_added} ICD codes",
            "total_rows": len(df),
            "codes_added": codes_added
        }
        
    except Exception as e:
        logging.error(f"Error uploading ICD codes: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")

# ========== DRG Price Management ==========
@router.get("/drg-prices")
async def get_drg_prices(year: Optional[int] = None):
    """Get DRG prices"""
    query = {}
    if year:
        query['year'] = year
    
    prices = await db.drg_prices.find(query, {"_id": 0}).to_list(1000)
    return {"prices": prices, "count": len(prices)}

@router.post("/drg-prices/upload")
async def upload_drg_prices(file: UploadFile = File(...)):
    """Upload DRG prices from Excel file
    
    Expected columns: drg_code, description_ar, description_en, weight, base_price, year
    """
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        required_cols = ['drg_code', 'description_ar', 'description_en', 'weight', 'base_price', 'year']
        if not all(col in df.columns for col in required_cols):
            raise HTTPException(
                status_code=400,
                detail=f"Excel must contain columns: {', '.join(required_cols)}"
            )
        
        # Insert prices
        prices_added = 0
        for _, row in df.iterrows():
            price_doc = DRGPrice(
                drg_code=str(row['drg_code']),
                description_ar=str(row['description_ar']),
                description_en=str(row['description_en']),
                weight=float(row['weight']),
                base_price=float(row['base_price']),
                year=int(row['year'])
            )
            
            doc = price_doc.model_dump()
            doc['created_at'] = doc['created_at'].isoformat()
            
            # Check if DRG already exists for this year
            existing = await db.drg_prices.find_one({
                "drg_code": doc['drg_code'],
                "year": doc['year']
            }, {"_id": 0})
            
            if not existing:
                await db.drg_prices.insert_one(doc)
                prices_added += 1
        
        return {
            "message": f"Successfully uploaded {prices_added} DRG prices",
            "total_rows": len(df),
            "prices_added": prices_added
        }
        
    except Exception as e:
        logging.error(f"Error uploading DRG prices: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")

# ========== Medical Cases Management (Supervisor) ==========
@router.post("/cases/manual")
async def create_case_manual(
    case_number: str,
    hospital_id: str,
    admission_days: int,
    assigned_coder_id: str,
    user_id: str,
    patient_id: str = None,
    chief_complaint: str = "إدخال يدوي",
    clinical_summary: str = "في انتظار الترميز"
):
    """Create single case manually and assign to specific coder"""
    import uuid
    from datetime import datetime, timezone, timedelta
    
    # Generate patient ID if not provided
    if not patient_id:
        patient_id = 'PT-' + str(uuid.uuid4())[:8].upper()
    
    # Calculate dates
    today = datetime.now(timezone.utc).date()
    admission_date = (today - timedelta(days=admission_days)).isoformat()
    discharge_date = today.isoformat()
    
    # Verify coder exists
    coder = await db.users.find_one(
        {"id": assigned_coder_id, "department": "coding", "coding_role": "coder"},
        {"_id": 0}
    )
    if not coder:
        raise HTTPException(status_code=404, detail="Coder not found")
    
    # Verify hospital exists
    hospital = await db.hospitals.find_one({"id": hospital_id}, {"_id": 0})
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")
    
    # Check if case number already exists
    existing = await db.medical_cases.find_one({"case_number": case_number}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Case number already exists")
    
    # Create case
    case_doc = {
        'id': str(uuid.uuid4()),
        'case_number': case_number,
        'patient_id': patient_id,
        'hospital_id': hospital_id,
        'admission_date': admission_date,
        'discharge_date': discharge_date,
        'age': 0,  # Will be updated later
        'gender': 'غير محدد',
        'chief_complaint': chief_complaint,
        'clinical_summary': clinical_summary,
        'procedures': [],
        'assigned_to': assigned_coder_id,
        'assigned_at': datetime.now(timezone.utc).isoformat(),
        'status': 'pending',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'created_by': user_id
    }
    
    await db.medical_cases.insert_one(case_doc)
    
    return {
        "message": f"Case {case_number} created and assigned to {coder['full_name']}",
        "case_id": case_doc['id'],
        "assigned_to": coder['full_name']
    }

@router.post("/cases/upload-excel")
async def upload_cases_excel(file: UploadFile = File(...), user_id: str = None):
    """Upload cases from Excel and distribute dynamically based on coder targets
    
    Expected columns: case_number, hospital_code, admission_days, patient_id (optional)
    """
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        required_cols = ['case_number', 'hospital_code', 'admission_days']
        if not all(col in df.columns for col in required_cols):
            raise HTTPException(
                status_code=400,
                detail=f"Excel must contain columns: {', '.join(required_cols)}"
            )
        
        # Get active coders with their daily targets
        coders = await db.users.find(
            {"department": "coding", "coding_role": "coder", "is_active": True},
            {"_id": 0}
        ).to_list(100)
        
        if not coders:
            raise HTTPException(status_code=400, detail="No active coders available")
        
        # Get today's assigned cases per coder
        today = datetime.now(timezone.utc).date()
        today_start = datetime.combine(today, datetime.min.time()).isoformat()
        
        coder_workload = {}
        for coder in coders:
            assigned_today = await db.medical_cases.count_documents({
                "assigned_to": coder['id'],
                "assigned_at": {"$gte": today_start}
            })
            daily_target = coder.get('daily_case_target', 10)
            remaining = max(0, daily_target - assigned_today)
            coder_workload[coder['id']] = {
                'coder': coder,
                'assigned_today': assigned_today,
                'daily_target': daily_target,
                'remaining': remaining
            }
        
        # Sort coders by remaining capacity (highest first)
        sorted_coders = sorted(coder_workload.items(), key=lambda x: x[1]['remaining'], reverse=True)
        
        cases_created = 0
        cases_skipped = 0
        distribution_log = []
        current_coder_index = 0
        
        for _, row in df.iterrows():
            case_number = str(row['case_number'])
            hospital_code = str(row['hospital_code'])
            admission_days = int(row['admission_days'])
            patient_id = str(row.get('patient_id', 'PT-' + str(uuid.uuid4())[:8].upper()))
            
            # Check if case exists
            existing = await db.medical_cases.find_one({"case_number": case_number}, {"_id": 0})
            if existing:
                cases_skipped += 1
                continue
            
            # Find hospital
            hospital = await db.hospitals.find_one({"code": hospital_code}, {"_id": 0})
            if not hospital:
                cases_skipped += 1
                continue
            
            # Assign to coder with capacity
            coder_assigned = False
            attempts = 0
            while not coder_assigned and attempts < len(sorted_coders):
                coder_id, workload = sorted_coders[current_coder_index]
                if workload['remaining'] > 0:
                    # Assign to this coder
                    admission_date = (datetime.now(timezone.utc).date() - timedelta(days=admission_days)).isoformat()
                    discharge_date = datetime.now(timezone.utc).date().isoformat()
                    
                    case_doc = {
                        'id': str(uuid.uuid4()),
                        'case_number': case_number,
                        'patient_id': patient_id,
                        'hospital_id': hospital['id'],
                        'admission_date': admission_date,
                        'discharge_date': discharge_date,
                        'age': 0,
                        'gender': 'غير محدد',
                        'chief_complaint': 'رفع Excel',
                        'clinical_summary': 'في انتظار الترميز',
                        'procedures': [],
                        'assigned_to': coder_id,
                        'assigned_at': datetime.now(timezone.utc).isoformat(),
                        'status': 'pending',
                        'created_at': datetime.now(timezone.utc).isoformat(),
                        'created_by': user_id or 'system'
                    }
                    
                    await db.medical_cases.insert_one(case_doc)
                    
                    # Update workload
                    workload['remaining'] -= 1
                    workload['assigned_today'] += 1
                    
                    distribution_log.append({
                        'case': case_number,
                        'coder': workload['coder']['full_name'],
                        'hospital': hospital['name']
                    })
                    
                    cases_created += 1
                    coder_assigned = True
                
                # Move to next coder (round-robin among those with capacity)
                current_coder_index = (current_coder_index + 1) % len(sorted_coders)
                attempts += 1
            
            if not coder_assigned:
                cases_skipped += 1
        
        return {
            "message": f"Successfully uploaded {cases_created} cases",
            "total_rows": len(df),
            "cases_created": cases_created,
            "cases_skipped": cases_skipped,
            "distribution": distribution_log[:10]  # Show first 10
        }
        
    except Exception as e:
        logging.error(f"Error uploading cases: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")

@router.post("/cases")
async def create_medical_case(case: MedicalCaseCreate, user_id: str):
    """Create new medical case for coding"""
    case_doc = MedicalCase(**case.dict(), created_by=user_id)
    doc = case_doc.model_dump()
    
    # Convert datetime fields to ISO format
    doc['created_at'] = doc['created_at'].isoformat()
    if doc.get('assigned_at'):
        doc['assigned_at'] = doc['assigned_at'].isoformat()
    if doc.get('coding_started_at'):
        doc['coding_started_at'] = doc['coding_started_at'].isoformat()
    if doc.get('coding_completed_at'):
        doc['coding_completed_at'] = doc['coding_completed_at'].isoformat()
    
    await db.medical_cases.insert_one(doc)
    return {"message": "Medical case created successfully", "case_id": doc['id']}

@router.get("/cases")
async def get_medical_cases(
    status: Optional[str] = None,
    hospital_id: Optional[str] = None,
    assigned_to: Optional[str] = None
):
    """Get medical cases with filters"""
    query = {}
    if status:
        query['status'] = status
    if hospital_id:
        query['hospital_id'] = hospital_id
    if assigned_to:
        query['assigned_to'] = assigned_to
    
    cases = await db.medical_cases.find(query, {"_id": 0}).to_list(1000)
    return {"cases": cases, "count": len(cases)}

@router.post("/cases/assign")
async def assign_cases_to_coders(distribution: str = "round_robin"):
    """Smart distribution of pending cases to available coders
    
    distribution options:
    - round_robin: Equal distribution
    - workload_based: Based on daily targets and current workload
    """
    # Get pending cases
    pending_cases = await db.medical_cases.find(
        {"status": "pending", "assigned_to": None},
        {"_id": 0}
    ).to_list(1000)
    
    if not pending_cases:
        return {"message": "No pending cases to assign", "assigned": 0}
    
    # Get active coders
    coders = await db.users.find(
        {"department": "coding", "coding_role": "coder", "is_active": True},
        {"_id": 0, "id": 1, "full_name": 1, "daily_case_target": 1}
    ).to_list(100)
    
    if not coders:
        raise HTTPException(status_code=400, detail="No active coders available")
    
    # Distribution logic
    assigned_count = 0
    if distribution == "round_robin":
        coder_index = 0
        for case in pending_cases:
            coder = coders[coder_index % len(coders)]
            
            await db.medical_cases.update_one(
                {"id": case['id']},
                {
                    "$set": {
                        "assigned_to": coder['id'],
                        "assigned_at": datetime.now(timezone.utc).isoformat(),
                        "status": "pending"
                    }
                }
            )
            
            assigned_count += 1
            coder_index += 1
    
    return {
        "message": f"Assigned {assigned_count} cases to {len(coders)} coders",
        "assigned": assigned_count,
        "coders": len(coders)
    }

@router.put("/cases/{case_id}/reassign/{coder_id}")
async def reassign_case(case_id: str, coder_id: str):
    """Reassign case to different coder"""
    # Verify coder exists
    coder = await db.users.find_one(
        {"id": coder_id, "department": "coding", "coding_role": "coder"},
        {"_id": 0}
    )
    if not coder:
        raise HTTPException(status_code=404, detail="Coder not found")
    
    result = await db.medical_cases.update_one(
        {"id": case_id},
        {
            "$set": {
                "assigned_to": coder_id,
                "assigned_at": datetime.now(timezone.utc).isoformat(),
                "status": "pending"
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Case not found")
    
    return {"message": "Case reassigned successfully"}

# ========== Coder Workspace ==========
@router.get("/my-cases")
async def get_my_cases(user_id: str, status: Optional[str] = None):
    """Get cases assigned to current coder"""
    query = {"assigned_to": user_id}
    if status:
        query['status'] = status
    
    cases = await db.medical_cases.find(query, {"_id": 0}).to_list(1000)
    return {"cases": cases, "count": len(cases)}

@router.post("/cases/{case_id}/start")
async def start_coding(case_id: str, user_id: str):
    """Start coding a case"""
    result = await db.medical_cases.update_one(
        {"id": case_id, "assigned_to": user_id},
        {
            "$set": {
                "status": "in_progress",
                "coding_started_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Case not found or not assigned to you")
    
    return {"message": "Coding started"}

@router.post("/cases/{case_id}/submit")
async def submit_coding(case_id: str, submission: CodingSubmission, user_id: str):
    """Submit completed coding"""
    # Verify case belongs to user
    case = await db.medical_cases.find_one(
        {"id": case_id, "assigned_to": user_id},
        {"_id": 0}
    )
    if not case:
        raise HTTPException(status_code=404, detail="Case not found or not assigned to you")
    
    # Calculate coding duration
    coding_started = datetime.fromisoformat(case.get('coding_started_at'))
    coding_completed = datetime.now(timezone.utc)
    duration_minutes = int((coding_completed - coding_started).total_seconds() / 60)
    
    # Update case with coding results
    result = await db.medical_cases.update_one(
        {"id": case_id},
        {
            "$set": {
                "principal_diagnosis": submission.principal_diagnosis.dict(),
                "secondary_diagnoses": [d.dict() for d in submission.secondary_diagnoses],
                "drg_code": submission.drg_code,
                "drg_description": submission.drg_description,
                "financial_value": submission.financial_value,
                "coding_completed_at": coding_completed.isoformat(),
                "coding_duration_minutes": duration_minutes,
                "status": "completed"
            }
        }
    )
    
    return {
        "message": "Coding submitted successfully",
        "duration_minutes": duration_minutes
    }

# ========== Auditor Workspace ==========
@router.get("/cases/for-audit")
async def get_cases_for_audit(sample_size: int = 10):
    """Get random sample of completed cases for audit (10% or specified size)"""
    # Get completed, non-audited cases
    completed_cases = await db.medical_cases.find(
        {"status": "completed"},
        {"_id": 0}
    ).to_list(1000)
    
    if not completed_cases:
        return {"cases": [], "count": 0}
    
    # Calculate 10% sample or use specified size
    sample_size = min(sample_size, max(1, int(len(completed_cases) * 0.1)))
    
    # Random sample
    sample_cases = random.sample(completed_cases, min(sample_size, len(completed_cases)))
    
    return {"cases": sample_cases, "count": len(sample_cases)}

@router.post("/audit/submit")
async def submit_audit(audit: AuditSubmission, auditor_id: str):
    """Submit audit findings"""
    # Get original case
    case = await db.medical_cases.find_one({"id": audit.case_id}, {"_id": 0})
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Calculate financial impact
    original_value = case.get('financial_value', 0)
    corrected_value = audit.corrected_value or original_value
    financial_impact = corrected_value - original_value
    impact_percentage = (financial_impact / original_value * 100) if original_value > 0 else 0
    
    # Count errors and check for critical
    total_errors = len(audit.errors)
    has_critical = any(e.severity == 'critical' for e in audit.errors)
    
    # Create audit record
    audit_doc = AuditRecord(
        case_id=audit.case_id,
        auditor_id=auditor_id,
        coder_id=case.get('assigned_to'),
        original_principal=case.get('principal_diagnosis', {}).get('code', ''),
        original_secondary=[d.get('code', '') for d in case.get('secondary_diagnoses', [])],
        original_drg=case.get('drg_code', ''),
        original_value=original_value,
        errors=[e.dict() for e in audit.errors],
        total_errors=total_errors,
        has_critical_errors=has_critical,
        corrected_principal=audit.corrected_principal,
        corrected_secondary=audit.corrected_secondary,
        corrected_drg=audit.corrected_drg,
        corrected_value=corrected_value,
        financial_impact=financial_impact,
        impact_percentage=impact_percentage,
        recommendations=audit.recommendations,
        risk_level=audit.risk_level
    )
    
    doc = audit_doc.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.audit_records.insert_one(doc)
    
    # Update case status
    await db.medical_cases.update_one(
        {"id": audit.case_id},
        {"$set": {"status": "audited"}}
    )
    
    return {
        "message": "Audit submitted successfully",
        "audit_id": doc['id'],
        "financial_impact": financial_impact,
        "total_errors": total_errors
    }

@router.get("/audits")
async def get_audits(coder_id: Optional[str] = None, risk_level: Optional[str] = None):
    """Get audit records with filters"""
    query = {}
    if coder_id:
        query['coder_id'] = coder_id
    if risk_level:
        query['risk_level'] = risk_level
    
    audits = await db.audit_records.find(query, {"_id": 0}).to_list(1000)
    return {"audits": audits, "count": len(audits)}

# ========== Statistics & KPIs ==========
@router.get("/stats/coders")
async def get_coder_statistics():
    """Get statistics for all coders"""
    coders = await db.users.find(
        {"department": "coding", "coding_role": "coder"},
        {"_id": 0}
    ).to_list(100)
    
    stats = []
    today = datetime.now(timezone.utc).date()
    
    for coder in coders:
        # Get total cases
        total_cases = await db.medical_cases.count_documents({"assigned_to": coder['id']})
        
        # Get completed today
        completed_today = await db.medical_cases.count_documents({
            "assigned_to": coder['id'],
            "status": "completed",
            "coding_completed_at": {
                "$gte": datetime.combine(today, datetime.min.time()).isoformat()
            }
        })
        
        # Get average coding time
        completed_cases = await db.medical_cases.find(
            {"assigned_to": coder['id'], "status": {"$in": ["completed", "audited"]}},
            {"_id": 0, "coding_duration_minutes": 1}
        ).to_list(1000)
        
        avg_time = sum(c.get('coding_duration_minutes', 0) for c in completed_cases) / len(completed_cases) if completed_cases else 0
        
        daily_target = coder.get('daily_case_target', 10)
        completion_rate = (completed_today / daily_target * 100) if daily_target > 0 else 0
        
        stats.append(CoderStats(
            user_id=coder['id'],
            full_name=coder['full_name'],
            total_cases=total_cases,
            completed_today=completed_today,
            avg_coding_time=round(avg_time, 2),
            daily_target=daily_target,
            completion_rate=round(completion_rate, 2)
        ).dict())
    
    return {"coders": stats}

@router.get("/stats/department")
async def get_department_kpis():
    """Get comprehensive KPIs for coding department"""
    # Case statistics
    total_cases = await db.medical_cases.count_documents({})
    completed_cases = await db.medical_cases.count_documents({"status": "completed"})
    pending_cases = await db.medical_cases.count_documents({"status": "pending"})
    in_progress_cases = await db.medical_cases.count_documents({"status": "in_progress"})
    audited_cases = await db.medical_cases.count_documents({"status": "audited"})
    
    # Staff statistics
    total_coders = await db.users.count_documents({"department": "coding", "coding_role": "coder"})
    total_auditors = await db.users.count_documents({"department": "coding", "coding_role": "auditor"})
    
    # Active coders today
    today = datetime.now(timezone.utc).date()
    active_coders = await db.medical_cases.distinct("assigned_to", {
        "coding_completed_at": {
            "$gte": datetime.combine(today, datetime.min.time()).isoformat()
        }
    })
    active_coders_today = len(active_coders)
    
    # Average coding time
    completed = await db.medical_cases.find(
        {"status": {"$in": ["completed", "audited"]}},
        {"_id": 0, "coding_duration_minutes": 1}
    ).to_list(10000)
    avg_coding_time = sum(c.get('coding_duration_minutes', 0) for c in completed) / len(completed) if completed else 0
    
    # Total financial value
    financial_values = await db.medical_cases.find(
        {"status": {"$in": ["completed", "audited"]}},
        {"_id": 0, "financial_value": 1}
    ).to_list(10000)
    total_financial_value = sum(c.get('financial_value', 0) for c in financial_values)
    
    # Audit statistics
    total_audits = await db.audit_records.count_documents({})
    if total_audits > 0:
        audits = await db.audit_records.find({}, {"_id": 0}).to_list(10000)
        total_errors = sum(a.get('total_errors', 0) for a in audits)
        error_rate = (total_errors / total_audits) if total_audits > 0 else 0
        
        # Financial accuracy
        total_impact = sum(abs(a.get('financial_impact', 0)) for a in audits)
        financial_accuracy = 100 - ((total_impact / total_financial_value * 100) if total_financial_value > 0 else 0)
    else:
        error_rate = 0
        financial_accuracy = 100
    
    kpis = DepartmentKPIs(
        total_cases=total_cases,
        completed_cases=completed_cases,
        pending_cases=pending_cases,
        in_progress_cases=in_progress_cases,
        audited_cases=audited_cases,
        total_coders=total_coders,
        active_coders_today=active_coders_today,
        total_auditors=total_auditors,
        avg_coding_time=round(avg_coding_time, 2),
        total_financial_value=round(total_financial_value, 2),
        error_rate=round(error_rate, 2),
        financial_accuracy=round(financial_accuracy, 2)
    )
    
    return kpis.dict()

@router.put("/users/{user_id}/daily-target")
async def update_daily_target(user_id: str, daily_target: int):
    """Update coder's daily case target"""
    result = await db.users.update_one(
        {"id": user_id, "department": "coding", "coding_role": "coder"},
        {"$set": {"daily_case_target": daily_target}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Coder not found")
    
    return {"message": "Daily target updated successfully"}

# ========== AI-Powered Coding Assistant ==========
@router.post("/ai/analyze-case")
async def ai_analyze_case(case_id: str):
    """Use AI to analyze case and suggest ICD codes"""
    try:
        # from coding_ai_helper import analyze_case_for_coding
        raise HTTPException(status_code=503, detail="Coding AI helper (Gemini) is disabled in offline mode")
        
        # Get case details
        case = await db.medical_cases.find_one({"id": case_id}, {"_id": 0})
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        
        # Get available ICD codes
        icd_codes = await db.icd_codes.find({}, {"_id": 0}).to_list(100)
        
        # Analyze with AI
        result = await analyze_case_for_coding(
            clinical_summary=case.get('clinical_summary', ''),
            chief_complaint=case.get('chief_complaint', ''),
            procedures=case.get('procedures', []),
            icd_codes=icd_codes
        )
        
        return result
        
    except Exception as e:
        logging.error(f"AI analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")

@router.post("/ai/search-icd")
async def ai_search_icd(query: str):
    """Smart ICD code search with AI"""
    try:
        # from coding_ai_helper import search_icd_smart
        raise HTTPException(status_code=503, detail="Smart ICD search (Gemini) is disabled in offline mode")
        
        # Get all ICD codes
        icd_codes = await db.icd_codes.find({}, {"_id": 0}).to_list(500)
        
        # Smart search
        results = await search_icd_smart(query, icd_codes)
        
        return {"codes": results, "count": len(results)}
        
    except Exception as e:
        logging.error(f"Smart search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ai/calculate-drg")
async def ai_calculate_drg(principal_code: str, secondary_codes: List[str] = []):
    """Calculate DRG and estimated value"""
    try:
        # from coding_ai_helper import calculate_drg_value
        raise HTTPException(status_code=503, detail="DRG value calculation (Gemini) is disabled in offline mode")
        
        # Get DRG prices
        drg_prices = await db.drg_prices.find({}, {"_id": 0}).to_list(100)
        
        # Calculate
        result = await calculate_drg_value(principal_code, secondary_codes, drg_prices)
        
        return result
        
    except Exception as e:
        logging.error(f"DRG calculation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

