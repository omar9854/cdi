# 🚀 دليل نقل نظام MediDoc AI إلى سيرفر خارجي

## إدارة تحسين التوثيق السريري - تجمع المدينة المنورة الصحي

---

## 📋 البيانات المطلوبة منك

قبل البدء في عملية النقل، أحتاج منك المعلومات التالية:

### 1️⃣ معلومات السيرفر

| البند | القيمة المطلوبة | مثال |
|-------|----------------|------|
| عنوان IP للسيرفر | | `192.168.1.100` |
| اسم المستخدم (SSH) | | `root` أو `admin` |
| منفذ SSH | | `22` (الافتراضي) |
| نظام التشغيل | | `Ubuntu 22.04` / `RHEL 8` |
| هل يوجد Domain Name؟ | | `cdi.moh.gov.sa` |

### 2️⃣ مواصفات السيرفر

| المكون | المواصفات الحالية | المواصفات الموصى بها |
|--------|------------------|---------------------|
| CPU | | 8+ Cores |
| RAM | | 32+ GB |
| Storage | | 500+ GB SSD |
| GPU | | NVIDIA RTX 3090+ / A100 |
| GPU VRAM | | 24+ GB |

### 3️⃣ معلومات GPU (مهمة للتشغيل الأوفلاين)

| البند | القيمة |
|-------|--------|
| نوع GPU | (مثال: NVIDIA RTX 4090) |
| حجم VRAM | (مثال: 24GB) |
| هل CUDA مثبت؟ | نعم / لا |
| إصدار CUDA | (مثال: 12.1) |
| هل NVIDIA Driver مثبت؟ | نعم / لا |

### 4️⃣ معلومات الشبكة

| البند | القيمة |
|-------|--------|
| هل السيرفر داخل شبكة وزارة الصحة؟ | نعم / لا |
| هل يوجد وصول للإنترنت للتثبيت الأولي؟ | نعم / لا |
| هل يوجد Firewall؟ | نعم / لا |
| المنافذ المفتوحة | (مثال: 22, 80, 443) |

---

## 🛠️ متطلبات البرمجيات للسيرفر

### البرمجيات الأساسية:
```bash
# نظام التشغيل
Ubuntu 22.04 LTS أو RHEL 8+

# Python
Python 3.11+

# Node.js
Node.js 20.x LTS

# قاعدة البيانات
MongoDB 6.x أو 7.x

# Reverse Proxy
Nginx 1.24+

# للتشغيل الأوفلاين مع AI
NVIDIA Driver 535+
CUDA Toolkit 12.x
Ollama (لتشغيل النماذج المحلية)
```

### متطلبات GPU للنموذج المحلي:

| النموذج | الحجم | متطلبات VRAM | الأداء |
|---------|-------|--------------|--------|
| Phi-3 Mini | 3.8B | 8 GB | سريع جداً |
| Phi-3 Medium | 14B | 16 GB | متوسط |
| Llama 3 8B | 8B | 16 GB | جيد |
| Meditron 7B | 7B | 16 GB | متخصص طبي |

---

## 📦 الملفات المطلوب نقلها

```
medidoc-ai/
├── backend/
│   ├── server.py              # الخادم الرئيسي
│   ├── requirements.txt       # اعتماديات Python
│   ├── .env                   # متغيرات البيئة
│   └── clinical_questions.json
├── frontend/
│   ├── src/                   # كود React
│   ├── public/                # الملفات الثابتة
│   ├── package.json           # اعتماديات Node
│   └── .env
├── documentation/             # التوثيق
├── docker-compose.yml         # إعداد Docker
└── nginx.conf                 # إعداد Nginx
```

---

## 🔧 خطوات النقل

### المرحلة 1: تجهيز السيرفر

```bash
# 1. تحديث النظام
sudo apt update && sudo apt upgrade -y

# 2. تثبيت الأدوات الأساسية
sudo apt install -y git curl wget build-essential

# 3. تثبيت Python 3.11
sudo apt install -y python3.11 python3.11-venv python3-pip

# 4. تثبيت Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# 5. تثبيت MongoDB
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt update && sudo apt install -y mongodb-org
sudo systemctl enable mongod && sudo systemctl start mongod

# 6. تثبيت Nginx
sudo apt install -y nginx
```

### المرحلة 2: تثبيت GPU و Ollama (للأوفلاين)

```bash
# 1. تثبيت NVIDIA Driver
sudo apt install -y nvidia-driver-535

# 2. تثبيت CUDA
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt update && sudo apt install -y cuda-toolkit-12-4

# 3. تثبيت Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 4. تحميل النموذج المحلي
ollama pull phi3
# أو للنموذج الطبي المتخصص:
ollama pull meditron
```

### المرحلة 3: نقل الملفات

