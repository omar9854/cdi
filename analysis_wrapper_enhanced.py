"""
Analysis wrapper - Routes all analysis to local_llm module
Enhanced version with better evidence extraction and query generation
"""

from local_llm import analyze_clinical_notes
import logging

logger = logging.getLogger(__name__)


async def analyze_with_local_llm(notes_text: str, doctor_notes: list) -> dict:
    """
    Analyze clinical notes using LOCAL Qwen2.5-72B AI model (100% Offline)
    Enhanced for better accuracy in:
    - Principal diagnosis identification
    - Evidence extraction
    - Documentation gaps
    - Physician queries with supporting evidence
    """
    
    # Format doctor notes with specialties
    formatted_parts = []
    for note in doctor_notes:
        specialty = note.get('specialty', 'General')
        text = note.get('text', '')
        formatted_parts.append(f"**{specialty}**:\n{text}")
    
    formatted_notes = "\n\n".join(formatted_parts)
    
    try:
        logger.info("🏥 Starting enhanced CDI analysis with Qwen2.5-72B...")
        
        # Use local_llm module for analysis
        result = analyze_clinical_notes(formatted_notes, hospital_type="A")
        
        # Convert to expected format with enhanced fields
        formatted_result = {
            "diagnoses_to_document": [],
            "missing_documentation": [],
            "gaps_ar": [],
            "gaps_en": [],
            "queries_ar": [],
            "queries_en": [],
            "recommendations_ar": result.get("recommendations_ar", []),
            "recommendations_en": result.get("recommendations_en", []),
            "summary_ar": result.get("summary_ar", ""),
            "summary_en": result.get("summary_en", "")
        }
        
        # Add principal diagnosis with evidence
        principal = result.get("principal_diagnosis", {})
        if principal:
            formatted_result["diagnoses_to_document"].append({
                "diagnosis_ar": principal.get("diagnosis_ar", ""),
                "diagnosis_en": principal.get("diagnosis_en", ""),
                "icd_code": principal.get("icd_code", ""),
                "type": "principal",
                "severity": "",
                "clinical_evidence": principal.get("evidence_ar", "") + " | " + principal.get("evidence_en", ""),
                "evidence_ar": principal.get("evidence_ar", ""),
                "evidence_en": principal.get("evidence_en", ""),
                "drg_code": principal.get("drg_code", ""),
                "drg_cost": principal.get("drg_cost", ""),
                "drg_description": principal.get("drg_description", "")
            })
        
        # Add secondary diagnoses with evidence
        for diag in result.get("secondary_diagnoses", []):
            formatted_result["diagnoses_to_document"].append({
                "diagnosis_ar": diag.get("diagnosis_ar", ""),
                "diagnosis_en": diag.get("diagnosis_en", ""),
                "icd_code": diag.get("icd_code", ""),
                "type": diag.get("category", "secondary"),
                "severity": "",
                "clinical_evidence": diag.get("evidence_ar", "") + " | " + diag.get("evidence_en", ""),
                "evidence_ar": diag.get("evidence_ar", ""),
                "evidence_en": diag.get("evidence_en", ""),
                "drg_code": diag.get("drg_code", ""),
                "drg_cost": diag.get("drg_cost", ""),
                "affects_drg": diag.get("affects_drg", False)
            })
        
        # Add documentation gaps with clinical indicators
        for gap in result.get("documentation_gaps", []):
            formatted_result["gaps_ar"].append(gap.get("gap_ar", ""))
            formatted_result["gaps_en"].append(gap.get("gap_en", ""))
            formatted_result["missing_documentation"].append({
                "item_ar": gap.get("gap_ar", ""),
                "item_en": gap.get("gap_en", ""),
                "clinical_indicator": gap.get("clinical_indicator", ""),
                "missing_info": gap.get("missing_info", ""),
                "impact": gap.get("impact_en", gap.get("impact_ar", ""))
            })
        
        # Add physician queries with evidence (Enhanced)
        for query in result.get("physician_queries", []):
            # Format Arabic query with evidence
            query_ar = query.get("query_ar", "")
            evidence = query.get("evidence_from_notes", "")
            target = query.get("target_diagnosis", "")
            
            if evidence and not evidence in query_ar:
                full_query_ar = f"استفسار حول: {target}\n"
                full_query_ar += f"الدليل من الملاحظات: {evidence}\n"
                full_query_ar += f"السؤال: {query_ar}"
            else:
                full_query_ar = query_ar
            
            formatted_result["queries_ar"].append(full_query_ar)
            
            # Format English query with evidence
            query_en = query.get("query_en", "")
            if evidence and not evidence in query_en:
                full_query_en = f"Query regarding: {target}\n"
                full_query_en += f"Evidence from notes: {evidence}\n"
                full_query_en += f"Question: {query_en}"
            else:
                full_query_en = query_en
            
            formatted_result["queries_en"].append(full_query_en)
        
        # Add recommendations if missing
        if not formatted_result["recommendations_ar"]:
            formatted_result["recommendations_ar"] = ["مراجعة التشخيصات المقترحة", "الرد على الاستفسارات"]
        if not formatted_result["recommendations_en"]:
            formatted_result["recommendations_en"] = ["Review suggested diagnoses", "Respond to queries"]
        
        logger.info(f"✅ Enhanced analysis complete: {len(formatted_result['diagnoses_to_document'])} diagnoses, {len(formatted_result['queries_ar'])} queries")
        return formatted_result
        
    except Exception as e:
        logger.error(f"Error in enhanced analysis: {str(e)}")
        raise
