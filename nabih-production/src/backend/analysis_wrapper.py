"""
Analysis wrapper v3.0 - High Precision
"""

from local_llm import analyze_clinical_notes
import logging

logger = logging.getLogger(__name__)


async def analyze_with_local_llm(notes_text: str, doctor_notes: list) -> dict:
    """Analyze clinical notes with high precision"""
    
    formatted_parts = []
    for note in doctor_notes:
        specialty = note.get('specialty', 'عام')
        text = note.get('text', '')
        formatted_parts.append(f"**{specialty}**:\n{text}")
    
    formatted_notes = "\n\n".join(formatted_parts)
    
    try:
        logger.info("🏥 Starting CDI analysis v3.0...")
        
        result = analyze_clinical_notes(formatted_notes, hospital_type="A")
        
        formatted_result = {
            "principal_diagnosis": None,
            "secondary_diagnoses": [],
            "inferred_diagnoses": [],
            "diagnoses_to_document": [],
            "documentation_gaps": [],
            "missing_documentation": [],
            "gaps_ar": [],
            "gaps_en": [],
            "queries_ar": [],
            "queries_en": [],
            "physician_queries": [],
            "case_summary": {},
            "summary_ar": "",
            "summary_en": "",
            "clinical_indicators": [],
            "treatments_found": [],
            "recommendations_ar": [],
            "recommendations_en": []
        }
        
        # 1. Principal Diagnosis
        principal = result.get("principal_diagnosis", {})
        if principal and (principal.get("diagnosis_ar") or principal.get("diagnosis_en")):
            formatted_result["principal_diagnosis"] = {
                "diagnosis_ar": principal.get("diagnosis_ar", ""),
                "diagnosis_en": principal.get("diagnosis_en", ""),
                "icd_code": principal.get("icd_code", ""),
                "evidence": principal.get("evidence", ""),
                "missing_details": principal.get("missing_details", []),
                "query": principal.get("query", ""),
                "drg_code": principal.get("drg_code", ""),
                "drg_cost": principal.get("drg_cost", "")
            }
            if principal.get("query"):
                formatted_result["queries_ar"].append(principal["query"])
                formatted_result["queries_en"].append(principal["query"])
        
        # 2. Secondary Diagnoses
        for diag in result.get("secondary_diagnoses", []):
            if diag.get("diagnosis_ar") or diag.get("diagnosis_en"):
                formatted_result["secondary_diagnoses"].append({
                    "diagnosis_ar": diag.get("diagnosis_ar", ""),
                    "diagnosis_en": diag.get("diagnosis_en", ""),
                    "icd_code": diag.get("icd_code", ""),
                    "evidence": diag.get("evidence", ""),
                    "missing_details": diag.get("missing_details", []),
                    "query": diag.get("query", ""),
                    "drg_code": diag.get("drg_code", ""),
                    "drg_cost": diag.get("drg_cost", "")
                })
                if diag.get("query"):
                    formatted_result["queries_ar"].append(diag["query"])
                    formatted_result["queries_en"].append(diag["query"])
        
        # 3. Inferred Diagnoses
        for diag in result.get("inferred_diagnoses", []):
            if diag.get("diagnosis_ar") or diag.get("diagnosis_en"):
                item = {
                    "diagnosis_ar": diag.get("diagnosis_ar", ""),
                    "diagnosis_en": diag.get("diagnosis_en", ""),
                    "icd_code": diag.get("icd_code", ""),
                    "lab_result": diag.get("lab_result", ""),
                    "treatment_given": diag.get("treatment_given", ""),
                    "reasoning": diag.get("reasoning", ""),
                    "query": diag.get("query", ""),
                    "drg_code": diag.get("drg_code", ""),
                    "drg_cost": diag.get("drg_cost", "")
                }
                formatted_result["inferred_diagnoses"].append(item)
                formatted_result["diagnoses_to_document"].append(item)
                if diag.get("query"):
                    formatted_result["queries_ar"].append(diag["query"])
                    formatted_result["queries_en"].append(diag["query"])
        
        # 4. Documentation Gaps
        for gap in result.get("documentation_gaps", []):
            formatted_result["documentation_gaps"].append(gap)
            formatted_result["missing_documentation"].append({
                "diagnosis": gap.get("diagnosis", ""),
                "description_ar": gap.get("what_is_missing", ""),
                "description_en": gap.get("what_is_missing", ""),
                "gap_type": gap.get("gap_type", "")
            })
            if gap.get("what_is_missing"):
                formatted_result["gaps_ar"].append(f"{gap.get('diagnosis', '')}: {gap.get('what_is_missing', '')}")
                formatted_result["gaps_en"].append(f"{gap.get('diagnosis', '')}: {gap.get('what_is_missing', '')}")
            if gap.get("query"):
                formatted_result["queries_ar"].append(gap["query"])
                formatted_result["queries_en"].append(gap["query"])
        
        # 5. Physician Queries
        formatted_result["physician_queries"] = [{"query_ar": q, "query_en": q} for q in formatted_result["queries_ar"]]
        
        # 6. Case Summary
        case_summary = result.get("case_summary", {})
        formatted_result["case_summary"] = case_summary
        formatted_result["summary_ar"] = case_summary.get("summary_ar", "")
        formatted_result["summary_en"] = case_summary.get("summary_en", "")
        
        # 7. Clinical Data
        formatted_result["clinical_indicators"] = result.get("clinical_indicators", [])
        formatted_result["treatments_found"] = result.get("treatments_found", [])
        
        # 8. Recommendations
        doc_count = len(formatted_result["secondary_diagnoses"])
        inf_count = len(formatted_result["inferred_diagnoses"])
        gap_count = len(formatted_result["gaps_ar"])
        
        if inf_count > 0:
            formatted_result["recommendations_ar"].append(f"يوجد {inf_count} تشخيص مستنتج يحتاج توثيق من الطبيب")
            formatted_result["recommendations_en"].append(f"{inf_count} inferred diagnosis(es) need documentation")
        if gap_count > 0:
            formatted_result["recommendations_ar"].append(f"يوجد {gap_count} فجوة في التوثيق")
            formatted_result["recommendations_en"].append(f"{gap_count} documentation gap(s)")
        
        logger.info(f"✅ Analysis: Principal + {doc_count} secondary + {inf_count} inferred + {gap_count} gaps")
        return formatted_result
        
    except Exception as e:
        logger.error(f"❌ Analysis error: {str(e)}")
        raise
