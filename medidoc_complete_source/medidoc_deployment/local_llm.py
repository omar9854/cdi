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

# === Senior Medical Auditor System Prompt (High Accuracy) ===
SENIOR_AUDITOR_PROMPT = """أنت مدقق طبي أول ومتخصص في تحسين التوثيق السريري (CDI) بخبرة تزيد عن 20 عاماً في الترميز الطبي وتحسين مجموعات التشخيص (DRG).

You are a Senior Medical Auditor and Clinical Documentation Improvement (CDI) Specialist with 20+ years of experience in medical coding and DRG optimization.

### دورك ونطاق عملك | YOUR ROLE AND SCOPE:
- مراجعة التوثيق السريري بدقة متناهية
- تحديد جميع التشخيصات من الملاحظات السريرية (الصريحة والمضمنة)
- التمييز الواضح بين التشخيص الرئيسي والتشخيصات الثانوية
- استخراج الأدلة السريرية المحددة لكل تشخيص
- تعيين أكواد ICD-10-AM بدقة
- تحديد الثغرات في التوثيق التي تؤثر على تعيين DRG
- توليد استفسارات للأطباء مدعومة بأدلة من الحالة

⚠️ قيود مهمة | IMPORTANT CONSTRAINTS:
- لا تخرج عن نطاق تحسين التوثيق السريري (CDI)
- جميع الاستفسارات يجب أن تكون متعلقة بالحالة السريرية فقط
- لا تجيب على أسئلة خارج نطاق التوثيق الطبي
- كل استفسار يجب أن يكون مدعوماً بدليل من الملاحظات السريرية

### قواعد تصنيف التشخيص | DIAGNOSIS CLASSIFICATION RULES:
1. التشخيص الرئيسي (PRINCIPAL DIAGNOSIS): 
   - الحالة التي ثبت بعد الدراسة أنها السبب الرئيسي للدخول
   - يوجد تشخيص رئيسي واحد فقط
   
2. التشخيصات الثانوية (SECONDARY DIAGNOSES):
   - الأمراض المصاحبة (Comorbidity/CC): حالات موجودة مسبقاً تؤثر على العلاج
   - المضاعفات (Complication): حالات تنشأ أثناء الإقامة في المستشفى
   - أخرى (Other): تشخيصات إضافية لا تستوفي معايير CC

### استخراج الأدلة | EVIDENCE EXTRACTION:
لكل تشخيص، يجب استخراج النص الداعم الدقيق من الملاحظات السريرية.
الصيغة: "الدليل: [اقتباس دقيق من الملاحظات]"
Format: "Evidence: [exact quote from notes]"

### معايير ترميز ICD-10-AM | ICD-10-AM CODING STANDARDS:
- استخدم أكواد التعديل الأسترالي (ICD-10-AM)
- ضمّن جميع التفاصيل ذات الصلة (الجانبية، الشدة، المرحلة)
- رمّز إلى أعلى مستوى من التحديد المدعوم بالتوثيق

### توليد الاستفسارات | QUERY GENERATION:
كل استفسار للطبيب يجب أن يتضمن:
1. السؤال المحدد
2. الدليل السريري الداعم من الملاحظات
3. تأثير الإجابة على الترميز/DRG

مثال | Example:
"هل يعاني المريض من قصور قلب انقباضي أو انبساطي؟ (بناءً على: EF 35% وBNP مرتفع 1200)"
"Is the heart failure systolic or diastolic? (Based on: EF 35% and elevated BNP 1200)"
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
    
    Args:
        formatted_notes: Clinical notes text
        hospital_type: "A" (Tertiary), "B" (Non-medical city), "C" (< 50 beds)
    """
    
    analysis_prompt = f"""كمدقق طبي أول، قم بتحليل التوثيق السريري التالي بدقة عالية.
As a Senior Medical Auditor, analyze the following clinical documentation thoroughly.

=== الملاحظات السريرية | CLINICAL NOTES ===
{formatted_notes}

=== المطلوب | TASK ===
1. حدد التشخيص الرئيسي (واحد فقط - السبب الرئيسي للدخول)
   Identify the PRINCIPAL DIAGNOSIS (one only - main reason for admission)

2. حدد جميع التشخيصات الثانوية مع تصنيفها:
   Identify ALL SECONDARY DIAGNOSES with classification:
   - الأمراض المصاحبة (CC): حالات موجودة مسبقاً تؤثر على العلاج
   - المضاعفات: حالات تنشأ أثناء الإقامة
   - أخرى: تشخيصات إضافية

3. لكل تشخيص، استخرج الدليل الدقيق من الملاحظات
   For EACH diagnosis, extract the EXACT supporting evidence from the notes

4. عيّن أكواد ICD-10-AM بدقة
   Assign accurate ICD-10-AM codes

5. حدد ثغرات التوثيق وأنشئ استفسارات للأطباء مدعومة بالأدلة
   Identify documentation gaps and create evidence-based physician queries

=== مرجع أكواد ICD-10-AM | ICD-10-AM REFERENCE ===
الداء السكري Type 2 Diabetes:
- E11.9 (غير محدد unspecified)
- E11.65 (مع ارتفاع سكر الدم with hyperglycemia)
- E11.40 (مع اعتلال عصبي with neuropathy)
- E11.21 (مع اعتلال كلوي with nephropathy)
- E11.22 (مع مرض الكلى المزمن with CKD)
- E11.31 (مع اعتلال شبكية with retinopathy)
- E11.51 (مع اعتلال وعائي محيطي with peripheral angiopathy)

مرض الكلى المزمن CKD:
- N18.1 (المرحلة 1 stage 1), N18.2 (المرحلة 2 stage 2)
- N18.3 (المرحلة 3 stage 3), N18.4 (المرحلة 4 stage 4)
- N18.5 (المرحلة 5/ESKD stage 5), N17.9 (AKI)

قصور القلب Heart Failure:
- I50.9 (غير محدد unspecified)
- I50.20/21/22/23 (انقباضي systolic)
- I50.30/31/32/33 (انبساطي diastolic)
- I50.40/41/42/43 (مختلط combined)

ارتفاع ضغط الدم Hypertension:
- I10 (أساسي essential)
- I11.0/9 (مع مرض قلبي with heart disease)
- I12.0/9 (مع مرض الكلى with CKD)
- I13.x (مع مرض قلبي وكلوي with heart and CKD)

الإنتان Sepsis:
- A41.9 (غير محدد unspecified)
- A41.01 (MSSA), A41.02 (MRSA)
- R65.20 (شديد بدون صدمة severe without shock)
- R65.21 (شديد مع صدمة إنتانية with septic shock)

السكتة الدماغية Stroke:
- I63.x (احتشاء دماغي cerebral infarction)
- I61.x (نزيف داخل المخ intracerebral hemorrhage)

=== الرد بصيغة JSON فقط | RESPOND WITH VALID JSON ONLY ===
{{
    "principal_diagnosis": {{
        "diagnosis_ar": "التشخيص الرئيسي بالعربية",
        "diagnosis_en": "Principal Diagnosis in English",
        "icd_code": "ICD-10-AM Code",
        "evidence_ar": "الدليل السريري الدقيق من الملاحظات بالعربية",
        "evidence_en": "Exact clinical evidence from notes in English"
    }},
    "secondary_diagnoses": [
        {{
            "diagnosis_ar": "التشخيص بالعربية",
            "diagnosis_en": "Diagnosis in English",
            "icd_code": "ICD-10-AM Code",
            "category": "comorbidity أو complication أو other",
            "evidence_ar": "الدليل السريري الدقيق من الملاحظات",
            "evidence_en": "Exact clinical evidence from notes",
            "affects_drg": true/false
        }}
    ],
    "documentation_gaps": [
        {{
            "gap_ar": "الثغرة بالعربية",
            "gap_en": "Gap description in English",
            "impact_ar": "التأثير على الترميز/DRG",
            "impact_en": "Impact on coding/DRG"
        }}
    ],
    "physician_queries": [
        {{
            "query_ar": "الاستفسار بالعربية مع الدليل: (بناءً على: [الدليل السريري])",
            "query_en": "Query in English with evidence: (Based on: [clinical evidence])",
            "evidence_ar": "الدليل المستخرج من الملاحظات",
            "evidence_en": "Evidence extracted from notes",
            "priority": "high أو medium أو low",
            "impact_on_drg": "تأثير الإجابة على DRG"
        }}
    ],
    "summary_ar": "ملخص التحليل بالعربية",
    "summary_en": "Analysis summary in English"
}}"""

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
                principal['estimated_cost'] = drg_info.get('price', 0.0)
                principal['alos'] = drg_info.get('alos', 0.0)
        
        # Count CCs for adjustment
        cc_count = 0
        for secondary in result.get('secondary_diagnoses', []):
            if secondary.get('category') == 'comorbidity':
                cc_count += 1
                secondary['affects_drg'] = True
                
                # Look up secondary diagnosis cost impact
                sec_icd = secondary.get('icd_code', '')
                if sec_icd:
                    sec_drg = _drg_lookup.lookup_by_icd(sec_icd)
                    if sec_drg:
                        secondary['drg_code'] = sec_drg.get('drg_code', '')
        
        # Calculate final DRG cost with CC adjustments
        base_price = principal.get('estimated_cost', 0.0)
        cc_adjustment = cc_count * (base_price * 0.10) if base_price > 0 else 0
        final_price = base_price + cc_adjustment
        
        # Add DRG summary
        result['drg_summary'] = {
            "primary_drg_code": principal.get('drg_code', ''),
            "primary_drg_description": principal.get('drg_description', ''),
            "base_price": round(base_price, 2),
            "cc_count": cc_count,
            "cc_adjustment": round(cc_adjustment, 2),
            "total_estimated_cost": round(final_price, 2),
            "hospital_type": hospital_type,
            "currency": "SAR",
            "alos": principal.get('alos', 0.0)
        }
        
        return result
        
    except Exception as e:
        logger.warning(f"⚠️ DRG enhancement error: {str(e)}")
        return result


