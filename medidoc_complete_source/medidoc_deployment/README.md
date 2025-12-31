# MediDoc AI - نظام تحسين التوثيق السريري

## 🏥 نظرة عامة | Overview

MediDoc AI هو نظام ذكاء اصطناعي متكامل لتحسين التوثيق السريري (CDI) مصمم خصيصاً للمؤسسات الصحية في المملكة العربية السعودية.

**✅ آمن 100% - يعمل بالكامل محلياً بدون اتصال بالإنترنت**

MediDoc AI is a comprehensive AI-powered Clinical Documentation Improvement (CDI) system designed specifically for healthcare institutions in Saudi Arabia.

**✅ 100% Secure - Operates entirely offline without internet connection**

---

## 🔒 ميزات الأمان | Security Features

- **لا توجد تبعيات خارجية**: جميع البيانات الطبية تبقى داخل الشبكة المحلية
- **معالجة محلية 100%**: نموذج الذكاء الاصطناعي يعمل على السيرفر المحلي
- **متوافق مع HIPAA**: تصميم يراعي خصوصية البيانات الطبية
- **تشفير البيانات**: في الراحة والنقل

---

## 🤖 نموذج الذكاء الاصطناعي | AI Model

- **النموذج**: Qwen2.5-72B-Instruct
- **التكميم**: 4-bit NF4 (لتقليل استخدام الذاكرة)
- **الجهاز المطلوب**: NVIDIA A100 40GB GPU
- **الدور**: مدقق طبي أول متخصص في CDI

---

## 📊 قدرات النظام | System Capabilities

### تحليل التوثيق السريري
- تحديد التشخيص الرئيسي والثانوي
- استخراج الأدلة السريرية لكل تشخيص
- تعيين أكواد ICD-10-AM بدقة

### حساب تكلفة DRG
- قاعدة بيانات AR-DRG v9 للسعودية
- 800+ كود DRG
- حساب التكلفة حسب نوع المستشفى (A, B, C)

### توليد الاستفسارات للأطباء
- استفسارات مدعومة بأدلة سريرية
- تحديد الثغرات في التوثيق
- تحسين دقة الترميز

---

## 🚀 التثبيت | Installation

### المتطلبات
- Ubuntu Server 22.04+
- NVIDIA A100 GPU (40GB)
- Python 3.11+
- MongoDB
- 64GB+ RAM

### خطوات التثبيت

```bash
# 1. نقل الملفات للسيرفر
scp -i MediDoc-Security.pem medidoc_deployment.tar.gz ubuntu@YOUR_SERVER_IP:/home/ubuntu/

# 2. الاتصال بالسيرفر
ssh -i MediDoc-Security.pem ubuntu@YOUR_SERVER_IP

# 3. فك الضغط
tar -xzf medidoc_deployment.tar.gz
cd medidoc_deployment

# 4. تشغيل سكربت التثبيت
chmod +x setup_server.sh
./setup_server.sh
```

---

## 📁 هيكل الملفات | File Structure

```
medidoc_deployment/
├── local_llm.py          # منطق الذكاء الاصطناعي المحلي
├── drg_lookup.py         # البحث في قاعدة بيانات DRG
├── cdi_endpoints.py      # نقاط API للتحليل
├── icd10am_codes.py      # أكواد ICD-10-AM
├── server_integration.py # تعليمات الدمج
├── setup_server.sh       # سكربت التثبيت
├── requirements.txt      # متطلبات Python
├── drg_prices.xlsx       # قائمة أسعار DRG
└── README.md             # هذا الملف
```

---

## ⚙️ التكوين | Configuration

### ملف .env
```bash
# MongoDB
MONGO_URL=mongodb://127.0.0.1:27017
DB_NAME=medidoc_production

# JWT Security
JWT_SECRET=your-secure-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Model Configuration
MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
HOSPITAL_TYPE=A

# DRG Price List
DRG_PRICE_LIST=/opt/medidoc-ai/data/drg_prices.xlsx
```

---

## 🔧 الأوامر المفيدة | Useful Commands

```bash
# التحقق من حالة الخدمة
sudo systemctl status medidoc-backend

# عرض السجلات
sudo journalctl -u medidoc-backend -f

# إعادة التشغيل
sudo systemctl restart medidoc-backend

# التحقق من GPU
nvidia-smi
```

---

## 📞 الدعم | Support

للدعم الفني، يرجى التواصل مع فريق تحسين التوثيق السريري.

---

## 📝 ملاحظات مهمة | Important Notes

1. **الأمان**: تأكد من تغيير JWT_SECRET قبل الإنتاج
2. **HTTPS**: قم بتثبيت شهادة SSL للإنتاج
3. **النسخ الاحتياطي**: قم بعمل نسخ احتياطي منتظم لقاعدة البيانات
4. **التحديثات**: قم بتحديث النظام بشكل دوري

---

© 2025 - تجمع المدينة المنورة الصحي | Madinah Health Cluster
