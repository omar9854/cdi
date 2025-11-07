# 🔐 دليل تشفير البيانات في MongoDB Atlas
## تفعيل Encryption at Rest

---

## 📋 نظرة عامة

MongoDB Atlas يدعم تشفير البيانات في حالة التخزين (Encryption at Rest) باستخدام مفاتيح خاصة بك. هذا الدليل يشرح كيفية إعداد التشفير.

---

## ✅ المتطلبات الأساسية

1. **حساب MongoDB Atlas**
   - مستوى الخدمة: M10 أو أعلى
   - (M0/M2/M5 Free Tier لا يدعم Encryption at Rest)

2. **مزود مفاتيح التشفير** (اختر واحد):
   - AWS Key Management Service (KMS)
   - Azure Key Vault
   - Google Cloud KMS

---

## 🎯 الخطوة 1: إنشاء Cluster في MongoDB Atlas

### 1.1 تسجيل الدخول
```
https://cloud.mongodb.com/
```

### 1.2 إنشاء Cluster جديد
```
1. اضغط "Build a Cluster"
2. اختر Cloud Provider (AWS/Azure/GCP)
3. اختر Region (مثلاً: me-south-1 للبحرين)
4. اختر Cluster Tier: M10+ (للحصول على Encryption at Rest)
```

### 1.3 إعدادات الأمان الأساسية
```
Database Access:
- Username: cdi_admin
- Password: [كلمة مرور قوية]
- Privileges: Atlas Admin

Network Access:
- IP Whitelist: 0.0.0.0/0 (للتطوير)
- أو IP محدد لخادمك (للإنتاج)
```

---

## 🔐 الخطوة 2: تفعيل Encryption at Rest

### الطريقة 1: استخدام AWS KMS (الأكثر شيوعاً)

#### 2.1 إنشاء KMS Key في AWS

```bash
# تسجيل الدخول إلى AWS Console
# اذهب إلى: Key Management Service (KMS)

# إنشاء مفتاح جديد
1. Create key
2. Key type: Symmetric
3. Key usage: Encrypt and decrypt
4. Alias: mongodb-atlas-encryption-key
5. Key administrators: [IAM User/Role]
6. Key users: [IAM User/Role for MongoDB Atlas]
```

#### 2.2 إنشاء IAM Policy للوصول

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "kms:Decrypt",
        "kms:Encrypt",
        "kms:DescribeKey"
      ],
      "Resource": "arn:aws:kms:REGION:ACCOUNT_ID:key/KEY_ID"
    }
  ]
}
```

#### 2.3 إنشاء IAM Role لـ MongoDB Atlas

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::AWS_ACCOUNT_ID:root"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "ATLAS_EXTERNAL_ID"
        }
      }
    }
  ]
}
```

#### 2.4 ربط KMS مع MongoDB Atlas

```
1. في MongoDB Atlas Dashboard
2. اذهب إلى: Security → Encryption at Rest
3. اختر: AWS KMS
4. أدخل:
   - AWS Access Key ID
   - AWS Secret Access Key
   - Customer Master Key ARN
   - AWS Region
5. Save
```

---

### الطريقة 2: استخدام Azure Key Vault

#### 2.1 إنشاء Key Vault

```bash
# Azure CLI
az keyvault create \
  --name mongodb-atlas-kv \
  --resource-group myResourceGroup \
  --location eastus
```

#### 2.2 إنشاء Key

```bash
az keyvault key create \
  --vault-name mongodb-atlas-kv \
  --name mongodb-encryption-key \
  --protection software
```

#### 2.3 إنشاء Service Principal

```bash
az ad sp create-for-rbac \
  --name mongodb-atlas-sp \
  --role Contributor \
  --scopes /subscriptions/SUBSCRIPTION_ID/resourceGroups/myResourceGroup
```

#### 2.4 ربط مع MongoDB Atlas

```
1. Security → Encryption at Rest
2. اختر: Azure Key Vault
3. أدخل:
   - Azure Subscription ID
   - Resource Group Name
   - Key Vault Name
   - Key Identifier
   - Azure Client ID
   - Azure Client Secret
   - Azure Tenant ID
4. Save
```

---

### الطريقة 3: استخدام Google Cloud KMS

#### 2.1 تفعيل Cloud KMS API

