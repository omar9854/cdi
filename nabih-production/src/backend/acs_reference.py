"""
ACS Standards Reference Module
ICD-10-AM 10th Edition Standards for CDI Analysis
Implements ACS 0001 for Principal Diagnosis determination
"""

import logging
import json
import re
from typing import Dict, List, Optional
import PyPDF2
import os

logger = logging.getLogger(__name__)

# ACS Key Standards Reference
ACS_STANDARDS = {
    "0001": {
        "title_en": "Principal Diagnosis",
        "title_ar": "التشخيص الرئيسي",
        "definition": "The diagnosis established after study to be chiefly responsible for occasioning an episode of admitted patient care",
        "definition_ar": "التشخيص الذي تم تحديده بعد الدراسة ليكون المسؤول الرئيسي عن نوبة الرعاية للمريض المقبول",
        "guidelines": [
            "Must be the condition chiefly responsible for the admission",
            "Must be documented in the clinical record",
            "Should reflect the final diagnosis after investigation",
            "Cannot be a symptom if a definitive diagnosis exists"
        ],
        "guidelines_ar": [
            "يجب أن يكون الحالة المسؤولة بشكل رئيسي عن الدخول",
            "يجب أن يكون موثقاً في السجل السريري",
            "يجب أن يعكس التشخيص النهائي بعد الفحص",
            "لا يمكن أن يكون عرضاً إذا وجد تشخيص نهائي"
        ]
    },
    "0002": {
        "title_en": "Additional Diagnoses",
        "title_ar": "التشخيصات الإضافية",
        "definition": "Conditions that coexist with the principal diagnosis or develop during the episode of care",
        "definition_ar": "الحالات التي تتواجد مع التشخيص الرئيسي أو تتطور خلال فترة الرعاية",
        "guidelines": [
            "Must require therapeutic treatment, diagnostic procedures, or increased nursing care",
            "Must be documented by a clinician",
            "Should not include conditions that no longer exist"
        ],
        "guidelines_ar": [
            "يجب أن تتطلب علاجاً أو إجراءات تشخيصية أو رعاية تمريضية متزايدة",
            "يجب أن تكون موثقة من قبل طبيب",
            "لا تشمل الحالات التي لم تعد موجودة"
        ]
    },
    "0003": {
        "title_en": "Supplementary Codes for Chronic Conditions",
        "title_ar": "الأكواد التكميلية للحالات المزمنة",
        "definition": "Codes for ongoing chronic conditions affecting patient care",
        "definition_ar": "أكواد للحالات المزمنة المستمرة التي تؤثر على رعاية المريض"
    },
    "0010": {
        "title_en": "General Abstraction Guidelines",
        "title_ar": "إرشادات الاستخراج العامة",
        "definition": "General guidelines for clinical coding abstraction",
        "definition_ar": "إرشادات عامة لاستخراج الترميز السريري"
    },
    "0050": {
        "title_en": "Unacceptable Principal Diagnosis Codes",
        "title_ar": "أكواد التشخيص الرئيسي غير المقبولة",
        "definition": "Codes that cannot be used as principal diagnosis",
        "definition_ar": "الأكواد التي لا يمكن استخدامها كتشخيص رئيسي",
        "examples": [
            "R codes (symptoms) when definitive diagnosis exists",
            "Z codes for history conditions as principal",
            "External cause codes"
        ]
    },
    "0110": {
        "title_en": "SIRS, Sepsis, Severe Sepsis and Septic Shock",
        "title_ar": "متلازمة الاستجابة الالتهابية الجهازية، الإنتان، الإنتان الشديد والصدمة الإنتانية",
        "definition": "Guidelines for coding sepsis-related conditions",
        "definition_ar": "إرشادات ترميز الحالات المتعلقة بالإنتان"
    }
}

# Common unacceptable principal diagnosis patterns (ACS 0050)
UNACCEPTABLE_PRINCIPAL_PATTERNS = [
    r'^R\d{2}',  # Most R codes (symptoms) - unless no definitive diagnosis
    r'^Z87',     # Personal history
    r'^Z88',     # Allergy status
    r'^Z86',     # Personal history of certain conditions
    r'^Y\d{2}',  # External causes
    r'^V\d{2}',  # External causes
    r'^W\d{2}',  # External causes
    r'^X\d{2}',  # External causes
]


