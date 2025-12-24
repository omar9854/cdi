#!/usr/bin/env python3
"""
MediDoc AI - System Documentation Generator
Creates comprehensive PDF documentation in Arabic
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, ListFlowable, ListItem
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
from datetime import datetime
import os

# Register Arabic font
try:
    pdfmetrics.registerFont(TTFont('Arabic', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
    FONT_NAME = 'Arabic'
except:
    FONT_NAME = 'Helvetica'

def create_styles():
    """Create custom styles for Arabic RTL support"""
    styles = getSampleStyleSheet()
    
    # Title style
    styles.add(ParagraphStyle(
        name='ArabicTitle',
        fontName=FONT_NAME,
        fontSize=24,
        alignment=TA_CENTER,
        spaceAfter=30,
        textColor=colors.HexColor('#1e40af'),
        leading=30
    ))
    
    # Heading 1
    styles.add(ParagraphStyle(
        name='ArabicH1',
        fontName=FONT_NAME,
        fontSize=18,
        alignment=TA_RIGHT,
        spaceAfter=15,
        spaceBefore=20,
        textColor=colors.HexColor('#1e3a8a'),
        leading=24
    ))
    
    # Heading 2
    styles.add(ParagraphStyle(
        name='ArabicH2',
        fontName=FONT_NAME,
        fontSize=14,
        alignment=TA_RIGHT,
        spaceAfter=10,
        spaceBefore=15,
        textColor=colors.HexColor('#3b82f6'),
        leading=20
    ))
    
    # Body text
    styles.add(ParagraphStyle(
        name='ArabicBody',
        fontName=FONT_NAME,
        fontSize=11,
        alignment=TA_RIGHT,
        spaceAfter=8,
        leading=18
    ))
    
    # Code style
    styles.add(ParagraphStyle(
        name='CodeBlock',
        fontName='Courier',
        fontSize=9,
        alignment=TA_LEFT,
        spaceAfter=8,
        backColor=colors.HexColor('#f3f4f6'),
        leading=14,
        leftIndent=10,
        rightIndent=10
    ))
    
    # Table header
    styles.add(ParagraphStyle(
        name='TableHeader',
        fontName=FONT_NAME,
        fontSize=10,
        alignment=TA_CENTER,
        textColor=colors.white
    ))
    
    return styles

def create_table(data, col_widths=None):
    """Create styled table"""
    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f1f5f9')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    return table

def generate_documentation():
    """Generate the complete system documentation PDF"""
    
    doc = SimpleDocTemplate(
        "/app/documentation/MediDoc_AI_System_Documentation.pdf",
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    styles = create_styles()
    story = []
    
    # ==================== COVER PAGE ====================
    story.append(Spacer(1, 2*inch))
    story.append(Paragraph("نظام MediDoc AI", styles['ArabicTitle']))
    story.append(Paragraph("التوثيق الفني الشامل", styles['ArabicTitle']))
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph("مركز تحسين التوثيق السريري والترميز الطبي", styles['ArabicH2']))
    story.append(Spacer(1, 1*inch))
    
    # Project info table
    project_info = [
        ['القيمة', 'البند'],
        ['MediDoc AI', 'اسم النظام'],
        ['2.0', 'الإصدار'],
        [datetime.now().strftime('%Y-%m-%d'), 'تاريخ التوثيق'],
        ['عمر المغذوي', 'المطور'],
        ['تجمع المدينة المنورة الصحي', 'الجهة المالكة'],
    ]
    story.append(create_table(project_info, [200, 200]))
    story.append(PageBreak())
    
    # ==================== TABLE OF CONTENTS ====================
    story.append(Paragraph("فهرس المحتويات", styles['ArabicH1']))
    story.append(Spacer(1, 20))
    
    toc_items = [
        "1. نظرة عامة على النظام",
        "2. البنية التقنية (Technical Architecture)",
        "3. تقنيات البرمجة المستخدمة",
        "4. قاعدة البيانات",
        "5. واجهات برمجة التطبيقات (APIs)",
        "6. متطلبات الأجهزة والبرمجيات",
        "7. متطلبات التشغيل الأوفلاين",
        "8. متطلبات النقل لسيرفرات وزارة الصحة",
        "9. إجراءات الأمان والحماية",
        "10. دليل التثبيت والنشر",
        "11. الصيانة والدعم الفني",
    ]
    
    for item in toc_items:
        story.append(Paragraph(item, styles['ArabicBody']))
    
    story.append(PageBreak())
    
    # ==================== SECTION 1: OVERVIEW ====================
    story.append(Paragraph("1. نظرة عامة على النظام", styles['ArabicH1']))
    
    story.append(Paragraph("1.1 وصف النظام", styles['ArabicH2']))
    story.append(Paragraph("""
    نظام MediDoc AI هو منصة متكاملة لتحسين التوثيق السريري (CDI) والترميز الطبي، 
    يعتمد على الذكاء الاصطناعي لتحليل الملاحظات السريرية وتقديم اقتراحات لتحسين التوثيق الطبي.
    يدعم النظام اللغتين العربية والإنجليزية ويتوافق مع معايير ICD-10-CM للترميز الطبي.
    """, styles['ArabicBody']))
    
    story.append(Paragraph("1.2 الميزات الرئيسية", styles['ArabicH2']))
    features = [
        "• تحليل الملاحظات السريرية بالذكاء الاصطناعي (Gemini AI)",
        "• اقتراح أكواد ICD-10-CM تلقائياً",
        "• نظام محادثة ذكي للاستفسارات الطبية",
        "• لوحة تحكم للمشرفين مع تقارير شاملة",
        "• نظام إدارة المستخدمين والصلاحيات",
        "• المصادقة الثنائية (MFA) لحماية الحسابات",
        "• تصدير التقارير بصيغ PDF و Excel",
        "• دعم كامل للغة العربية (RTL)",
    ]
    for f in features:
        story.append(Paragraph(f, styles['ArabicBody']))
    
    story.append(PageBreak())
    
    # ==================== SECTION 2: ARCHITECTURE ====================
    story.append(Paragraph("2. البنية التقنية (Technical Architecture)", styles['ArabicH1']))
    
    story.append(Paragraph("2.1 نمط البنية", styles['ArabicH2']))
    story.append(Paragraph("""
    يتبع النظام نمط البنية ثلاثية الطبقات (Three-Tier Architecture):
    """, styles['ArabicBody']))
    
    arch_data = [
        ['الوصف', 'التقنية', 'الطبقة'],
        ['واجهة المستخدم التفاعلية', 'React.js 19', 'العرض (Presentation)'],
        ['معالجة الطلبات والمنطق', 'FastAPI (Python)', 'التطبيق (Application)'],
        ['تخزين البيانات', 'MongoDB', 'البيانات (Data)'],
    ]
    story.append(create_table(arch_data, [180, 120, 100]))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("2.2 مخطط البنية", styles['ArabicH2']))
    arch_diagram = """
    ┌─────────────────────────────────────────────────────────────┐
    │                    المستخدمون (Users)                        │
    │                   متصفح الويب (Browser)                      │
    └─────────────────────────┬───────────────────────────────────┘
                              │ HTTPS
    ┌─────────────────────────▼───────────────────────────────────┐
    │                 Nginx Reverse Proxy                         │
    │                    (Load Balancer)                          │
    └─────────────┬───────────────────────────────┬───────────────┘
                  │                               │
    ┌─────────────▼─────────────┐   ┌─────────────▼─────────────┐
    │     Frontend Server       │   │     Backend Server        │
    │      React.js:3000        │   │     FastAPI:8001          │
    └───────────────────────────┘   └─────────────┬─────────────┘
                                                  │
                                    ┌─────────────▼─────────────┐
                                    │        MongoDB            │
                                    │       Port: 27017         │
                                    └─────────────┬─────────────┘
                                                  │
                                    ┌─────────────▼─────────────┐
                                    │     External APIs         │
                                    │   • Google Gemini AI      │
                                    │   • SMTP (Email)          │
                                    └───────────────────────────┘
    """
    story.append(Paragraph(arch_diagram.replace('\n', '<br/>'), styles['CodeBlock']))
    
    story.append(PageBreak())
    
    # ==================== SECTION 3: TECHNOLOGIES ====================
    story.append(Paragraph("3. تقنيات البرمجة المستخدمة", styles['ArabicH1']))
    
    story.append(Paragraph("3.1 الواجهة الأمامية (Frontend)", styles['ArabicH2']))
    frontend_tech = [
        ['الاستخدام', 'الإصدار', 'التقنية'],
        ['إطار واجهة المستخدم', '19.0.0', 'React.js'],
        ['التوجيه والملاحة', '7.x', 'React Router DOM'],
        ['إدارة الحالة', 'Built-in', 'React Hooks'],
        ['طلبات HTTP', '1.x', 'Axios'],
        ['تصميم UI', '3.4.x', 'Tailwind CSS'],
        ['مكونات جاهزة', '0.x', 'Shadcn/UI'],
        ['الأيقونات', '0.x', 'Lucide React'],
        ['الإشعارات', '1.x', 'Sonner'],
        ['الرسوم البيانية', '2.x', 'Recharts'],
    ]
    story.append(create_table(frontend_tech, [150, 80, 170]))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("3.2 الواجهة الخلفية (Backend)", styles['ArabicH2']))
    backend_tech = [
        ['الاستخدام', 'الإصدار', 'التقنية'],
        ['لغة البرمجة', '3.11+', 'Python'],
        ['إطار API', '0.110+', 'FastAPI'],
        ['قاعدة البيانات', '4.6+', 'Motor (Async MongoDB)'],
        ['المصادقة', 'PyJWT', 'JWT Tokens'],
        ['تشفير كلمات المرور', '4.1+', 'bcrypt'],
        ['الذكاء الاصطناعي', 'Gemini 2.0', 'Google Generative AI'],
        ['إنشاء PDF', '4.x', 'ReportLab'],
        ['إنشاء Excel', '3.x', 'OpenPyXL'],
        ['البريد الإلكتروني', '4.x', 'aiosmtplib'],
        ['تحديد المعدل', '0.1.x', 'SlowAPI'],
        ['المراقبة', '0.x', 'Prometheus'],
    ]
    story.append(create_table(backend_tech, [150, 80, 170]))
    
    story.append(PageBreak())
    
    # ==================== SECTION 4: DATABASE ====================
    story.append(Paragraph("4. قاعدة البيانات", styles['ArabicH1']))
    
    story.append(Paragraph("4.1 نوع قاعدة البيانات", styles['ArabicH2']))
    story.append(Paragraph("""
    يستخدم النظام MongoDB كقاعدة بيانات NoSQL. تم اختيار MongoDB للأسباب التالية:
    • المرونة في تخزين البيانات غير المنظمة
    • الأداء العالي مع البيانات الكبيرة
    • سهولة التوسع الأفقي (Horizontal Scaling)
    • دعم ممتاز للـ Async operations مع Python
    """, styles['ArabicBody']))
    
    story.append(Paragraph("4.2 المجموعات (Collections)", styles['ArabicH2']))
    collections_data = [
        ['عدد الوثائق', 'الوصف', 'المجموعة'],
        ['~10+', 'بيانات المستخدمين', 'users'],
        ['~40+', 'الملاحظات السريرية', 'clinical_notes'],
        ['~40+', 'نتائج التحليل', 'analyses'],
        ['~35+', 'جلسات المستخدمين', 'user_sessions'],
        ['~5+', 'المستشفيات', 'hospitals'],
        ['~100+', 'رسائل المحادثة', 'chat_messages'],
        ['~3+', 'أسعار DRG', 'drg_prices'],
        ['~10+', 'سجلات الأمان', 'audit_logs'],
        ['~2+', 'إعدادات AI', 'ai_settings'],
    ]
    story.append(create_table(collections_data, [80, 150, 170]))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("4.3 مخطط البيانات الرئيسي (Schema)", styles['ArabicH2']))
    
    # Users Schema
    story.append(Paragraph("جدول المستخدمين (users):", styles['ArabicBody']))
    users_schema = """
    {
      "id": "UUID",
      "email": "string (unique)",
      "password_hash": "string (bcrypt)",
      "full_name": "string",
      "phone_number": "string",
      "role": "enum: user|admin|supervisor",
      "department": "enum: cdi|coding",
      "coding_role": "enum: coder|auditor|supervisor",
      "mfa_enabled": "boolean",
      "is_active": "boolean",
      "created_at": "datetime",
      "updated_at": "datetime"
    }
    """
    story.append(Paragraph(users_schema, styles['Code']))
    
    # Clinical Notes Schema
    story.append(Paragraph("جدول الملاحظات السريرية (clinical_notes):", styles['ArabicBody']))
    notes_schema = """
    {
      "id": "UUID",
      "user_id": "UUID (reference)",
      "title": "string",
      "patient_name": "string",
      "doctor_notes": [
        {
          "text": "string",
          "specialty": "string",
          "timestamp": "datetime"
        }
      ],
      "created_at": "datetime",
      "updated_at": "datetime"
    }
    """
    story.append(Paragraph(notes_schema, styles['Code']))
    
    story.append(PageBreak())
    
    # ==================== SECTION 5: APIs ====================
    story.append(Paragraph("5. واجهات برمجة التطبيقات (APIs)", styles['ArabicH1']))
    
    story.append(Paragraph("5.1 نقاط النهاية الرئيسية", styles['ArabicH2']))
    
    apis_data = [
        ['الوصف', 'الطريقة', 'المسار'],
        ['تسجيل الدخول (خطوة 1)', 'POST', '/api/auth/login-step1'],
        ['التحقق من OTP (خطوة 2)', 'POST', '/api/auth/login-step2'],
        ['تسجيل مستخدم جديد', 'POST', '/api/auth/register'],
        ['الملاحظات السريرية', 'GET/POST', '/api/notes'],
        ['تحليل ملاحظة', 'POST', '/api/analyze'],
        ['الأسئلة السريرية', 'GET', '/api/clinical-questions'],
        ['سؤال جاهز', 'POST', '/api/chat/ask-question/{id}'],
        ['إحصائيات المشرف', 'GET', '/api/supervisor/stats'],
        ['تقرير شهري', 'GET', '/api/supervisor/monthly-report'],
        ['إعدادات AI', 'GET/PUT', '/api/ai-settings'],
    ]
    story.append(create_table(apis_data, [170, 60, 170]))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("5.2 المصادقة", styles['ArabicH2']))
    story.append(Paragraph("""
    يستخدم النظام JWT (JSON Web Tokens) للمصادقة:
    • صلاحية التوكن: 7 أيام
    • خوارزمية التشفير: HS256
    • يُرسل التوكن في Header: Authorization: Bearer {token}
    """, styles['ArabicBody']))
    
    story.append(PageBreak())
    
    # ==================== SECTION 6: REQUIREMENTS ====================
    story.append(Paragraph("6. متطلبات الأجهزة والبرمجيات", styles['ArabicH1']))
    
    story.append(Paragraph("6.1 متطلبات السيرفر (Production)", styles['ArabicH2']))
    server_req = [
        ['الموصى به', 'الحد الأدنى', 'المكون'],
        ['16 Core', '8 Core', 'المعالج (CPU)'],
        ['32 GB', '16 GB', 'الذاكرة (RAM)'],
        ['500 GB SSD', '200 GB SSD', 'التخزين'],
        ['1 Gbps', '100 Mbps', 'الشبكة'],
    ]
    story.append(create_table(server_req, [120, 120, 160]))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("6.2 متطلبات البرمجيات", styles['ArabicH2']))
    software_req = [
        ['الإصدار', 'البرنامج'],
        ['Ubuntu 22.04 LTS أو RHEL 8+', 'نظام التشغيل'],
        ['3.11+', 'Python'],
        ['20.x LTS', 'Node.js'],
        ['6.x أو 7.x', 'MongoDB'],
        ['1.24+', 'Nginx'],
        ['20.x+', 'Docker (اختياري)'],
        ['2.x (اختياري)', 'Docker Compose'],
    ]
    story.append(create_table(software_req, [200, 200]))
    
    story.append(PageBreak())
    
    # ==================== SECTION 7: OFFLINE REQUIREMENTS ====================
    story.append(Paragraph("7. متطلبات التشغيل الأوفلاين", styles['ArabicH1']))
    
    story.append(Paragraph("7.1 التحديات", styles['ArabicH2']))
    story.append(Paragraph("""
    لتشغيل النظام بدون اتصال بالإنترنت، يجب معالجة التحديات التالية:
    """, styles['ArabicBody']))
    
    challenges = [
        "• استبدال Gemini AI بنموذج محلي",
        "• توفير خدمة البريد الإلكتروني داخلياً أو تعطيلها",
        "• تحميل جميع الاعتماديات مسبقاً",
    ]
    for c in challenges:
        story.append(Paragraph(c, styles['ArabicBody']))
    
    story.append(Paragraph("7.2 الحل: نموذج AI محلي", styles['ArabicH2']))
    story.append(Paragraph("""
    خيارات النماذج المحلية للذكاء الاصطناعي:
    """, styles['ArabicBody']))
    
    ai_models = [
        ['المتطلبات', 'الحجم', 'النموذج'],
        ['GPU 24GB+ أو CPU 32GB RAM', '7B-70B', 'Llama 3'],
        ['GPU 8GB+ أو CPU 16GB RAM', '3.8B', 'Phi-3'],
        ['GPU 16GB+ أو CPU 24GB RAM', '7B', 'Meditron (طبي متخصص)'],
        ['GPU 8GB+ أو CPU 16GB RAM', '7B', 'Mistral'],
    ]
    story.append(create_table(ai_models, [150, 80, 170]))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("7.3 البرمجيات المطلوبة للأوفلاين", styles['ArabicH2']))
    offline_software = [
        ['الغرض', 'البرنامج'],
        ['تشغيل النماذج المحلية', 'Ollama'],
        ['بديل للبريد الإلكتروني', 'Mailhog أو تعطيل MFA'],
        ['الحاويات', 'Docker + Docker Compose'],
        ['تحميل الاعتماديات', 'pip download + yarn cache'],
    ]
    story.append(create_table(offline_software, [200, 200]))
    
    story.append(Paragraph("7.4 خطوات التحضير للأوفلاين", styles['ArabicH2']))
    offline_steps = """
    # 1. تحميل اعتماديات Python
    pip download -r requirements.txt -d ./offline_packages/
    
    # 2. تحميل اعتماديات Node.js
    yarn config set yarn-offline-mirror ./npm-packages-offline-cache
    yarn install
    
    # 3. تحميل نموذج AI المحلي
    ollama pull phi3
    # أو للنموذج الطبي:
    ollama pull meditron
    
    # 4. تصدير قاعدة البيانات
    mongodump --db clinical_doc_center --out ./backup/
    
    # 5. إنشاء صورة Docker كاملة
    docker build -t medidoc-ai:offline .
    docker save medidoc-ai:offline > medidoc-offline.tar
    """
    story.append(Paragraph(offline_steps, styles['Code']))
    
    story.append(PageBreak())
    
    # ==================== SECTION 8: MOH REQUIREMENTS ====================
    story.append(Paragraph("8. متطلبات النقل لسيرفرات وزارة الصحة", styles['ArabicH1']))
    
    story.append(Paragraph("8.1 المتطلبات الأمنية", styles['ArabicH2']))
    security_req = [
        "• شهادة SSL/TLS صالحة (Let's Encrypt أو CA معتمدة)",
        "• تشفير البيانات في الراحة (at-rest) والنقل (in-transit)",
        "• جدار حماية (Firewall) مع قواعد صارمة",
        "• نظام كشف التسلل (IDS/IPS)",
        "• تسجيل الأحداث الأمنية (Security Audit Logs)",
        "• المصادقة الثنائية (MFA) للمستخدمين",
        "• سياسات كلمات مرور قوية (12+ حرف)",
    ]
    for s in security_req:
        story.append(Paragraph(s, styles['ArabicBody']))
    
    story.append(Paragraph("8.2 المتطلبات التنظيمية", styles['ArabicH2']))
    regulatory_req = [
        "• التوافق مع نظام حماية البيانات الشخصية السعودي",
        "• التوافق مع معايير HIPAA (إن لزم)",
        "• سياسة الاحتفاظ بالبيانات",
        "• خطة استعادة الكوارث (Disaster Recovery)",
        "• اتفاقية مستوى الخدمة (SLA)",
    ]
    for r in regulatory_req:
        story.append(Paragraph(r, styles['ArabicBody']))
    
    story.append(Paragraph("8.3 متطلبات الشبكة", styles['ArabicH2']))
    network_req = [
        ['القيمة', 'المتطلب'],
        ['Static IP أو DNS hostname', 'عنوان IP'],
        ['443 (HTTPS), 27017 (MongoDB internal)', 'المنافذ المطلوبة'],
        ['50 Mbps+', 'عرض النطاق'],
        ['Load Balancer (اختياري)', 'موازنة الحمل'],
        ['نعم', 'VPN للوصول الإداري'],
    ]
    story.append(create_table(network_req, [200, 200]))
    
    story.append(Paragraph("8.4 الوثائق المطلوبة للنقل", styles['ArabicH2']))
    docs_required = [
        "• وثيقة البنية التقنية (هذا المستند)",
        "• دليل التثبيت والتشغيل",
        "• تقرير اختبار الاختراق (Penetration Test)",
        "• شهادة تقييم الأمان",
        "• خطة النسخ الاحتياطي",
        "• قائمة الاعتماديات والتراخيص",
        "• دليل المستخدم",
    ]
    for d in docs_required:
        story.append(Paragraph(d, styles['ArabicBody']))
    
    story.append(PageBreak())
    
    # ==================== SECTION 9: SECURITY ====================
    story.append(Paragraph("9. إجراءات الأمان والحماية", styles['ArabicH1']))
    
    story.append(Paragraph("9.1 حماية البيانات", styles['ArabicH2']))
    data_protection = [
        ['التطبيق', 'الإجراء'],
        ['bcrypt مع salt عشوائي', 'تشفير كلمات المرور'],
        ['HTTPS مع TLS 1.3', 'تشفير الاتصال'],
        ['MongoDB encryption', 'تشفير قاعدة البيانات'],
        ['JWT with expiry', 'إدارة الجلسات'],
        ['Rate limiting', 'حماية من هجمات DDoS'],
        ['Input sanitization', 'حماية من SQL Injection'],
        ['CORS policy', 'حماية من CSRF'],
    ]
    story.append(create_table(data_protection, [200, 200]))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("9.2 سجلات الأمان", styles['ArabicH2']))
    story.append(Paragraph("""
    يسجل النظام الأحداث التالية في مجموعة audit_logs:
    • محاولات تسجيل الدخول (ناجحة وفاشلة)
    • تغييرات بيانات المستخدمين
    • الوصول للملفات الحساسة
    • عمليات التحليل والتصدير
    • أخطاء النظام الحرجة
    """, styles['ArabicBody']))
    
    story.append(PageBreak())
    
    # ==================== SECTION 10: INSTALLATION ====================
    story.append(Paragraph("10. دليل التثبيت والنشر", styles['ArabicH1']))
    
    story.append(Paragraph("10.1 التثبيت باستخدام Docker (موصى به)", styles['ArabicH2']))
    docker_install = """
    # 1. استنساخ المشروع
    git clone https://github.com/your-repo/medidoc-ai.git
    cd medidoc-ai
    
    # 2. إنشاء ملف البيئة
    cp .env.example .env
    nano .env  # تعديل القيم
    
    # 3. بناء وتشغيل الحاويات
    docker-compose up -d --build
    
    # 4. التحقق من التشغيل
    docker-compose ps
    docker-compose logs -f
    """
    story.append(Paragraph(docker_install, styles['Code']))
    
    story.append(Paragraph("10.2 التثبيت اليدوي", styles['ArabicH2']))
    manual_install = """
    # Backend
    cd backend
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    uvicorn server:app --host 0.0.0.0 --port 8001
    
    # Frontend
    cd frontend
    yarn install
    yarn build
    serve -s build -l 3000
    
    # MongoDB
    sudo systemctl start mongod
    """
    story.append(Paragraph(manual_install, styles['Code']))
    
    story.append(Paragraph("10.3 متغيرات البيئة المطلوبة", styles['ArabicH2']))
    env_vars = [
        ['الوصف', 'المتغير'],
        ['رابط MongoDB', 'MONGO_URL'],
        ['اسم قاعدة البيانات', 'DB_NAME'],
        ['مفتاح JWT', 'JWT_SECRET'],
        ['مفاتيح Gemini API', 'GEMINI_API_KEY_1..7'],
        ['خادم SMTP', 'SMTP_HOST'],
        ['منفذ SMTP', 'SMTP_PORT'],
        ['مستخدم SMTP', 'SMTP_USER'],
        ['كلمة مرور SMTP', 'SMTP_PASSWORD'],
        ['رابط الواجهة الأمامية', 'FRONTEND_URL'],
    ]
    story.append(create_table(env_vars, [200, 200]))
    
    story.append(PageBreak())
    
    # ==================== SECTION 11: MAINTENANCE ====================
    story.append(Paragraph("11. الصيانة والدعم الفني", styles['ArabicH1']))
    
    story.append(Paragraph("11.1 النسخ الاحتياطي", styles['ArabicH2']))
    backup_script = """
    # نسخ احتياطي يومي
    #!/bin/bash
    DATE=$(date +%Y%m%d)
    mongodump --db clinical_doc_center --out /backup/$DATE
    tar -czf /backup/medidoc_$DATE.tar.gz /backup/$DATE
    
    # حذف النسخ الأقدم من 30 يوم
    find /backup -name "*.tar.gz" -mtime +30 -delete
    """
    story.append(Paragraph(backup_script, styles['Code']))
    
    story.append(Paragraph("11.2 المراقبة", styles['ArabicH2']))
    story.append(Paragraph("""
    يدعم النظام Prometheus للمراقبة. المقاييس المتاحة:
    • عدد الطلبات (/metrics)
    • زمن الاستجابة
    • معدل الأخطاء
    • استخدام الذاكرة
    """, styles['ArabicBody']))
    
    story.append(Paragraph("11.3 معلومات الاتصال", styles['ArabicH2']))
    contact_info = [
        ['القيمة', 'البند'],
        ['عمر المغذوي', 'المطور'],
        ['almaghthawi.cdi@gmail.com', 'البريد الإلكتروني'],
        ['+966 XX XXX XXXX', 'الهاتف'],
        ['تجمع المدينة المنورة الصحي', 'الجهة'],
    ]
    story.append(create_table(contact_info, [200, 200]))
    
    story.append(Spacer(1, 1*inch))
    
    # Footer
    story.append(Paragraph("─" * 50, styles['ArabicBody']))
    story.append(Paragraph(f"تم إنشاء هذا التوثيق بتاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['ArabicBody']))
    story.append(Paragraph("© 2025 MediDoc AI - جميع الحقوق محفوظة", styles['ArabicBody']))
    
    # Build PDF
    doc.build(story)
    print("✅ تم إنشاء ملف PDF بنجاح!")
    return "/app/documentation/MediDoc_AI_System_Documentation.pdf"

if __name__ == "__main__":
    os.makedirs("/app/documentation", exist_ok=True)
    pdf_path = generate_documentation()
    print(f"📄 الملف: {pdf_path}")
