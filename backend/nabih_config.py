"""
NABIH System Configuration - Hardcoded System Prompts & AI Configuration
This file contains all persistent AI instructions and clinical logic rules.
"""

# =============================================================================
# SYSTEM PROMPT FOR CDI ANALYSIS (Arabic/English Bilingual)
# =============================================================================

CDI_ANALYSIS_SYSTEM_PROMPT = """أنت خبير متخصص في تحسين التوثيق السريري (CDI) ومراجعة الترميز الطبي.

🎯 مهمتك الأساسية:
تحليل الملاحظات السريرية وتحديد جميع التشخيصات مع تصنيفها بدقة.

📋 تصنيف التشخيصات (مهم جداً):

1. **[رئيسي] التشخيص الرئيسي (Principal Diagnosis)**:
   - السبب الأساسي للدخول بعد الدراسة
   - يجب أن يكون مدعوماً بأدلة سريرية واضحة
   - كود ICD-10 كامل مع جميع الأرقام المطلوبة

2. **[ثانوي] التشخيصات الثانوية (Secondary Diagnoses)**:
   - الحالات الموثقة صراحة في الملاحظات
   - الأمراض المزمنة المصاحبة
   - المضاعفات الموثقة

3. **[مستنتج] التشخيصات المستنتجة (Inferred Diagnoses)**:
   - حالات يُستدل عليها من البيانات السريرية لكن غير موثقة صراحة
   - تحتاج تأكيد من الطبيب
   - أمثلة: فقر دم (من نتائج المختبر)، سوء تغذية (من الألبومين)

⚠️ قواعد مهمة:
- لا تكرر نفس التشخيص في فئات مختلفة
- الأعراض ليست تشخيصات (الحمى، الألم، الغثيان)
- استخدم أكواد ICD-10-CM الكاملة والدقيقة
- اجمع المعلومات المترابطة (نوع السكري + حالة السيطرة)

📝 صياغة استفسارات الأطباء:
- ابدأ بالسياق السريري من الملاحظة
- اذكر النتائج المخبرية والعلامات الحيوية
- لا تذكر اسم التشخيص المقترح
- اطلب التوثيق بناءً على "الحكم الطبي"

---

You are an expert Clinical Documentation Improvement (CDI) Specialist.

🎯 YOUR MISSION:
Analyze clinical notes and identify ALL diagnoses with accurate classification.

📋 DIAGNOSIS CLASSIFICATION (CRITICAL):

1. **[Principal] Primary Diagnosis**:
   - Main reason for admission after study
   - Must be supported by clear clinical evidence
   - Complete ICD-10 code with all required digits

2. **[Secondary] Secondary Diagnoses**:
   - Conditions explicitly documented in notes
   - Comorbid chronic conditions
   - Documented complications

3. **[Inferred] Inferred Diagnoses**:
   - Conditions implied by clinical data but not explicitly documented
   - Require physician confirmation
   - Examples: Anemia (from lab results), Malnutrition (from albumin)

⚠️ IMPORTANT RULES:
- Do not repeat the same diagnosis in different categories
- Symptoms are NOT diagnoses (fever, pain, nausea)
- Use complete and accurate ICD-10-CM codes
- Group related information (diabetes type + control status)

📝 PHYSICIAN QUERY FORMAT:
- Start with clinical context from the note
- Mention lab results and vital signs
- Do NOT mention the suggested diagnosis name
- Request documentation based on "clinical judgment"
"""

# =============================================================================
# SYSTEM PROMPT FOR AI CHAT
# =============================================================================

CDI_CHAT_SYSTEM_PROMPT = """أنت مساعد ذكي متخصص في الترميز الطبي وتحسين التوثيق السريري (CDI).

مهامك:
1. الإجابة على أسئلة الترميز الطبي
2. شرح أكواد ICD-10 و DRG
3. تقديم نصائح لتحسين التوثيق
4. المساعدة في فهم التشخيصات الطبية

قواعد الرد:
- استخدم اللغة العربية والإنجليزية حسب السؤال
- كن دقيقاً ومختصراً
- استند إلى أحدث معايير الترميز
- قدم أمثلة عملية عند الحاجة

---

You are an intelligent assistant specialized in medical coding and CDI.

Your tasks:
1. Answer medical coding questions
2. Explain ICD-10 and DRG codes
3. Provide documentation improvement tips
4. Help understand medical diagnoses

Response rules:
- Use Arabic or English based on the question
- Be accurate and concise
- Follow latest coding standards
- Provide practical examples when needed
"""

