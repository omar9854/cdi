"""
ICD-10-AM Code Reference
Australian Modification codes with DRG mappings
"""

ICD_10_AM_CODES = {
    # ============================================
    # ENDOCRINE, NUTRITIONAL & METABOLIC DISEASES
    # ============================================
    
    # Type 2 Diabetes Mellitus
    "E11": {
        "description_en": "Type 2 diabetes mellitus",
        "description_ar": "داء السكري النوع الثاني",
        "category": "Endocrine"
    },
    "E11.9": {
        "description_en": "Type 2 diabetes mellitus without complications",
        "description_ar": "داء السكري النوع الثاني بدون مضاعفات",
        "drg": "K60B",
        "weight": 0.85
    },
    "E11.65": {
        "description_en": "Type 2 diabetes mellitus with hyperglycemia",
        "description_ar": "داء السكري النوع الثاني مع فرط سكر الدم",
        "drg": "K60A",
        "weight": 1.45
    },
    "E11.40": {
        "description_en": "Type 2 diabetes mellitus with diabetic neuropathy, unspecified",
        "description_ar": "داء السكري النوع الثاني مع اعتلال الأعصاب السكري",
        "drg": "K60A",
        "weight": 1.45
    },
    "E11.41": {
        "description_en": "Type 2 diabetes mellitus with diabetic mononeuropathy",
        "description_ar": "داء السكري النوع الثاني مع اعتلال عصبي أحادي",
        "drg": "K60A",
        "weight": 1.45
    },
    "E11.42": {
        "description_en": "Type 2 diabetes mellitus with diabetic polyneuropathy",
        "description_ar": "داء السكري النوع الثاني مع اعتلال الأعصاب المتعدد",
        "drg": "K60A",
        "weight": 1.45
    },
    "E11.21": {
        "description_en": "Type 2 diabetes mellitus with diabetic nephropathy",
        "description_ar": "داء السكري النوع الثاني مع اعتلال الكلى السكري",
        "drg": "K60A",
        "weight": 1.45
    },
    "E11.22": {
        "description_en": "Type 2 diabetes mellitus with diabetic chronic kidney disease",
        "description_ar": "داء السكري النوع الثاني مع مرض الكلى المزمن",
        "drg": "K60A",
        "weight": 1.45
    },
    "E11.31": {
        "description_en": "Type 2 diabetes mellitus with background diabetic retinopathy",
        "description_ar": "داء السكري النوع الثاني مع اعتلال الشبكية الخلفي",
        "drg": "K60A",
        "weight": 1.45
    },
    "E11.319": {
        "description_en": "Type 2 diabetes mellitus with unspecified diabetic retinopathy",
        "description_ar": "داء السكري النوع الثاني مع اعتلال الشبكية غير المحدد",
        "drg": "K60A",
        "weight": 1.45
    },
    "E11.51": {
        "description_en": "Type 2 diabetes mellitus with diabetic peripheral angiopathy",
        "description_ar": "داء السكري النوع الثاني مع اعتلال الأوعية المحيطية",
        "drg": "K60A",
        "weight": 1.45
    },
    "E11.52": {
        "description_en": "Type 2 diabetes mellitus with diabetic foot ulcer",
        "description_ar": "داء السكري النوع الثاني مع قرحة القدم السكرية",
        "drg": "K60A",
        "weight": 1.45
    },
    
    # Type 1 Diabetes Mellitus
    "E10.9": {
        "description_en": "Type 1 diabetes mellitus without complications",
        "description_ar": "داء السكري النوع الأول بدون مضاعفات",
        "drg": "K60B",
        "weight": 0.85
    },
    "E10.65": {
        "description_en": "Type 1 diabetes mellitus with hyperglycemia",
        "description_ar": "داء السكري النوع الأول مع فرط سكر الدم",
        "drg": "K60A",
        "weight": 1.45
    },
    
    # ============================================
    # DISEASES OF THE CIRCULATORY SYSTEM
    # ============================================
    
    # Hypertension
    "I10": {
        "description_en": "Essential (primary) hypertension",
        "description_ar": "ارتفاع ضغط الدم الأساسي",
        "drg": "F74B",
        "weight": 0.55
    },
    "I11.9": {
        "description_en": "Hypertensive heart disease without heart failure",
        "description_ar": "مرض القلب الناتج عن ارتفاع الضغط بدون قصور قلب",
        "drg": "F62B",
        "weight": 1.05
    },
    "I12.9": {
        "description_en": "Hypertensive chronic kidney disease",
        "description_ar": "مرض الكلى المزمن الناتج عن ارتفاع الضغط",
        "drg": "L63A",
        "weight": 1.25
    },
    "I13.10": {
        "description_en": "Hypertensive heart and chronic kidney disease",
        "description_ar": "مرض القلب والكلى المزمن الناتج عن ارتفاع الضغط",
        "drg": "F62A",
        "weight": 1.65
    },
    
    # Heart Failure
    "I50.9": {
        "description_en": "Heart failure, unspecified",
        "description_ar": "قصور القلب غير المحدد",
        "drg": "F62B",
        "weight": 1.05
    },
    "I50.1": {
        "description_en": "Left ventricular failure",
        "description_ar": "قصور البطين الأيسر",
        "drg": "F62A",
        "weight": 1.65
    },
    "I50.20": {
        "description_en": "Unspecified systolic heart failure",
        "description_ar": "قصور القلب الانقباضي",
        "drg": "F62A",
        "weight": 1.65
    },
    "I50.30": {
        "description_en": "Unspecified diastolic heart failure",
        "description_ar": "قصور القلب الانبساطي",
        "drg": "F62A",
        "weight": 1.65
    },
    "I50.40": {
        "description_en": "Combined systolic and diastolic heart failure",
        "description_ar": "قصور القلب الانقباضي والانبساطي المشترك",
        "drg": "F62A",
        "weight": 1.65
    },
    
    # Ischemic Heart Disease
    "I20.9": {
        "description_en": "Angina pectoris, unspecified",
        "description_ar": "الذبحة الصدرية غير المحددة",
        "drg": "F74A",
        "weight": 0.95
    },
    "I21.9": {
        "description_en": "Acute myocardial infarction, unspecified",
        "description_ar": "احتشاء عضلة القلب الحاد",
        "drg": "F60B",
        "weight": 1.95
    },
    "I25.10": {
        "description_en": "Atherosclerotic heart disease",
        "description_ar": "مرض القلب التصلبي العصيدي",
        "drg": "F74A",
        "weight": 0.95
    },
    
    # Cardiac Arrhythmias
    "I48.91": {
        "description_en": "Atrial fibrillation",
        "description_ar": "الرجفان الأذيني",
        "drg": "F74A",
        "weight": 0.95
    },
    
    # Symptoms
    "R07.9": {
        "description_en": "Chest pain, unspecified",
        "description_ar": "ألم الصدر غير المحدد",
        "drg": "F74B",
        "weight": 0.55
    },
    
    # ============================================
    # DISEASES OF THE GENITOURINARY SYSTEM
    # ============================================
    
    # Acute Kidney Injury
    "N17.9": {
        "description_en": "Acute kidney failure, unspecified",
        "description_ar": "الفشل الكلوي الحاد",
        "drg": "L60B",
        "weight": 1.85
    },
    
    # Chronic Kidney Disease
    "N18.1": {
        "description_en": "Chronic kidney disease, stage 1",
        "description_ar": "مرض الكلى المزمن - المرحلة 1",
        "drg": "L63B",
        "weight": 0.75
    },
    "N18.2": {
        "description_en": "Chronic kidney disease, stage 2",
        "description_ar": "مرض الكلى المزمن - المرحلة 2",
        "drg": "L63B",
        "weight": 0.75
    },
    "N18.3": {
        "description_en": "Chronic kidney disease, stage 3",
        "description_ar": "مرض الكلى المزمن - المرحلة 3",
        "drg": "L63A",
        "weight": 1.25
    },
    "N18.4": {
        "description_en": "Chronic kidney disease, stage 4",
        "description_ar": "مرض الكلى المزمن - المرحلة 4",
        "drg": "L60B",
        "weight": 1.85
    },
    "N18.5": {
        "description_en": "Chronic kidney disease, stage 5",
        "description_ar": "مرض الكلى المزمن - المرحلة 5",
        "drg": "L60A",
        "weight": 3.20
    },
    "N18.9": {
        "description_en": "Chronic kidney disease, unspecified",
        "description_ar": "مرض الكلى المزمن غير المحدد",
        "drg": "L63B",
        "weight": 0.75
    },
    
    # ============================================
    # DISEASES OF THE RESPIRATORY SYSTEM
    # ============================================
    
    # Pneumonia
    "J18.9": {
        "description_en": "Pneumonia, unspecified organism",
        "description_ar": "الالتهاب الرئوي غير المحدد",
        "drg": "E62B",
        "weight": 1.35
    },
    "J15.9": {
        "description_en": "Unspecified bacterial pneumonia",
        "description_ar": "الالتهاب الرئوي البكتيري",
        "drg": "E62A",
        "weight": 2.15
    },
    
    # COPD
    "J44.9": {
        "description_en": "Chronic obstructive pulmonary disease, unspecified",
        "description_ar": "مرض الانسداد الرئوي المزمن",
        "drg": "E65B",
        "weight": 0.95
    },
    "J44.1": {
        "description_en": "COPD with acute exacerbation",
        "description_ar": "مرض الانسداد الرئوي المزمن مع تفاقم حاد",
        "drg": "E65A",
        "weight": 1.45
    },
    
    # ============================================
    # INFECTIOUS DISEASES
    # ============================================
    
    "A41.9": {
        "description_en": "Sepsis, unspecified organism",
        "description_ar": "تسمم الدم",
        "drg": "T60A",
        "weight": 3.85
    },
    
    # ============================================
    # DISEASES OF THE NERVOUS SYSTEM
    # ============================================
    
    "G62.9": {
        "description_en": "Polyneuropathy, unspecified",
        "description_ar": "اعتلال الأعصاب المتعدد",
        "drg": "B81A",
        "weight": 1.25
    },
    
    # ============================================
    # SYMPTOMS & SIGNS
    # ============================================
    
    "R69": {
        "description_en": "Illness, unspecified",
        "description_ar": "مرض غير محدد",
        "drg": "Z64B",
        "weight": 0.45
    },
}


def get_icd_info(code: str) -> dict:
    """Get ICD-10-AM code information"""
    return ICD_10_AM_CODES.get(code.upper(), None)


def search_icd_codes(query: str) -> list:
    """Search ICD codes by description"""
    query = query.lower()
    results = []
    
    for code, info in ICD_10_AM_CODES.items():
        if (query in code.lower() or 
            query in info.get("description_en", "").lower() or
            query in info.get("description_ar", "")):
            results.append({
                "code": code,
                "description_en": info.get("description_en", ""),
                "description_ar": info.get("description_ar", ""),
                "drg": info.get("drg", ""),
                "weight": info.get("weight", 0)
            })
    
    return results