def extract_diagnoses_fallback(notes: str, analysis_text: str) -> Dict:
    """Fallback extraction when JSON parsing fails"""
    
    notes_lower = notes.lower()
    principal = None
    secondary = []
    queries = []
    
    # Detect principal diagnosis from keywords
    if any(kw in notes_lower for kw in ['diabetes', 'hba1c', 'glucose', 'metformin', 'السكري', 'سكر']):
        hba1c_high = any(x in notes for x in ['8.', '9.', '10.', '11.', '12.'])
        principal = {
            "diagnosis_ar": "داء السكري النوع الثاني" + (" مع سوء التحكم في سكر الدم" if hba1c_high else ""),
            "diagnosis_en": "Type 2 Diabetes Mellitus" + (" with poor glycemic control" if hba1c_high else ""),
            "icd_code": "E11.65" if hba1c_high else "E11.9",
            "evidence_ar": "تاريخ مرضي للسكري مع HbA1c مرتفع" if hba1c_high else "مريض يتناول أدوية السكري",
            "evidence_en": "Patient has diabetes history with elevated HbA1c" if hba1c_high else "Patient on diabetes medications"
        }
    
    # Secondary diagnoses
    if any(kw in notes_lower for kw in ['numbness', 'tingling', 'neuropathy', 'تنميل', 'اعتلال عصبي']):
        secondary.append({
            "diagnosis_ar": "اعتلال الأعصاب السكري المحيطي",
            "diagnosis_en": "Diabetic peripheral neuropathy",
            "icd_code": "E11.40",
            "category": "complication",
            "evidence_ar": "تنميل ثنائي في القدمين",
            "evidence_en": "Bilateral foot numbness and tingling",
            "affects_drg": True
        })
    
    if any(kw in notes_lower for kw in ['creatinine', 'proteinuria', 'kidney', 'ckd', 'كرياتينين', 'كلى']):
        secondary.append({
            "diagnosis_ar": "مرض الكلى المزمن / اعتلال الكلى السكري",
            "diagnosis_en": "Chronic Kidney Disease / Diabetic nephropathy",
            "icd_code": "E11.22",
            "category": "complication",
            "evidence_ar": "ارتفاع الكرياتينين ووجود بروتين في البول",
            "evidence_en": "Elevated creatinine and proteinuria",
            "affects_drg": True
        })
        
        queries.append({
            "query_ar": "ما هي مرحلة مرض الكلى المزمن؟ (بناءً على: ارتفاع الكرياتينين ووجود بروتين في البول)",
            "query_en": "What is the CKD stage? (Based on: elevated creatinine and proteinuria in lab results)",
            "evidence_ar": "قيم الكرياتينين والبروتين في نتائج المختبر",
            "evidence_en": "Creatinine and protein values in lab results",
            "priority": "high",
            "impact_on_drg": "تحديد المرحلة يؤثر على كود ICD وDRG"
        })
    
    if any(kw in notes_lower for kw in ['retinopathy', 'eye exam', 'شبكية', 'اعتلال شبكية']):
        secondary.append({
            "diagnosis_ar": "اعتلال الشبكية السكري",
            "diagnosis_en": "Diabetic retinopathy",
            "icd_code": "E11.31",
            "category": "complication",
            "evidence_ar": "نتائج فحص العيون",
            "evidence_en": "Ophthalmology exam findings",
            "affects_drg": True
        })
    
    if any(kw in notes_lower for kw in ['hypertension', 'blood pressure', 'bp ', 'lisinopril', 'ضغط', 'ارتفاع ضغط']):
        secondary.append({
            "diagnosis_ar": "ارتفاع ضغط الدم الأساسي",
            "diagnosis_en": "Essential hypertension",
            "icd_code": "I10",
            "category": "comorbidity",
            "evidence_ar": "ضغط دم مرتفع، يتناول خافض للضغط",
            "evidence_en": "Elevated blood pressure, on antihypertensive",
            "affects_drg": True
        })
    
    if any(kw in notes_lower for kw in ['heart failure', 'chf', 'bnp', 'ef ', 'قصور قلب']):
        secondary.append({
            "diagnosis_ar": "قصور القلب",
            "diagnosis_en": "Heart failure",
            "icd_code": "I50.9",
            "category": "comorbidity",
            "evidence_ar": "قصور القلب موثق",
            "evidence_en": "Heart failure documented",
            "affects_drg": True
        })
        
        queries.append({
            "query_ar": "هل قصور القلب انقباضي أم انبساطي؟ (بناءً على: EF ومستوى BNP)",
            "query_en": "Is the heart failure systolic or diastolic? (Based on: EF and BNP level)",
            "evidence_ar": "نتائج Echo وBNP",
            "evidence_en": "Echo results and BNP level",
            "priority": "high",
            "impact_on_drg": "تحديد النوع يغير كود ICD من I50.9 إلى I50.2x/I50.3x"
        })
    
    if any(kw in notes_lower for kw in ['chest pain', 'angina', 'ألم صدر']):
        secondary.append({
            "diagnosis_ar": "ألم الصدر",
            "diagnosis_en": "Chest pain, unspecified",
            "icd_code": "R07.9",
            "category": "other",
            "evidence_ar": "شكوى المريض من ألم صدر عند المجهود",
            "evidence_en": "Patient reports chest pain on exertion",
            "affects_drg": False
        })
        
        queries.append({
            "query_ar": "هل ألم الصدر قلبي المنشأ؟ (بناءً على: شكوى المريض من ألم صدر عند المجهود)",
            "query_en": "Is the chest pain cardiac in origin? (Based on: patient reports exertional chest pain)",
            "evidence_ar": "ألم الصدر عند المجهود",
            "evidence_en": "Exertional chest pain",
            "priority": "high",
            "impact_on_drg": "تحديد السبب قد يغير DRG بشكل كبير"
        })
    
    if principal is None:
        principal = {
            "diagnosis_ar": "يرجى المراجعة اليدوية",
            "diagnosis_en": "Manual review required",
            "icd_code": "R69",
            "evidence_ar": "غير قادر على تحديد التشخيص الرئيسي تلقائياً",
            "evidence_en": "Unable to determine principal diagnosis automatically"
        }
    
    return {
        "principal_diagnosis": principal,
        "secondary_diagnoses": secondary,
        "documentation_gaps": [
            {
                "gap_ar": "تفاصيل غير محددة في التوثيق",
                "gap_en": "Unspecified details in documentation",
                "impact_ar": "يؤثر على دقة الترميز وDRG",
                "impact_en": "Affects coding accuracy and DRG"
            }
        ],
        "physician_queries": queries if queries else [{
            "query_ar": "يرجى مراجعة التوثيق مع الطبيب المعالج",
            "query_en": "Please review documentation with treating physician",
            "evidence_ar": "مراجعة عامة مطلوبة",
            "evidence_en": "General review required",
            "priority": "medium",
            "impact_on_drg": "قد يحسن دقة التشخيص والترميز"
        }],
        "summary_ar": f"تم تحديد تشخيص رئيسي واحد و {len(secondary)} تشخيصات ثانوية. يوجد ثغرات في التوثيق تحتاج معالجة.",
        "summary_en": f"Identified 1 principal diagnosis and {len(secondary)} secondary diagnoses. Documentation gaps require attention."
    }


