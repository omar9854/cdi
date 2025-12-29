"""
MediDoc AI - Local LLM Module
Uses Qwen2.5-72B-Instruct with 4-bit quantization for A100 40GB
Role: Senior Medical Auditor for Clinical Documentation Improvement
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import logging
import json
import re
from typing import Dict, List, Optional
from drg_lookup import DRGLookup

logger = logging.getLogger(__name__)

# Global instances
_model = None
_tokenizer = None
_model_name = None
_drg_lookup = None

# Model configuration
DEFAULT_MODEL = "Qwen/Qwen2.5-72B-Instruct"
FALLBACK_MODEL = "Qwen/Qwen2.5-7B-Instruct"

# Senior Medical Auditor System Prompt
SENIOR_AUDITOR_PROMPT = """You are a Senior Medical Auditor and Clinical Documentation Improvement (CDI) Specialist with 20+ years of experience in medical coding and DRG optimization.

YOUR ROLE:
- Review clinical documentation with expert precision
- Identify ALL diagnoses from clinical notes (explicit and implied)
- Distinguish clearly between Principal Diagnosis and Secondary Diagnoses
- Extract specific clinical evidence for each diagnosis
- Map findings to accurate ICD-10-AM codes
- Identify documentation gaps that impact DRG assignment

DIAGNOSIS CLASSIFICATION RULES:
1. PRINCIPAL DIAGNOSIS: The condition established after study to be chiefly responsible for occasioning the admission. There can only be ONE principal diagnosis.
2. SECONDARY DIAGNOSES (Comorbidities/Complications):
   - Comorbidity (CC): Pre-existing condition that affects treatment
   - Complication: Condition that arises during the hospital stay
   - Other: Additional diagnoses that don't meet CC criteria

EVIDENCE EXTRACTION:
For EVERY diagnosis, you MUST extract the exact supporting text from the clinical notes.
Format: "Evidence: [exact quote from notes]"

ICD-10-AM CODING STANDARDS:
- Use Australian Modification codes (ICD-10-AM)
- Include all relevant specificity (laterality, severity, stage)
- Code to highest level of specificity supported by documentation"""


def get_drg_lookup():
    """Get or create DRG lookup instance"""
    global _drg_lookup
    if _drg_lookup is None:
        _drg_lookup = DRGLookup()
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


def analyze_clinical_notes(formatted_notes: str) -> Dict:
    """
    Perform comprehensive CDI analysis as Senior Medical Auditor
    Returns structured JSON with diagnoses, evidence, and DRG costs
    """
    
    analysis_prompt = f"""As a Senior Medical Auditor, analyze the following clinical documentation thoroughly.

CLINICAL NOTES:
{formatted_notes}

TASK:
1. Identify the PRINCIPAL DIAGNOSIS (one only - main reason for admission)
2. Identify ALL SECONDARY DIAGNOSES:
   - Comorbidities (CC): Pre-existing conditions affecting treatment
   - Complications: Conditions arising during admission
   - Other relevant diagnoses
3. For EACH diagnosis, extract the EXACT supporting evidence from the notes
4. Assign accurate ICD-10-AM codes
5. Identify documentation gaps

ICD-10-AM REFERENCE:
- Type 2 Diabetes: E11.9 (unspecified), E11.65 (with hyperglycemia), E11.40 (with neuropathy), E11.21 (with nephropathy), E11.31 (with retinopathy)
- Type 1 Diabetes: E10.x
- Hypertension: I10 (essential), I11.9 (with heart disease), I12.9 (with CKD), I13.10 (with heart and CKD)
- CKD: N18.1 (stage 1), N18.2 (stage 2), N18.3 (stage 3), N18.4 (stage 4), N18.5 (stage 5), N18.9 (unspecified)
- Heart Failure: I50.9 (unspecified), I50.1 (left ventricular), I50.20 (systolic), I50.30 (diastolic)
- AKI: N17.9
- Pneumonia: J18.9 (unspecified), J15.9 (bacterial)
- COPD: J44.9 (unspecified), J44.1 (with acute exacerbation)
- Sepsis: A41.9
- Chest Pain: R07.9

