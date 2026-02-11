#!/usr/bin/env python3
"""
Backend API Testing for MediDoc AI Medical Application
Comprehensive testing based on user requirements in Arabic
اختبار شامل للتطبيق الطبي MediDoc AI
"""

import requests
import sys
import json
from datetime import datetime
import time

class MediDocAITester:
    def __init__(self, base_url="https://medical-app-preview.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_data = None
        self.test_user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.note_id = None
        self.analysis_id = None
        
        # Test user data as specified in the request
        import time
        timestamp = str(int(time.time()))
        self.test_user = {
            "email": f"test.cdi.{timestamp}@hospital.sa",
            "full_name": "Test CDI User",
            "phone_number": f"96650000{timestamp[-4:]}",
            "password": "TestPassword123!"
        }
        
        # Clinical note data as specified in the request
        self.test_clinical_note = {
            "title": "Test Clinical Note",
            "doctor_notes": [
                {
                    "text": "Patient is a 55-year-old male with Type 2 Diabetes Mellitus, HbA1c 9.2%, on Metformin. Also has hypertension on Lisinopril. Reports bilateral foot numbness.",
                    "specialty": "internal_medicine"
                }
            ]
        }

    def log_test(self, name, success, details="", response_data=None):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - نجح")
        else:
            print(f"❌ {name} - فشل: {details}")
        
        self.test_results.append({
            "test_name": name,
            "success": success,
            "details": details,
            "response_data": response_data
        })

    def test_health_check(self):
        """Test API health check"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Message: {data.get('message', '')}"
            self.log_test("Health Check", success, details, response.json() if success else None)
            return success
        except Exception as e:
            self.log_test("Health Check", False, str(e))
            return False

    def test_auth_register(self):
        """Test POST /api/auth/register - تسجيل مستخدم جديد"""
        try:
            response = requests.post(
                f"{self.api_url}/auth/register",
                json=self.test_user,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                self.token = data.get('access_token')
                self.user_data = data.get('user')
                self.test_user_id = self.user_data.get('id')
                details = f"User registered successfully: {self.user_data.get('email')}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("POST /api/auth/register", success, details, response.json() if success else None)
            return success
        except Exception as e:
            self.log_test("POST /api/auth/register", False, str(e))
            return False

    def test_auth_login(self):
        """Test POST /api/auth/login - تسجيل الدخول"""
        try:
            login_data = {
                "email": self.test_user["email"],
                "password": self.test_user["password"]
            }
            response = requests.post(
                f"{self.api_url}/auth/login",
                json=login_data,
                timeout=10
            )
            
            # Handle MFA flow if required
            if response.status_code == 202:
                # MFA required, try step1 and step2
                return self.test_auth_login_with_mfa()
            
            success = response.status_code == 200
            if success:
                data = response.json()
                self.token = data.get('access_token')
                self.user_data = data.get('user')
                self.test_user_id = self.user_data.get('id')
                details = f"Login successful for: {data.get('user', {}).get('email')}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("POST /api/auth/login", success, details, response.json() if success else None)
            return success
        except Exception as e:
            self.log_test("POST /api/auth/login", False, str(e))
            return False

    def test_auth_login_with_mfa(self):
        """Handle MFA login flow"""
        try:
            # Step 1: Send credentials
            login_data = {
                "email": self.test_user["email"],
                "password": self.test_user["password"]
            }
            response = requests.post(
                f"{self.api_url}/auth/login-step1",
                json=login_data,
                timeout=10
            )
            
            if response.status_code != 200:
                details = f"Step 1 failed - Status: {response.status_code}, Error: {response.text}"
                self.log_test("POST /api/auth/login (MFA Step 1)", False, details)
                return False
            
            step1_data = response.json()
            if not step1_data.get('requires_mfa'):
                # No MFA required, direct login
                self.token = step1_data.get('access_token')
                self.user_data = step1_data.get('user')
                self.test_user_id = self.user_data.get('id')
                self.log_test("POST /api/auth/login (Direct)", True, "Login successful without MFA")
                return True
            
            # MFA required - we cannot complete this automatically
            self.log_test("POST /api/auth/login (MFA Required)", False, "MFA required - cannot complete automated test")
            return False
            
        except Exception as e:
            self.log_test("POST /api/auth/login (MFA)", False, str(e))
            return False

    def test_auth_me(self):
        """Test GET /api/auth/me - الحصول على بيانات المستخدم الحالي"""
        if not self.token:
            self.log_test("GET /api/auth/me", False, "No authentication token")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(
                f"{self.api_url}/auth/me",
                headers=headers,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                required_fields = ['id', 'email', 'full_name', 'role']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    success = False
                    details = f"Missing required fields: {', '.join(missing_fields)}"
                else:
                    details = f"User data retrieved - Email: {data.get('email')}, Role: {data.get('role')}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("GET /api/auth/me", success, details, response.json() if success else None)
            return success
        except Exception as e:
            self.log_test("GET /api/auth/me", False, str(e))
            return False

    def test_notes_create(self):
        """Test POST /api/notes - إنشاء ملاحظة سريرية جديدة"""
        if not self.token:
            self.log_test("POST /api/notes", False, "No authentication token")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.post(
                f"{self.api_url}/notes",
                json=self.test_clinical_note,
                headers=headers,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                self.note_id = data.get('id')
                details = f"Clinical note created successfully with ID: {self.note_id}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("POST /api/notes", success, details, response.json() if success else None)
            return success
        except Exception as e:
            self.log_test("POST /api/notes", False, str(e))
            return False

    def test_notes_list(self):
        """Test GET /api/notes - الحصول على قائمة الملاحظات"""
        if not self.token:
            self.log_test("GET /api/notes", False, "No authentication token")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(
                f"{self.api_url}/notes",
                headers=headers,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                details = f"Retrieved {len(data)} clinical notes"
                # Verify response format
                if data and isinstance(data, list):
                    first_note = data[0]
                    required_fields = ['id', 'title', 'doctor_notes', 'created_at']
                    missing_fields = [field for field in required_fields if field not in first_note]
                    if missing_fields:
                        success = False
                        details += f" - Missing fields: {', '.join(missing_fields)}"
                    else:
                        details += " - All required fields present"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("GET /api/notes", success, details, response.json() if success else None)
            return success
        except Exception as e:
            self.log_test("GET /api/notes", False, str(e))
            return False

    def test_analysis_create(self):
        """Test POST /api/analyze - تحليل ملاحظة سريرية"""
        if not self.token or not self.note_id:
            self.log_test("POST /api/analyze", False, "No authentication token or note ID")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            analyze_data = {"note_id": self.note_id}
            
            print("🔄 Starting AI analysis (this may take 10-30 seconds)...")
            start_time = time.time()
            
            response = requests.post(
                f"{self.api_url}/analyze",
                json=analyze_data,
                headers=headers,
                timeout=60  # Longer timeout for AI processing
            )
            
            end_time = time.time()
            analysis_time = end_time - start_time
            
            success = response.status_code == 200
            if success:
                data = response.json()
                self.analysis_id = data.get('id')
                
                # Verify response structure
                required_fields = ['id', 'note_id', 'diagnoses_to_document', 'gaps_ar', 'gaps_en', 'queries_ar', 'queries_en']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    success = False
                    details = f"Missing required fields: {', '.join(missing_fields)}"
                else:
                    diagnoses_count = len(data.get('diagnoses_to_document', []))
                    gaps_ar_count = len(data.get('gaps_ar', []))
                    gaps_en_count = len(data.get('gaps_en', []))
                    queries_ar_count = len(data.get('queries_ar', []))
                    queries_en_count = len(data.get('queries_en', []))
                    
                    details = f"Analysis completed in {analysis_time:.2f}s - Diagnoses: {diagnoses_count}, Gaps (AR): {gaps_ar_count}, Gaps (EN): {gaps_en_count}, Queries (AR): {queries_ar_count}, Queries (EN): {queries_en_count}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("POST /api/analyze", success, details, response.json() if success else None)
            return success
        except Exception as e:
            self.log_test("POST /api/analyze", False, str(e))
            return False

    def test_json_format_validation(self):
        """Test that all API responses return valid JSON format"""
        if not self.token:
            self.log_test("JSON Format Validation", False, "No authentication token")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            endpoints_to_test = [
                ("/auth/me", "GET"),
                ("/notes", "GET"),
            ]
            
            if self.analysis_id:
                endpoints_to_test.append((f"/analysis/{self.analysis_id}", "GET"))
            
            all_valid = True
            details_list = []
            
            for endpoint, method in endpoints_to_test:
                try:
                    if method == "GET":
                        response = requests.get(f"{self.api_url}{endpoint}", headers=headers, timeout=10)
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            details_list.append(f"{endpoint}: Valid JSON ✓")
                        except json.JSONDecodeError:
                            all_valid = False
                            details_list.append(f"{endpoint}: Invalid JSON ✗")
                    else:
                        details_list.append(f"{endpoint}: HTTP {response.status_code}")
                        
                except Exception as e:
                    all_valid = False
                    details_list.append(f"{endpoint}: Error - {str(e)}")
            
            details = "; ".join(details_list)
            self.log_test("JSON Format Validation", all_valid, details)
            return all_valid
            
        except Exception as e:
            self.log_test("JSON Format Validation", False, str(e))
            return False

    def test_token_authentication(self):
        """Test that authentication tokens work correctly"""
        if not self.token:
            self.log_test("Token Authentication", False, "No authentication token")
            return False
        
        try:
            # Test with valid token
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.api_url}/auth/me", headers=headers, timeout=10)
            valid_token_works = response.status_code == 200
            
            # Test with invalid token
            invalid_headers = {"Authorization": "Bearer invalid_token_12345"}
            response = requests.get(f"{self.api_url}/auth/me", headers=invalid_headers, timeout=10)
            invalid_token_rejected = response.status_code == 401
            
            # Test without token
            response = requests.get(f"{self.api_url}/auth/me", timeout=10)
            no_token_rejected = response.status_code == 401
            
            success = valid_token_works and invalid_token_rejected and no_token_rejected
            
            if success:
                details = "Valid token accepted, invalid token rejected, no token rejected"
            else:
                details = f"Valid token: {valid_token_works}, Invalid rejected: {invalid_token_rejected}, No token rejected: {no_token_rejected}"
            
            self.log_test("Token Authentication", success, details)
            return success
            
        except Exception as e:
            self.log_test("Token Authentication", False, str(e))
            return False

    def run_comprehensive_test(self):
        """Run comprehensive test suite for MediDoc AI"""
        print("🏥 بدء الاختبار الشامل للتطبيق الطبي MediDoc AI")
        print("=" * 60)
        print(f"Backend URL: {self.base_url}")
        print(f"API URL: {self.api_url}")
        print("=" * 60)
        
        # Test sequence as specified in the request
        tests = [
            ("Health Check", self.test_health_check),
            ("Authentication - Register", self.test_auth_register),
            ("Authentication - Login", self.test_auth_login),
            ("Authentication - Get User Info", self.test_auth_me),
            ("Notes - Create Clinical Note", self.test_notes_create),
            ("Notes - List Notes", self.test_notes_list),
            ("Analysis - Analyze Clinical Note", self.test_analysis_create),
            ("Validation - JSON Format", self.test_json_format_validation),
            ("Validation - Token Authentication", self.test_token_authentication),
        ]
        
        for test_name, test_func in tests:
            print(f"\n🔍 Running: {test_name}")
            try:
                test_func()
            except Exception as e:
                self.log_test(test_name, False, f"Test execution error: {str(e)}")
            
            # Small delay between tests
            time.sleep(0.5)
        
        # Print summary
        self.print_test_summary()
        
        return self.tests_passed == self.tests_run

    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 60)
        print("📊 ملخص نتائج الاختبار - Test Results Summary")
        print("=" * 60)
        
        print(f"إجمالي الاختبارات: {self.tests_run}")
        print(f"الاختبارات الناجحة: {self.tests_passed}")
        print(f"الاختبارات الفاشلة: {self.tests_run - self.tests_passed}")
        print(f"معدل النجاح: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        print("\n📋 تفاصيل النتائج - Detailed Results:")
        print("-" * 60)
        
        for result in self.test_results:
            status = "✅ نجح" if result['success'] else "❌ فشل"
            print(f"{status} {result['test_name']}")
            if not result['success'] and result['details']:
                print(f"   التفاصيل: {result['details']}")
        
        print("\n" + "=" * 60)
        
        if self.tests_passed == self.tests_run:
            print("🎉 جميع الاختبارات نجحت! - All tests passed!")
        else:
            print("⚠️  بعض الاختبارات فشلت - Some tests failed")
            failed_tests = [r for r in self.test_results if not r['success']]
            print(f"الاختبارات الفاشلة: {len(failed_tests)}")
            for failed in failed_tests:
                print(f"  - {failed['test_name']}: {failed['details']}")
        
        print("=" * 60)

def main():
    """Main function to run the tests"""
    print("🚀 بدء اختبار التطبيق الطبي MediDoc AI")
    print("Starting MediDoc AI Medical Application Testing")
    
    # Initialize tester
    tester = MediDocAITester()
    
    # Run comprehensive tests
    success = tester.run_comprehensive_test()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()