def get_acs_standard(standard_number: str) -> Optional[Dict]:
    """Get ACS standard details by number"""
    return ACS_STANDARDS.get(standard_number)


def get_principal_diagnosis_guidelines() -> Dict:
    """Get ACS 0001 Principal Diagnosis guidelines"""
    return ACS_STANDARDS["0001"]


def validate_principal_diagnosis_code(icd_code: str, has_definitive_diagnosis: bool = True) -> Dict:
    """
    Validate if an ICD code is acceptable as principal diagnosis per ACS 0001 & 0050
    
    Returns:
        Dict with 'valid', 'acs_reference', 'reason_ar', 'reason_en'
    """
    code = icd_code.upper().strip()
    
    # Check against unacceptable patterns
    for pattern in UNACCEPTABLE_PRINCIPAL_PATTERNS:
        if re.match(pattern, code):
            # R codes (symptoms) may be acceptable if no definitive diagnosis exists
            if pattern == r'^R\d{2}' and not has_definitive_diagnosis:
                return {
                    "valid": True,
                    "acs_reference": "ACS 0001",
                    "reason_ar": "مقبول - لا يوجد تشخيص نهائي موثق",
                    "reason_en": "Acceptable - no definitive diagnosis documented"
                }
            
            return {
                "valid": False,
                "acs_reference": "ACS 0050",
                "reason_ar": f"كود {code} غير مقبول كتشخيص رئيسي حسب معيار ACS 0050",
                "reason_en": f"Code {code} is unacceptable as principal diagnosis per ACS 0050"
            }
    
    return {
        "valid": True,
        "acs_reference": "ACS 0001",
        "reason_ar": "مقبول كتشخيص رئيسي",
        "reason_en": "Acceptable as principal diagnosis"
    }


def get_acs_reference_for_diagnosis(diagnosis_type: str) -> str:
    """Get relevant ACS reference number based on diagnosis type"""
    mapping = {
        "principal": "ACS 0001",
        "secondary": "ACS 0002",
        "chronic": "ACS 0003",
        "sepsis": "ACS 0110",
        "symptom": "ACS 0001/0050"
    }
    return mapping.get(diagnosis_type.lower(), "ACS 0001")


def format_query_with_acs(
    clinical_evidence: List[str],
    requested_documentation: str,
    acs_reference: str = "ACS 0001"
) -> Dict[str, str]:
    """
    Format a non-leading physician query with ACS reference
    
    Args:
        clinical_evidence: List of clinical findings supporting the query
        requested_documentation: What documentation is being requested
        acs_reference: Relevant ACS standard number
        
    Returns:
        Dict with 'query_ar' and 'query_en'
    """
    evidence_ar = "\n".join([f"• {e}" for e in clinical_evidence])
    evidence_en = "\n".join([f"• {e}" for e in clinical_evidence])
    
    query_ar = f"""بناءً على المعطيات السريرية التالية:
{evidence_ar}

بناءً على حكمكم الطبي، يرجى توثيق {requested_documentation} المتوافق مع المعطيات المذكورة.

المرجع: {acs_reference}"""

    query_en = f"""Based on the following clinical indicators:
{evidence_en}

Based on your clinical judgment, please document {requested_documentation} consistent with the above indicators.

Reference: {acs_reference}"""

    return {
        "query_ar": query_ar,
        "query_en": query_en,
        "acs_reference": acs_reference
    }


