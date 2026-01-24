"""
MediDoc AI - vLLM Engine for V100 GPU
Enhanced CDI Analysis v3.0 - High Precision
"""

import logging
import json
import re
from typing import Dict, List, Optional
import os

from vllm import LLM, SamplingParams

logger = logging.getLogger(__name__)

_llm = None
_drg_lookup = None

MODEL_NAME = "Qwen/Qwen2.5-32B-Instruct-GPTQ-Int4"
TENSOR_PARALLEL_SIZE = 1
GPU_MEMORY_UTILIZATION = 0.85
RANDOM_SEED = 42
TEMPERATURE = 0.0

SENIOR_AUDITOR_PROMPT = """أنت مدقق طبي أول (Senior CDI Specialist) متخصص في تحسين التوثيق السريري.

## الاختصارات الطبية (تعتبر تشخيصات موثقة):
DM = Diabetes | HTN = Hypertension | CKD = Chronic Kidney Disease | AKI = Acute Kidney Injury
CHF/HF = Heart Failure | COPD = Chronic Obstructive Pulmonary Disease | CAD = Coronary Artery Disease
CVA = Stroke | DVT = Deep Vein Thrombosis | PE = Pulmonary Embolism | UTI = Urinary Tract Infection
Pneumonia = Pneumonia | Sepsis = Sepsis | AF = Atrial Fibrillation | ESRD = End Stage Renal Disease
NSTEMI/STEMI = MI | GI Bleeding = GI Bleeding | GERD = GERD | Asthma = Asthma

## ⛔ هذه أعراض وليست تشخيصات (لا تضعها كتشخيصات أبداً):
ضيق التنفس، Dyspnea، SOB، حرارة، Fever، ألم، Pain، غثيان، قيء، سعال، تورم عام، ضعف، دوخة

## قاعدة التشخيص الرئيسي:
التشخيص الرئيسي = سبب الدخول الرئيسي (ليس عرض)
- ✅ صحيح: "Pneumonia" كتشخيص رئيسي إذا دخل بسبب التهاب رئوي
- ❌ خطأ: "ضيق التنفس" كتشخيص رئيسي (هذا عرض وليس تشخيص)

## صيغة الاستفسار للطبيب (إلزامية):
"الدكتور/ة [الاسم إن وجد] المحترم/ة،
بناءً على المعطيات السريرية التالية: [اذكر المعطيات المحددة من الملاحظات]
بناءً على حكمكم الطبي، يرجى توثيق [النوع/الشدة/المرحلة/التشخيص] المتوافق مع هذه المعطيات.
مع التقدير"
"""

CDI_CHAT_PROMPT = """أنت أخصائي توثيق سريري (CDI Specialist).

## مهمتك:
عندما يقدم لك الأخصائي معلومات جديدة (أدوية، تحاليل، ملاحظات عمليات):
1. حلل المعلومات الجديدة
2. استنتج التشخيصات المحتملة مع أكواد ICD-10
3. اقترح استفسارات للطبيب

## عند طلب التشخيصات:
اعرض بوضوح:
- التشخيص الرئيسي (سبب الدخول) + الكود
- التشخيصات الثانوية الموثقة + الأكواد
- التشخيصات المستنتجة + الأكواد + الدليل

## قواعد:
- الأعراض ليست تشخيصات
- لا تجيب على أسئلة خارج التوثيق السريري
- أجب بنفس لغة السؤال"""


def get_llm():
    global _llm
    if _llm is not None:
        return _llm
    
    logger.info(f"🚀 Loading {MODEL_NAME}...")
    try:
        _llm = LLM(
            model=MODEL_NAME,
            tensor_parallel_size=TENSOR_PARALLEL_SIZE,
            gpu_memory_utilization=GPU_MEMORY_UTILIZATION,
            trust_remote_code=True,
            max_model_len=8192,
            dtype="float16",
            seed=RANDOM_SEED,
        )
        logger.info(f"✅ {MODEL_NAME} loaded!")
        return _llm
    except Exception as e:
        logger.error(f"❌ Failed: {str(e)}")
        raise


def generate_text(prompt: str, max_tokens: int = 4000, temperature: float = None, use_chat_prompt: bool = False) -> str:
    llm = get_llm()
    temp = temperature if temperature is not None else TEMPERATURE
    system_prompt = CDI_CHAT_PROMPT if use_chat_prompt else SENIOR_AUDITOR_PROMPT
    
    full_prompt = f"""<|im_start|>system
{system_prompt}<|im_end|>
<|im_start|>user
{prompt}<|im_end|>
<|im_start|>assistant
"""
    
    sampling_params = SamplingParams(
        max_tokens=max_tokens,
        temperature=temp,
        top_p=0.95 if temp > 0 else 1.0,
        seed=RANDOM_SEED,
        stop=["<|im_end|>", "<|endoftext|>"]
    )
    
    outputs = llm.generate([full_prompt], sampling_params)
    return outputs[0].outputs[0].text.strip()


