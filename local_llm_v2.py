"""
MediDoc AI - Local LLM Module (100% Offline)
Uses Qwen2.5-72B-Instruct with 4-bit quantization for A100 40GB
Role: Senior Medical Auditor for Clinical Documentation Improvement (CDI)

FOCUS: Discovering UNDOCUMENTED diagnoses and generating evidence-based queries
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

# === CDI Specialist System Prompt - Focus on UNDOCUMENTED Diagnoses ===
SENIOR_AUDITOR_PROMPT = """أنت أخصائي تحسين التوثيق السريري (CDI Specialist) بخبرة عالية.

## مهمتك الأساسية:
اكتشاف التشخيصات التي **لم تُوثَّق صراحةً** في الملاحظات السريرية، لكن يوجد لها **معطيات ومؤشرات سريرية** تدعمها.

## ما يجب أن تفعله:

### 1. البحث عن التشخيصات غير الموثقة:
ابحث عن مؤشرات سريرية (قيم مخبرية، أعراض، علامات، أدوية) تشير إلى تشخيصات **لم يذكرها الطبيب صراحة**.

أمثلة:
- HbA1c = 9.5% ← يدل على سكري غير مسيطر عليه (هل وُثِّق؟)
- Creatinine = 3.2, GFR = 25 ← يدل على CKD Stage 4 (هل وُثِّقت المرحلة؟)
- EF = 30% ← يدل على قصور قلب انقباضي (هل وُثِّق النوع؟)
- مريض على Metformin + Insulin ← سكري (هل وُثِّق النوع والمضاعفات؟)
- BNP = 1500 + تورم الأطراف ← قصور قلب (هل وُثِّق؟)

### 2. توليد استفسارات للطبيب:
لكل تشخيص غير موثق وجدت له معطيات، أنشئ استفساراً يتضمن:
- **المعطيات الداعمة**: القيم/الأعراض من الملاحظات
- **التشخيص المحتمل**: ما يجب توثيقه
- **طلب التوضيح**: النوع، الشدة، المرحلة، السبب

### 3. طلب تحديد التفاصيل الناقصة:
لكل تشخيص موثق، تحقق هل يحتاج توضيح:
- **النوع (Type)**: انقباضي/انبساطي، Type 1/Type 2
- **الشدة (Severity)**: خفيف/متوسط/شديد، مسيطر/غير مسيطر
- **المرحلة (Stage)**: Stage 1-5 للكلى، NYHA Class للقلب
- **السبب (Etiology)**: ما سبب الحالة؟

## أمثلة على الاستفسارات الصحيحة:

### مثال 1 - سكري:
"بناءً على: HbA1c = 10.2% والمريض على Insulin
السؤال: هل السكري من النوع الأول أم الثاني؟ وهل هو مسيطر عليه أم غير مسيطر؟
التأثير: يؤثر على كود ICD وDRG"

### مثال 2 - الكلى:
"بناءً على: Creatinine = 2.8 mg/dL و GFR = 28 mL/min
السؤال: يرجى توثيق مرحلة مرض الكلى المزمن (CKD Stage 4 بناءً على GFR)
التأثير: N18.4 بدلاً من N18.9"

### مثال 3 - القلب:
"بناءً على: EF = 35% وBNP = 1200 pg/mL وتورم الأطراف السفلية
السؤال: هل يوجد قصور قلب؟ وإذا نعم، هل هو انقباضي أم انبساطي؟ وما درجته (NYHA)؟
التأثير: توثيق I50.20-23 للانقباضي أو I50.30-33 للانبساطي"

### مثال 4 - الإنتان:
"بناءً على: WBC = 18,000 وحرارة 39.5 وضغط 85/50 ولاكتيت = 4
السؤال: هل يوجد إنتان؟ وهل هو إنتان شديد أو صدمة إنتانية؟
التأثير: A41.9 للإنتان، R65.20 للشديد، R65.21 مع صدمة"

## قواعد مهمة:
1. ركّز على التشخيصات **غير الموثقة** أكثر من الموثقة
2. كل استفسار يجب أن يحتوي على **دليل/معطى من الملاحظات**
3. اطلب دائماً: النوع، الشدة، المرحلة، السبب
4. لا تفترض تشخيصاً بدون معطيات داعمة

## مرجع أكواد ICD-10-AM:

السكري (Diabetes):
- E11.9 Type 2 غير محدد | E10.9 Type 1 غير محدد
- E11.65 Type 2 مع ارتفاع سكر | E11.69 مع مضاعفات أخرى
- E11.40 مع اعتلال عصبي | E11.21 مع اعتلال كلوي
- E11.22 مع CKD | E11.31 مع اعتلال شبكية

