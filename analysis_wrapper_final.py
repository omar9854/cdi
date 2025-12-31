"""
Analysis wrapper - Converts local_llm output to frontend format
Handles: Documented diagnoses, Inferred diagnoses, Gaps, Queries
"""

from local_llm import analyze_clinical_notes
import logging

logger = logging.getLogger(__name__)


async def analyze_with_local_llm(notes_text: str, doctor_notes: list) -> dict:
    """
    Analyze clinical notes using LOCAL Qwen2.5-72B AI
    Returns structured result for frontend display
    """
    
    # Format doctor notes
    formatted_parts = []
    for note in doctor_notes:
        specialty = note.get('specialty', 'General')
        text = note.get('text', '')
        formatted_parts.append(f"**{specialty}**:\n{text}")
    
    formatted_notes = "\n\n".join(formatted_parts)
    
    try:
        logger.info("🏥 Starting comprehensive CDI analysis...")
        
        result = analyze_clinical_notes(formatted_notes, hospital_type="A")
        
        # Convert to frontend format
        formatted_result = {
            "diagnoses_to_document": [],
            "missing_documentation": [],
            "gaps_ar": [],
            "gaps_en": [],
            "queries_ar": [],
            "queries_en": [],
            "recommendations_ar": [],
            "recommendations_en": [],
            "summary_ar": "",
            "summary_en": ""
        }
        
        # === 1. Principal Diagnosis ===
        principal = result.get("principal_diagnosis", {})
        if principal and principal.get("diagnosis_ar"):
            missing = principal.get("missing_details", [])
            formatted_result["diagnoses_to_document"].append({
                "diagnosis_ar": principal.get("diagnosis_ar", ""),
                "diagnosis_en": principal.get("diagnosis_en", ""),
                "icd_code": principal.get("icd_code", ""),
                "type": "التشخيص الرئيسي",
                "type_en": "Principal Diagnosis",
                "evidence": principal.get("evidence", ""),
                "drg_code": principal.get("drg_code", ""),
                "drg_cost": principal.get("drg_cost", ""),
                "is_documented": True,
                "missing_details": missing,
                "needs_clarification": len(missing) > 0
            })
            
            # Add gaps for principal diagnosis
            for detail in missing:
                formatted_result["gaps_ar"].append(f"التشخيص الرئيسي: {detail} غير محدد")
                formatted_result["gaps_en"].append(f"Principal diagnosis: {detail} not specified")
        
        # === 2. Documented Secondary Diagnoses ===
        for diag in result.get("documented_diagnoses", []):
            if diag.get("diagnosis_ar"):
                missing = diag.get("missing_details", [])
                category = diag.get("category", "secondary")
                category_ar = "مرض مصاحب" if category == "comorbidity" else "مضاعفة" if category == "complication" else "ثانوي"
                
                formatted_result["diagnoses_to_document"].append({
                    "diagnosis_ar": diag.get("diagnosis_ar", ""),
                    "diagnosis_en": diag.get("diagnosis_en", ""),
                    "icd_code": diag.get("icd_code", ""),
                    "type": category_ar,
                    "type_en": category.capitalize(),
                    "evidence": diag.get("evidence", ""),
                    "drg_code": diag.get("drg_code", ""),
                    "drg_cost": diag.get("drg_cost", ""),
                    "is_documented": True,
                    "missing_details": missing,
                    "needs_clarification": len(missing) > 0
                })
                
                # Add gaps
                for detail in missing:
                    formatted_result["gaps_ar"].append(f"{diag.get('diagnosis_ar', '')}: {detail} غير محدد")
                    formatted_result["gaps_en"].append(f"{diag.get('diagnosis_en', '')}: {detail} not specified")
        
        # === 3. Inferred Diagnoses (Not documented but has evidence) ===
        for diag in result.get("inferred_diagnoses", []):
            if diag.get("diagnosis_ar"):
                confidence = diag.get("confidence", "medium")
                confidence_ar = "عالية" if confidence == "high" else "متوسطة" if confidence == "medium" else "منخفضة"
                
                formatted_result["diagnoses_to_document"].append({
                    "diagnosis_ar": diag.get("diagnosis_ar", ""),
                    "diagnosis_en": diag.get("diagnosis_en", ""),
                    "icd_code": diag.get("potential_icd_code", ""),
                    "type": f"مستنتج (ثقة {confidence_ar})",
                    "type_en": f"Inferred ({confidence} confidence)",
                    "evidence": diag.get("supporting_evidence", ""),
                    "rationale": diag.get("rationale", ""),
                    "drg_code": diag.get("potential_drg_code", ""),
                    "drg_cost": diag.get("potential_drg_cost", ""),
                    "is_documented": False,
                    "is_inferred": True,
                    "confidence": confidence,
                    "needs_documentation": True
                })
                
                # Add to gaps
                evidence = diag.get("supporting_evidence", "")
                formatted_result["gaps_ar"].append(
                    f"تشخيص مستنتج: {diag.get('diagnosis_ar', '')} - الدليل: {evidence}"
                )
                formatted_result["gaps_en"].append(
                    f"Inferred: {diag.get('diagnosis_en', '')} - Evidence: {evidence}"
                )
        
        # === 4. Documentation Gaps ===
        for gap in result.get("documentation_gaps", []):
            gap_desc_ar = gap.get("gap_description_ar", "")
            gap_desc_en = gap.get("gap_description_en", "")
            
            if gap_desc_ar and gap_desc_ar not in formatted_result["gaps_ar"]:
                formatted_result["gaps_ar"].append(gap_desc_ar)
            if gap_desc_en and gap_desc_en not in formatted_result["gaps_en"]:
                formatted_result["gaps_en"].append(gap_desc_en)
            
            formatted_result["missing_documentation"].append({
                "diagnosis": gap.get("diagnosis", ""),
                "gap_type": gap.get("gap_type", ""),
                "description_ar": gap_desc_ar,
                "description_en": gap_desc_en,
                "current_code": gap.get("current_code", ""),
                "potential_code": gap.get("potential_code", "")
            })
        
        # === 5. Physician Queries ===
        for query in result.get("physician_queries", []):
            query_ar = query.get("query_ar", "")
            query_en = query.get("query_en", "")
            
            if query_ar:
                formatted_result["queries_ar"].append(query_ar)
            if query_en:
                formatted_result["queries_en"].append(query_en)
        
        # === 6. Summary & Recommendations ===
        summary = result.get("summary", {})
        doc_count = summary.get("documented_count", len(result.get("documented_diagnoses", [])))
        inf_count = summary.get("inferred_count", len(result.get("inferred_diagnoses", [])))
        gap_count = summary.get("gaps_count", len(result.get("documentation_gaps", [])))
        query_count = summary.get("queries_count", len(result.get("physician_queries", [])))
        
        formatted_result["summary_ar"] = summary.get("summary_ar", 
            f"تم تحليل الحالة: {doc_count} تشخيص موثق، {inf_count} تشخيص مستنتج، {gap_count} ثغرة، {query_count} استفسار"
        )
        formatted_result["summary_en"] = summary.get("summary_en",
            f"Analysis: {doc_count} documented, {inf_count} inferred, {gap_count} gaps, {query_count} queries"
        )
        
        # Recommendations
        if inf_count > 0:
            formatted_result["recommendations_ar"].append(
                f"يوجد {inf_count} تشخيص/تشخيصات مستنتجة تحتاج توثيق من الطبيب"
            )
            formatted_result["recommendations_en"].append(
                f"{inf_count} inferred diagnosis(es) need physician documentation"
            )
        
        if gap_count > 0:
            formatted_result["recommendations_ar"].append(
                f"يوجد {gap_count} ثغرة في التوثيق تحتاج استكمال (النوع/الشدة/المرحلة)"
            )
            formatted_result["recommendations_en"].append(
                f"{gap_count} documentation gap(s) need completion (type/severity/stage)"
            )
        
        if query_count > 0:
            formatted_result["recommendations_ar"].append(
                f"تم توليد {query_count} استفسار للطبيب - يرجى مراجعتها وإرسالها"
            )
            formatted_result["recommendations_en"].append(
                f"Generated {query_count} physician query(ies) - please review and send"
            )
        
        logger.info(f"✅ Analysis complete: {doc_count + 1} documented, {inf_count} inferred, {query_count} queries")
        return formatted_result
        
    except Exception as e:
        logger.error(f"Error in analysis: {str(e)}")
        raise