RESPOND WITH VALID JSON ONLY:
{{
    "principal_diagnosis": {{
        "diagnosis_ar": "التشخيص الرئيسي بالعربية",
        "diagnosis_en": "Principal Diagnosis in English",
        "icd_code": "ICD-10-AM Code",
        "evidence": "Exact supporting text from clinical notes",
        "drg_code": "DRG code if applicable",
        "relative_weight": 0.0,
        "estimated_cost": 0.0
    }},
    "secondary_diagnoses": [
        {{
            "diagnosis_ar": "التشخيص بالعربية",
            "diagnosis_en": "Diagnosis in English",
            "icd_code": "ICD-10-AM Code",
            "category": "comorbidity OR complication OR other",
            "evidence": "Exact supporting text from clinical notes",
            "affects_drg": true
        }}
    ],
    "documentation_gaps": [
        {{
            "gap_ar": "الثغرة بالعربية",
            "gap_en": "Gap description in English",
            "impact": "Impact on coding/DRG",
            "query": "Suggested physician query with evidence"
        }}
    ],
    "physician_queries": [
        {{
            "query_ar": "الاستفسار بالعربية (مع الدليل السريري)",
            "query_en": "Query in English (Based on: specific evidence from notes)",
            "priority": "high OR medium OR low"
        }}
    ],
    "drg_summary": {{
        "estimated_drg": "DRG Code",
        "drg_description": "DRG Description",
        "base_drg_weight": 0.0,
        "cc_adjustment": 0.0,
        "final_weight": 0.0,
        "base_rate": 5000.0,
        "total_estimated_cost": 0.0
    }},
    "summary_ar": "ملخص التحليل بالعربية",
    "summary_en": "Analysis summary in English"
}}"""

    try:
        response_text = generate_text(analysis_prompt, max_new_tokens=3500, temperature=0.1)
        result = parse_json_response(response_text)
        
        # Enhance with DRG lookup
        result = enhance_with_drg_pricing(result)
        
        # Validate structure
        if not result.get('principal_diagnosis'):
            result = extract_diagnoses_fallback(formatted_notes, response_text)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Analysis error: {str(e)}")
        raise


def enhance_with_drg_pricing(result: Dict) -> Dict:
    """Add DRG pricing information using RAG lookup"""
    try:
        drg = get_drg_lookup()
        
        # Get principal diagnosis ICD code
        principal = result.get('principal_diagnosis', {})
        icd_code = principal.get('icd_code', '')
        
        if icd_code:
            drg_info = drg.lookup_by_icd(icd_code)
            if drg_info:
                principal['drg_code'] = drg_info.get('drg_code', '')
                principal['relative_weight'] = drg_info.get('relative_weight', 0.0)
                principal['estimated_cost'] = drg_info.get('estimated_cost', 0.0)
                
                # Update DRG summary
                if 'drg_summary' not in result:
                    result['drg_summary'] = {}
                
                result['drg_summary'].update({
                    'estimated_drg': drg_info.get('drg_code', ''),
                    'drg_description': drg_info.get('description', ''),
                    'base_drg_weight': drg_info.get('relative_weight', 0.0),
                    'final_weight': drg_info.get('relative_weight', 0.0),
                    'base_rate': drg.base_rate,
                    'total_estimated_cost': drg_info.get('estimated_cost', 0.0)
                })
        
        # Check secondary diagnoses for CC impact
        cc_count = 0
        for secondary in result.get('secondary_diagnoses', []):
            if secondary.get('category') == 'comorbidity':
                cc_count += 1
                secondary['affects_drg'] = True
        
        # Adjust weight for CCs if applicable
        if cc_count > 0 and 'drg_summary' in result:
            cc_adjustment = cc_count * 0.1  # Simplified adjustment
            result['drg_summary']['cc_adjustment'] = cc_adjustment
            base_weight = result['drg_summary'].get('base_drg_weight', 1.0)
            result['drg_summary']['final_weight'] = base_weight + cc_adjustment
            result['drg_summary']['total_estimated_cost'] = (
                result['drg_summary']['final_weight'] * drg.base_rate
            )
        
        return result
        
    except Exception as e:
        logger.warning(f"⚠️ DRG enhancement error: {str(e)}")
        return result


def extract_diagnoses_fallback(notes: str, analysis_text: str) -> Dict:
    """Fallback extraction when JSON parsing fails"""
    
    notes_lower = notes.lower()
    principal = None
    secondary = []
    
    # Detect principal diagnosis
    if any(kw in notes_lower for kw in ['diabetes', 'hba1c', 'glucose', 'metformin']):
        hba1c_high = any(x in notes for x in ['8.', '9.', '10.', '11.', '12.'])
        principal = {
            "diagnosis_ar": "داء السكري النوع الثاني" + (" مع سوء التحكم" if hba1c_high else ""),
            "diagnosis_en": "Type 2 Diabetes Mellitus" + (" with poor glycemic control" if hba1c_high else ""),
            "icd_code": "E11.65" if hba1c_high else "E11.9",
            "evidence": "Patient has diabetes history with elevated HbA1c" if hba1c_high else "Patient on diabetes medications",
            "drg_code": "",
            "relative_weight": 0.0,
            "estimated_cost": 0.0
        }
    
    # Secondary diagnoses
    if any(kw in notes_lower for kw in ['numbness', 'tingling', 'neuropathy']):
        secondary.append({
            "diagnosis_ar": "اعتلال الأعصاب السكري المحيطي",
            "diagnosis_en": "Diabetic peripheral neuropathy",
            "icd_code": "E11.40",
            "category": "complication",
            "evidence": "Bilateral foot numbness and tingling",
            "affects_drg": True
        })
    
    if any(kw in notes_lower for kw in ['creatinine', 'proteinuria', 'kidney', 'ckd']):
        secondary.append({
            "diagnosis_ar": "مرض الكلى المزمن / اعتلال الكلى السكري",
            "diagnosis_en": "Chronic Kidney Disease / Diabetic nephropathy",
            "icd_code": "E11.21",
            "category": "complication",
            "evidence": "Elevated creatinine and proteinuria",
            "affects_drg": True
        })
    
    if any(kw in notes_lower for kw in ['retinopathy', 'eye exam', 'ophthalmology']):
        secondary.append({
            "diagnosis_ar": "اعتلال الشبكية السكري",
            "diagnosis_en": "Diabetic retinopathy",
            "icd_code": "E11.31",
            "category": "complication",
            "evidence": "Ophthalmology exam findings",
            "affects_drg": True
        })
    
    if any(kw in notes_lower for kw in ['hypertension', 'blood pressure', 'bp ', 'lisinopril']):
        secondary.append({
            "diagnosis_ar": "ارتفاع ضغط الدم الأساسي",
            "diagnosis_en": "Essential hypertension",
            "icd_code": "I10",
            "category": "comorbidity",
            "evidence": "Elevated blood pressure, on antihypertensive",
            "affects_drg": True
        })
    
    if any(kw in notes_lower for kw in ['chest pain', 'angina']):
        secondary.append({
            "diagnosis_ar": "ألم الصدر",
            "diagnosis_en": "Chest pain, unspecified",
            "icd_code": "R07.9",
            "category": "other",
            "evidence": "Patient reports chest pain on exertion",
            "affects_drg": False
        })
    
    if any(kw in notes_lower for kw in ['heart failure', 'chf', 'bnp']):
        secondary.append({
            "diagnosis_ar": "قصور القلب",
            "diagnosis_en": "Heart failure",
            "icd_code": "I50.9",
            "category": "comorbidity",
            "evidence": "Heart failure documented",
            "affects_drg": True
        })
    
    if principal is None:
        principal = {
            "diagnosis_ar": "يرجى المراجعة اليدوية",
            "diagnosis_en": "Manual review required",
            "icd_code": "R69",
            "evidence": "Unable to determine principal diagnosis automatically",
            "drg_code": "",
            "relative_weight": 0.0,
            "estimated_cost": 0.0
        }
    
    # Build queries with evidence
    queries = []
    if 'creatinine' in notes_lower:
        queries.append({
            "query_ar": "ما هي مرحلة مرض الكلى المزمن؟ (بناءً على: ارتفاع الكرياتينين ووجود بروتين في البول)",
            "query_en": "What is the CKD stage? (Based on: elevated creatinine and proteinuria in lab results)",
            "priority": "high"
        })
    
    if 'chest pain' in notes_lower:
        queries.append({
            "query_ar": "هل ألم الصدر قلبي المنشأ؟ (بناءً على: شكوى المريض من ألم صدر عند المجهود)",
            "query_en": "Is the chest pain cardiac in origin? (Based on: patient reports exertional chest pain)",
            "priority": "high"
        })
    
    return {
        "principal_diagnosis": principal,
        "secondary_diagnoses": secondary,
        "documentation_gaps": [
            {
                "gap_ar": "مرحلة مرض الكلى المزمن غير محددة",
                "gap_en": "CKD stage not specified",
                "impact": "Affects DRG weight and reimbursement",
                "query": "Please specify CKD stage based on eGFR"
            }
        ],
        "physician_queries": queries if queries else [{
            "query_ar": "يرجى مراجعة التوثيق مع الطبيب المعالج",
            "query_en": "Please review documentation with treating physician",
            "priority": "medium"
        }],
        "drg_summary": {
            "estimated_drg": "TBD",
            "drg_description": "Requires DRG lookup",
            "base_drg_weight": 1.0,
            "cc_adjustment": len([s for s in secondary if s.get('category') == 'comorbidity']) * 0.1,
            "final_weight": 1.0,
            "base_rate": 5000.0,
            "total_estimated_cost": 5000.0
        },
        "summary_ar": f"تم تحديد تشخيص رئيسي واحد و {len(secondary)} تشخيصات ثانوية. يوجد ثغرات في التوثيق تحتاج معالجة.",
        "summary_en": f"Identified 1 principal diagnosis and {len(secondary)} secondary diagnoses. Documentation gaps require attention."
    }


def chat_with_context(message: str, context: str, history: List = None) -> str:
    """CDI-focused chat - rejects off-topic questions"""
    
    off_topic = [
        'weather', 'news', 'sports', 'politics', 'movie', 'music', 'recipe', 
        'joke', 'story', 'game', 'travel', 'shopping', 'الطقس', 'أخبار',
        'رياضة', 'سياسة', 'فيلم', 'موسيقى', 'وصفة', 'نكتة', 'قصة', 'لعبة',
        'code', 'programming', 'برمجة', 'write me', 'اكتب لي', 'python', 'javascript'
    ]
    
    msg_lower = message.lower()
    if any(kw in msg_lower for kw in off_topic):
        return """عذراً، أنا مدقق طبي أول متخصص في تحسين التوثيق السريري (CDI) فقط.