الكلى (Kidney):
- N18.1 CKD Stage 1 (GFR ≥90)
- N18.2 CKD Stage 2 (GFR 60-89)
- N18.3 CKD Stage 3 (GFR 30-59)
- N18.4 CKD Stage 4 (GFR 15-29)
- N18.5 CKD Stage 5 (GFR <15)
- N17.9 AKI غير محدد

القلب (Heart Failure):
- I50.20 Systolic unspecified | I50.21 Acute systolic
- I50.22 Chronic systolic | I50.23 Acute on chronic systolic
- I50.30 Diastolic unspecified | I50.31 Acute diastolic
- I50.32 Chronic diastolic | I50.33 Acute on chronic diastolic
- I50.40 Combined | I50.9 Unspecified

ارتفاع الضغط (Hypertension):
- I10 Essential | I11.0 مع قصور قلب | I11.9 مع مرض قلبي
- I12.0 مع CKD Stage 5 | I12.9 مع CKD
- I13.0 مع قلب وكلى Stage 5 | I13.10 مع قلب وكلى

الإنتان (Sepsis):
- A41.9 غير محدد | A41.01 MSSA | A41.02 MRSA
- R65.20 Severe sepsis without shock
- R65.21 Severe sepsis with septic shock
"""

# Chat-specific prompt for discussions
CDI_CHAT_PROMPT = """أنت أخصائي تحسين التوثيق السريري (CDI Specialist).

## دورك في المناقشة:
1. **اكتشاف التشخيصات غير الموثقة**: ابحث عن مؤشرات سريرية تدل على تشخيصات لم تُذكر
2. **توليد استفسارات**: ساعد في صياغة أسئلة للطبيب مدعومة بالأدلة
3. **توضيح التفاصيل**: اشرح لماذا نحتاج النوع/الشدة/المرحلة

## عند الإجابة:
- إذا سُئلت عن تشخيص، ابحث عن معطيات تدعمه في الملاحظات
- إذا وجدت مؤشرات لتشخيص غير موثق، اقترح استفساراً للطبيب
- اذكر دائماً الدليل من الملاحظات
- اقترح الكود ICD-10 المناسب

## مثال على الإجابة الجيدة:
المستخدم: "هل يوجد قصور قلب؟"
الإجابة: "نعم، يوجد مؤشرات تدعم قصور القلب:
- EF = 35% (يدل على ضعف الانقباض)
- BNP = 1200 (مرتفع جداً)
- تورم الأطراف السفلية

استفسار مقترح للطبيب:
'بناءً على EF 35% وBNP 1200، هل يمكن توثيق قصور قلب انقباضي (I50.22) وتحديد درجته؟'

لم يُوثَّق: النوع (انقباضي/انبساطي) ودرجة NYHA"
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


