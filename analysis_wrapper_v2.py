"""
Analysis wrapper - Routes all analysis to local_llm module
FOCUS: Discovering UNDOCUMENTED diagnoses and generating evidence-based queries
"""

from local_llm import analyze_clinical_notes
import logging

logger = logging.getLogger(__name__)


async def analyze_with_local_llm(notes_text: str, doctor_notes: list) -> dict:
    """
    Analyze clinical notes using LOCAL Qwen2.5-72B AI model (100% Offline)
    
    FOCUS:
    - Discovering UNDOCUMENTED diagnoses with clinical indicators
    - Generating physician queries with evidence
    - Requesting Type, Severity, Stage for each diagnosis
    """
    
    # Format doctor notes with specialties
    formatted_parts = []
    for note in doctor_notes:
        specialty = note.get('specialty', 'General')
        text = note.get('text', '')
        formatted_parts.append(f"**{specialty}**:\n{text}")
    
    formatted_notes = "\n\n".join(formatted_parts)
    
    try:
        logger.info("🏥 Starting CDI analysis - Focus on UNDOCUMENTED diagnoses...")
        
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
            missing = principal.get("missing_details", [])
            formatted_result["diagnoses_to_document"].append({
                "diagnosis_ar": principal.get("diagnosis_ar", ""),
                "diagnosis_en": principal.get("diagnosis_en", ""),
                "icd_code": principal.get("icd_code", ""),
                "type": "principal",
                "evidence_ar": principal.get("evidence_ar", ""),
                "evidence_en": principal.get("evidence_en", ""),
                "clinical_evidence": principal.get("evidence_ar", "") + " | " + principal.get("evidence_en", ""),
                "drg_code": principal.get("drg_code", ""),
                "drg_cost": principal.get("drg_cost", ""),
                "drg_description": principal.get("drg_description", ""),
                "missing_details": missing,
                "is_fully_documented": len(missing) == 0
            })
            
            # Add gaps for missing details in principal diagnosis
            for detail in missing:
                formatted_result["gaps_ar"].append(f"التشخيص الرئيسي: {detail}")
                formatted_result["gaps_en"].append(f"Principal diagnosis: {detail} not specified")
        
        # Add secondary diagnoses
        for diag in result.get("secondary_diagnoses", []):
            missing = diag.get("missing_details", [])
            formatted_result["diagnoses_to_document"].append({
                "diagnosis_ar": diag.get("diagnosis_ar", ""),
                "diagnosis_en": diag.get("diagnosis_en", ""),
                "icd_code": diag.get("icd_code", ""),
                "type": diag.get("category", "secondary"),
                "evidence_ar": diag.get("evidence_ar", ""),
                "evidence_en": diag.get("evidence_en", ""),
                "clinical_evidence": diag.get("evidence_ar", "") + " | " + diag.get("evidence_en", ""),
                "drg_code": diag.get("drg_code", ""),
                "drg_cost": diag.get("drg_cost", ""),
                "affects_drg": diag.get("affects_drg", False),
                "missing_details": missing,
                "is_fully_documented": diag.get("is_fully_documented", len(missing) == 0)
            })
        
        # Add UNDOCUMENTED diagnoses (most important!)
        for undoc in result.get("undocumented_diagnoses", []):
            formatted_result["diagnoses_to_document"].append({
                "diagnosis_ar": undoc.get("suggested_diagnosis_ar", ""),
                "diagnosis_en": undoc.get("suggested_diagnosis_en", ""),
                "icd_code": undoc.get("potential_icd_code", ""),
                "type": "undocumented",
                "evidence_ar": undoc.get("clinical_indicator_ar", ""),
                "evidence_en": undoc.get("clinical_indicator_en", ""),
                "clinical_evidence": undoc.get("clinical_indicator_ar", "") + " | " + undoc.get("clinical_indicator_en", ""),
                "drg_code": undoc.get("potential_drg_code", ""),
                "drg_cost": undoc.get("potential_drg_cost", ""),
                "confidence": undoc.get("confidence", ""),
                "is_undocumented": True,
                "reason": undoc.get("reason_not_documented", "لم يُوثَّق صراحة")
            })
            
            # Add to gaps
            indicator = undoc.get("clinical_indicator_ar", "")
            suggested = undoc.get("suggested_diagnosis_ar", "")
            formatted_result["gaps_ar"].append(f"تشخيص غير موثق: {suggested} (المؤشر: {indicator})")
            formatted_result["gaps_en"].append(f"Undocumented: {undoc.get('suggested_diagnosis_en', '')} (Indicator: {undoc.get('clinical_indicator_en', '')})")
        
        # Add documentation gaps
        for gap in result.get("documentation_gaps", []):
            formatted_result["gaps_ar"].append(gap.get("gap_ar", ""))
            formatted_result["gaps_en"].append(gap.get("gap_en", ""))
            formatted_result["missing_documentation"].append({
                "item_ar": gap.get("gap_ar", ""),
                "item_en": gap.get("gap_en", ""),
                "clinical_indicator": gap.get("clinical_indicator", ""),
                "what_is_missing": gap.get("what_is_missing", ""),
                "impact": gap.get("impact_en", gap.get("impact_ar", ""))
            })
        
        # Add physician queries (Enhanced with evidence)
        for query in result.get("physician_queries", []):
            evidence = query.get("evidence_from_notes", "")
            potential_diag = query.get("potential_diagnosis", "")
            potential_code = query.get("potential_icd_code", "")
            details_needed = query.get("details_needed", [])
            
            # Format Arabic query
            query_ar = query.get("query_ar", "")
            if not query_ar:
                query_ar = f"بناءً على: {evidence}\n"
                query_ar += f"التشخيص المحتمل: {potential_diag} ({potential_code})\n"
                query_ar += f"المطلوب توثيقه: {', '.join(details_needed)}"
            
            # Ensure evidence is included
            if evidence and evidence not in query_ar:
                query_ar = f"الدليل من الملاحظات: {evidence}\n{query_ar}"
            
            formatted_result["queries_ar"].append(query_ar)
            
            # Format English query
            query_en = query.get("query_en", "")
            if not query_en:
                query_en = f"Based on: {evidence}\n"
                query_en += f"Potential diagnosis: {potential_diag} ({potential_code})\n"
                query_en += f"Please document: {', '.join(details_needed)}"
            
            if evidence and evidence not in query_en:
                query_en = f"Evidence from notes: {evidence}\n{query_en}"
            
            formatted_result["queries_en"].append(query_en)
        
        # Generate recommendations based on findings
        undoc_count = len(result.get("undocumented_diagnoses", []))
        gap_count = len(result.get("documentation_gaps", []))
        query_count = len(result.get("physician_queries", []))
        
        if undoc_count > 0:
            formatted_result["recommendations_ar"].append(f"تم اكتشاف {undoc_count} تشخيص/تشخيصات غير موثقة تحتاج مراجعة")
            formatted_result["recommendations_en"].append(f"Found {undoc_count} undocumented diagnosis(es) requiring review")
        
        if gap_count > 0:
            formatted_result["recommendations_ar"].append(f"يوجد {gap_count} ثغرة في التوثيق تحتاج استكمال")
            formatted_result["recommendations_en"].append(f"{gap_count} documentation gap(s) need to be addressed")
        
        if query_count > 0:
            formatted_result["recommendations_ar"].append(f"تم توليد {query_count} استفسار للطبيب")
            formatted_result["recommendations_en"].append(f"Generated {query_count} physician query(ies)")
        
        formatted_result["recommendations_ar"].append("راجع الاستفسارات وأرسلها للطبيب المعالج")
        formatted_result["recommendations_en"].append("Review queries and send to treating physician")
        
        logger.info(f"✅ Analysis complete: {len(formatted_result['diagnoses_to_document'])} diagnoses, {undoc_count} undocumented, {query_count} queries")
        return formatted_result
        
    except Exception as e:
        logger.error(f"Error in CDI analysis: {str(e)}")
        raise
