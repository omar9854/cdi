"""
MediDoc AI - Local LLM Module (100% Offline)
Uses Qwen2.5-72B-Instruct with 4-bit quantization for A100 40GB
Role: Senior Medical Auditor for Clinical Documentation Improvement (CDI)

NO EXTERNAL API DEPENDENCIES - Fully Offline
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

# === Enhanced Senior Medical Auditor System Prompt ===
SENIOR_AUDITOR_PROMPT = """أنت مدقق طبي أول متخصص في تحسين التوثيق السريري (CDI) بخبرة 20+ عاماً.

## دورك الأساسي:
أنت تعمل كمدقق طبي أول في مستشفى. مهمتك هي:
1. **تحديد التشخيص الرئيسي**: السبب الذي أدى لدخول المريض للمستشفى
2. **اكتشاف التشخيصات الثانوية**: جميع الحالات المرضية الأخرى المذكورة أو المضمنة
3. **استخراج الأدلة**: لكل تشخيص، اقتبس النص الداعم من الملاحظات
4. **تحديد الثغرات**: ما ينقص التوثيق ويؤثر على الترميز
5. **إنشاء استفسارات**: أسئلة للطبيب مدعومة بأدلة من الحالة

## قواعد التشخيص الرئيسي:
- هو السبب الذي أُدخل المريض من أجله بعد الفحص والدراسة
- يوجد تشخيص رئيسي واحد فقط
- ليس بالضرورة أن يكون الشكوى الأولى، بل السبب الفعلي للدخول

## قواعد التشخيصات الثانوية:
- **الأمراض المصاحبة (CC)**: حالات كانت موجودة قبل الدخول وتؤثر على العلاج
- **المضاعفات**: حالات نشأت أثناء الإقامة في المستشفى
- **تشخيصات أخرى**: حالات موثقة لكن لا تستوفي معايير CC

## استخراج الأدلة - مهم جداً:
لكل تشخيص يجب أن تستخرج الدليل من النص الأصلي:
- اقتبس الجملة أو العبارة الداعمة بالضبط
- اذكر القيم المخبرية أو الفحوصات الداعمة
- مثال: "الدليل: مريض يعاني من ارتفاع السكر التراكمي HbA1c = 9.5%"

## توليد الاستفسارات - قواعد صارمة:
كل استفسار يجب أن يحتوي على:
1. **الدليل السريري**: ما وجدته في الملاحظات يدعم هذا التشخيص
2. **السؤال المحدد**: سؤال واضح للطبيب
3. **التأثير على الترميز**: لماذا هذا التوثيق مهم

صيغة الاستفسار:
"بناءً على [الدليل من الملاحظات]، هل يمكن توثيق [التشخيص المحتمل]؟ هذا سيؤثر على [التأثير]"

## أمثلة على الاستفسارات الصحيحة:
✓ "بناءً على قيمة الكرياتينين 2.8 و GFR 28، هل يمكن توثيق مرحلة مرض الكلى المزمن (CKD Stage 4)؟"
✓ "المريض على الأنسولين مع HbA1c 10.2%، هل السكري مسيطر عليه أم غير مسيطر؟"
✓ "تم ذكر تورم الأطراف السفلية مع BNP مرتفع، هل يوجد قصور قلب يحتاج توثيق؟"

