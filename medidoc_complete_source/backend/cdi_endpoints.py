"""
MediDoc AI - API Endpoints for CDI Analysis
Integration module for server.py
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict
import logging

from local_llm import analyze_clinical_notes, chat_with_context, check_model_health
from drg_lookup import get_drg_lookup

logger = logging.getLogger(__name__)

# Router for CDI endpoints
cdi_router = APIRouter(prefix="/api/cdi", tags=["CDI Analysis"])


class AnalysisRequest(BaseModel):
    note_id: str
    clinical_notes: Optional[str] = None


class AnalysisResponse(BaseModel):
    id: str
    note_id: str
    principal_diagnosis: Dict
    secondary_diagnoses: List[Dict]
    documentation_gaps: List[Dict]
    physician_queries: List[Dict]
    drg_summary: Dict
    summary_ar: str
    summary_en: str
    created_at: str


class ChatRequest(BaseModel):
    analysis_id: str
    message: str


class ChatResponse(BaseModel):
    message: str
    role: str


class DRGLookupRequest(BaseModel):
    code: str
    code_type: str = "drg"  # "drg" or "icd"


class DRGLookupResponse(BaseModel):
    drg_code: str
    description: str
    relative_weight: float
    estimated_cost: float


@cdi_router.post("/analyze", response_model=AnalysisResponse)
async def perform_cdi_analysis(request: AnalysisRequest):
    """
    Perform CDI analysis on clinical notes
    Returns structured analysis with diagnoses, evidence, and DRG costs
    """
    try:
        logger.info(f"📋 Starting CDI analysis for note: {request.note_id}")
        
        # Get clinical notes (from request or database)
        clinical_notes = request.clinical_notes
        if not clinical_notes:
            # TODO: Fetch from database
            raise HTTPException(status_code=400, detail="Clinical notes required")
        
        # Perform analysis
        result = analyze_clinical_notes(clinical_notes)
        
        # Add metadata
        from datetime import datetime, timezone
        from uuid import uuid4
        
        response = {
            "id": str(uuid4()),
            "note_id": request.note_id,
            "principal_diagnosis": result.get("principal_diagnosis", {}),
            "secondary_diagnoses": result.get("secondary_diagnoses", []),
            "documentation_gaps": result.get("documentation_gaps", []),
            "physician_queries": result.get("physician_queries", []),
            "drg_summary": result.get("drg_summary", {}),
            "summary_ar": result.get("summary_ar", ""),
            "summary_en": result.get("summary_en", ""),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"✅ CDI analysis complete for note: {request.note_id}")
        return response
        
    except Exception as e:
        logger.error(f"❌ CDI analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@cdi_router.post("/chat", response_model=ChatResponse)
async def cdi_chat(request: ChatRequest):
    """
    Chat with CDI specialist about an analysis
    Only answers questions related to clinical documentation improvement
    """
    try:
        logger.info(f"💬 CDI chat for analysis: {request.analysis_id}")
        
        # TODO: Get context from database based on analysis_id
        context = f"Analysis ID: {request.analysis_id}"
        
        # Generate response
        response = chat_with_context(
            message=request.message,
            context=context,
            history=[]
        )
        
        return {
            "message": response,
            "role": "assistant"
        }
        
    except Exception as e:
        logger.error(f"❌ CDI chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@cdi_router.get("/drg/lookup/{code}")
async def lookup_drg(code: str, code_type: str = "drg"):
    """
    Look up DRG information by code
    
    Args:
        code: DRG code (e.g., K60A) or ICD code (e.g., E11.65)
        code_type: "drg" or "icd"
    """
    try:
        drg = get_drg_lookup()
        
        if code_type == "icd":
            result = drg.lookup_by_icd(code)
        else:
            result = drg.lookup_by_drg(code)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Code not found: {code}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ DRG lookup error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lookup failed: {str(e)}")


@cdi_router.get("/drg/calculate")
async def calculate_drg_cost(drg_code: str, cc_count: int = 0):
    """
    Calculate DRG cost with CC adjustments
    
    Args:
        drg_code: DRG code
        cc_count: Number of comorbidities/complications
    """
    try:
        drg = get_drg_lookup()
        result = drg.calculate_cost(drg_code, cc_count)
        return result
        
    except Exception as e:
        logger.error(f"❌ DRG calculation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Calculation failed: {str(e)}")


@cdi_router.get("/drg/search")
async def search_drg(query: str):
    """Search DRG by description or code"""
    try:
        drg = get_drg_lookup()
        results = drg.search_drg(query)
        return {"results": results}
        
    except Exception as e:
        logger.error(f"❌ DRG search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@cdi_router.post("/drg/load-pricelist")
async def load_drg_pricelist(file_path: str, base_rate: float = 5000.0):
    """
    Load DRG price list from file
    
    Args:
        file_path: Path to Excel/CSV file
        base_rate: Base rate for cost calculation
    """
    try:
        drg = get_drg_lookup()
        drg.set_base_rate(base_rate)
        
        success = drg.load_from_file(file_path)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to load file")
        
        return {
            "message": "Price list loaded successfully",
            "drg_count": len(drg.drg_data),
            "base_rate": base_rate
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Price list load error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Load failed: {str(e)}")


@cdi_router.get("/model/health")
async def model_health():
    """Check model health status"""
    return check_model_health()


@cdi_router.get("/icd/search")
async def search_icd(query: str):
    """Search ICD-10-AM codes"""
    from icd10am_codes import search_icd_codes
    results = search_icd_codes(query)
    return {"results": results}


@cdi_router.get("/icd/{code}")
async def get_icd_info(code: str):
    """Get ICD-10-AM code information"""
    from icd10am_codes import get_icd_info
    info = get_icd_info(code)
    if not info:
        raise HTTPException(status_code=404, detail=f"ICD code not found: {code}")
    return {"code": code, **info}