def extract_clinical_context(clinical_notes: str) -> Dict:
    """
    Extract clinical context elements from notes
    
    Returns:
        Dict with 'chief_complaint', 'clinical_indicators', 'care_treatment'
    """
    context = {
        "chief_complaint": "",
        "chief_complaint_ar": "",
        "clinical_indicators": [],
        "clinical_indicators_ar": [],
        "care_treatment": [],
        "care_treatment_ar": []
    }
    
    # Common clinical indicator patterns
    lab_patterns = [
        (r'HbA1c[:\s]*(\d+\.?\d*)\s*%?', 'HbA1c'),
        (r'(?:Creatinine|كرياتينين)[:\s]*(\d+\.?\d*)', 'Creatinine'),
        (r'GFR[:\s]*(\d+\.?\d*)', 'GFR'),
        (r'BNP[:\s]*(\d+\.?\d*)', 'BNP'),
        (r'EF[:\s]*(\d+\.?\d*)\s*%?', 'Ejection Fraction'),
        (r'(?:BP|ضغط)[:\s]*(\d+/\d+)', 'Blood Pressure'),
        (r'(?:Hemoglobin|هيموجلوبين)[:\s]*(\d+\.?\d*)', 'Hemoglobin'),
        (r'(?:Potassium|بوتاسيوم)[:\s]*(\d+\.?\d*)', 'Potassium'),
        (r'(?:Sodium|صوديوم)[:\s]*(\d+\.?\d*)', 'Sodium'),
        (r'(?:WBC|كريات بيضاء)[:\s]*(\d+\.?\d*)', 'WBC'),
    ]
    
    # Extract lab values
    for pattern, name in lab_patterns:
        match = re.search(pattern, clinical_notes, re.IGNORECASE)
        if match:
            value = match.group(1)
            context["clinical_indicators"].append(f"{name}: {value}")
            context["clinical_indicators_ar"].append(f"{name}: {value}")
    
    # Common medication patterns indicating treatment
    med_patterns = [
        (r'(?:أنسولين|Insulin)', 'Insulin therapy'),
        (r'(?:ميتفورمين|Metformin)', 'Metformin'),
        (r'(?:فوروسيمايد|Furosemide|Lasix)', 'Diuretic therapy'),
        (r'(?:أملوديبين|Amlodipine)', 'Antihypertensive'),
        (r'(?:هيبارين|Heparin)', 'Anticoagulation'),
        (r'(?:مضاد حيوي|Antibiotic)', 'Antibiotic therapy'),
        (r'(?:أكسجين|Oxygen|O2)', 'Oxygen therapy'),
        (r'(?:غسيل كلوي|Dialysis|غسيل)', 'Dialysis'),
    ]
    
    for pattern, treatment in med_patterns:
        if re.search(pattern, clinical_notes, re.IGNORECASE):
            context["care_treatment"].append(treatment)
            context["care_treatment_ar"].append(treatment)
    
    return context


class ACSReferenceSystem:
    """ACS Reference System for CDI Analysis"""
    
    def __init__(self, pdf_path: str = None):
        self.standards = ACS_STANDARDS
        self.pdf_path = pdf_path or "/opt/nabih/backend/reference_data/acs_standards.pdf"
        
    def get_standard(self, number: str) -> Optional[Dict]:
        """Get a specific ACS standard"""
        return self.standards.get(number)
    
    def get_principal_diagnosis_rule(self) -> Dict:
        """Get ACS 0001 rule for principal diagnosis"""
        return self.standards["0001"]
    
    def validate_diagnosis(self, icd_code: str, diagnosis_type: str = "principal") -> Dict:
        """Validate a diagnosis code against ACS standards"""
        if diagnosis_type == "principal":
            return validate_principal_diagnosis_code(icd_code)
        return {"valid": True, "acs_reference": get_acs_reference_for_diagnosis(diagnosis_type)}
    
    def generate_non_leading_query(
        self,
        clinical_evidence: List[str],
        documentation_request: str,
        diagnosis_type: str = "principal"
    ) -> Dict:
        """Generate a non-leading physician query"""
        acs_ref = get_acs_reference_for_diagnosis(diagnosis_type)
        return format_query_with_acs(clinical_evidence, documentation_request, acs_ref)


# Global instance
_acs_system = None

def get_acs_system() -> ACSReferenceSystem:
    """Get or create ACS reference system instance"""
    global _acs_system
    if _acs_system is None:
        _acs_system = ACSReferenceSystem()
    return _acs_system
