# 🔑 دليل ترقية مفاتيح API - AI Keys Upgrade Guide

## ⚠️ **المشكلة الحالية**

المفاتيح المستخدمة حالياً هي **Free Tier (مجانية)** ولها حد **20 طلب فقط في اليوم لكل مفتاح**.

### **الأخطاء التي قد تظهر:**
```
Error 429: Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests
Limit: 20 requests per day
```

---

## 📊 **السعة الحالية**

| المزود | عدد المفاتيح | الحد اليومي | الإجمالي |
|--------|--------------|-------------|----------|
| **Gemini (Free)** | 6 مفاتيح | 20 طلب/مفتاح | **120 طلب/يوم** ❌ |
| **Azure** | 1 مفتاح | يعتمد على الاشتراك | غير معروف |

**النتيجة:** ⚠️ **120 طلب يومياً غير كافية للاستخدام الإنتاجي!**

---

## ✅ **الحلول المتاحة**

### **الحل 1: ترقية مفاتيح Gemini إلى مدفوعة** (موصى به 🌟)

#### **الخطوات:**

1. **اذهب إلى Google AI Studio:**
   - https://aistudio.google.com/

2. **أنشئ مشروع جديد في Google Cloud:**
   - https://console.cloud.google.com/
   - Enable Billing (فعّل الفوترة)

3. **احصل على API Key مدفوع:**
   - Enable "Generative Language API"
   - Create Credentials → API Key
   - ربط المفتاح بحساب فوترة نشط

4. **الأسعار بعد الترقية:**
   ```
   Gemini 2.5 Flash:
   - Input: $0.075 per 1M tokens
   - Output: $0.30 per 1M tokens
   
   الحدود بعد الدفع:
   - 1,000 طلب/دقيقة
   - 4,000,000 طلب/يوم
   ```

5. **استبدل المفاتيح في `/app/backend/.env`:**
   ```env
   GEMINI_API_KEY_1="new-paid-key-here"
   GEMINI_API_KEY_2="new-paid-key-here"
   # ... إلخ
   ```

---

### **الحل 2: استخدام Azure OpenAI بشكل أساسي**

#### **تحديث إعدادات Azure:**

1. **إعداد Azure OpenAI Resource:**
   - اذهب إلى: https://portal.azure.com/
   - Create "Azure OpenAI" resource
   - Deploy model (GPT-4 أو GPT-3.5-turbo)

2. **احصل على البيانات:**
   ```
   - Endpoint: https://YOUR-RESOURCE.openai.azure.com/
   - API Key: من Azure Portal
   - Deployment Name: اسم النموذج الذي نشرته
   ```

3. **حدّث `/app/backend/.env`:**
   ```env
   AZURE_OPENAI_KEY="your-azure-key"
   AZURE_OPENAI_ENDPOINT="https://YOUR-RESOURCE.openai.azure.com/"
   AZURE_OPENAI_DEPLOYMENT="gpt-4"
   AZURE_OPENAI_API_VERSION="2024-02-15-preview"
   ```

4. **الأسعار:**
   ```
   GPT-4 Turbo:
   - Input: $0.01 per 1K tokens
   - Output: $0.03 per 1K tokens
   
   GPT-3.5 Turbo:
   - Input: $0.0005 per 1K tokens
   - Output: $0.0015 per 1K tokens
   ```

---

### **الحل 3: استخدام Emergent Universal Key** (إذا كان متاحاً)

إذا كان لديك اشتراك في Emergent مع Universal Key:

1. **استخدم أداة Emergent Integrations:**
   ```python
   from emergentintegrations import get_llm_key
   key = get_llm_key()
   ```

2. **هذا المفتاح يعمل مع:**
   - OpenAI (Text & Image)
   - Anthropic Claude (Text)
   - Google Gemini (Text & Image)

---

## 🔄 **الحل المؤقت - Auto Fallback**

✅ **تم تطبيقه بالفعل!**

النظام الآن يحتوي على:
1. **محاولة Gemini أولاً** (جميع المفاتيح الـ6)
2. **إذا فشل Gemini** → تلقائياً ينتقل لـ **Azure**
3. **إذا فشل Azure** → رسالة خطأ واضحة

**كيفية الاستخدام:**
- المستخدم يختار "Gemini" في الواجهة
- إذا وصلت المفاتيح للحد → النظام يستخدم Azure تلقائياً
- ✅ لا يحتاج المستخدم فعل أي شيء

---

## 📈 **توصيات للإنتاج**

### **للاستخدام المكثف (50+ موظف):**

**Option A: Gemini مدفوع**
```
التكلفة المتوقعة:
- 2,000 تحليل/يوم
- ~4,000,000 tokens/يوم
- التكلفة: ~$300-400/شهر
```

**Option B: Azure GPT-3.5 Turbo**
```
التكلفة المتوقعة:
- 2,000 تحليل/يوم
- ~4,000,000 tokens/يوم
- التكلفة: ~$60-80/شهر
```

**Option C: مزيج (Hybrid)**
```
- Gemini للتحليل الخفيف
- Azure للتحليل المعقد
- التكلفة: ~$150-200/شهر
```

---

## 🚀 **الإجراء الموصى به الآن**

### **خطوة 1: استخدم Azure فوراً**
```
1. حدّث AZURE_OPENAI_ENDPOINT في .env
2. أعد تشغيل backend
3. اختر "Azure" في الواجهة بدلاً من Gemini
```

### **خطوة 2: ترقية Gemini (للمستقبل)**
```
1. احصل على مفاتيح مدفوعة
2. استبدل المفاتيح في .env
3. أعد تشغيل backend
```

### **خطوة 3: مراقبة الاستخدام**
```
- Google Cloud Console: لمراقبة Gemini
- Azure Portal: لمراقبة Azure
- إعداد تنبيهات عند الوصول لـ80% من الحد
```

---

## 📞 **الدعم**

إذا واجهت أي مشاكل:
1. تحقق من backend logs: `tail -f /var/log/supervisor/backend.err.log`
2. راجع هذا الدليل
3. تواصل مع فريق Emergent

---

## ✅ **الخلاصة**

| الحالة | الحل |
|--------|------|
| **الآن** | استخدم Azure (تأكد من endpoint صحيح) |
| **قصير المدى** | ترقية مفاتيح Gemini أو Azure |
| **طويل المدى** | نظام hybrid مع مراقبة |

**النظام الآن محمي بـ Auto-Fallback! ✅**