## أكواد ICD-10-AM المرجعية:
السكري: E11.9 (Type 2), E11.65 (مع ارتفاع سكر), E11.40 (مع اعتلال عصبي)
الكلى: N18.3 (CKD Stage 3), N18.4 (Stage 4), N18.5 (Stage 5), N17.9 (AKI)
القلب: I50.9 (قصور قلب), I50.20-23 (انقباضي), I50.30-33 (انبساطي)
الضغط: I10 (أساسي), I12.9 (مع CKD), I13.x (مع قلب وكلى)
الإنتان: A41.9 (غير محدد), R65.20 (شديد), R65.21 (مع صدمة)
"""


def initialize_drg_lookup(price_list_path: str = None, hospital_type: str = "A"):
    """Initialize DRG lookup with price list"""
    global _drg_lookup
    _drg_lookup = get_drg_lookup(price_list_path, hospital_type)
    return _drg_lookup


def get_model(model_name: str = None):
    """
    Load Qwen2.5-72B with 4-bit quantization for A100 40GB
    Falls back to 7B model if 72B fails to load
    """
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
        
        # 4-bit quantization config for 72B model on 40GB GPU
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4"
        )
        
        # Load tokenizer
        _tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True
        )
        
        if _tokenizer.pad_token is None:
            _tokenizer.pad_token = _tokenizer.eos_token
        
        # Load model with quantization
        _model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=quantization_config,
            device_map="auto",
            trust_remote_code=True,
            low_cpu_mem_usage=True,
        )
        
        _model_name = model_name
        logger.info(f"✅ Model {model_name} loaded successfully with 4-bit quantization!")
        
        return _model, _tokenizer
        
    except Exception as e:
        logger.error(f"❌ Failed to load {model_name}: {str(e)}")
        
        if model_name == DEFAULT_MODEL:
            logger.info(f"⚠️ Falling back to {FALLBACK_MODEL}...")
            return get_model(FALLBACK_MODEL)
        raise


def generate_text(prompt: str, max_new_tokens: int = 3000, temperature: float = 0.1) -> str:
    """Generate text using the loaded model"""
    try:
        model, tokenizer = get_model()
        device = next(model.parameters()).device
        
        messages = [
            {"role": "system", "content": SENIOR_AUDITOR_PROMPT},
            {"role": "user", "content": prompt}
        ]
        
        formatted_prompt = tokenizer.apply_chat_template(
            messages, 
            tokenize=False, 
            add_generation_prompt=True
        )
        
        inputs = tokenizer(
            formatted_prompt, 
            return_tensors="pt", 
            truncation=True, 
            max_length=8192
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
    """
    Perform comprehensive CDI analysis as Senior Medical Auditor
    Returns structured JSON with diagnoses, evidence, and DRG costs
    """
    
    analysis_prompt = f"""## المهمة: تحليل CDI شامل ودقيق

اقرأ الملاحظات السريرية التالية بعناية فائقة وقم بتحليلها كمدقق طبي أول.

=== الملاحظات السريرية ===
{formatted_notes}

=== المطلوب بدقة ===

### 1. التشخيص الرئيسي (واحد فقط):
- حدد السبب الرئيسي الذي أدى لدخول المريض
- اقتبس الدليل من الملاحظات بالضبط
- اذكر كود ICD-10-AM الدقيق

### 2. التشخيصات الثانوية (جميعها):
لكل تشخيص ثانوي:
- اسم التشخيص
- التصنيف: (CC = مرض مصاحب / Complication = مضاعفة / Other = أخرى)
- الدليل: اقتباس من الملاحظات
- كود ICD-10-AM

### 3. ثغرات التوثيق:
ما ينقص من المعلومات التي تؤثر على الترميز:
- معلومات ناقصة عن شدة المرض
- تفاصيل غير موثقة
- علاقات سببية غير واضحة

### 4. استفسارات للطبيب (مهم جداً):
لكل تشخيص محتمل وجدت له أدلة في الملاحظات لكنه غير موثق صراحة:

الصيغة المطلوبة:
"استفسار: [التشخيص المحتمل]
الدليل من الملاحظات: [اقتباس دقيق]
السؤال للطبيب: [سؤال محدد]
التأثير: [كيف سيؤثر على DRG/الترميز]"

=== الرد بصيغة JSON فقط ===
{{
    "principal_diagnosis": {{
        "diagnosis_ar": "التشخيص الرئيسي بالعربية مع التفاصيل",
        "diagnosis_en": "Principal Diagnosis with details",
        "icd_code": "كود ICD-10-AM",
        "evidence_ar": "الدليل المقتبس من الملاحظات بالعربية",
        "evidence_en": "Evidence quoted from notes"
    }},
    "secondary_diagnoses": [
        {{
            "diagnosis_ar": "التشخيص بالعربية",
            "diagnosis_en": "Diagnosis in English",
            "icd_code": "ICD-10-AM",
            "category": "comorbidity/complication/other",
            "evidence_ar": "الدليل المقتبس من الملاحظات",
            "evidence_en": "Evidence from notes",
            "affects_drg": true
        }}
    ],
    "documentation_gaps": [
        {{
            "gap_ar": "وصف الثغرة بالعربية",
            "gap_en": "Gap description",
            "clinical_indicator": "المؤشر السريري الموجود",
            "missing_info": "المعلومة الناقصة",
            "impact_ar": "التأثير على الترميز",
            "impact_en": "Impact on coding"
        }}
    ],
    "physician_queries": [
        {{
            "target_diagnosis": "التشخيص المستهدف",
            "evidence_from_notes": "الدليل المقتبس من الملاحظات الذي يدعم هذا التشخيص",
            "query_ar": "السؤال الكامل للطبيب بالعربية مع ذكر الدليل",
            "query_en": "Full query for physician with evidence",
            "potential_icd_code": "الكود المحتمل",
            "priority": "high/medium/low",
            "drg_impact": "التأثير على DRG"
        }}
    ],
    "recommendations_ar": ["توصية 1", "توصية 2"],
    "recommendations_en": ["Recommendation 1", "Recommendation 2"],
    "summary_ar": "ملخص شامل للحالة والتوصيات",
    "summary_en": "Comprehensive case summary"
}}

