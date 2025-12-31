"""
Clinical Documentation Improvement - Predefined Questions
أسئلة ثابتة متخصصة في التوثيق السريري
"""

CLINICAL_QUESTIONS = {
    "ar": [
        {
            "id": "q1",
            "category": "التشخيصات",
            "question": "ما هي التشخيصات الموثقة والمستنتجة مع أكواد ICD-10-CM؟",
            "prompt": "من فضلك قدم قائمة مفصلة بـ:\n1. التشخيصات الموثقة نصاً في الملاحظات (Documented Diagnoses) مع أكواد ICD-10-CM\n2. التشخيصات المستنتجة من السياق السريري (Inferred Diagnoses) مع أكواد ICD-10-CM\n3. الفرق بين كل منهما وسبب الاستنتاج\n\nاستخدم هذا التنسيق:\n\n**التشخيصات الموثقة:**\n- التشخيص بالعربية (Diagnosis in English) - [ICD-10 Code]\n  * مكان التوثيق: [ذكر أين ورد في الملاحظات]\n\n**التشخيصات المستنتجة:**\n- التشخيص بالعربية (Diagnosis in English) - [ICD-10 Code]\n  * سبب الاستنتاج: [الأعراض أو المؤشرات السريرية]"
        },
        {
            "id": "q2",
            "category": "التشخيصات",
            "question": "ما الفرق بين التشخيص الرئيسي (Principal) والتشخيصات الثانوية (Secondary)؟",
            "prompt": "حدد:\n1. التشخيص الرئيسي (Principal Diagnosis) - [ICD-10 Code]\n2. التشخيصات الثانوية (Secondary Diagnoses) مع أكوادها\n3. التشخيصات المصاحبة (Comorbidities) و المضاعفات (Complications)\n4. سبب اختيار هذا التشخيص كرئيسي\n\nملاحظة: التشخيص الرئيسي هو السبب الأساسي للدخول أو الزيارة بعد الدراسة."
        },
        {
            "id": "q3",
            "category": "التوثيق الناقص",
            "question": "ما هي الوثائق الناقصة أو غير المكتملة؟",
            "prompt": "حدد:\n1. المعلومات الناقصة في التوثيق الحالي\n2. التفاصيل السريرية المطلوبة لكل تشخيص\n3. النتائج المعملية أو الإشعاعية الداعمة المفقودة\n4. أي توضيحات إضافية مطلوبة للترميز الدقيق"
        },
        {
            "id": "q4",
            "category": "الاستفسارات",
            "question": "ما هي الاستفسارات المطلوبة للطبيب (Physician Queries)؟",
            "prompt": "أنشئ استفسارات احترافية للطبيب حول:\n1. التشخيصات غير الواضحة أو غير المحددة\n2. العلاقة بين الأعراض والتشخيصات\n3. مضاعفات لم يتم توثيقها بوضوح\n4. تأكيدات مطلوبة للتشخيصات المستنتجة\n\nاستخدم صيغة احترافية ومحترمة."
        },
        {
            "id": "q5",
            "category": "DRG",
            "question": "ما هو DRG المتوقع للحالة الحالية؟",
            "prompt": "احسب:\n1. DRG المتوقع بناءً على التشخيصات الموثقة فقط (Current DRG)\n2. DRG المحتمل بعد توثيق جميع التشخيصات المستنتجة (Potential DRG)\n3. الفرق في الوزن النسبي (Relative Weight)\n4. الفرق المتوقع في التعويض المالي\n\nملاحظة: إذا لم تكن متأكداً من DRG المحدد، قدم التحليل العام والعوامل المؤثرة."
        },
        {
            "id": "q6",
            "category": "الجودة",
            "question": "ما هي مؤشرات جودة التوثيق (Clinical Documentation Quality)؟",
            "prompt": "قيّم:\n1. دقة التوثيق (Accuracy)\n2. اكتمال التوثيق (Completeness)\n3. التوقيت المناسب (Timeliness)\n4. الوضوح (Clarity)\n5. التوافق مع المعايير السريرية\n\nوقدم توصيات للتحسين."
        },
        {
            "id": "q7",
            "category": "الامتثال",
            "question": "هل هناك مشاكل في الامتثال أو الترميز (Coding Compliance)؟",
            "prompt": "راجع:\n1. مدى الامتثال لإرشادات ICD-10-CM الرسمية\n2. أي تناقضات في التوثيق\n3. احتمالية رفض المطالبة (Claim Denial Risk)\n4. توصيات لتحسين الامتثال"
        },
        {
            "id": "q8",
            "category": "تحليل عام",
            "question": "قدم تحليل شامل للحالة السريرية",
            "prompt": "قدم تحليلاً شاملاً يتضمن:\n1. ملخص الحالة السريرية\n2. التشخيصات الرئيسية مع أكوادها\n3. الثغرات في التوثيق\n4. التوصيات لتحسين الترميز\n5. الأثر المالي المحتمل\n6. نقاط القوة والضعف في التوثيق الحالي"
        }
    ],
    "en": [
        {
            "id": "q1",
            "category": "Diagnoses",
            "question": "What are the documented vs inferred diagnoses with ICD-10-CM codes?",
            "prompt": "Please provide a detailed list of:\n1. Documented Diagnoses (explicitly stated in notes) with ICD-10-CM codes\n2. Inferred Diagnoses (derived from clinical context) with ICD-10-CM codes\n3. The difference between them and reasoning for inference\n\nUse this format:\n\n**Documented Diagnoses:**\n- Diagnosis in Arabic (Diagnosis in English) - [ICD-10 Code]\n  * Documentation location: [where it appears in notes]\n\n**Inferred Diagnoses:**\n- Diagnosis in Arabic (Diagnosis in English) - [ICD-10 Code]\n  * Inference reasoning: [symptoms or clinical indicators]"
        },
        {
            "id": "q2",
            "category": "Diagnoses",
            "question": "What is the difference between Principal and Secondary diagnoses?",
            "prompt": "Identify:\n1. Principal Diagnosis - [ICD-10 Code]\n2. Secondary Diagnoses with codes\n3. Comorbidities and Complications\n4. Reasoning for principal diagnosis selection\n\nNote: Principal diagnosis is the main reason for admission after study."
        },
        {
            "id": "q3",
            "category": "Missing Documentation",
            "question": "What documentation is missing or incomplete?",
            "prompt": "Identify:\n1. Missing information in current documentation\n2. Required clinical details for each diagnosis\n3. Missing supporting lab or imaging results\n4. Additional clarifications needed for accurate coding"
        },
        {
            "id": "q4",
            "category": "Queries",
            "question": "What physician queries are needed?",
            "prompt": "Create professional physician queries about:\n1. Unclear or unspecified diagnoses\n2. Relationship between symptoms and diagnoses\n3. Undocumented complications\n4. Confirmations needed for inferred diagnoses\n\nUse professional and respectful language."
        },
        {
            "id": "q5",
            "category": "DRG",
            "question": "What is the expected DRG for this case?",
            "prompt": "Calculate:\n1. Expected DRG based on documented diagnoses only (Current DRG)\n2. Potential DRG after documenting all inferred diagnoses (Potential DRG)\n3. Difference in Relative Weight\n4. Expected difference in reimbursement\n\nNote: If specific DRG is uncertain, provide general analysis and affecting factors."
        },
        {
            "id": "q6",
            "category": "Quality",
            "question": "What are the clinical documentation quality indicators?",
            "prompt": "Assess:\n1. Accuracy\n2. Completeness\n3. Timeliness\n4. Clarity\n5. Compliance with clinical standards\n\nProvide improvement recommendations."
        },
        {
            "id": "q7",
            "category": "Compliance",
            "question": "Are there any coding compliance issues?",
            "prompt": "Review:\n1. Compliance with official ICD-10-CM guidelines\n2. Any documentation inconsistencies\n3. Claim denial risk\n4. Recommendations for compliance improvement"
        },
        {
            "id": "q8",
            "category": "General Analysis",
            "question": "Provide comprehensive case analysis",
            "prompt": "Provide comprehensive analysis including:\n1. Clinical case summary\n2. Main diagnoses with codes\n3. Documentation gaps\n4. Coding improvement recommendations\n5. Potential financial impact\n6. Documentation strengths and weaknesses"
        }
    ]
}

def get_questions(language="ar"):
    """Get predefined questions for specified language"""
    return CLINICAL_QUESTIONS.get(language, CLINICAL_QUESTIONS["ar"])

def get_question_by_id(question_id, language="ar"):
    """Get specific question by ID"""
    questions = get_questions(language)
    for q in questions:
        if q["id"] == question_id:
            return q
    return None

def get_categories(language="ar"):
    """Get unique categories"""
    questions = get_questions(language)
    categories = list(set([q["category"] for q in questions]))
    return sorted(categories)