def analyze_clinical_notes(formatted_notes: str, hospital_type: str = "A") -> Dict:
    
    analysis_prompt = f"""حلل الملاحظات السريرية التالية بدقة عالية جداً.

⚠️ تعليمات صارمة:
1. التشخيص الرئيسي = سبب الدخول (ليس عرض مثل ضيق التنفس أو حرارة)
2. استخرج كل تشخيص مذكور في النص (حتى لو كان اختصار مثل DM, HTN, CKD)
3. لا تضع الأعراض كتشخيصات (ضيق التنفس، حرارة، ألم = أعراض)
4. كن دقيقاً جداً في الربط بين التحاليل والتشخيصات

## المطلوب:

### 1. التشخيص الرئيسي (Principal Diagnosis):
- سبب الدخول الرئيسي (ليس عرض!)
- إذا كان المريض دخل بسبب "ضيق التنفس" ابحث عن السبب (Pneumonia? CHF? COPD exacerbation?)

### 2. التشخيصات الثانوية الموثقة نصاً:
- كل تشخيص مذكور في النص بأي شكل
- الاختصارات: DM, HTN, CKD, CHF, COPD, CAD, AF, etc.
- المكتوب بالعربية: سكري، ضغط، كلى، قلب

### 3. التشخيصات المستنتجة (من التحاليل + العلاج):
- Na < 135 + علاج = Hyponatremia
- K > 5.5 + علاج = Hyperkalemia  
- Hb < 12 + نقل دم = Anemia
- HbA1c > 8% = Uncontrolled DM
- Cr↑ + GFR↓ = CKD بمرحلتها

### 4. صيغة الاستفسار (إلزامية):
"الدكتور/ة المحترم/ة،
بناءً على المعطيات السريرية التالية: [المعطيات]
بناءً على حكمكم الطبي، يرجى توثيق [ما ينقص].
مع التقدير"

=== الملاحظات السريرية ===
{formatted_notes}
=== نهاية الملاحظات ===

=== أجب بـ JSON فقط ===
{{
    "principal_diagnosis": {{
        "diagnosis_ar": "التشخيص الرئيسي (سبب الدخول - ليس عرض!)",
        "diagnosis_en": "Principal Diagnosis (admission reason - not symptom!)",
        "icd_code": "ICD-10",
        "evidence": "الدليل من النص",
        "missing_details": ["ما ينقص: النوع/الشدة/المرحلة"],
        "query": "الدكتور/ة المحترم/ة،\\nبناءً على المعطيات السريرية التالية: [المعطيات]\\nبناءً على حكمكم الطبي، يرجى توثيق [ما ينقص].\\nمع التقدير"
    }},
    
    "secondary_diagnoses": [
        {{
            "diagnosis_ar": "التشخيص الثانوي",
            "diagnosis_en": "Secondary Diagnosis",
            "icd_code": "ICD-10",
            "evidence": "الدليل (اقتباس أو اختصار)",
            "missing_details": ["ما ينقص"],
            "query": "استفسار للطبيب إن وجد نقص"
        }}
    ],
    
    "inferred_diagnoses": [
        {{
            "diagnosis_ar": "التشخيص المستنتج",
            "diagnosis_en": "Inferred Diagnosis",
            "icd_code": "ICD-10",
            "lab_result": "نتيجة التحليل (مثل: Na = 128)",
            "treatment_given": "العلاج المقدم (مثل: تصحيح صوديوم)",
            "reasoning": "سبب الاستنتاج: نتيجة التحليل + العلاج = التشخيص",
            "query": "الدكتور/ة المحترم/ة،\\nبناءً على المعطيات السريرية التالية: [نتيجة التحليل + العلاج]\\nبناءً على حكمكم الطبي، يرجى توثيق [التشخيص].\\nمع التقدير"
        }}
    ],
    
    "documentation_gaps": [
        {{
            "diagnosis": "التشخيص",
            "gap_type": "النوع/الشدة/المرحلة/السبب",
            "what_is_missing": "ما ينقص بالتحديد",
            "why_important": "لماذا مهم للترميز",
            "query": "الدكتور/ة المحترم/ة،\\nبناءً على المعطيات السريرية التالية: [...]\\nبناءً على حكمكم الطبي، يرجى توثيق [ما ينقص].\\nمع التقدير"
        }}
    ],
    
    "case_summary": {{
        "admission_reason": "سبب الدخول الحقيقي",
        "patient_profile": "وصف المريض",
        "documented_conditions": ["قائمة كل الحالات الموثقة"],
        "inferred_conditions": ["قائمة الحالات المستنتجة"],
        "summary_ar": "ملخص شامل بالعربية",
        "summary_en": "Summary in English"
    }},
    
    "clinical_indicators": ["نتائج التحاليل المذكورة"],
    "treatments_found": ["العلاجات المذكورة"]
}}"""

    try:
        response_text = generate_text(analysis_prompt, max_tokens=6000, temperature=0.0)
        result = parse_json_response(response_text)
        result = ensure_result_structure(result)
        result = enhance_with_drg_pricing(result, hospital_type)
        return result
    except Exception as e:
        logger.error(f"❌ Analysis error: {str(e)}")
        raise


