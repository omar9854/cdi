# 📊 دليل إعداد نظام المراقبة Prometheus + Grafana
## للتطبيق CDI System

---

## 📋 نظرة عامة

هذا الدليل يشرح كيفية إعداد نظام مراقبة شامل باستخدام:
- **Prometheus**: لجمع المقاييس (Metrics Collection)
- **Grafana**: لعرض البيانات (Data Visualization)
- **FastAPI Metrics**: مقاييس من تطبيق FastAPI
- **MongoDB Exporter**: مقاييس من قاعدة البيانات

---

## ✅ المتطلبات الأساسية

```bash
# نظام التشغيل: Linux (Ubuntu/Debian recommended)
# Docker & Docker Compose (أسهل طريقة)
# أو تثبيت يدوي على الخادم
```

---

## 🎯 الطريقة 1: التثبيت باستخدام Docker Compose (موصى به)

### الخطوة 1.1: إنشاء ملف docker-compose.yml

```yaml
# /app/monitoring/docker-compose.yml
version: '3.8'

services:
  # Prometheus
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'
    ports:
      - '9090:9090'
    restart: unless-stopped
    networks:
      - monitoring

  # Grafana
  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana-dashboards:/etc/grafana/provisioning/dashboards
      - ./grafana-datasources:/etc/grafana/provisioning/datasources
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=CDI-Grafana-2024
      - GF_USERS_ALLOW_SIGN_UP=false
    ports:
      - '3001:3000'
    restart: unless-stopped
    depends_on:
      - prometheus
    networks:
      - monitoring

  # MongoDB Exporter
  mongodb-exporter:
    image: bitnami/mongodb-exporter:latest
    container_name: mongodb-exporter
    environment:
      - MONGODB_URI=mongodb://YOUR_MONGO_URI
    ports:
      - '9216:9216'
    restart: unless-stopped
    networks:
      - monitoring

  # Node Exporter (for system metrics)
  node-exporter:
    image: prom/node-exporter:latest
    container_name: node-exporter
    ports:
      - '9100:9100'
    restart: unless-stopped
    networks:
      - monitoring

volumes:
  prometheus-data:
  grafana-data:

networks:
  monitoring:
    driver: bridge
```

### الخطوة 1.2: إنشاء ملف prometheus.yml

```yaml
# /app/monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    monitor: 'cdi-system'

scrape_configs:
  # FastAPI Backend Metrics
  - job_name: 'fastapi-backend'
    static_configs:
      - targets: ['host.docker.internal:8001']
    metrics_path: '/metrics'

  # MongoDB Metrics
  - job_name: 'mongodb'
    static_configs:
      - targets: ['mongodb-exporter:9216']

  # System Metrics
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']

  # Prometheus Self-Monitoring
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
```

### الخطوة 1.3: تشغيل المراقبة

```bash
cd /app/monitoring

# تشغيل جميع الخدمات
docker-compose up -d

# التحقق من الحالة
docker-compose ps

# عرض السجلات
docker-compose logs -f
```

---

## 🎯 الطريقة 2: إضافة Metrics إلى FastAPI

### الخطوة 2.1: تثبيت المكتبات

```bash
cd /app/backend
pip install prometheus-client prometheus-fastapi-instrumentator
pip freeze | grep prometheus >> requirements.txt
```

### الخطوة 2.2: تعديل server.py

```python
# في بداية server.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi.responses import Response
import time

# بعد إنشاء app
app = FastAPI()

# إضافة Prometheus Instrumentation
instrumentor = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=[".*admin.*", "/metrics"],
    env_var_name="ENABLE_METRICS",
    inprogress_name="fastapi_inprogress",
    inprogress_labels=True,
)

# إضافة metrics مخصصة
REQUESTS_TOTAL = Counter(
    'cdi_requests_total',
    'Total requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'cdi_request_duration_seconds',
    'Request duration',
    ['method', 'endpoint']
)

ACTIVE_USERS = Gauge(
    'cdi_active_users',
    'Number of active users'
)

AI_REQUESTS = Counter(
    'cdi_ai_requests_total',
    'Total AI requests',
    ['type']  # analyze, chat, predefined_question
)

AI_RESPONSE_TIME = Histogram(
    'cdi_ai_response_time_seconds',
    'AI response time',
    ['type']
)

DB_OPERATIONS = Counter(
    'cdi_db_operations_total',
    'Total database operations',
    ['operation', 'collection']
)

# تفعيل Instrumentation
instrumentor.instrument(app).expose(app)

# Endpoint للـ Metrics
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(REGISTRY), media_type="text/plain")

# Middleware لتتبع الطلبات
@app.middleware("http")
async def track_requests(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    
    # تسجيل المقاييس
    REQUESTS_TOTAL.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response

# تتبع AI Requests
async def track_ai_request(request_type: str):
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        AI_REQUESTS.labels(type=request_type).inc()
        AI_RESPONSE_TIME.labels(type=request_type).observe(duration)

# استخدام في analyze endpoint
@api_router.post("/analyze")
async def analyze_note(...):
    async with track_ai_request("analyze"):
        # existing code
        pass

# تتبع Active Users
@app.on_event("startup")
async def update_active_users():
    import asyncio
    
    async def check_active_users():
        while True:
            try:
                # عد الجلسات النشطة (آخر 30 دقيقة)
                cutoff = datetime.now(timezone.utc) - timedelta(minutes=30)
                active_count = await db.user_sessions.count_documents({
                    "last_activity": {"$gte": cutoff.isoformat()},
                    "is_active": True
                })
                ACTIVE_USERS.set(active_count)
            except Exception as e:
                logging.error(f"Error updating active users: {e}")
            
            await asyncio.sleep(60)  # كل دقيقة
    
    asyncio.create_task(check_active_users())
```

