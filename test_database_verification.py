#!/usr/bin/env python3
"""Database verification after reset"""
import subprocess
import json
from datetime import datetime

def run_mongo_query(query):
    """Run MongoDB query and return result"""
    cmd = [
        'mongosh', 
        'mongodb://localhost:27017/clinical_doc_center',
        '--quiet',
        '--eval',
        f'JSON.stringify({query})'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    if result.returncode == 0:
        return json.loads(result.stdout.strip())
    return None

print("=" * 80)
print("🗄️  DATABASE VERIFICATION - After Reset")
print("=" * 80)

# 1. Check admin account
print("\n1️⃣  Admin Account Verification:")
admins = run_mongo_query('db.users.find({role: "admin"}).toArray()')
if admins:
    print(f"   ✅ Found {len(admins)} admin account(s)")
    if len(admins) == 1:
        admin = admins[0]
        print(f"   ✅ Exactly 1 admin account (as expected)")
        print(f"   - Email: {admin.get('email')}")
        print(f"   - Full Name: {admin.get('full_name')}")
        print(f"   - MFA Enabled: {admin.get('mfa_enabled')}")
        print(f"   - Account Locked: {admin.get('account_locked_until') is not None}")
        print(f"   - Has password_hash: {'password_hash' in admin}")
        print(f"   - Failed Login Attempts: {admin.get('failed_login_attempts', 0)}")
        
        # Verify email
        if admin.get('email') == 'medidocai@gmail.com':
            print(f"   ✅ Email is correct: medidocai@gmail.com")
        else:
            print(f"   ❌ Email mismatch: {admin.get('email')}")
        
        # Verify MFA
        if admin.get('mfa_enabled'):
            print(f"   ✅ MFA is enabled")
        else:
            print(f"   ❌ MFA is NOT enabled")
        
        # Verify not locked
        if not admin.get('account_locked_until'):
            print(f"   ✅ Account is NOT locked")
        else:
            print(f"   ❌ Account is locked until: {admin.get('account_locked_until')}")
        
        # Verify password_hash field
        if 'password_hash' in admin:
            print(f"   ✅ Has password_hash field (not 'password')")
        else:
            print(f"   ❌ Missing password_hash field")
    else:
        print(f"   ❌ Expected 1 admin, found {len(admins)}")
else:
    print(f"   ❌ No admin accounts found")

# 2. Check total users
print("\n2️⃣  Total Users:")
total_users = run_mongo_query('db.users.countDocuments({})')
print(f"   Total: {total_users}")
if total_users == 37:
    print(f"   ✅ Matches expected count (37)")
else:
    print(f"   ⚠️  Expected 37, found {total_users}")

# 3. Check total notes
print("\n3️⃣  Total Notes:")
total_notes = run_mongo_query('db.clinical_notes.countDocuments({})')
print(f"   Total: {total_notes}")
if total_notes >= 58:  # >= because we just created a test note
    print(f"   ✅ At least 58 notes (expected 58, may have test notes)")
else:
    print(f"   ⚠️  Expected 58, found {total_notes}")

# 4. Check total analyses
print("\n4️⃣  Total Analyses:")
total_analyses = run_mongo_query('db.analyses.countDocuments({})')
print(f"   Total: {total_analyses}")
if total_analyses == 58:
    print(f"   ✅ Matches expected count (58)")
else:
    print(f"   ⚠️  Expected 58, found {total_analyses}")

# 5. Check for duplicate admin accounts
print("\n5️⃣  Duplicate Admin Check:")
admin_emails = run_mongo_query('db.users.find({role: "admin"}, {email: 1}).toArray()')
if admin_emails:
    emails = [a['email'] for a in admin_emails]
    unique_emails = set(emails)
    if len(emails) == len(unique_emails):
        print(f"   ✅ No duplicate admin accounts")
    else:
        print(f"   ❌ Found duplicate admin accounts: {emails}")
else:
    print(f"   ⚠️  Could not check for duplicates")

# 6. Check OTP records
print("\n6️⃣  OTP Records:")
latest_otp = run_mongo_query('db.otp_records.find({email: "medidocai@gmail.com"}).sort({created_at: -1}).limit(1).toArray()')
if latest_otp:
    otp = latest_otp[0]
    created_at = datetime.fromisoformat(otp['created_at'].replace('Z', '+00:00'))
    expires_at = datetime.fromisoformat(otp['expires_at'].replace('Z', '+00:00'))
    expiry_minutes = (expires_at - created_at).total_seconds() / 60
    
    print(f"   ✅ OTP records exist for admin")
    print(f"   - Latest OTP Code: {otp.get('otp_code')}")
    print(f"   - Created: {otp.get('created_at')}")
    print(f"   - Expires: {otp.get('expires_at')}")
    print(f"   - Expiry Time: {expiry_minutes:.1f} minutes")
    
    if abs(expiry_minutes - 30) < 1:
        print(f"   ✅ OTP expiration is 30 minutes (as expected)")
    else:
        print(f"   ⚠️  OTP expiration is {expiry_minutes:.1f} minutes (expected 30)")
else:
    print(f"   ⚠️  No OTP records found")

# 7. Check login attempts tracking
print("\n7️⃣  Login Attempts Tracking:")
login_attempts = run_mongo_query('db.login_attempts.find({email: "medidocai@gmail.com"}).sort({timestamp: -1}).limit(5).toArray()')
if login_attempts:
    print(f"   ✅ Login attempts are being tracked")
    print(f"   - Recent attempts: {len(login_attempts)}")
    for attempt in login_attempts[:3]:
        print(f"     • {attempt.get('timestamp')}: Success={attempt.get('success')}")
else:
    print(f"   ⚠️  No login attempts tracked yet")

# 8. Check rate limiting
print("\n8️⃣  Rate Limiting Configuration:")
admin_user = run_mongo_query('db.users.findOne({email: "medidocai@gmail.com"})')
if admin_user:
    failed_attempts = admin_user.get('failed_login_attempts', 0)
    locked_until = admin_user.get('account_locked_until')
    
    print(f"   - Failed Login Attempts: {failed_attempts}")
    print(f"   - Account Locked Until: {locked_until}")
    
    if failed_attempts == 0 and not locked_until:
        print(f"   ✅ Admin account not blocked by rate limiting")
    else:
        print(f"   ⚠️  Admin account may have rate limiting issues")

print("\n" + "=" * 80)
print("✅ DATABASE VERIFICATION COMPLETE")
print("=" * 80)