```bash
# من جهازك المحلي:
scp -r ./medidoc-ai user@SERVER_IP:/opt/

# أو باستخدام rsync:
rsync -avz --progress ./medidoc-ai/ user@SERVER_IP:/opt/medidoc-ai/
```

### المرحلة 4: إعداد التطبيق

```bash
# 1. الدخول للسيرفر
ssh user@SERVER_IP

# 2. إعداد Backend
cd /opt/medidoc-ai/backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. إعداد Frontend
cd /opt/medidoc-ai/frontend
npm install
npm run build

# 4. إعداد متغيرات البيئة
cp .env.example .env
nano .env  # تعديل القيم
```

### المرحلة 5: إعداد Nginx

```nginx
# /etc/nginx/sites-available/medidoc

server {
    listen 80;
    server_name your-domain.moh.gov.sa;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.moh.gov.sa;

    ssl_certificate /etc/ssl/certs/your-cert.crt;
    ssl_certificate_key /etc/ssl/private/your-key.key;

    # Frontend
    location / {
        root /opt/medidoc-ai/frontend/build;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
    }
}
```

### المرحلة 6: إعداد Systemd Services

```bash
# Backend Service
sudo nano /etc/systemd/system/medidoc-backend.service
```

```ini
[Unit]
Description=MediDoc AI Backend
After=network.target mongod.service

[Service]
User=www-data
WorkingDirectory=/opt/medidoc-ai/backend
Environment="PATH=/opt/medidoc-ai/backend/venv/bin"
ExecStart=/opt/medidoc-ai/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# تفعيل الخدمات
sudo systemctl daemon-reload
sudo systemctl enable medidoc-backend
sudo systemctl start medidoc-backend
```

---

## 🔐 إعدادات الأمان

### 1. Firewall
```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### 2. SSL Certificate
```bash
# باستخدام Let's Encrypt (إذا كان متاح إنترنت)
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.moh.gov.sa

# أو باستخدام شهادة وزارة الصحة
# ضع الشهادة في /etc/ssl/certs/
```

### 3. MongoDB Security
```bash
# تعديل /etc/mongod.conf
security:
  authorization: enabled
```

---

## ⚙️ إعداد التشغيل الأوفلاين

### تعديل الكود لاستخدام النموذج المحلي:

سأقوم بتعديل `server.py` ليستخدم Ollama بدلاً من Gemini عند عدم توفر الإنترنت.

```python
# في server.py - إضافة دعم النموذج المحلي
import requests

def get_ai_response_offline(prompt: str) -> str:
    """استخدام Ollama للتشغيل الأوفلاين"""
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "phi3",  # أو meditron
            "prompt": prompt,
            "stream": False
        },
        timeout=120
    )
    return response.json()["response"]
```

---

## 📊 متغيرات البيئة للأوفلاين

```env
# /opt/medidoc-ai/backend/.env

# قاعدة البيانات
MONGO_URL=mongodb://localhost:27017
DB_NAME=clinical_doc_center

# JWT
JWT_SECRET=your-super-secret-key-change-this

# AI - للأوفلاين
AI_PROVIDER=ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=phi3

# للأونلاين (اختياري)
GEMINI_API_KEY_1=...
GEMINI_API_KEY_2=...

# البريد (تعطيل للأوفلاين)
MFA_ENABLED=false
SMTP_HOST=
```

---

## ✅ قائمة التحقق قبل النقل

- [ ] السيرفر جاهز بالمواصفات المطلوبة
- [ ] GPU مثبت ويعمل (nvidia-smi يظهر الـ GPU)
- [ ] CUDA مثبت
- [ ] Ollama مثبت والنموذج محمل
- [ ] MongoDB يعمل
- [ ] Nginx مكون
- [ ] شهادة SSL جاهزة
- [ ] Firewall مكون
- [ ] النسخة الاحتياطية من قاعدة البيانات جاهزة

---

## 📞 الخطوة التالية

**أرسل لي المعلومات التالية:**

1. **عنوان IP للسيرفر** و **بيانات SSH**
2. **مواصفات السيرفر** (CPU, RAM, Storage)
3. **معلومات GPU** (النوع، VRAM)
4. **هل NVIDIA Driver و CUDA مثبتين؟**
5. **هل يوجد Domain Name؟**
6. **هل السيرفر داخل شبكة وزارة الصحة أم خارجها؟**

بعد استلام هذه المعلومات، سأقوم بـ:
1. تجهيز ملفات التثبيت الكاملة
2. إعداد Docker Compose للتشغيل السهل
3. تعديل الكود لدعم النموذج المحلي
4. إنشاء سكريبت التثبيت الآلي

---

**© 2025 إدارة تحسين التوثيق السريري - تجمع المدينة المنورة الصحي**
