# 🚀 دليل تثبيت Coolify مع دعم GPU على Ubuntu 24.04

## 📋 المتطلبات
- Ubuntu 24.04 LTS
- RAM: 4GB+ (موصى 8GB+)
- مساحة: 50GB+
- NVIDIA GPU مع Drivers
- وصول Root

---

## 🔧 الجزء الأول: تجهيز السيرفر

### 1.1 الاتصال بالسيرفر
```bash
ssh root@8.213.39.104
```

### 1.2 تحديث النظام
```bash
apt update && apt upgrade -y
```

### 1.3 تثبيت المتطلبات الأساسية
```bash
apt install -y curl wget git apt-transport-https ca-certificates software-properties-common
```

---

## 🎮 الجزء الثاني: تثبيت NVIDIA Drivers و CUDA

### 2.1 التحقق من GPU
```bash
lspci | grep -i nvidia
```

### 2.2 تثبيت NVIDIA Drivers
```bash
# إضافة مستودع NVIDIA
apt install -y nvidia-driver-535

# إعادة التشغيل
reboot
```

### 2.3 التحقق من التثبيت (بعد إعادة التشغيل)
```bash
nvidia-smi
```

### 2.4 تثبيت NVIDIA Container Toolkit
```bash
# إضافة مستودع NVIDIA Container Toolkit
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

apt update
apt install -y nvidia-container-toolkit

# تكوين Docker لاستخدام NVIDIA runtime
nvidia-ctk runtime configure --runtime=docker
systemctl restart docker
```

### 2.5 اختبار GPU مع Docker
```bash
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

---

## 🐳 الجزء الثالث: تثبيت Coolify

### 3.1 تثبيت Coolify
```bash
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash
```

### 3.2 انتظر اكتمال التثبيت (5-10 دقائق)
ستظهر رسالة بالرابط عند الانتهاء.

### 3.3 الوصول لـ Coolify
افتح في المتصفح:
```
http://8.213.39.104:8000
```

### 3.4 إنشاء حساب Admin
- أدخل البريد الإلكتروني
- أدخل كلمة مرور قوية
- اضغط "Register"

---

## 🔗 الجزء الرابع: ربط GitHub

### 4.1 في Coolify Dashboard:
1. اذهب إلى **Settings** → **Sources**
2. اضغط **+ Add**
3. اختر **GitHub App**

### 4.2 إنشاء GitHub App:
1. اضغط **Create GitHub App**
2. سيفتح GitHub في نافذة جديدة
3. اختر اسم للتطبيق (مثال: `coolify-nabeeh`)
4. اضغط **Create GitHub App**
5. اضغط **Install** على حسابك/مؤسستك
6. اختر المستودعات (أو All repositories)

### 4.3 التحقق من الربط:
- عد لـ Coolify
- يجب أن ترى GitHub متصل بنجاح ✅

---

## 📦 الجزء الخامس: إنشاء مشروع نبيه

### 5.1 إنشاء Project جديد
1. في Coolify Dashboard → **Projects**
2. اضغط **+ Add**
3. اسم المشروع: `Nabeeh`
4. اضغط **Save**

### 5.2 إضافة Environment
1. داخل المشروع → **+ New Environment**
2. اسم: `production`

### 5.3 إضافة Resource (التطبيق)
1. داخل Environment → **+ New Resource**
2. اختر **Public Repository** أو **Private Repository** (GitHub)
3. أدخل رابط المستودع:
   ```
   https://github.com/omar9854/clinical-doc-ai-tool.git
   ```

---

## ⚙️ الجزء السادس: إعداد Docker Compose مع GPU

### 6.1 إنشاء ملف docker-compose.yml في مستودعك:

```yaml
version: '3.8'

services:
  # ===================
  # MongoDB Database
  # ===================
  mongodb:
    image: mongo:7.0
    container_name: nabeeh-mongodb
    restart: always
    volumes:
      - mongodb_data:/data/db
    networks:
      - nabeeh-network
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongosh localhost:27017/test --quiet
      interval: 10s
      timeout: 5s
      retries: 5

  # ===================
  # vLLM AI Engine (GPU)
  # ===================
  vllm:
    image: vllm/vllm-openai:latest
    container_name: nabeeh-vllm
    restart: always
    runtime: nvidia
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
    command: >
      --model Qwen/Qwen2.5-32B-Instruct
      --tensor-parallel-size 4
      --gpu-memory-utilization 0.90
      --max-model-len 8192
      --port 8000
      --host 0.0.0.0
    volumes:
      - huggingface_cache:/root/.cache/huggingface
    networks:
      - nabeeh-network
    healthcheck:
      test: curl -f http://localhost:8000/health || exit 1
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 300s

  # ===================
  # Backend (FastAPI)
  # ===================
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: nabeeh-backend
    restart: always
    environment:
      - MONGO_URL=mongodb://mongodb:27017
      - DB_NAME=clinical_doc_center
      - VLLM_API_URL=http://vllm:8000/v1
      - JWT_SECRET=${JWT_SECRET:-your-secret-key-change-in-production}
      - CORS_ORIGINS=*
    depends_on:
      mongodb:
        condition: service_healthy
      vllm:
        condition: service_healthy
    networks:
      - nabeeh-network
    healthcheck:
      test: curl -f http://localhost:8001/api/health || exit 1
      interval: 10s
      timeout: 5s
      retries: 5

  # ===================
  # Frontend (React)
  # ===================
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: nabeeh-frontend
    restart: always
    environment:
      - REACT_APP_BACKEND_URL=
    depends_on:
      - backend
    networks:
      - nabeeh-network

  # ===================
  # Nginx Reverse Proxy
  # ===================
  nginx:
    image: nginx:alpine
    container_name: nabeeh-nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - frontend
      - backend
    networks:
      - nabeeh-network

