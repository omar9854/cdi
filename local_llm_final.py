"""
MediDoc AI - Local LLM Module (100% Offline)
Senior Medical Auditor for Clinical Documentation Improvement (CDI)
Model: Qwen2.5-72B-Instruct with 4-bit quantization for A100 40GB
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import logging
import json
import re
from typing import Dict, List, Optional
from drg_lookup import DRGLookup, get_drg_lookup

logger = logging.getLogger(__name__)

# Global instances
_model = None
_tokenizer = None
_model_name = None
_drg_lookup = None

# Model configuration
DEFAULT_MODEL = "Qwen/Qwen2.5-72B-Instruct"
FALLBACK_MODEL = "Qwen/Qwen2.5-7B-Instruct"

# === Senior Medical Auditor System Prompt ===
SENIOR_AUDITOR_PROMPT = """أنت مدقق طبي أول (Senior Medical Auditor) متخصص في تحسين التوثيق السريري (CDI).

## مهمتك بالترتيب:

### 1️⃣ التشخيص الرئيسي (Principal Diagnosis):
- هو السبب الرئيسي الذي أُدخل المريض للمستشفى من أجله بعد الفحص والدراسة
- يوجد تشخيص رئيسي واحد فقط
- استخرج الدليل من الملاحظات
- حدد: النوع (Type)، الشدة (Severity)، المرحلة (Stage) إن وُجدت

### 2️⃣ التشخيصات الثانوية الموثقة (Documented Secondary Diagnoses):
هذه التشخيصات المذكورة صراحةً في الملاحظات السريرية.
لكل تشخيص موثق:
- اقتبس النص الذي يذكره من الملاحظات
- حدد التصنيف: مرض مصاحب (Comorbidity) أو مضاعفة (Complication)
- حدد إذا كان النوع/الشدة/المرحلة موثقة أم ناقصة
- اذكر كود ICD-10-AM

### 3️⃣ التشخيصات المستنتجة (Inferred Diagnoses):
هذه تشخيصات لم تُذكر صراحة لكن يوجد معطيات سريرية تدعمها.
أمثلة:
- قيم مخبرية غير طبيعية → تشخيص محتمل
- أعراض وعلامات → تشخيص محتمل  
- أدوية موصوفة → تشخيص يفسر استخدامها

لكل تشخيص مستنتج:
- المعطيات/الأدلة من الملاحظات
- التشخيص المحتمل
- كود ICD-10-AM المحتمل
- درجة الثقة (عالية/متوسطة/منخفضة)

### 4️⃣ ثغرات التوثيق (Documentation Gaps):
لكل تشخيص (موثق أو مستنتج)، حدد ما ينقص:
- النوع (Type): مثل Type 1/Type 2، انقباضي/انبساطي
- الشدة (Severity): خفيف/متوسط/شديد، مسيطر/غير مسيطر
- المرحلة (Stage): Stage 1-5، NYHA Class I-IV
- السبب (Etiology): سبب الحالة

### 5️⃣ استفسارات للطبيب (Physician Queries):
لكل ثغرة أو تشخيص مستنتج، أنشئ استفساراً بالصيغة:

"بناءً على: [الدليل المقتبس من الملاحظات]
يرجى توثيق/توضيح: [التشخيص أو التفصيل المطلوب]
الكود المحتمل: [ICD-10-AM]
التأثير: [على الترميز/DRG]"

## أمثلة على اكتشاف التشخيصات:

### مثال 1 - تشخيص موثق يحتاج تفاصيل:
الملاحظة: "مريض سكري على الأنسولين"
✓ موثق: السكري
✗ ناقص: النوع (1 أم 2)، مسيطر أم لا، المضاعفات
→ استفسار: "بناءً على ذكر السكري واستخدام الأنسولين، يرجى توثيق النوع (E10 أو E11) ومستوى السيطرة"

### مثال 2 - تشخيص مستنتج:
الملاحظة: "Creatinine 2.8 mg/dL, GFR 25 mL/min"
✗ غير موثق: مرض الكلى المزمن ومرحلته
→ استفسار: "بناءً على GFR 25، هل يمكن توثيق CKD Stage 4 (N18.4)؟"