يمكنني مساعدتك في:
• شرح التشخيصات الرئيسية والثانوية
• توضيح أكواد ICD-10-AM وتأثيرها على DRG
• مناقشة الأدلة السريرية الداعمة للتشخيصات
• تقديم استفسارات للطبيب لتحسين التوثيق
• حساب تكلفة DRG التقديرية

---

Sorry, I am a Senior Medical Auditor specializing in Clinical Documentation Improvement (CDI) only.

I can help you with:
• Explaining principal and secondary diagnoses
• Clarifying ICD-10-AM codes and their DRG impact
• Discussing clinical evidence supporting diagnoses
• Providing physician queries for documentation improvement
• Calculating estimated DRG costs

Please ask about the clinical case analysis."""
    
    history_text = ""
    if history:
        for msg in history[-5:]:
            role = "User" if msg.get('role') == 'user' else "Senior Medical Auditor"
            history_text += f"{role}: {msg.get('message', '')}\n"
    
    prompt = f"""As a Senior Medical Auditor, answer this question about the clinical case.

CASE CONTEXT:
{context}

CONVERSATION HISTORY:
{history_text}

USER QUESTION:
{message}

Provide a professional, evidence-based response focused on CDI.
Respond in the same language as the question."""

    try:
        return generate_text(prompt, max_new_tokens=1000, temperature=0.3).strip()
    except Exception as e:
        logger.error(f"❌ Chat error: {str(e)}")
        raise


def parse_json_response(response_text: str) -> Dict:
    """Parse JSON from LLM response"""
    try:
        text = response_text.strip()
        
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            parts = text.split("```")
            if len(parts) >= 2:
                text = parts[1].strip()
        
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
            return {
                "status": "healthy",
                "model": _model_name,
                "device": "cuda" if torch.cuda.is_available() else "cpu",
                "quantization": "4-bit",
                "gpu_memory": f"{torch.cuda.memory_allocated() / 1024**3:.2f} GB" if torch.cuda.is_available() else "N/A"
            }
        return {"status": "not_loaded", "model": None}
    except Exception as e:
        return {"status": "error", "error": str(e)}