def generate_text(prompt: str, max_new_tokens: int = 3000, temperature: float = 0.1, use_chat_prompt: bool = False) -> str:
    """Generate text using the loaded model"""
    try:
        model, tokenizer = get_model()
        device = next(model.parameters()).device
        
        # Choose appropriate system prompt
        system_prompt = CDI_CHAT_PROMPT if use_chat_prompt else SENIOR_AUDITOR_PROMPT
        
        messages = [
            {"role": "system", "content": system_prompt},
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
    Perform comprehensive CDI analysis focusing on UNDOCUMENTED diagnoses
    """
    
    analysis_prompt = f"""## مهمة تحليل CDI - التركيز على التشخيصات غير الموثقة

اقرأ الملاحظات السريرية التالية بدقة عالية.

=== الملاحظات السريرية ===
{formatted_notes}

=== المطلوب ===

### 1. التشخيص الرئيسي (السبب الرئيسي للدخول):
حدد التشخيص الرئيسي مع:
- الدليل من الملاحظات
- كود ICD-10-AM
- هل النوع/الشدة/المرحلة موثقة؟ إذا لا، اذكر ذلك

### 2. التشخيصات الثانوية الموثقة:
لكل تشخيص مذكور في الملاحظات:
- هل النوع محدد؟ (Type 1/2, انقباضي/انبساطي)
- هل الشدة محددة؟ (خفيف/متوسط/شديد، مسيطر/غير مسيطر)
- هل المرحلة محددة؟ (Stage 1-5)
- هل السبب محدد؟

### 3. التشخيصات غير الموثقة (الأهم!):
ابحث عن معطيات سريرية تشير إلى تشخيصات **لم تُذكر صراحة**:
- قيم مخبرية غير طبيعية بدون تشخيص مقابل
- أعراض/علامات بدون تشخيص
- أدوية بدون تشخيص موثق لاستخدامها

لكل معطى وجدته، اذكر:
- المعطى/الدليل من الملاحظات
- التشخيص المحتمل غير الموثق
- كود ICD-10-AM المحتمل

### 4. استفسارات للطبيب (لكل تشخيص غير موثق):
صيغة كل استفسار:
"بناءً على: [المعطيات من الملاحظات]
التشخيص المحتمل: [التشخيص + الكود]
السؤال: [ما يجب على الطبيب توثيقه - النوع/الشدة/المرحلة/السبب]
التأثير: [على الترميز/DRG]"

=== الرد بصيغة JSON فقط ===
{{
    "principal_diagnosis": {{
        "diagnosis_ar": "التشخيص الرئيسي",
        "diagnosis_en": "Principal Diagnosis",
        "icd_code": "كود ICD-10-AM",
        "evidence_ar": "الدليل من الملاحظات",
        "evidence_en": "Evidence from notes",
        "missing_details": ["النوع غير محدد", "الشدة غير محددة"] 
    }},
    "secondary_diagnoses": [
        {{
            "diagnosis_ar": "التشخيص",
            "diagnosis_en": "Diagnosis",
            "icd_code": "ICD-10-AM",
            "category": "comorbidity/complication/other",
            "evidence_ar": "الدليل",
            "evidence_en": "Evidence",
            "is_fully_documented": false,
            "missing_details": ["النوع", "الشدة", "المرحلة"],
            "affects_drg": true
        }}
    ],
    "undocumented_diagnoses": [
        {{
            "clinical_indicator_ar": "المؤشر السريري من الملاحظات",
            "clinical_indicator_en": "Clinical indicator from notes",
            "suggested_diagnosis_ar": "التشخيص المحتمل",
            "suggested_diagnosis_en": "Potential diagnosis",
            "potential_icd_code": "الكود المحتمل",
            "confidence": "high/medium/low",
            "reason_not_documented": "لم يُذكر صراحة في التوثيق"
        }}
    ],
    "documentation_gaps": [
        {{
            "gap_ar": "الثغرة",
            "gap_en": "Gap",
            "clinical_indicator": "المؤشر الموجود",
            "what_is_missing": "ما ينقص (النوع/الشدة/المرحلة/السبب)",
            "impact_ar": "التأثير",
            "impact_en": "Impact"
        }}
    ],
    "physician_queries": [
        {{
            "evidence_from_notes": "المعطيات/الدليل من الملاحظات (اقتباس دقيق)",
            "potential_diagnosis": "التشخيص المحتمل غير الموثق",
            "potential_icd_code": "الكود المحتمل",
            "query_ar": "بناءً على [الدليل]، يرجى توثيق [التشخيص] مع تحديد [النوع/الشدة/المرحلة]",
            "query_en": "Based on [evidence], please document [diagnosis] specifying [type/severity/stage]",
            "details_needed": ["النوع", "الشدة", "المرحلة", "السبب"],
            "priority": "high/medium/low",
            "drg_impact": "التأثير على DRG"
        }}
    ],
    "summary_ar": "ملخص: عدد التشخيصات غير الموثقة، والثغرات الرئيسية",
    "summary_en": "Summary: undocumented diagnoses count and main gaps"
}}

⚠️ تذكر:
- ركز على التشخيصات **غير الموثقة** التي لها معطيات داعمة
- كل استفسار يجب أن يحتوي على **دليل مقتبس من الملاحظات**
- اطلب دائماً: النوع، الشدة، المرحلة، السبب
- الرد JSON فقط بدون أي نص آخر"""

    try:
        response_text = generate_text(analysis_prompt, max_new_tokens=4000, temperature=0.1)
        result = parse_json_response(response_text)
        
        # Enhance with DRG pricing
        result = enhance_with_drg_pricing(result, hospital_type)
        
        # Validate structure
        if not result.get('principal_diagnosis'):
            result = create_fallback_result(response_text)
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
            "evidence_en": "",
            "missing_details": []
        },
        "secondary_diagnoses": [],
        "undocumented_diagnoses": [],
        "documentation_gaps": [],
        "physician_queries": [],
        "summary_ar": response_text[:1500] if response_text else "لا يوجد تحليل",
        "summary_en": f"Raw analysis: {response_text[:1500] if response_text else 'No analysis'}"
    }


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
        
        # Add DRG info to undocumented diagnoses
        for diag in result.get('undocumented_diagnoses', []):
            pot_icd = diag.get('potential_icd_code', '')
            if pot_icd:
                drg_info = _drg_lookup.lookup_by_icd(pot_icd)
                if drg_info:
                    diag['potential_drg_code'] = drg_info.get('drg_code', '')
                    diag['potential_drg_cost'] = drg_info.get('price', '')
        
        return result
        
    except Exception as e:
        logger.error(f"DRG lookup error: {str(e)}")
        return result