```bash
gcloud services enable cloudkms.googleapis.com
```

#### 2.2 إنشاء Key Ring و Key

```bash
# إنشاء Key Ring
gcloud kms keyrings create mongodb-atlas-keyring \
  --location global

# إنشاء Key
gcloud kms keys create mongodb-encryption-key \
  --location global \
  --keyring mongodb-atlas-keyring \
  --purpose encryption
```

#### 2.3 إنشاء Service Account

```bash
gcloud iam service-accounts create mongodb-atlas-sa \
  --display-name "MongoDB Atlas Service Account"
```

#### 2.4 منح الصلاحيات

```bash
gcloud kms keys add-iam-policy-binding mongodb-encryption-key \
  --location global \
  --keyring mongodb-atlas-keyring \
  --member serviceAccount:mongodb-atlas-sa@PROJECT_ID.iam.gserviceaccount.com \
  --role roles/cloudkms.cryptoKeyEncrypterDecrypter
```

#### 2.5 ربط مع MongoDB Atlas

```
1. Security → Encryption at Rest
2. اختر: Google Cloud KMS
3. أدخل:
   - Service Account Key (JSON)
   - Key Resource ID
4. Save
```

---

## 🔄 الخطوة 3: تفعيل التشفير على Cluster الموجود

إذا كان لديك cluster موجود بالفعل:

```
⚠️ تحذير: لا يمكن تفعيل Encryption at Rest على cluster موجود مباشرة.
يجب عمل Migration:

1. إنشاء cluster جديد مع Encryption enabled
2. استخدام mongodump/mongorestore
3. نقل البيانات
4. تحديث connection string في التطبيق
```

### خطوات Migration:

```bash
# 1. Backup من Cluster القديم
mongodump --uri="mongodb+srv://OLD_CLUSTER_URI" --out=/backup

# 2. Restore إلى Cluster الجديد (المشفر)
mongorestore --uri="mongodb+srv://NEW_ENCRYPTED_CLUSTER_URI" /backup

# 3. تحديث .env
MONGO_URL=mongodb+srv://NEW_ENCRYPTED_CLUSTER_URI
```

---

## ✅ الخطوة 4: التحقق من التشفير

### 4.1 التحقق من Atlas Dashboard

```
1. اذهب إلى Cluster
2. Security → Encryption at Rest
3. تأكد من: Status = Enabled
4. تحقق من: Key Provider = AWS KMS/Azure/GCP
```

### 4.2 التحقق من Logs

```
1. Activity Feed
2. ابحث عن: "Encryption at Rest enabled"
```

---

## 🔐 الخطوة 5: تشفير إضافي (Client-Side Field Level Encryption)

لتشفير حقول محددة على مستوى التطبيق:

### 5.1 تثبيت المكتبات

```bash
pip install pymongo[encryption]
```

### 5.2 كود Python للتشفير

```python
from pymongo import MongoClient
from pymongo.encryption import ClientEncryption
from pymongo.encryption_options import AutoEncryptionOpts
import os

# KMS Configuration
kms_providers = {
    "aws": {
        "accessKeyId": os.environ.get('AWS_ACCESS_KEY_ID'),
        "secretAccessKey": os.environ.get('AWS_SECRET_ACCESS_KEY')
    }
}

# Key Vault Configuration
key_vault_namespace = "encryption.__keyVault"
key_vault_client = MongoClient(os.environ.get('MONGO_URL'))

# Client Encryption
client_encryption = ClientEncryption(
    kms_providers,
    key_vault_namespace,
    key_vault_client,
    codec_options=None
)

# Create Data Encryption Key
data_key_id = client_encryption.create_data_key(
    "aws",
    master_key={
        "region": "us-east-1",
        "key": "arn:aws:kms:us-east-1:ACCOUNT:key/KEY_ID"
    }
)

# Schema Map for Auto-Encryption
schema_map = {
    "cdi_database.users": {
        "bsonType": "object",
        "properties": {
            "password_hash": {
                "encrypt": {
                    "bsonType": "string",
                    "algorithm": "AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic",
                    "keyId": [data_key_id]
                }
            },
            "phone_number": {
                "encrypt": {
                    "bsonType": "string",
                    "algorithm": "AEAD_AES_256_CBC_HMAC_SHA_512-Random",
                    "keyId": [data_key_id]
                }
            }
        }
    }
}

# Auto-Encryption Options
auto_encryption_opts = AutoEncryptionOpts(
    kms_providers,
    key_vault_namespace,
    schema_map=schema_map
)

# Connect with Encryption
client = MongoClient(
    os.environ.get('MONGO_URL'),
    auto_encryption_opts=auto_encryption_opts
)
```

