"""
Migration script for Medical Coding System
1. Update existing users to CDI department
2. Create sample coding users (supervisor, coder, auditor)
3. Create sample hospitals, ICD codes, DRG prices, and cases
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import bcrypt
import uuid
from datetime import datetime, timezone, timedelta
import os

async def main():
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'nabih_db')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("🚀 Starting Medical Coding System Migration...\n")
    
    # ========== Step 1: Update existing users to CDI department ==========
    print("📝 Step 1: Updating existing users to CDI department...")
    result = await db.users.update_many(
        {"department": {"$exists": False}},
        {
            "$set": {
                "department": "cdi",
                "coding_role": None,
                "daily_case_target": None
            }
        }
    )
    print(f"✅ Updated {result.modified_count} existing users to CDI department\n")
    
    # ========== Step 2: Create Coding Department Test Users ==========
    print("👥 Step 2: Creating coding department test users...")
    
    # Check if users already exist
    existing_supervisor = await db.users.find_one({"email": "supervisor@hospital.sa"}, {"_id": 0})
    existing_coder = await db.users.find_one({"email": "coder@hospital.sa"}, {"_id": 0})
    existing_auditor = await db.users.find_one({"email": "auditor@hospital.sa"}, {"_id": 0})
    
    test_users = []
    
    if not existing_supervisor:
        supervisor = {
            'id': str(uuid.uuid4()),
            'email': 'supervisor@hospital.sa',
            'password_hash': bcrypt.hashpw('Super123!'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            'full_name': 'مشرف الترميز الطبي - Coding Supervisor',
            'phone_number': '+966501111111',
            'role': 'supervisor',
            'department': 'coding',
            'coding_role': None,
            'daily_case_target': None,
            'mfa_enabled': False,
            'is_active': True,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'password_last_changed': datetime.now(timezone.utc).isoformat(),
            'password_expires_at': (datetime.now(timezone.utc) + timedelta(days=90)).isoformat(),
            'account_locked': False,
            'failed_login_attempts': 0
        }
        test_users.append(supervisor)
    
    if not existing_coder:
        coder = {
            'id': str(uuid.uuid4()),
            'email': 'coder@hospital.sa',
            'password_hash': bcrypt.hashpw('Coder123!'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            'full_name': 'مرمز طبي - Medical Coder',
            'phone_number': '+966502222222',
            'role': 'user',
            'department': 'coding',
            'coding_role': 'coder',
            'daily_case_target': 15,
            'mfa_enabled': False,
            'is_active': True,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'password_last_changed': datetime.now(timezone.utc).isoformat(),
            'password_expires_at': (datetime.now(timezone.utc) + timedelta(days=90)).isoformat(),
            'account_locked': False,
            'failed_login_attempts': 0
        }
        test_users.append(coder)
    
    if not existing_auditor:
        auditor = {
            'id': str(uuid.uuid4()),
            'email': 'auditor@hospital.sa',
            'password_hash': bcrypt.hashpw('Auditor123!'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            'full_name': 'مدقق ترميز طبي - Medical Auditor',
            'phone_number': '+966503333333',
            'role': 'user',
            'department': 'coding',
            'coding_role': 'auditor',
            'daily_case_target': None,
            'mfa_enabled': False,
            'is_active': True,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'password_last_changed': datetime.now(timezone.utc).isoformat(),
            'password_expires_at': (datetime.now(timezone.utc) + timedelta(days=90)).isoformat(),
            'account_locked': False,
            'failed_login_attempts': 0
        }
        test_users.append(auditor)
    
    if test_users:
        await db.users.insert_many(test_users)
        print(f"✅ Created {len(test_users)} coding department users:")
        for user in test_users:
            print(f"   - {user['email']} ({user['coding_role'] or 'supervisor'})")
    else:
        print("⏭️  All coding users already exist")
    
    print()
    
    # ========== Step 3: Create Sample Hospitals ==========
    print("🏥 Step 3: Creating sample hospitals...")
    
    hospitals = [
        {
            'id': str(uuid.uuid4()),
            'name': 'مستشفى الملك فيصل التخصصي',
            'code': 'KFSH',
            'location': 'الرياض',
            'is_active': True,
            'created_at': datetime.now(timezone.utc).isoformat()
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'مستشفى الملك فهد',
            'code': 'KFH',
            'location': 'جدة',
            'is_active': True,
            'created_at': datetime.now(timezone.utc).isoformat()
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'مستشفى الملك عبدالعزيز',
            'code': 'KAAH',
            'location': 'الدمام',
            'is_active': True,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
    ]
    
    # Check existing
    existing_hospitals = await db.hospitals.count_documents({})
    if existing_hospitals == 0:
        await db.hospitals.insert_many(hospitals)
        print(f"✅ Created {len(hospitals)} hospitals")
    else:
        print(f"⏭️  {existing_hospitals} hospitals already exist")
    
    print()
    
    # ========== Step 4: Create ICD-10-AM Codes ==========
    print("📋 Step 4: Creating ICD-10-AM sample codes...")
    
    icd_codes = [
        {
            'id': str(uuid.uuid4()),
            'code': 'E11.9',
            'description_ar': 'داء السكري من النوع 2 بدون مضاعفات',
            'description_en': 'Type 2 diabetes mellitus without complications',
            'category': 'Endocrine',
            'is_principal': True,
            'created_at': datetime.now(timezone.utc).isoformat()
        },
        {
            'id': str(uuid.uuid4()),
            'code': 'I10',
            'description_ar': 'ارتفاع ضغط الدم الأساسي',
            'description_en': 'Essential (primary) hypertension',
            'category': 'Cardiovascular',
            'is_principal': True,
            'created_at': datetime.now(timezone.utc).isoformat()
        },
        {
            'id': str(uuid.uuid4()),
            'code': 'J18.9',
            'description_ar': 'التهاب رئوي غير محدد',
            'description_en': 'Pneumonia, unspecified organism',
            'category': 'Respiratory',
            'is_principal': True,
            'created_at': datetime.now(timezone.utc).isoformat()
        },
        {
            'id': str(uuid.uuid4()),
            'code': 'N18.5',
            'description_ar': 'مرض الكلى المزمن المرحلة 5',
            'description_en': 'Chronic kidney disease, stage 5',
            'category': 'Renal',
            'is_principal': True,
            'created_at': datetime.now(timezone.utc).isoformat()
        },
        {
            'id': str(uuid.uuid4()),
            'code': 'K29.7',
            'description_ar': 'التهاب المعدة غير محدد',
            'description_en': 'Gastritis, unspecified',
            'category': 'Digestive',
            'is_principal': False,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
    ]
    
    existing_codes = await db.icd_codes.count_documents({})
    if existing_codes == 0:
        await db.icd_codes.insert_many(icd_codes)
        print(f"✅ Created {len(icd_codes)} ICD-10-AM codes")
    else:
        print(f"⏭️  {existing_codes} ICD codes already exist")
    
    print()
    
    # ========== Step 5: Create DRG Prices ==========
    print("💰 Step 5: Creating DRG price samples...")
    
    drg_prices = [
        {
            'id': str(uuid.uuid4()),
            'drg_code': 'DRG-641',
            'description_ar': 'سكري مع مضاعفات رئيسية',
            'description_en': 'Diabetes with major complications',
            'weight': 1.2345,
            'base_price': 25000.00,
            'year': 2025,
            'created_at': datetime.now(timezone.utc).isoformat()
        },
        {
            'id': str(uuid.uuid4()),
            'drg_code': 'DRG-195',
            'description_ar': 'التهاب رئوي بسيط',
            'description_en': 'Simple pneumonia',
            'weight': 0.8765,
            'base_price': 18000.00,
            'year': 2025,
            'created_at': datetime.now(timezone.utc).isoformat()
        },
        {
            'id': str(uuid.uuid4()),
            'drg_code': 'DRG-682',
            'description_ar': 'أمراض الكلى المزمنة',
            'description_en': 'Chronic kidney disease',
            'weight': 1.5678,
            'base_price': 32000.00,
            'year': 2025,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
    ]
    
    existing_drgs = await db.drg_prices.count_documents({})
    if existing_drgs == 0:
        await db.drg_prices.insert_many(drg_prices)
        print(f"✅ Created {len(drg_prices)} DRG prices")
    else:
        print(f"⏭️  {existing_drgs} DRG prices already exist")
    
    print()
    
    # ========== Step 6: Create Sample Medical Cases ==========
    print("📁 Step 6: Creating sample medical cases...")
    
    # Get first hospital
    hospital = await db.hospitals.find_one({}, {"_id": 0})
    if not hospital:
        print("❌ No hospital found, skipping case creation")
    else:
        coder_user = await db.users.find_one({"coding_role": "coder"}, {"_id": 0})
        supervisor_user = await db.users.find_one({"department": "coding", "role": "supervisor"}, {"_id": 0})
        
        cases = [
            {
                'id': str(uuid.uuid4()),
                'case_number': 'CASE-2025-001',
                'patient_id': 'PT-' + str(uuid.uuid4())[:8].upper(),
                'hospital_id': hospital['id'],
                'admission_date': '2025-01-15',
                'discharge_date': '2025-01-20',
                'age': 65,
                'gender': 'ذكر',
                'chief_complaint': 'ضيق في التنفس وارتفاع في درجة الحرارة',
                'clinical_summary': 'مريض يبلغ من العمر 65 عاماً يعاني من داء السكري من النوع 2 وارتفاع ضغط الدم. تم إدخاله بسبب ضيق تنفس وحمى. الفحوصات أظهرت التهاب رئوي بكتيري. تم العلاج بالمضادات الحيوية لمدة 5 أيام مع تحسن ملحوظ.',
                'procedures': ['أشعة سينية على الصدر', 'فحص دم شامل', 'زراعة البلغم'],
                'assigned_to': coder_user['id'] if coder_user else None,
                'assigned_at': datetime.now(timezone.utc).isoformat() if coder_user else None,
                'status': 'pending',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'created_by': supervisor_user['id'] if supervisor_user else 'system'
            },
            {
                'id': str(uuid.uuid4()),
                'case_number': 'CASE-2025-002',
                'patient_id': 'PT-' + str(uuid.uuid4())[:8].upper(),
                'hospital_id': hospital['id'],
                'admission_date': '2025-01-16',
                'discharge_date': '2025-01-25',
                'age': 58,
                'gender': 'أنثى',
                'chief_complaint': 'آلام في البطن وغثيان',
                'clinical_summary': 'مريضة 58 سنة تعاني من التهاب المعدة المزمن. تم إدخالها بسبب آلام حادة في البطن مع غثيان وقيء. الفحوصات والمنظار أظهر التهاب معدة شديد. تم العلاج الدوائي مع استجابة جيدة.',
                'procedures': ['منظار معدة', 'فحص دم', 'أشعة تلفزيونية على البطن'],
                'assigned_to': None,
                'assigned_at': None,
                'status': 'pending',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'created_by': supervisor_user['id'] if supervisor_user else 'system'
            },
            {
                'id': str(uuid.uuid4()),
                'case_number': 'CASE-2025-003',
                'patient_id': 'PT-' + str(uuid.uuid4())[:8].upper(),
                'hospital_id': hospital['id'],
                'admission_date': '2025-01-10',
                'discharge_date': '2025-01-22',
                'age': 72,
                'gender': 'ذكر',
                'chief_complaint': 'فشل كلوي مزمن - جلسة غسيل كلى',
                'clinical_summary': 'مريض 72 سنة يعاني من الفشل الكلوي المزمن المرحلة الخامسة. يخضع لغسيل كلى منتظم ثلاث مرات أسبوعياً. تم إدخاله لتعديل جلسات الغسيل ومتابعة الحالة العامة. الحالة مستقرة.',
                'procedures': ['غسيل كلى (3 جلسات)', 'فحص كيمياء الدم', 'أشعة تلفزيونية على الكلى'],
                'assigned_to': None,
                'assigned_at': None,
                'status': 'pending',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'created_by': supervisor_user['id'] if supervisor_user else 'system'
            }
        ]
        
        existing_cases = await db.medical_cases.count_documents({})
        if existing_cases == 0:
            await db.medical_cases.insert_many(cases)
            print(f"✅ Created {len(cases)} sample medical cases")
        else:
            print(f"⏭️  {existing_cases} medical cases already exist")
    
    print()
    
    # ========== Summary ==========
    print("=" * 60)
    print("✅ Migration Complete!\n")
    
    # Count users by department
    cdi_users = await db.users.count_documents({"department": "cdi"})
    coding_users = await db.users.count_documents({"department": "coding"})
    coders = await db.users.count_documents({"coding_role": "coder"})
    auditors = await db.users.count_documents({"coding_role": "auditor"})
    
    print(f"📊 Database Summary:")
    print(f"   - CDI Department Users: {cdi_users}")
    print(f"   - Coding Department Users: {coding_users}")
    print(f"     * Coders: {coders}")
    print(f"     * Auditors: {auditors}")
    print(f"   - Hospitals: {await db.hospitals.count_documents({})}")
    print(f"   - ICD-10-AM Codes: {await db.icd_codes.count_documents({})}")
    print(f"   - DRG Prices: {await db.drg_prices.count_documents({})}")
    print(f"   - Medical Cases: {await db.medical_cases.count_documents({})}")
    
    print("\n🔑 Test Credentials (MFA Disabled for Testing):")
    print("   Coding Supervisor: supervisor@hospital.sa / Super123!")
    print("   Medical Coder: coder@hospital.sa / Coder123!")
    print("   Medical Auditor: auditor@hospital.sa / Auditor123!")
    print("\n✅ Direct login without MFA for easy testing")
    print("=" * 60)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