⚠️ مهم: 
- كل استفسار يجب أن يحتوي على دليل مقتبس من الملاحظات
- لا تضع استفسارات بدون أدلة داعمة
- ركز على التشخيصات التي لها مؤشرات سريرية لكنها غير موثقة صراحة
- الرد يجب أن يكون JSON صالح فقط بدون أي نص إضافي"""

    try:
        response_text = generate_text(analysis_prompt, max_new_tokens=4000, temperature=0.1)
        result = parse_json_response(response_text)
        
        # Enhance with DRG pricing
        result = enhance_with_drg_pricing(result, hospital_type)
        
        # Validate structure
        if not result.get('principal_diagnosis'):
            result = extract_diagnoses_fallback(formatted_notes, response_text)
            result = enhance_with_drg_pricing(result, hospital_type)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Analysis error: {str(e)}")
        raise


def parse_json_response(response_text: str) -> Dict:
    """Parse JSON from model response with fallback handling"""
    try:
        # Clean response
        text = response_text.strip()
        
        # Remove markdown code blocks
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        
        # Find JSON object
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            text = json_match.group(0)
        
        return json.loads(text)
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {str(e)}")
        return create_fallback_result(response_text)


def create_fallback_result(response_text: str) -> Dict:
    """Create a structured result when JSON parsing fails"""
    return {
        "principal_diagnosis": {
            "diagnosis_ar": "يرجى مراجعة التحليل",
            "diagnosis_en": "Please review analysis",
            "icd_code": "",
            "evidence_ar": "",
            "evidence_en": ""
        },
        "secondary_diagnoses": [],
        "documentation_gaps": [],
        "physician_queries": [],
        "recommendations_ar": ["مراجعة التحليل النصي"],
        "recommendations_en": ["Review text analysis"],
        "summary_ar": response_text[:1500] if response_text else "لا يوجد تحليل",
        "summary_en": f"Raw analysis: {response_text[:1500] if response_text else 'No analysis'}"
    }


def extract_diagnoses_fallback(notes: str, response_text: str) -> Dict:
    """Fallback extraction when structured parsing fails"""
    return create_fallback_result(response_text)


def enhance_with_drg_pricing(result: Dict, hospital_type: str = "A") -> Dict:
    """Add DRG pricing information using RAG lookup"""
    try:
        global _drg_lookup
        if _drg_lookup is None:
            _drg_lookup = get_drg_lookup(hospital_type=hospital_type)
        
        # Get principal diagnosis ICD code
        principal = result.get('principal_diagnosis', {})
        icd_code = principal.get('icd_code', '')
        
        if icd_code:
            drg_info = _drg_lookup.lookup_by_icd(icd_code)
            if drg_info:
                principal['drg_code'] = drg_info.get('drg_code', '')
                principal['drg_description'] = drg_info.get('description', '')
                principal['drg_cost'] = drg_info.get('price', '')
                principal['drg_weight'] = drg_info.get('weight', '')
        
        # Add DRG info to secondary diagnoses
        for diag in result.get('secondary_diagnoses', []):
            sec_icd = diag.get('icd_code', '')
            if sec_icd:
                drg_info = _drg_lookup.lookup_by_icd(sec_icd)
                if drg_info:
                    diag['drg_code'] = drg_info.get('drg_code', '')
                    diag['drg_cost'] = drg_info.get('price', '')
        
        return result
        
    except Exception as e:
        logger.error(f"DRG lookup error: {str(e)}")
        return result