---

## 📊 الخطوة 3: إعداد Grafana Dashboards

### 3.1 الوصول إلى Grafana

```
URL: http://YOUR_SERVER:3001
Username: admin
Password: CDI-Grafana-2024
```

### 3.2 إضافة Prometheus Data Source

```
1. Configuration → Data Sources
2. Add data source
3. اختر Prometheus
4. URL: http://prometheus:9090
5. Save & Test
```

### 3.3 استيراد Dashboards جاهزة

```
1. Dashboards → Import
2. Dashboard IDs الموصى بها:
   - 1860: Node Exporter Full
   - 2949: MongoDB Overview
   - 12124: FastAPI Metrics
3. اختر Prometheus data source
4. Import
```

### 3.4 إنشاء Dashboard مخصص لـ CDI

```json
{
  "dashboard": {
    "title": "CDI System Monitoring",
    "panels": [
      {
        "title": "Active Users",
        "targets": [{
          "expr": "cdi_active_users"
        }],
        "type": "stat"
      },
      {
        "title": "AI Requests per Minute",
        "targets": [{
          "expr": "rate(cdi_ai_requests_total[1m])"
        }],
        "type": "graph"
      },
      {
        "title": "AI Response Time (p95)",
        "targets": [{
          "expr": "histogram_quantile(0.95, cdi_ai_response_time_seconds_bucket)"
        }],
        "type": "graph"
      },
      {
        "title": "Request Rate by Endpoint",
        "targets": [{
          "expr": "rate(cdi_requests_total[5m])"
        }],
        "type": "graph"
      },
      {
        "title": "Database Operations",
        "targets": [{
          "expr": "rate(cdi_db_operations_total[1m])"
        }],
        "type": "graph"
      }
    ]
  }
}
```

---

## 🔔 الخطوة 4: إعداد التنبيهات (Alerts)

### 4.1 تنبيهات Prometheus (alertmanager)

```yaml
# /app/monitoring/alert.rules.yml
groups:
  - name: cdi_alerts
    interval: 30s
    rules:
      # تنبيه عند توقف الخدمة
      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.job }} is down"
          description: "{{ $labels.instance }} has been down for more than 1 minute"

      # تنبيه عند ارتفاع Response Time
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(cdi_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is above 2 seconds"

      # تنبيه عند ارتفاع معدل الأخطاء
      - alert: HighErrorRate
        expr: rate(cdi_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is above 5%"

      # تنبيه عند انخفاض مساحة التخزين
      - alert: LowDiskSpace
        expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Low disk space"
          description: "Disk space is below 10%"

      # تنبيه عند ارتفاع استخدام الذاكرة
      - alert: HighMemoryUsage
        expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is above 90%"
```

### 4.2 تكامل مع البريد الإلكتروني

```yaml
# /app/monitoring/alertmanager.yml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'medidocai@gmail.com'
  smtp_auth_username: 'medidocai@gmail.com'
  smtp_auth_password: 'YOUR_APP_PASSWORD'

route:
  receiver: 'email-notifications'
  group_by: ['alertname', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h

receivers:
  - name: 'email-notifications'
    email_configs:
      - to: 'admin@yourdomain.com'
        headers:
          Subject: '🚨 CDI System Alert: {{ .GroupLabels.alertname }}'
```

---

## 📈 المقاييس الهامة للمراقبة

### 1. مقاييس التطبيق (Application Metrics)

```
✅ Request Rate (requests/second)
✅ Response Time (p50, p95, p99)
✅ Error Rate (%)
✅ Active Users
✅ AI Request Count & Duration
✅ Database Operations Count
```

### 2. مقاييس النظام (System Metrics)

```
✅ CPU Usage (%)
✅ Memory Usage (MB, %)
✅ Disk Usage (GB, %)
✅ Network I/O (MB/s)
✅ Disk I/O (operations/s)
```

### 3. مقاييس قاعدة البيانات (Database Metrics)

```
✅ Connection Pool Usage
✅ Query Duration
✅ Operations per Second
✅ Document Count per Collection
✅ Index Hit Rate
```

---

## 🔒 الأمان

### تأمين Prometheus و Grafana

```nginx
# Nginx Reverse Proxy للحماية
server {
    listen 443 ssl;
    server_name monitoring.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:3001;
        proxy_set_header Host $host;
        auth_basic "Restricted Access";
        auth_basic_user_file /etc/nginx/.htpasswd;
    }
}
```

---

## ✅ قائمة التحقق

- [ ] Docker و Docker Compose مثبتة
- [ ] Prometheus يعمل ويجمع المقاييس
- [ ] Grafana يعمل ويعرض Dashboards
- [ ] MongoDB Exporter متصل
- [ ] FastAPI Metrics مُفعّلة
- [ ] Alerts مُعدّة
- [ ] إشعارات البريد الإلكتروني تعمل
- [ ] HTTPS مُفعّل
- [ ] Authentication مُفعّل
- [ ] Backup للـ Dashboards

---

**تاريخ الإنشاء:** 2024-11-07  
**الحالة:** جاهز للتطبيق ✅