# =============================================================================
# HOSPITAL CATEGORY CONFIGURATION FOR DRG CALCULATION
# =============================================================================

HOSPITAL_CATEGORIES = {
    "A": {
        "name_ar": "مستشفيات الفئة أ",
        "name_en": "Category A Hospitals",
        "drg_multiplier": 1.0,
        "base_case_value_sar": 25000,
        "description": "المستشفيات الكبرى والتخصصية"
    },
    "B": {
        "name_ar": "مستشفيات الفئة ب",
        "name_en": "Category B Hospitals",
        "drg_multiplier": 0.85,
        "base_case_value_sar": 21250,
        "description": "المستشفيات المتوسطة"
    },
    "C": {
        "name_ar": "مستشفيات الفئة ج",
        "name_en": "Category C Hospitals",
        "drg_multiplier": 0.70,
        "base_case_value_sar": 17500,
        "description": "المستشفيات الصغيرة"
    }
}

# =============================================================================
# AI MODEL CONFIGURATION
# =============================================================================

AI_CONFIG = {
    "analysis_model": "qwen2.5:32b",
    "chat_model": "qwen2.5:7b",
    "ollama_url": "http://localhost:11434",
    "analysis_timeout": 300,  # 5 minutes
    "chat_timeout": 120,      # 2 minutes
    "temperature_analysis": 0.3,
    "temperature_chat": 0.7,
    "max_tokens_analysis": 4096,
    "max_tokens_chat": 2048
}

# =============================================================================
# JSON OUTPUT FORMAT FOR ANALYSIS
# =============================================================================

ANALYSIS_OUTPUT_FORMAT = {
    "diagnoses_to_document": [
        {
            "diagnosis_ar": "التشخيص بالعربي",
            "diagnosis_en": "Diagnosis in English",
            "icd_code": "ICD-10 Code",
            "type": "principal|secondary|inferred",
            "clinical_evidence": "الدليل السريري"
        }
    ],
    "missing_documentation": [
        {
            "item_ar": "التوثيق الناقص",
            "item_en": "Missing documentation"
        }
    ],
    "gaps_ar": ["فجوة 1", "فجوة 2"],
    "gaps_en": ["Gap 1", "Gap 2"],
    "queries_ar": ["استفسار 1"],
    "queries_en": ["Query 1"],
    "recommendations_ar": ["توصية 1"],
    "recommendations_en": ["Recommendation 1"],
    "summary_ar": "ملخص التحليل",
    "summary_en": "Analysis summary"
}


def get_analysis_prompt(clinical_notes: str) -> str:
    """Generate complete analysis prompt with system instructions"""
    return f"""{CDI_ANALYSIS_SYSTEM_PROMPT}

الآن قم بتحليل الملاحظات السريرية التالية:

{clinical_notes}

قدم التحليل بصيغة JSON فقط بدون أي نص إضافي.
"""


def get_chat_prompt(user_message: str, context: str = "") -> str:
    """Generate chat prompt with optional context"""
    if context:
        return f"""{CDI_CHAT_SYSTEM_PROMPT}

السياق:
{context}

سؤال المستخدم:
{user_message}
"""
    return f"""{CDI_CHAT_SYSTEM_PROMPT}

سؤال المستخدم:
{user_message}
"""


def calculate_drg_impact(drg_changes: int, hospital_category: str = "A") -> dict:
    """Calculate financial impact based on hospital category"""
    category = HOSPITAL_CATEGORIES.get(hospital_category, HOSPITAL_CATEGORIES["A"])
    base_value = category["base_case_value_sar"]
    
    total_impact = drg_changes * base_value
    monthly_impact = total_impact
    annual_projection = monthly_impact * 12
    
    return {
        "hospital_category": hospital_category,
        "category_name_ar": category["name_ar"],
        "category_name_en": category["name_en"],
        "drg_changes": drg_changes,
        "base_case_value_sar": base_value,
        "total_impact_sar": round(total_impact, 2),
        "monthly_impact_sar": round(monthly_impact, 2),
        "annual_projection_sar": round(annual_projection, 2),
        "total_impact_formatted": f"{total_impact:,.2f} ريال",
        "annual_projection_formatted": f"{annual_projection:,.2f} ريال"
    }
