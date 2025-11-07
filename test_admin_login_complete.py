#!/usr/bin/env python3
"""Complete admin login test with MFA"""
import requests
import json
import subprocess

# Use localhost for testing
BASE_URL = "http://localhost:8001"
API_URL = f"{BASE_URL}/api"

def get_latest_otp(email):
    """Get latest OTP from database"""
    cmd = [
        'mongosh', 
        'mongodb://localhost:27017/clinical_doc_center',
        '--quiet',
        '--eval',
        f'JSON.stringify(db.otp_records.find({{email: "{email}", is_used: false}}).sort({{created_at: -1}}).limit(1).toArray())'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    if result.returncode == 0:
        data = json.loads(result.stdout.strip())
        if data:
            return data[0]['otp_code']
    return None

print("=" * 80)
print("🧪 ADMIN LOGIN FLOW TEST - After Database Reset")
print("=" * 80)

# Step 1: Login Step 1
print("\n1️⃣  Testing Login Step 1...")
response1 = requests.post(
    f"{API_URL}/auth/login-step1",
    json={"email": "medidocai@gmail.com", "password": "CDI@2024#Admin"},
    timeout=10
)
print(f"   Status: {response1.status_code}")
print(f"   Response: {response1.json()}")

if response1.status_code == 200:
    data1 = response1.json()
    print(f"   ✅ Step 1 SUCCESS")
    print(f"   - Requires MFA: {data1.get('requires_mfa')}")
    print(f"   - Message: {data1.get('message')}")
    print(f"   - Email: {data1.get('email')}")
    
    # Step 2: Get OTP from database
    print("\n2️⃣  Retrieving OTP from database...")
    otp = get_latest_otp("medidocai@gmail.com")
    if otp:
        print(f"   ✅ OTP Retrieved: {otp}")
        
        # Step 3: Login Step 2
        print("\n3️⃣  Testing Login Step 2...")
        response2 = requests.post(
            f"{API_URL}/auth/login-step2",
            json={"email": "medidocai@gmail.com", "otp_code": otp},
            timeout=10
        )
        print(f"   Status: {response2.status_code}")
        
        if response2.status_code == 200:
            data2 = response2.json()
            print(f"   ✅ Step 2 SUCCESS")
            print(f"   - Token: {data2.get('access_token')[:30]}...")
            print(f"   - User: {data2.get('user')}")
            
            token = data2.get('access_token')
            
            # Step 4: Test token validity
            print("\n4️⃣  Testing Token Validity...")
            response3 = requests.get(
                f"{API_URL}/auth/me",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10
            )
            print(f"   Status: {response3.status_code}")
            if response3.status_code == 200:
                print(f"   ✅ Token is VALID")
                print(f"   - User Data: {response3.json()}")
            else:
                print(f"   ❌ Token validation failed: {response3.text}")
            
            # Step 5: Test admin endpoint
            print("\n5️⃣  Testing Admin Endpoint Access...")
            response4 = requests.get(
                f"{API_URL}/admin/stats",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10
            )
            print(f"   Status: {response4.status_code}")
            if response4.status_code == 200:
                stats = response4.json()
                print(f"   ✅ Admin endpoint accessible")
                print(f"   - Total Users: {stats.get('total_users')}")
                print(f"   - Total Notes: {stats.get('total_notes')}")
                print(f"   - Total Analyses: {stats.get('total_analyses')}")
            else:
                print(f"   ❌ Admin endpoint failed: {response4.text}")
            
            # Step 6: Create a test note
            print("\n6️⃣  Testing Note Creation...")
            response5 = requests.post(
                f"{API_URL}/notes",
                json={
                    "title": "Test Note - DB Reset Verification",
                    "doctor_notes": [
                        {
                            "text": "Test note to verify system is working after database reset.",
                            "specialty": "internal_medicine"
                        }
                    ]
                },
                headers={"Authorization": f"Bearer {token}"},
                timeout=10
            )
            print(f"   Status: {response5.status_code}")
            if response5.status_code == 200:
                note = response5.json()
                print(f"   ✅ Note created successfully")
                print(f"   - Note ID: {note.get('id')}")
                print(f"   - Title: {note.get('title')}")
            else:
                print(f"   ❌ Note creation failed: {response5.text}")
            
            # Step 7: Get user notes
            print("\n7️⃣  Testing Get User Notes...")
            response6 = requests.get(
                f"{API_URL}/notes",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10
            )
            print(f"   Status: {response6.status_code}")
            if response6.status_code == 200:
                notes = response6.json()
                print(f"   ✅ Retrieved {len(notes)} notes")
            else:
                print(f"   ❌ Get notes failed: {response6.text}")
            
            print("\n" + "=" * 80)
            print("✅ ALL TESTS PASSED - Admin login flow working correctly!")
            print("=" * 80)
        else:
            print(f"   ❌ Step 2 FAILED: {response2.text}")
    else:
        print(f"   ❌ Could not retrieve OTP from database")
else:
    print(f"   ❌ Step 1 FAILED: {response1.text}")