### مثال 3 - مضاعفة مستنتجة:
الملاحظة: "مريض سكري + Creatinine 3.5"
✗ غير موثق: اعتلال الكلى السكري
→ استفسار: "بناءً على السكري وارتفاع الكرياتينين، هل يوجد اعتلال كلى سكري (E11.22)؟"

## مرجع أكواد ICD-10-AM:

### السكري (Diabetes Mellitus):
- E10.x Type 1 | E11.x Type 2
- E1x.65 مع ارتفاع سكر الدم (غير مسيطر)
- E1x.9 بدون مضاعفات
- E1x.21 مع اعتلال كلوي | E1x.22 مع CKD
- E1x.40 مع اعتلال عصبي | E1x.31 مع اعتلال شبكية

### الكلى (Kidney Disease):
- N18.1 CKD Stage 1 (GFR ≥90) | N18.2 Stage 2 (60-89)
- N18.3 Stage 3 (30-59) | N18.4 Stage 4 (15-29)
- N18.5 Stage 5 (<15) | N17.9 AKI

### القلب (Heart Failure):
- I50.20-23 انقباضي (Systolic) | I50.30-33 انبساطي (Diastolic)
- I50.40-43 مختلط | I50.9 غير محدد

### ارتفاع الضغط (Hypertension):
- I10 أساسي | I11.x مع مرض قلبي
- I12.x مع CKD | I13.x مع قلب وكلى

### الإنتان (Sepsis):
- A41.9 غير محدد | R65.20 شديد | R65.21 مع صدمة
"""

# === Chat Prompt for Discussions ===
CDI_CHAT_PROMPT = """أنت مدقق طبي أول (Senior Medical Auditor) متخصص في تحسين التوثيق السريري.

## دورك في المناقشة:

### عند السؤال عن تشخيص معين:
1. ابحث عن الأدلة في الملاحظات التي تدعمه
2. حدد إذا كان موثقاً صراحة أم مستنتجاً
3. اذكر ما ينقص من تفاصيل (النوع/الشدة/المرحلة)
4. اقترح صيغة الاستفسار للطبيب

### عند السؤال عن استفسار للطبيب:
صِغ الاستفسار بهذه الطريقة:
"بناءً على: [الدليل من الملاحظات]
يرجى توثيق/توضيح: [التشخيص أو التفصيل]
الكود المحتمل: [ICD-10-AM]
التأثير: [على الترميز]"

### عند السؤال عن النوع/الشدة/المرحلة:
اشرح لماذا هذا التفصيل مهم للترميز واذكر الأكواد الممكنة.

### قواعد عامة:
- كن دقيقاً واحترافياً
- استشهد دائماً بالدليل من الملاحظات
- اذكر أكواد ICD-10-AM
- أجب بنفس لغة السؤال
"""


def initialize_drg_lookup(price_list_path: str = None, hospital_type: str = "A"):
    """Initialize DRG lookup with price list"""
    global _drg_lookup
    _drg_lookup = get_drg_lookup(price_list_path, hospital_type)
    return _drg_lookup


def get_model(model_name: str = None):
    """Load Qwen2.5-72B with 4-bit quantization for A100 40GB"""
    global _model, _tokenizer, _model_name
    
    if model_name is None:
        model_name = DEFAULT_MODEL
    
    if _model is not None and _model_name == model_name:
        return _model, _tokenizer
    
    logger.info(f"🚀 Loading {model_name} with 4-bit quantization...")
    
    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"📱 Device: {device}")
        
        if device == "cuda":
            gpu_name = torch.cuda.get_device_name(0)
            gpu_mem = torch.cuda.get_device_properties(0).total_memory / 1024**3
            logger.info(f"🎮 GPU: {gpu_name} ({gpu_mem:.1f} GB)")
        
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4"
        )
        
        _tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        if _tokenizer.pad_token is None:
            _tokenizer.pad_token = _tokenizer.eos_token
        
        _model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=quantization_config,
            device_map="auto",
            trust_remote_code=True,
            low_cpu_mem_usage=True,
        )
        
        _model_name = model_name
        logger.info(f"✅ Model {model_name} loaded successfully!")
        return _model, _tokenizer
        
    except Exception as e:
        logger.error(f"❌ Failed to load {model_name}: {str(e)}")
        if model_name == DEFAULT_MODEL:
            logger.info(f"⚠️ Falling back to {FALLBACK_MODEL}...")
            return get_model(FALLBACK_MODEL)
        raise


def generate_text(prompt: str, max_new_tokens: int = 4000, temperature: float = 0.1, use_chat_prompt: bool = False) -> str:
    """Generate text using the loaded model"""
    try:
        model, tokenizer = get_model()
        device = next(model.parameters()).device
        
        system_prompt = CDI_CHAT_PROMPT if use_chat_prompt else SENIOR_AUDITOR_PROMPT
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        formatted_prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        
        inputs = tokenizer(
            formatted_prompt, return_tensors="pt", 
            truncation=True, max_length=8192
        ).to(device)
        
        logger.info("📤 Generating response...")
        
        with torch.no_grad():
            outputs = model.generate(
                input_ids=inputs['input_ids'],
                attention_mask=inputs['attention_mask'],
                max_new_tokens=max_new_tokens,
                do_sample=True,
                temperature=temperature,
                top_p=0.9,
                pad_token_id=tokenizer.eos_token_id,
            )
        
        response = tokenizer.decode(
            outputs[0][inputs['input_ids'].shape[1]:], 
            skip_special_tokens=True
        )
        
        logger.info(f"✅ Generated {len(response)} characters")
        return response.strip()
        
    except Exception as e:
        logger.error(f"❌ Generation error: {str(e)}")
        raise


def analyze_clinical_notes(formatted_notes: str, hospital_type: str = "A") -> Dict:
    """Perform comprehensive CDI analysis"""
    
    analysis_prompt = f"""## مهمة تحليل CDI الشامل

