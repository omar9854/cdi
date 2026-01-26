# 🏥 دليل تثبيت نظام نبيه على خادم GPU

## 📋 المتطلبات

| المتطلب | الحد الأدنى | الموصى به |
|---------|-------------|-----------|
| نظام التشغيل | Ubuntu 20.04 | Ubuntu 22.04 |
| GPU | V100 16GB | 4x V100 32GB |
| RAM | 32GB | 64GB+ |
| التخزين | 100GB SSD | 200GB NVMe |
| الإنترنت | للتحميل الأولي | - |

---

## 🚀 خطوات التثبيت

### الخطوة 1: تحميل الكود

من منصة **Emergent**:
1. اضغط على **"Download Code"** 
2. حمّل ملف الكود المضغوط

أو استخدم الأمر:
```bash
# من جهازك المحلي
scp nabeeh-code.zip root@YOUR_SERVER_IP:/tmp/
```

### الخطوة 2: الاتصال بالخادم

```bash
ssh root@YOUR_SERVER_IP
```

### الخطوة 3: فك الضغط

```bash
cd /tmp
unzip nabeeh-code.zip
# أو إذا كان tar.gz
tar -xzf nabeeh-code.tar.gz
```

### الخطوة 4: تشغيل سكربت التثبيت

```bash
chmod +x INSTALL_GPU_SERVER.sh
sudo ./INSTALL_GPU_SERVER.sh
```

### الخطوة 5: نسخ الكود

بعد تشغيل السكربت، انسخ الكود:

```bash
# نسخ Backend
cp -r /tmp/backend/* /opt/nabeeh/backend/

# نسخ Frontend  
cp -r /tmp/frontend/* /opt/nabeeh/frontend/
```

### الخطوة 6: تعديل الإعدادات

```bash
nano /opt/nabeeh/backend/.env
```

**غيّر هذه القيم:**
```env
JWT_SECRET="كلمة_سرية_طويلة_وعشوائية"
ADMIN_EMAIL="بريدك@example.com"
ADMIN_PASSWORD="كلمة_مرور_قوية"
```

### الخطوة 7: بناء الواجهة وتشغيل الخدمات

```bash
cd /opt/nabeeh/frontend
yarn install
yarn build

# تشغيل الخدمات
systemctl start nabeeh-vllm
systemctl start nabeeh-backend
systemctl start nabeeh-frontend
```

---

## ✅ التحقق من التثبيت

```bash
# حالة الخدمات
systemctl status nabeeh-vllm
systemctl status nabeeh-backend
systemctl status nabeeh-frontend

# اختبار API
curl http://localhost:8001/api/health

# اختبار الموقع
curl http://localhost:3000
```

---

## 🔧 الأوامر المفيدة

### إدارة الخدمات

```bash
# إعادة تشغيل الكل
systemctl restart nabeeh-vllm nabeeh-backend nabeeh-frontend

# إيقاف الكل
systemctl stop nabeeh-vllm nabeeh-backend nabeeh-frontend

# تشغيل الكل
systemctl start nabeeh-vllm nabeeh-backend nabeeh-frontend
```

### مشاهدة السجلات

```bash
# سجلات vLLM (نموذج الذكاء الاصطناعي)
journalctl -u nabeeh-vllm -f

# سجلات Backend
journalctl -u nabeeh-backend -f

# سجلات Nginx
tail -f /var/log/nginx/error.log
```

### مراقبة GPU

```bash
# حالة GPU
nvidia-smi

# مراقبة مستمرة
watch -n 1 nvidia-smi

# أو استخدم nvtop
nvtop
```

---

## 🔄 التحديث

لتحديث الكود دون إعادة التثبيت الكامل:

```bash
./QUICK_UPDATE.sh
```

---

## 🛠️ حل المشاكل

### vLLM لا يبدأ

```bash
# تحقق من السجلات
journalctl -u nabeeh-vllm -n 100

# تحقق من ذاكرة GPU
nvidia-smi

# إذا الذاكرة ممتلئة، أعد التشغيل
sudo reboot
```

### Backend لا يبدأ

```bash
# تحقق من السجلات
journalctl -u nabeeh-backend -n 100

# تحقق من MongoDB
systemctl status mongod

# تحقق من ملف .env
cat /opt/nabeeh/backend/.env
```

### خطأ في الاتصال

```bash
# تحقق من Nginx
nginx -t
systemctl status nginx

# تحقق من المنافذ
netstat -tlnp | grep -E '80|3000|8001|8000'
```

---

## 📊 معلومات النظام

| الخدمة | المنفذ | الوصف |
|--------|--------|-------|
| Nginx | 80 | Reverse Proxy |
| Frontend | 3000 | واجهة المستخدم |
| Backend | 8001 | API Server |
| vLLM | 8000 | نموذج AI |
| MongoDB | 27017 | قاعدة البيانات |

---

## 📞 للدعم

إذا واجهت أي مشاكل:
1. راجع السجلات أولاً
2. تأكد من أن جميع الخدمات تعمل
3. تحقق من إعدادات .env

---

آخر تحديث: يناير 2025