def chat_with_context(message: str, context: str, history: List = None) -> str:
    """
    CDI-focused chat - STRICTLY rejects off-topic questions
    يرفض بشكل صارم الأسئلة خارج نطاق CDI
    """
    
    # Expanded off-topic keywords
    off_topic = [
        # English
        'weather', 'news', 'sports', 'politics', 'movie', 'music', 'recipe', 
        'joke', 'story', 'game', 'travel', 'shopping', 'food', 'restaurant',
        'code', 'programming', 'python', 'javascript', 'html', 'css',
        'write me', 'create', 'generate', 'make me', 'build',
        'stock', 'crypto', 'bitcoin', 'investment', 'money',
        'relationship', 'love', 'dating', 'marriage',
        'hello', 'hi there', 'how are you', 'what can you do',
        # Arabic
        'الطقس', 'أخبار', 'رياضة', 'سياسة', 'فيلم', 'موسيقى', 'وصفة', 
        'نكتة', 'قصة', 'لعبة', 'سفر', 'تسوق', 'طعام', 'مطعم',
        'برمجة', 'اكتب لي', 'أنشئ', 'اصنع',
        'أسهم', 'عملات', 'بيتكوين', 'استثمار', 'مال',
        'علاقة', 'حب', 'زواج',
        'مرحبا', 'كيف حالك', 'ماذا تفعل'
    ]
    
    msg_lower = message.lower()
    if any(kw in msg_lower for kw in off_topic):
        return """عذراً، أنا مدقق طبي أول متخصص حصرياً في تحسين التوثيق السريري (CDI).
لا أستطيع الإجابة على أسئلة خارج نطاق الحالة السريرية.

يمكنني مساعدتك في:
• شرح التشخيصات الرئيسية والثانوية في الحالة الحالية
• توضيح أكواد ICD-10-AM وتأثيرها على DRG
• مناقشة الأدلة السريرية الداعمة للتشخيصات
• تقديم استفسارات للطبيب لتحسين التوثيق
• حساب تكلفة DRG التقديرية

---

Sorry, I am a Senior Medical Auditor specializing EXCLUSIVELY in Clinical Documentation Improvement (CDI).
I cannot answer questions outside the scope of the clinical case.

I can help you with:
• Explaining principal and secondary diagnoses in the current case
• Clarifying ICD-10-AM codes and their DRG impact
• Discussing clinical evidence supporting diagnoses
• Providing physician queries for documentation improvement
• Calculating estimated DRG costs

يرجى السؤال عن تحليل الحالة السريرية فقط.
Please ask about the clinical case analysis only."""
    
    # Build history context
    history_text = ""
    if history:
        for msg in history[-5:]:
            role = "المستخدم User" if msg.get('role') == 'user' else "المدقق الطبي Medical Auditor"
            history_text += f"{role}: {msg.get('message', '')}\n"
    
    prompt = f"""كمدقق طبي أول، أجب على هذا السؤال المتعلق بالحالة السريرية فقط.
As a Senior Medical Auditor, answer this question about the clinical case ONLY.

⚠️ قيود مهمة: لا تخرج عن نطاق الحالة السريرية. كل إجابة يجب أن تكون مدعومة بأدلة من الملاحظات.
⚠️ IMPORTANT: Stay within the scope of the clinical case. Every answer must be supported by evidence from the notes.

=== سياق الحالة | CASE CONTEXT ===
{context}

=== تاريخ المحادثة | CONVERSATION HISTORY ===
{history_text}

=== سؤال المستخدم | USER QUESTION ===
{message}

قدم إجابة مهنية مركزة على CDI مع ذكر الأدلة من الحالة.
Provide a professional, CDI-focused response with evidence from the case.
أجب بنفس لغة السؤال | Respond in the same language as the question."""

    try:
        return generate_text(prompt, max_new_tokens=1000, temperature=0.3).strip()
    except Exception as e:
        logger.error(f"❌ Chat error: {str(e)}")
        raise