networks:
  nabeeh-network:
    driver: bridge

volumes:
  mongodb_data:
  huggingface_cache:
```

### 6.2 إنشاء Dockerfile للـ Backend:
ملف: `backend/Dockerfile`

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# تثبيت المتطلبات
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ الكود
COPY . .

# تشغيل الخادم
EXPOSE 8001
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "4"]
```

### 6.3 إنشاء Dockerfile للـ Frontend:
ملف: `frontend/Dockerfile`

```dockerfile
# مرحلة البناء
FROM node:20-alpine AS builder

WORKDIR /app
COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile

COPY . .
RUN yarn build

# مرحلة التشغيل
FROM node:20-alpine

WORKDIR /app
RUN npm install -g serve

COPY --from=builder /app/build ./build

EXPOSE 3000
CMD ["serve", "-s", "build", "-l", "3000"]
```

### 6.4 إنشاء nginx.conf:
```nginx
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    upstream frontend {
        server frontend:3000;
    }

    upstream backend {
        server backend:8001;
    }

    server {
        listen 80;
        server_name _;

        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_cache_bypass $http_upgrade;
        }

        # Backend API
        location /api {
            proxy_pass http://backend/api;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_read_timeout 300s;
            proxy_connect_timeout 75s;
            client_max_body_size 50M;
        }
    }
}
```

---

## 🔄 الجزء السابع: إعداد النشر التلقائي

### 7.1 في Coolify - إعدادات المشروع:

1. اذهب لـ Resource (التطبيق)
2. اضغط **Settings**
3. فعّل:
   - ✅ **Auto Deploy** - نشر تلقائي عند Push
   - ✅ **Preview Deployments** - معاينة للـ Pull Requests

### 7.2 إعداد Webhook (تلقائي):
Coolify يُنشئ Webhook تلقائياً عند ربط GitHub App.

### 7.3 إعداد Environment Variables:
في Coolify → Resource → **Environment Variables**:

```
JWT_SECRET=your-super-secret-key-change-this
ADMIN_EMAIL=admin@nabeeh.local
ADMIN_PASSWORD=StrongPassword123!
```

---

## 🎯 الجزء الثامن: النشر الأول

### 8.1 اضغط **Deploy** في Coolify

### 8.2 راقب السجلات:
- اضغط **Logs** لمشاهدة التقدم
- انتظر تحميل نموذج Qwen (قد يستغرق 30-60 دقيقة أول مرة)

### 8.3 التحقق:
```bash
# على السيرفر
docker ps
docker logs nabeeh-vllm
docker logs nabeeh-backend
```

---

## ✅ الجزء التاسع: التحقق النهائي

### 9.1 اختبار الموقع:
```
http://8.213.39.104
```

### 9.2 اختبار API:
```bash
curl http://8.213.39.104/api/health
```

### 9.3 اختبار GPU:
```bash
docker exec nabeeh-vllm nvidia-smi
```

---

## 🔧 حل المشاكل الشائعة

### مشكلة: GPU غير مكتشف في Docker
```bash
# تأكد من تثبيت nvidia-container-toolkit
nvidia-ctk runtime configure --runtime=docker
systemctl restart docker
```

### مشكلة: نفاد ذاكرة GPU
```bash
# قلل استخدام الذاكرة في docker-compose.yml
--gpu-memory-utilization 0.80
```

### مشكلة: Coolify لا يتصل بـ GitHub
- تأكد من تثبيت GitHub App على المستودع
- أعد إنشاء GitHub App من Coolify

### مشكلة: النشر التلقائي لا يعمل
- تحقق من Webhook في GitHub Settings
- تأكد من أن الـ Branch صحيح (main/master)

---

## 📊 الأوامر المفيدة

```bash
# حالة الحاويات
docker ps

# سجلات حاوية معينة
docker logs -f nabeeh-backend

# إعادة تشغيل الكل
docker compose restart

# مسح وإعادة بناء
docker compose down
docker compose up -d --build

# مراقبة GPU
watch -n 1 nvidia-smi
```

---

## 🎉 تم!

الآن عند كل `git push` لمستودع GitHub:
1. ✅ Coolify يستلم Webhook
2. ✅ يسحب الكود الجديد
3. ✅ يبني الحاويات
4. ✅ ينشر التحديث تلقائياً

---

آخر تحديث: يناير 2025