---

## 📊 الخطوة 6: مراقبة التشفير

### 6.1 تنبيهات Atlas

```
1. Alerts → Add Alert
2. Alert Type: "Encryption at Rest"
3. Condition: "is disabled"
4. Notification: Email
```

### 6.2 Audit Logs

```
1. Security → Database Auditing
2. Enable Auditing
3. Filter: "encryptionKeyRotation"
```

---

## 🔄 الخطوة 7: دوران المفاتيح (Key Rotation)

### يدوياً (Manual):

```
1. إنشاء مفتاح جديد في KMS
2. تحديث Atlas Configuration
3. Atlas سيُعيد تشفير البيانات تلقائياً
```

### تلقائياً (Automatic - AWS KMS):

```bash
# في AWS KMS
aws kms enable-key-rotation --key-id KEY_ID

# التحقق
aws kms get-key-rotation-status --key-id KEY_ID
```

---

## 🔒 أفضل الممارسات

### 1. الأمان:
```
✅ استخدم IAM Roles بدلاً من Access Keys
✅ فعّل MFA على حسابات AWS/Azure/GCP
✅ قيّد الصلاحيات إلى الحد الأدنى (Principle of Least Privilege)
✅ راجع الصلاحيات كل 3 أشهر
✅ استخدم Secrets Manager لتخزين المفاتيح
```

### 2. النسخ الاحتياطي:
```
✅ فعّل Atlas Continuous Backup
✅ اختبر استعادة البيانات شهرياً
✅ احفظ نسخة من مفاتيح التشفير في مكان آمن منفصل
✅ وثّق جميع المفاتيح والصلاحيات
```

### 3. المراقبة:
```
✅ فعّل Database Auditing في Atlas
✅ راقب KMS API calls
✅ تنبيهات لأي تغيير في إعدادات التشفير
✅ مراجعة دورية لسجلات الوصول
```

### 4. الامتثال:
```
✅ وثّق جميع إعدادات التشفير
✅ احفظ نسخة من Encryption Policies
✅ مراجعة سنوية من جهة خارجية
✅ تأكد من الامتثال لـ HIPAA/GDPR/PDPL
```

---

## 💰 التكلفة

### MongoDB Atlas:
```
M10 Cluster (الحد الأدنى للتشفير):
- حوالي $60-80/شهر
- يشمل: 10GB storage, 2GB RAM
```

### AWS KMS:
```
- $1/شهر لكل Customer Master Key
- $0.03 لكل 10,000 طلب تشفير/فك تشفير
```

### Azure Key Vault:
```
- $0.03 لكل 10,000 عملية
- Standard tier: مُضمن مع Azure
```

### Google Cloud KMS:
```
- $0.06/شهر لكل key version
- $0.03 لكل 10,000 عملية تشفير
```

---

## 🔗 الموارد الإضافية

**MongoDB Atlas:**
- https://docs.atlas.mongodb.com/security-kms-encryption/

**AWS KMS:**
- https://docs.aws.amazon.com/kms/

**Azure Key Vault:**
- https://docs.microsoft.com/azure/key-vault/

**Google Cloud KMS:**
- https://cloud.google.com/kms/docs

---

## ✅ قائمة التحقق النهائية

قبل النشر:

- [ ] MongoDB Atlas Cluster نوع M10+
- [ ] Encryption at Rest مُفعّل
- [ ] KMS Key مُنشأ ومُختبر
- [ ] IAM Roles/Service Accounts مُعدّة
- [ ] Connection String محدّث في .env
- [ ] النسخ الاحتياطي يعمل بشكل صحيح
- [ ] Audit Logging مُفعّل
- [ ] Alerts مُعدّة
- [ ] وثّقت جميع المفاتيح والصلاحيات
- [ ] اختبرت استعادة البيانات

---

**تم إنشاء هذا الدليل:** 2024-11-07  
**الحالة:** جاهز للتطبيق ✅

