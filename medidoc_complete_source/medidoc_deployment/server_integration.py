"""
MediDoc AI - Server Integration Patch
Apply this to server.py to integrate the new CDI analysis system
"""

# ============================================
# ADD THESE IMPORTS AT THE TOP OF server.py
# ============================================

# from local_llm import analyze_clinical_notes, chat_with_context, check_model_health
# from drg_lookup import get_drg_lookup, DRGLookup
# from cdi_endpoints import cdi_router

# ============================================
# ADD THIS LINE AFTER app = FastAPI(...)
# ============================================

# app.include_router(cdi_router)

# ============================================
# REPLACE analyze_with_ai FUNCTION WITH THIS
# ============================================

async def analyze_with_ai(notes_text: str, doctor_notes: list, provider: str = 'local') -> dict:
    """
    Analyze clinical notes using local LLM (Qwen2.5-72B)
    Acts as Senior Medical Auditor for CDI
    """
    import logging
    from local_llm import analyze_clinical_notes
    
    logger = logging.getLogger(__name__)
    
    # Format notes
    formatted_notes = "\n\n".join([
        f"**{note['specialty']}**:\n{note['text']}"
        for note in doctor_notes
    ])
    
    logger.info("🏥 Using Senior Medical Auditor AI for CDI analysis...")
    
    try:
        result = analyze_clinical_notes(formatted_notes)
        
        # Convert to legacy format for backward compatibility
        legacy_result = convert_to_legacy_format(result)
        
        logger.info(f"✅ CDI analysis complete - Principal: {result.get('principal_diagnosis', {}).get('icd_code', 'N/A')}")
        return legacy_result
        
    except Exception as e:
        logger.error(f"❌ CDI analysis error: {str(e)}")
        raise


def convert_to_legacy_format(result: dict) -> dict:
    """
    Convert new CDI format to legacy format for backward compatibility
    """
    diagnoses = []
    
    # Add principal diagnosis
    principal = result.get('principal_diagnosis', {})
    if principal:
        diagnoses.append({
            "diagnosis_ar": principal.get('diagnosis_ar', ''),
            "diagnosis_en": principal.get('diagnosis_en', ''),
            "icd_code": principal.get('icd_code', ''),
            "type": "principal",
            "clinical_evidence": principal.get('evidence', ''),
            "drg_code": principal.get('drg_code', ''),
            "relative_weight": principal.get('relative_weight', 0),
            "estimated_cost": principal.get('estimated_cost', 0)
        })
    
    # Add secondary diagnoses
    for secondary in result.get('secondary_diagnoses', []):
        diagnoses.append({
            "diagnosis_ar": secondary.get('diagnosis_ar', ''),
            "diagnosis_en": secondary.get('diagnosis_en', ''),
            "icd_code": secondary.get('icd_code', ''),
            "type": f"secondary ({secondary.get('category', 'other')})",
            "clinical_evidence": secondary.get('evidence', ''),
            "affects_drg": secondary.get('affects_drg', False)
        })
    
    # Build queries with evidence
    queries_ar = []
    queries_en = []
    for q in result.get('physician_queries', []):
        queries_ar.append(q.get('query_ar', ''))
        queries_en.append(q.get('query_en', ''))
    
    # Build gaps
    gaps_ar = [g.get('gap_ar', '') for g in result.get('documentation_gaps', [])]
    gaps_en = [g.get('gap_en', '') for g in result.get('documentation_gaps', [])]
    
    return {
        "diagnoses_to_document": diagnoses,
        "missing_documentation": result.get('documentation_gaps', []),
        "gaps_ar": gaps_ar,
        "gaps_en": gaps_en,
        "queries_ar": queries_ar,
        "queries_en": queries_en,
        "recommendations_ar": ["مراجعة التوثيق مع المدقق الطبي"],
        "recommendations_en": ["Review documentation with medical auditor"],
        "summary_ar": result.get('summary_ar', ''),
        "summary_en": result.get('summary_en', ''),
        "drg_summary": result.get('drg_summary', {})
    }


# ============================================
# REPLACE chat_with_ai_by_path FUNCTION WITH THIS
# ============================================

async def chat_with_ai_by_path(
    analysis_id: str,
    user_question: str,
    context: str,
    system_message: str,
    previous_messages: list = None
) -> str:
    """
    CDI-focused chat using local LLM
    Only answers questions related to clinical documentation improvement
    """
    import logging
    from local_llm import chat_with_context
    
    logger = logging.getLogger(__name__)
    
    logger.info("💬 Using Senior Medical Auditor AI for chat...")
    
    try:
        history = []
        if previous_messages:
            for msg in previous_messages:
                history.append({
                    "role": msg.get('role', 'user'),
                    "message": msg.get('message', msg.get('question', ''))
                })
        
        response = chat_with_context(
            message=user_question,
            context=f"{system_message}\n\n{context}",
            history=history
        )
        
        logger.info("✅ CDI chat response generated")
        return response
        
    except Exception as e:
        logger.error(f"❌ CDI chat error: {str(e)}")
        raise


# ============================================
# ADD THIS ENDPOINT FOR DRG LOOKUP
# ============================================

# @api_router.get("/drg/lookup/{code}")
# async def lookup_drg(code: str, code_type: str = "drg"):
#     """Look up DRG information by code"""
#     from drg_lookup import get_drg_lookup
#     
#     drg = get_drg_lookup()
#     
#     if code_type == "icd":
#         result = drg.lookup_by_icd(code)
#     else:
#         result = drg.lookup_by_drg(code)
#     
#     if not result:
#         raise HTTPException(status_code=404, detail=f"Code not found: {code}")
#     
#     return result

# ============================================
# ADD THIS ENDPOINT FOR MODEL HEALTH
# ============================================

# @api_router.get("/model/health")
# async def model_health():
#     """Check model health status"""
#     from local_llm import check_model_health
#     return check_model_health()
