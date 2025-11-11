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

# Continued in next part...