اقرأ الملاحظات السريرية التالية بدقة عالية وحللها كمدقق طبي أول.

=== الملاحظات السريرية ===
{formatted_notes}
=== نهاية الملاحظات ===

## المطلوب:

### 1. التشخيص الرئيسي (Principal Diagnosis):
حدد السبب الرئيسي للدخول مع:
- الدليل من الملاحظات (اقتباس)
- كود ICD-10-AM
- هل النوع/الشدة/المرحلة موثقة؟

### 2. التشخيصات الثانوية الموثقة (Documented):
اذكر كل تشخيص مذكور صراحة في الملاحظات مع:
- اقتباس النص الذي يذكره
- التصنيف (مرض مصاحب/مضاعفة)
- كود ICD-10-AM
- ما ينقص (النوع/الشدة/المرحلة)

### 3. التشخيصات المستنتجة (Inferred):
اذكر التشخيصات غير المذكورة صراحة لكن لها معطيات تدعمها:
- المعطيات/الأدلة من الملاحظات
- التشخيص المحتمل
- كود ICD-10-AM المحتمل
- درجة الثقة

### 4. ثغرات التوثيق:
لكل تشخيص، حدد ما ينقص:
- النوع | الشدة | المرحلة | السبب

### 5. استفسارات للطبيب:
لكل ثغرة أو تشخيص مستنتج، أنشئ استفساراً.

=== الرد بصيغة JSON فقط ===
{{
    "principal_diagnosis": {{
        "diagnosis_ar": "التشخيص الرئيسي بالعربية",
        "diagnosis_en": "Principal Diagnosis in English",
        "icd_code": "كود ICD-10-AM",
        "evidence": "الدليل المقتبس من الملاحظات",
        "type_documented": true/false,
        "severity_documented": true/false,
        "stage_documented": true/false,
        "missing_details": ["النوع", "الشدة"]
    }},
    "documented_diagnoses": [
        {{
            "diagnosis_ar": "التشخيص بالعربية",
            "diagnosis_en": "Diagnosis in English",
            "icd_code": "ICD-10-AM",
            "category": "comorbidity أو complication",
            "evidence": "النص المقتبس من الملاحظات الذي يذكر هذا التشخيص",
            "type_documented": true/false,
            "severity_documented": true/false,
            "stage_documented": true/false,
            "missing_details": ["ما ينقص"]
        }}
    ],
    "inferred_diagnoses": [
        {{
            "diagnosis_ar": "التشخيص المستنتج",
            "diagnosis_en": "Inferred Diagnosis",
            "potential_icd_code": "الكود المحتمل",
            "supporting_evidence": "المعطيات من الملاحظات التي تدعم هذا التشخيص",
            "confidence": "high/medium/low",
            "rationale": "سبب الاستنتاج"
        }}
    ],
    "documentation_gaps": [
        {{
            "diagnosis": "التشخيص",
            "gap_type": "type/severity/stage/etiology",
            "gap_description_ar": "وصف الثغرة",
            "gap_description_en": "Gap description",
            "current_code": "الكود الحالي",
            "potential_code": "الكود بعد التوثيق"
        }}
    ],
    "physician_queries": [
        {{
            "query_ar": "بناءً على: [الدليل]\\nيرجى توثيق/توضيح: [المطلوب]\\nالكود المحتمل: [ICD]\\nالتأثير: [على الترميز]",
            "query_en": "Based on: [evidence]\\nPlease document/clarify: [what's needed]\\nPotential code: [ICD]\\nImpact: [on coding]",
            "target_diagnosis": "التشخيص المستهدف",
            "evidence": "الدليل",
            "priority": "high/medium/low"
        }}
    ],
    "summary": {{
        "documented_count": 0,
        "inferred_count": 0,
        "gaps_count": 0,
        "queries_count": 0,
        "summary_ar": "ملخص التحليل",
        "summary_en": "Analysis summary"
    }}
}}

