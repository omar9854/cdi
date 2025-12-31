"""
Analysis wrapper - Routes all analysis to local_llm module
This is a bridge between the old API format and new local_llm module
"""

from local_llm import analyze_clinical_notes
import logging

logger = logging.getLogger(__name__)


async def analyze_with_local_llm(notes_text: str, doctor_notes: list) -> dict:
    """
    Analyze clinical notes using LOCAL Qwen2.5-72B AI model (100% Offline)
    Uses local_llm module with A100 GPU for inference
    """
    
    # Format doctor notes with specialties
    formatted_parts = []
    for note in doctor_notes:
        specialty = note.get('specialty', 'General')
        text = note.get('text', '')
        formatted_parts.append(f"**{specialty}**:\n{text}")
    
    formatted_notes = "\n\n".join(formatted_parts)
    
    try:
        logger.info("Starting analysis with Qwen2.5-72B Local AI...")
        
        # Use local_llm module for analysis
        result = analyze_clinical_notes(formatted_notes, hospital_type="A")
        
        # Convert to expected format
        formatted_result = {
            "diagnoses_to_document": [],
            "missing_documentation": [],
            "gaps_ar": [],
            "gaps_en": [],
            "queries_ar": [],
            "queries_en": [],
            "recommendations_ar": [],
            "recommendations_en": [],
            "summary_ar": result.get("summary_ar", ""),
            "summary_en": result.get("summary_en", "")
        }
        
        # Add principal diagnosis
        principal = result.get("principal_diagnosis", {})
        if principal:
            formatted_result["diagnoses_to_document"].append({
                "diagnosis_ar": principal.get("diagnosis_ar", ""),
                "diagnosis_en": principal.get("diagnosis_en", ""),
                "icd_code": principal.get("icd_code", ""),
                "type": "principal",
                "severity": "",
                "clinical_evidence": principal.get("evidence_en", principal.get("evidence_ar", "")),
                "drg_code": principal.get("drg_code", ""),
                "drg_cost": principal.get("drg_cost", "")
            })
        
        # Add secondary diagnoses
        for diag in result.get("secondary_diagnoses", []):
            formatted_result["diagnoses_to_document"].append({
                "diagnosis_ar": diag.get("diagnosis_ar", ""),
                "diagnosis_en": diag.get("diagnosis_en", ""),
                "icd_code": diag.get("icd_code", ""),
                "type": diag.get("category", "secondary"),
                "severity": "",
                "clinical_evidence": diag.get("evidence_en", diag.get("evidence_ar", "")),
                "drg_code": diag.get("drg_code", ""),
                "drg_cost": diag.get("drg_cost", "")
            })
        
        # Add documentation gaps
        for gap in result.get("documentation_gaps", []):
            formatted_result["gaps_ar"].append(gap.get("gap_ar", ""))
            formatted_result["gaps_en"].append(gap.get("gap_en", ""))
            formatted_result["missing_documentation"].append({
                "item_ar": gap.get("gap_ar", ""),
                "item_en": gap.get("gap_en", ""),
                "impact": gap.get("impact_en", "")
            })
        
        # Add physician queries
        for query in result.get("physician_queries", []):
            formatted_result["queries_ar"].append(query.get("query_ar", ""))
            formatted_result["queries_en"].append(query.get("query_en", ""))
        
        # Add recommendations
        formatted_result["recommendations_ar"] = result.get("recommendations_ar", [])
        formatted_result["recommendations_en"] = result.get("recommendations_en", [])
        
        logger.info(f"Analysis complete: {len(formatted_result['diagnoses_to_document'])} diagnoses found")
        return formatted_result
        
    except Exception as e:
        logger.error(f"Error analyzing with Local AI: {str(e)}")
        raise
