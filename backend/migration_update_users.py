#!/usr/bin/env python3
"""
Migration Script: Update All Users with Security Features
يجب تشغيله بعد كل نشر (deployment) للتأكد من تطبيق التحديثات
"""

import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import bcrypt

# إضافة المسار للوصول لـ security_utils
sys.path.append('/app/backend')

async def main():
    print("=" * 60)
    print("🔄 بدء تحديث جميع المستخدمين...")
    print("=" * 60)
    
    # الاتصال بقاعدة البيانات
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/cdi_database')
    client = AsyncIOMotorClient(mongo_url)
    
    # استخراج اسم قاعدة البيانات من الـ URL
    if 'mongodb+srv://' in mongo_url or 'mongodb://' in mongo_url:
        db_name = mongo_url.split('/')[-1].split('?')[0]
        if not db_name or db_name == '':
            db_name = 'cdi_database'
    else:
        db_name = 'cdi_database'
    
    db = client[db_name]
    
    print(f"📊 قاعدة البيانات: {db_name}")
    print()
    
    # 1. تحديث جميع المستخدمين بحقول الأمان
    print("1️⃣ تحديث حقول الأمان...")
    
    users = await db.users.find({}).to_list(None)
    updated_count = 0
    
    for user in users:
        update_fields = {}
        
        # إضافة حقول الأمان إذا لم تكن موجودة
        if 'mfa_enabled' not in user:
            update_fields['mfa_enabled'] = True  # تفعيل MFA افتراضياً
        
        if 'password_changed_at' not in user:
            update_fields['password_changed_at'] = datetime.now(timezone.utc).isoformat()
        
        if 'last_login' not in user:
            update_fields['last_login'] = None
        
        if 'failed_login_attempts' not in user:
            update_fields['failed_login_attempts'] = 0
        
        if 'account_locked_until' not in user:
            update_fields['account_locked_until'] = None
        
        if 'is_active' not in user:
            update_fields['is_active'] = True
        
        # تحديث اسم حقل كلمة المرور
        if 'password' in user and 'password_hash' not in user:
            update_fields['password_hash'] = user['password']
            # حذف الحقل القديم
            await db.users.update_one(
                {'id': user['id']},
                {'$unset': {'password': ''}}
            )
        
        if update_fields:
            await db.users.update_one(
                {'id': user['id']},
                {'$set': update_fields}
            )
            updated_count += 1
            print(f"   ✅ تم تحديث: {user.get('email', 'unknown')}")
    
    print(f"   📊 تم تحديث {updated_count} مستخدم")
    print()
    
    # 2. التأكد من وجود حساب Admin وتحديث الإيميل إلى medidocai@gmail.com
    print("2️⃣ التحقق من حساب Admin وتحديث الإيميل...")
    
    # البحث عن جميع حسابات الأدمن
    all_admins = await db.users.find({'role': 'admin'}).to_list(None)
    
    print(f"   📊 عدد حسابات الأدمن: {len(all_admins)}")
    
    # حذف الحسابات الزائدة (نبقي واحد فقط)
    if len(all_admins) > 1:
        print(f"   🗑️ حذف {len(all_admins) - 1} حسابات أدمن زائدة...")
        keep_admin = all_admins[0]
        for admin in all_admins[1:]:
            await db.users.delete_one({'id': admin['id']})
        admin = keep_admin
    elif len(all_admins) == 1:
        admin = all_admins[0]
    else:
        admin = None
    
    if admin:
        # تحديث كلمة مرور Admin
        new_password = "CDI@2024#Admin"
        hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        
        old_email = admin.get('email')
        
        await db.users.update_one(
            {'id': admin['id']},
            {
                '$set': {
                    'email': 'es012@hotmail.com',
                    'password_hash': hashed.decode('utf-8'),
                    'role': 'admin',
                    'mfa_enabled': True,
                    'is_active': True,
                    'full_name': 'مدير النظام - System Administrator',
                    'password_changed_at': datetime.now(timezone.utc).isoformat(),
                    'failed_login_attempts': 0,
                    'account_locked_until': None
                },
                '$unset': {
                    'password': ''  # حذف حقل password القديم إن وجد
                }
            }
        )
        print(f"   ✅ تم تحديث حساب Admin من {old_email} إلى es012@hotmail.com")
        print(f"   🔑 Password: {new_password}")
        
        # حذف جميع login attempts للأدمن
        await db.login_attempts.delete_many({'email': {'$in': ['es012@hotmail.com', old_email]}})
        print(f"   ✅ تم حذف login attempts")
    else:
        # إنشاء حساب Admin جديد
        import uuid
        new_password = "CDI@2024#Admin"
        hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        
        admin_user = {
            'id': str(uuid.uuid4()),
            'email': 'ES012@HOTMAIL.COM',
            'password_hash': hashed.decode('utf-8'),
            'full_name': 'مدير النظام - System Administrator',
            'role': 'admin',
            'mfa_enabled': True,
            'is_active': True,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'password_changed_at': datetime.now(timezone.utc).isoformat(),
            'last_login': None,
            'failed_login_attempts': 0,
            'account_locked_until': None
        }
        
        await db.users.insert_one(admin_user)
        print("   ✅ تم إنشاء حساب Admin جديد")
        print(f"   📧 Email: ES012@HOTMAIL.COM")
        print(f"   🔑 Password: {new_password}")
    
    print()
    
    # 3. تنظيف OTP و login attempts القديمة
    print("3️⃣ تنظيف البيانات القديمة...")
    
    otp_deleted = await db.otp_records.delete_many({})
    print(f"   ✅ تم حذف {otp_deleted.deleted_count} سجل OTP قديم")
    
    attempts_deleted = await db.login_attempts.delete_many({})
    print(f"   ✅ تم حذف {attempts_deleted.deleted_count} محاولة تسجيل دخول")
    
    print()
    
    # 4. إنشاء Indexes لتحسين الأداء
    print("4️⃣ إنشاء Indexes...")
    
    try:
        # Users
        await db.users.create_index('email', unique=True)
        await db.users.create_index('id', unique=True)
        print("   ✅ Users indexes")
        
        # Clinical Notes
        await db.clinical_notes.create_index('user_id')
        await db.clinical_notes.create_index('created_at')
        await db.clinical_notes.create_index('id', unique=True)
        print("   ✅ Clinical Notes indexes")
        
        # Analyses
        await db.analyses.create_index('note_id')
        await db.analyses.create_index('user_id')
        await db.analyses.create_index('created_at')
        await db.analyses.create_index('id', unique=True)
        print("   ✅ Analyses indexes")
        
        # Audit Logs
        await db.audit_logs.create_index('timestamp')
        await db.audit_logs.create_index('user_id')
        await db.audit_logs.create_index('action')
        print("   ✅ Audit Logs indexes")
        
        # Chat Messages
        await db.chat_messages.create_index('analysis_id')
        await db.chat_messages.create_index('created_at')
        print("   ✅ Chat Messages indexes")
        
    except Exception as e:
        print(f"   ⚠️ بعض الـ indexes موجودة بالفعل: {str(e)}")
    
    print()
    
    # 5. إحصائيات نهائية
    print("5️⃣ الإحصائيات النهائية:")
    total_users = await db.users.count_documents({})
    total_admins = await db.users.count_documents({'role': 'admin'})
    total_supervisors = await db.users.count_documents({'role': 'supervisor'})
    total_regular = await db.users.count_documents({'role': 'user'})
    total_notes = await db.clinical_notes.count_documents({})
    total_analyses = await db.analyses.count_documents({})
    
    print(f"   👥 إجمالي المستخدمين: {total_users}")
    print(f"   👔 الأدمن: {total_admins}")
    print(f"   👨‍💼 المشرفين: {total_supervisors}")
    print(f"   👤 المستخدمين: {total_regular}")
    print(f"   📝 الملاحظات: {total_notes}")
    print(f"   📊 التحليلات: {total_analyses}")
    
    print()
    print("=" * 60)
    print("✅ تم إكمال Migration بنجاح!")
    print("=" * 60)
    print()
    print("📋 معلومات تسجيل الدخول:")
    print("   Email: ES012@HOTMAIL.COM")
    print("   Password: CDI@2024#Admin")
    print()
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