⚠️ مهم جداً:
1. التشخيصات الموثقة = المذكورة صراحة في النص
2. التشخيصات المستنتجة = لها معطيات لكن غير مذكورة صراحة
3. كل استفسار يجب أن يحتوي على دليل مقتبس
4. الرد JSON صالح فقط"""

    try:
        response_text = generate_text(analysis_prompt, max_new_tokens=5000, temperature=0.1)
        result = parse_json_response(response_text)
        result = enhance_with_drg_pricing(result, hospital_type)
        
        if not result.get('principal_diagnosis'):
            result = create_fallback_result(response_text)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Analysis error: {str(e)}")
        raise


def parse_json_response(response_text: str) -> Dict:
    """Parse JSON from model response"""
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
        logger.error(f"JSON parsing error: {str(e)}")
        return create_fallback_result(response_text)


def create_fallback_result(response_text: str) -> Dict:
    """Create fallback result when parsing fails"""
    return {
        "principal_diagnosis": {
            "diagnosis_ar": "يرجى مراجعة التحليل",
            "diagnosis_en": "Please review analysis",
            "icd_code": "",
            "evidence": "",
            "missing_details": []
        },
        "documented_diagnoses": [],
        "inferred_diagnoses": [],
        "documentation_gaps": [],
        "physician_queries": [],
        "summary": {
            "documented_count": 0,
            "inferred_count": 0,
            "gaps_count": 0,
            "queries_count": 0,
            "summary_ar": response_text[:2000] if response_text else "لا يوجد تحليل",
            "summary_en": "Raw analysis available in Arabic summary"
        }
    }


def enhance_with_drg_pricing(result: Dict, hospital_type: str = "A") -> Dict:
    """Add DRG pricing information"""
    try:
        global _drg_lookup
        if _drg_lookup is None:
            _drg_lookup = get_drg_lookup(hospital_type=hospital_type)
        
        # Principal diagnosis
        principal = result.get('principal_diagnosis', {})
        icd_code = principal.get('icd_code', '')
        if icd_code:
            drg_info = _drg_lookup.lookup_by_icd(icd_code)
            if drg_info:
                principal['drg_code'] = drg_info.get('drg_code', '')
                principal['drg_cost'] = drg_info.get('price', '')
        
        # Documented diagnoses
        for diag in result.get('documented_diagnoses', []):
            icd = diag.get('icd_code', '')
            if icd:
                drg_info = _drg_lookup.lookup_by_icd(icd)
                if drg_info:
                    diag['drg_code'] = drg_info.get('drg_code', '')
                    diag['drg_cost'] = drg_info.get('price', '')
        
        # Inferred diagnoses
        for diag in result.get('inferred_diagnoses', []):
            icd = diag.get('potential_icd_code', '')
            if icd:
                drg_info = _drg_lookup.lookup_by_icd(icd)
                if drg_info:
                    diag['potential_drg_code'] = drg_info.get('drg_code', '')
                    diag['potential_drg_cost'] = drg_info.get('price', '')
        
        return result
        
    except Exception as e:
        logger.error(f"DRG lookup error: {str(e)}")
        return result
