#!/usr/bin/env python3
"""
Production Login Issue Testing
Tests the critical login issue where admin cannot login to production site
"""

import requests
import sys
import json
from datetime import datetime
import subprocess

class ProductionLoginTester:
    def __init__(self):
        self.production_url = "https://medidoc-ai.emergent.host"
        self.api_url = f"{self.production_url}/api"
        
        # Admin credentials from review request
        self.admin_credentials = {
            "email": "medidocai@gmail.com",
            "password": "CDI@2024#Admin"
        }
        
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
    def log_test(self, name, success, details="", response_data=None):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
            if details:
                print(f"   {details}")
        else:
            print(f"❌ {name}")
            if details:
                print(f"   ERROR: {details}")
        
        self.test_results.append({
            "test_name": name,
            "success": success,
            "details": details,
            "response_data": response_data
        })
        print()
    
    def check_database_admin(self):
        """Check admin user in database"""
        print("🔍 Checking database for admin user...")
        print("=" * 70)
        
        try:
            # Check if admin exists with correct email
            result = subprocess.run([
                'mongosh', 'mongodb://localhost:27017/clinical_doc_center', 
                '--quiet', '--eval', 
                f'db.users.findOne({{email: "{self.admin_credentials["email"]}"}}, {{_id: 0, password_hash: 1, mfa_enabled: 1, account_locked: 1, locked_until: 1, email: 1, role: 1}})'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                output = result.stdout.strip()
                print(f"Database query result:\n{output}\n")
                
                # Parse the output
                if "null" in output:
                    self.log_test("Database - Admin Exists", False, 
                                f"Admin user with email {self.admin_credentials['email']} NOT FOUND in database")
                    return False
                else:
                    # Check for required fields
                    has_password_hash = "password_hash" in output
                    has_mfa = "mfa_enabled" in output
                    is_locked = "account_locked" in output and "true" in output.lower()
                    
                    details = f"Admin found: email={self.admin_credentials['email']}"
                    if has_password_hash:
                        details += ", has password_hash ✓"
                    else:
                        details += ", MISSING password_hash ✗"
                    
                    if has_mfa:
                        details += ", has mfa_enabled ✓"
                    else:
                        details += ", MISSING mfa_enabled ✗"
                    
                    if is_locked:
                        details += ", ACCOUNT IS LOCKED ✗"
                    else:
                        details += ", account not locked ✓"
                    
                    success = has_password_hash and not is_locked
                    self.log_test("Database - Admin Exists", success, details)
                    return success
            else:
                self.log_test("Database - Admin Exists", False, 
                            f"Database query failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.log_test("Database - Admin Exists", False, str(e))
            return False
    
    def check_login_attempts(self):
        """Check if there are any login attempts blocking the admin"""
        print("🔍 Checking login_attempts collection...")
        print("=" * 70)
        
        try:
            result = subprocess.run([
                'mongosh', 'mongodb://localhost:27017/clinical_doc_center', 
                '--quiet', '--eval', 
                f'db.login_attempts.find({{email: "{self.admin_credentials["email"]}"}}).toArray()'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                output = result.stdout.strip()
                print(f"Login attempts:\n{output}\n")
                
                if "[]" in output or not output:
                    self.log_test("Database - Login Attempts", True, 
                                "No login attempts found - rate limiting should not block")
                    return True
                else:
                    self.log_test("Database - Login Attempts", False, 
                                f"Found login attempts that may be blocking: {output}")
                    return False
            else:
                self.log_test("Database - Login Attempts", False, 
                            f"Query failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.log_test("Database - Login Attempts", False, str(e))
            return False
    
    def clear_login_attempts(self):
        """Clear login attempts for admin email"""
        print("🧹 Clearing login attempts for admin...")
        
        try:
            result = subprocess.run([
                'mongosh', 'mongodb://localhost:27017/clinical_doc_center', 
                '--quiet', '--eval', 
                f'db.login_attempts.deleteMany({{email: "{self.admin_credentials["email"]}"}})'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print(f"✅ Cleared login attempts\n")
                return True
            else:
                print(f"❌ Failed to clear: {result.stderr}\n")
                return False
                
        except Exception as e:
            print(f"❌ Error: {str(e)}\n")
            return False
    
    def test_health_check(self):
        """Test API health check"""
        print("🏥 Testing API Health Check...")
        print("=" * 70)
        
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                details = f"Status: {response.status_code}, Message: {data.get('message', '')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
            
            self.log_test("API Health Check", success, details)
            return success
        except Exception as e:
            self.log_test("API Health Check", False, str(e))
            return False
    
    def test_login_step1(self):
        """Test POST /api/auth/login-step1 with admin credentials"""
        print("🔐 Testing Login Step 1 (Credentials + OTP Send)...")
        print("=" * 70)
        
        try:
            response = requests.post(
                f"{self.api_url}/auth/login-step1",
                json=self.admin_credentials,
                timeout=30
            )
            
            print(f"Response Status: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            print(f"Response Body: {response.text}\n")
            
            success = response.status_code == 200
            
            if success:
                data = response.json()
                requires_mfa = data.get('requires_mfa', False)
                message = data.get('message', '')
                email = data.get('email', '')
                
                details = f"Status: {response.status_code}, requires_mfa: {requires_mfa}, message: '{message}', email: '{email}'"
                
                # Verify expected response
                if requires_mfa and message == "OTP sent to your email" and email == self.admin_credentials['email']:
                    self.log_test("Login Step 1", True, details, data)
                    return True, data
                else:
                    self.log_test("Login Step 1", False, 
                                f"Unexpected response format: {details}", data)
                    return False, None
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
                self.log_test("Login Step 1", False, details)
                return False, None
                
        except Exception as e:
            self.log_test("Login Step 1", False, str(e))
            return False, None
    
    def check_otp_in_database(self):
        """Check if OTP was saved to database"""
        print("🔍 Checking OTP in database...")
        print("=" * 70)
        
        try:
            result = subprocess.run([
                'mongosh', 'mongodb://localhost:27017/clinical_doc_center', 
                '--quiet', '--eval', 
                f'db.otp_records.find({{email: "{self.admin_credentials["email"]}"}}).sort({{created_at: -1}}).limit(1).toArray()'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                output = result.stdout.strip()
                print(f"OTP records:\n{output}\n")
                
                if "[]" in output or not output or "null" in output:
                    self.log_test("Database - OTP Saved", False, 
                                "No OTP record found in database")
                    return False, None
                else:
                    # Try to extract OTP code from output
                    import re
                    otp_match = re.search(r"otp_code:\s*'(\d{6})'", output)
                    if otp_match:
                        otp_code = otp_match.group(1)
                        self.log_test("Database - OTP Saved", True, 
                                    f"OTP found in database: {otp_code}")
                        return True, otp_code
                    else:
                        self.log_test("Database - OTP Saved", True, 
                                    "OTP record exists but couldn't extract code")
                        return True, None
            else:
                self.log_test("Database - OTP Saved", False, 
                            f"Query failed: {result.stderr}")
                return False, None
                
        except Exception as e:
            self.log_test("Database - OTP Saved", False, str(e))
            return False, None
    
    def test_login_step2(self, otp_code):
        """Test POST /api/auth/login-step2 with OTP code"""
        print("🔐 Testing Login Step 2 (OTP Verification)...")
        print("=" * 70)
        
        if not otp_code:
            self.log_test("Login Step 2", False, "No OTP code provided")
            return False, None
        
        try:
            verification_data = {
                "email": self.admin_credentials['email'],
                "otp_code": otp_code
            }
            
            response = requests.post(
                f"{self.api_url}/auth/login-step2",
                json=verification_data,
                timeout=30
            )
            
            print(f"Response Status: {response.status_code}")
            print(f"Response Body: {response.text}\n")
            
            success = response.status_code == 200
            
            if success:
                data = response.json()
                access_token = data.get('access_token')
                user = data.get('user', {})
                
                details = f"Status: {response.status_code}, token: {'present' if access_token else 'missing'}, user: {user.get('email', '')}, role: {user.get('role', '')}"
                
                if access_token and user.get('email') == self.admin_credentials['email']:
                    self.log_test("Login Step 2", True, details, data)
                    return True, access_token
                else:
                    self.log_test("Login Step 2", False, 
                                f"Unexpected response: {details}", data)
                    return False, None
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
                self.log_test("Login Step 2", False, details)
                return False, None
                
        except Exception as e:
            self.log_test("Login Step 2", False, str(e))
            return False, None
    
    def test_token_validity(self, token):
        """Test if the token works for authenticated endpoints"""
        print("🎫 Testing Token Validity...")
        print("=" * 70)
        
        if not token:
            self.log_test("Token Validity", False, "No token provided")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(
                f"{self.api_url}/auth/me",
                headers=headers,
                timeout=10
            )
            
            success = response.status_code == 200
            
            if success:
                data = response.json()
                details = f"Token valid - User: {data.get('email', '')}, Role: {data.get('role', '')}"
                self.log_test("Token Validity", True, details, data)
                return True
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
                self.log_test("Token Validity", False, details)
                return False
                
        except Exception as e:
            self.log_test("Token Validity", False, str(e))
            return False
    
    def run_all_tests(self):
        """Run all production login tests"""
        print("\n" + "=" * 70)
        print("🚨 PRODUCTION LOGIN ISSUE - COMPREHENSIVE TESTING")
        print("=" * 70)
        print(f"Production URL: {self.production_url}")
        print(f"Admin Email: {self.admin_credentials['email']}")
        print(f"Testing Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70 + "\n")
        
        # Phase 1: Database Verification
        print("📊 PHASE 1: DATABASE VERIFICATION")
        print("=" * 70 + "\n")
        
        db_admin_ok = self.check_database_admin()
        db_attempts_ok = self.check_login_attempts()
        
        if not db_attempts_ok:
            print("⚠️  Found blocking login attempts - clearing them...\n")
            self.clear_login_attempts()
        
        # Phase 2: API Health Check
        print("\n📊 PHASE 2: API HEALTH CHECK")
        print("=" * 70 + "\n")
        
        api_ok = self.test_health_check()
        
        if not api_ok:
            print("❌ API is not responding - cannot continue tests\n")
            self.print_summary()
            return
        
        # Phase 3: Login Flow Testing
        print("\n📊 PHASE 3: LOGIN FLOW TESTING")
        print("=" * 70 + "\n")
        
        step1_ok, step1_data = self.test_login_step1()
        
        if not step1_ok:
            print("❌ Login Step 1 failed - cannot continue to Step 2\n")
            self.print_summary()
            return
        
        # Check if OTP was saved
        otp_saved, otp_code = self.check_otp_in_database()
        
        if not otp_saved or not otp_code:
            print("❌ OTP not found in database - cannot test Step 2\n")
            print("⚠️  This indicates the OTP generation/saving is failing\n")
            self.print_summary()
            return
        
        # Test Step 2 with OTP
        step2_ok, token = self.test_login_step2(otp_code)
        
        if not step2_ok:
            print("❌ Login Step 2 failed - login flow is broken\n")
            self.print_summary()
            return
        
        # Phase 4: Token Validation
        print("\n📊 PHASE 4: TOKEN VALIDATION")
        print("=" * 70 + "\n")
        
        token_ok = self.test_token_validity(token)
        
        # Final Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100) if self.tests_run > 0 else 0:.1f}%")
        print("=" * 70)
        
        # Print failed tests
        failed_tests = [t for t in self.test_results if not t['success']]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   - {test['test_name']}")
                if test['details']:
                    print(f"     {test['details']}")
        else:
            print("\n✅ ALL TESTS PASSED!")
        
        print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    tester = ProductionLoginTester()
    tester.run_all_tests()