def ensure_result_structure(result: Dict) -> Dict:
    defaults = {
        "principal_diagnosis": {"diagnosis_ar": "", "diagnosis_en": "", "icd_code": "", "evidence": "", "missing_details": [], "query": ""},
        "secondary_diagnoses": [],
        "inferred_diagnoses": [],
        "documentation_gaps": [],
        "case_summary": {"admission_reason": "", "patient_profile": "", "documented_conditions": [], "inferred_conditions": [], "summary_ar": "", "summary_en": ""},
        "clinical_indicators": [],
        "treatments_found": []
    }
    
    for key, default_value in defaults.items():
        if key not in result:
            result[key] = default_value
    
    # Frontend compatibility
    result["diagnoses_to_document"] = result.get("inferred_diagnoses", [])
    result["missing_documentation"] = result.get("documentation_gaps", [])
    
    # Extract queries
    queries = []
    if result.get("principal_diagnosis", {}).get("query"):
        queries.append(result["principal_diagnosis"]["query"])
    for diag in result.get("secondary_diagnoses", []):
        if diag.get("query"):
            queries.append(diag["query"])
    for diag in result.get("inferred_diagnoses", []):
        if diag.get("query"):
            queries.append(diag["query"])
    for gap in result.get("documentation_gaps", []):
        if gap.get("query"):
            queries.append(gap["query"])
    
    result["queries_ar"] = queries
    result["queries_en"] = queries
    result["physician_queries"] = [{"query_ar": q, "query_en": q} for q in queries]
    
    # Gaps
    result["gaps_ar"] = [g.get("what_is_missing", "") for g in result.get("documentation_gaps", []) if g.get("what_is_missing")]
    result["gaps_en"] = result["gaps_ar"]
    
    # Summary
    case_summary = result.get("case_summary", {})
    result["summary_ar"] = case_summary.get("summary_ar", "")
    result["summary_en"] = case_summary.get("summary_en", "")
    
    return result


def parse_json_response(response_text: str) -> Dict:
    try:
        text = response_text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            text = json_match.group(0)
        
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"JSON error: {str(e)}")
        return {}


def initialize_drg_lookup(price_list_path: str = None, hospital_type: str = "A"):
    global _drg_lookup
    try:
        from drg_lookup import get_drg_lookup
        _drg_lookup = get_drg_lookup(price_list_path, hospital_type)
    except Exception as e:
        logger.warning(f"DRG lookup not available: {str(e)}")
    return _drg_lookup


def enhance_with_drg_pricing(result: Dict, hospital_type: str = "A") -> Dict:
    global _drg_lookup
    if _drg_lookup is None:
        try:
            initialize_drg_lookup(hospital_type=hospital_type)
        except:
            return result
    
    if _drg_lookup is None:
        return result
    
    try:
        principal = result.get('principal_diagnosis', {})
        icd_code = principal.get('icd_code', '')
        if icd_code:
            drg_info = _drg_lookup.lookup_by_icd(icd_code, hospital_type)
            if drg_info:
                principal['drg_code'] = drg_info.get('drg_code', '')
                principal['drg_cost'] = drg_info.get('price', '')
        
        for diag in result.get('secondary_diagnoses', []):
            icd = diag.get('icd_code', '')
            if icd:
                drg_info = _drg_lookup.lookup_by_icd(icd, hospital_type)
                if drg_info:
                    diag['drg_code'] = drg_info.get('drg_code', '')
                    diag['drg_cost'] = drg_info.get('price', '')
        
        for diag in result.get('inferred_diagnoses', []):
            icd = diag.get('icd_code', '')
            if icd:
                drg_info = _drg_lookup.lookup_by_icd(icd, hospital_type)
                if drg_info:
                    diag['drg_code'] = drg_info.get('drg_code', '')
                    diag['drg_cost'] = drg_info.get('price', '')
    except Exception as e:
        logger.warning(f"DRG enhancement failed: {str(e)}")
    
    return result