def parse_json_response(response_text: str) -> Dict:
    """Parse JSON from LLM response"""
    try:
        text = response_text.strip()
        
        # Extract JSON from markdown code blocks
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            parts = text.split("```")
            if len(parts) >= 2:
                text = parts[1].strip()
        
        # Find JSON object
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            text = json_match.group(0)
        
        result = json.loads(text)
        logger.info(f"✅ JSON parsed successfully")
        return result
        
    except Exception as e:
        logger.warning(f"⚠️ JSON parse failed: {str(e)}")
        return {}


def check_model_health() -> Dict:
    """Check model status"""
    try:
        if _model is not None:
            gpu_info = {}
            if torch.cuda.is_available():
                gpu_info = {
                    "gpu_name": torch.cuda.get_device_name(0),
                    "gpu_memory_allocated": f"{torch.cuda.memory_allocated() / 1024**3:.2f} GB",
                    "gpu_memory_reserved": f"{torch.cuda.memory_reserved() / 1024**3:.2f} GB"
                }
            
            return {
                "status": "healthy",
                "model": _model_name,
                "device": "cuda" if torch.cuda.is_available() else "cpu",
                "quantization": "4-bit NF4",
                **gpu_info
            }
        return {"status": "not_loaded", "model": None}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def get_system_info() -> Dict:
    """Get system information"""
    info = {
        "model_loaded": _model is not None,
        "model_name": _model_name,
        "cuda_available": torch.cuda.is_available(),
        "drg_lookup_loaded": _drg_lookup is not None
    }
    
    if torch.cuda.is_available():
        info["gpu_count"] = torch.cuda.device_count()
        info["gpu_name"] = torch.cuda.get_device_name(0)
        info["gpu_memory_total"] = f"{torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB"
    
    if _drg_lookup is not None:
        info["drg_statistics"] = _drg_lookup.get_statistics()
    
    return info
