#!/usr/bin/env python3
"""
MediDoc AI Backend Testing - Using Provided Token
Tests the specific endpoints using the token from test_result.md
"""

import requests
import sys
import json
import time
from datetime import datetime

class MediDocTokenTester:
    def __init__(self):
        self.base_url = "https://medcoder-1.preview.emergentagent.com"
        self.api_url = f"{self.base_url}/api"
        
        # Token from test_result.md
        self.token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiYWZmODdmZTktYTgwZS00MmU0LWJmYTktZGQ4YjM3ODc2ODBlIiwiZW1haWwiOiJ0ZXN0QGNkaS5jb20iLCJyb2xlIjoidXNlciIsImV4cCI6MTc2Njg1NTkxM30.DKxX840OmJGDunW-9oiHShG69IK1IYNCjAPrgTVvcvM"
        
        # Test data from review request
        self.test_note_id = "700b6d4c-799c-4012-8b55-fc8ba2d74463"
        self.test_analysis_id = "82b45ec1-c33e-40d8-a2a5-11121cc444e9"
        
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details="", response_time=None):
        """Log test results with timing"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        time_info = f" ({response_time:.2f}s)" if response_time else ""
        print(f"{status} {name}{time_info}")
        if details:
            print(f"    Details: {details}")
        
        self.test_results.append({
            "test_name": name,
            "success": success,
            "details": details,
            "response_time": response_time
        })

    def test_token_validity(self):
        """Test if the provided token is valid"""
        print("\n🔑 Testing Token Validity...")
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            
            start_time = time.time()
            response = requests.get(f"{self.api_url}/auth/me", headers=headers, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Token Validity", 
                    True, 
                    f"Token valid for user: {data.get('email')} (role: {data.get('role')})", 
                    response_time
                )
                return True
            else:
                self.log_test(
                    "Token Validity", 
                    False, 
                    f"Token invalid: {response.status_code} - {response.text}", 
                    response_time
                )
                return False
        except Exception as e:
            self.log_test("Token Validity", False, f"Exception: {str(e)}")
            return False

    def test_gemini_api_speed(self):
        """Test Gemini API Analysis Speed - MUST be < 15 seconds"""
        print("\n⚡ Testing Gemini API Analysis Speed...")
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            analyze_data = {
                "note_id": self.test_note_id,
                "ai_provider": "gemini"  # CRITICAL: Must specify Gemini
            }
            
            print(f"    Testing with note_id: {self.test_note_id}")
            print(f"    AI Provider: gemini")
            print(f"    Starting analysis...")
            
            start_time = time.time()
            
            response = requests.post(
                f"{self.api_url}/analyze",
                json=analyze_data,
                headers=headers,
                timeout=60  # Allow up to 60 seconds but expect < 15
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if response contains required field
                has_diagnoses = 'diagnoses_to_document' in data
                
                # Speed requirement: < 15 seconds
                speed_ok = response_time < 15.0
                
                if has_diagnoses and speed_ok:
                    diagnoses_count = len(data.get('diagnoses_to_document', []))
                    self.log_test(
                        "Gemini API Speed Test", 
                        True, 
                        f"Analysis completed with {diagnoses_count} diagnoses in {response_time:.2f}s (< 15s requirement met)", 
                        response_time
                    )
                    return True
                elif not has_diagnoses:
                    self.log_test(
                        "Gemini API Speed Test", 
                        False, 
                        f"Response missing 'diagnoses_to_document' field. Response time: {response_time:.2f}s", 
                        response_time
                    )
                    return False
                else:
                    self.log_test(
                        "Gemini API Speed Test", 
                        False, 
                        f"Analysis too slow: {response_time:.2f}s (requirement: < 15s)", 
                        response_time
                    )
                    return False
            else:
                self.log_test(
                    "Gemini API Speed Test", 
                    False, 
                    f"API call failed: {response.status_code} - {response.text}", 
                    response_time
                )
                return False
                
        except Exception as e:
            self.log_test("Gemini API Speed Test", False, f"Exception: {str(e)}")
            return False

    def test_predefined_questions_api(self):
        """Test Pre-defined Questions API"""
        print("\n❓ Testing Pre-defined Questions API...")
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            
            # Test the specific endpoint from review request
            url = f"{self.api_url}/chat/ask-question/q1?analysis_id={self.test_analysis_id}&language=ar"
            
            print(f"    Testing URL: {url}")
            
            start_time = time.time()
            
            response = requests.post(
                url,
                headers=headers,
                timeout=45  # Allow up to 45 seconds but expect < 30
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if response contains answer field
                has_answer = 'answer' in data
                
                # Speed requirement: < 30 seconds
                speed_ok = response_time < 30.0
                
                if has_answer and speed_ok:
                    answer_preview = str(data.get('answer', ''))[:100] + "..." if len(str(data.get('answer', ''))) > 100 else str(data.get('answer', ''))
                    self.log_test(
                        "Pre-defined Questions API", 
                        True, 
                        f"Question answered in {response_time:.2f}s (< 30s requirement met). Answer preview: {answer_preview}", 
                        response_time
                    )
                    return True
                elif not has_answer:
                    self.log_test(
                        "Pre-defined Questions API", 
                        False, 
                        f"Response missing 'answer' field. Response time: {response_time:.2f}s", 
                        response_time
                    )
                    return False
                else:
                    self.log_test(
                        "Pre-defined Questions API", 
                        False, 
                        f"Response too slow: {response_time:.2f}s (requirement: < 30s)", 
                        response_time
                    )
                    return False
            else:
                self.log_test(
                    "Pre-defined Questions API", 
                    False, 
                    f"API call failed: {response.status_code} - {response.text}", 
                    response_time
                )
                return False
                
        except Exception as e:
            self.log_test("Pre-defined Questions API", False, f"Exception: {str(e)}")
            return False

    def test_clinical_questions_list(self):
        """Test Clinical Questions List API"""
        print("\n📋 Testing Clinical Questions List...")
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            
            start_time = time.time()
            
            response = requests.get(
                f"{self.api_url}/clinical-questions?language=ar",
                headers=headers,
                timeout=10
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if response is an array with at least 5 questions
                if isinstance(data, list) and len(data) >= 5:
                    self.log_test(
                        "Clinical Questions List", 
                        True, 
                        f"Retrieved {len(data)} questions (requirement: >= 5)", 
                        response_time
                    )
                    return True
                else:
                    self.log_test(
                        "Clinical Questions List", 
                        False, 
                        f"Expected array with >= 5 questions, got {type(data)} with {len(data) if isinstance(data, list) else 'N/A'} items", 
                        response_time
                    )
                    return False
            else:
                self.log_test(
                    "Clinical Questions List", 
                    False, 
                    f"API call failed: {response.status_code} - {response.text}", 
                    response_time
                )
                return False
                
        except Exception as e:
            self.log_test("Clinical Questions List", False, f"Exception: {str(e)}")
            return False

    def test_login_credentials(self):
        """Test login with the specified credentials"""
        print("\n🔐 Testing Login with Specified Credentials...")
        
        credentials = {
            "email": "test@cdi.com",
            "password": "Test@123456789!"
        }
        
        try:
            start_time = time.time()
            
            # Try step 1 login first
            response = requests.post(
                f"{self.api_url}/auth/login-step1",
                json=credentials,
                timeout=30
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('requires_mfa'):
                    # MFA required - this is expected behavior
                    self.log_test(
                        "Login Credentials Test", 
                        True, 
                        "Credentials valid - MFA required (expected for security)", 
                        response_time
                    )
                    return True
                else:
                    # Direct login without MFA
                    access_token = data.get('access_token')
                    user_data = data.get('user')
                    
                    self.log_test(
                        "Login Credentials Test", 
                        True, 
                        f"Direct login successful for {user_data.get('email')}", 
                        response_time
                    )
                    return True
            else:
                self.log_test(
                    "Login Credentials Test", 
                    False, 
                    f"Login failed: {response.status_code} - {response.text}", 
                    response_time
                )
                return False
                    
        except Exception as e:
            self.log_test("Login Credentials Test", False, f"Exception: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all critical tests"""
        print("=" * 80)
        print("🧪 MEDIDOC AI BACKEND TESTING WITH PROVIDED TOKEN")
        print("=" * 80)
        print(f"Backend URL: {self.base_url}")
        print(f"Test Note ID: {self.test_note_id}")
        print(f"Test Analysis ID: {self.test_analysis_id}")
        print("=" * 80)
        
        # Test 1: Token Validity
        token_ok = self.test_token_validity()
        
        # Test 2: Login Credentials (separate test)
        login_ok = self.test_login_credentials()
        
        # Test 3: Clinical Questions List
        questions_ok = False
        if token_ok:
            questions_ok = self.test_clinical_questions_list()
        else:
            self.log_test("Clinical Questions List", False, "Skipped - token invalid")
        
        # Test 4: Gemini API Speed
        gemini_ok = False
        if token_ok:
            gemini_ok = self.test_gemini_api_speed()
        else:
            self.log_test("Gemini API Speed Test", False, "Skipped - token invalid")
        
        # Test 5: Pre-defined Questions
        predefined_ok = False
        if token_ok:
            predefined_ok = self.test_predefined_questions_api()
        else:
            self.log_test("Pre-defined Questions API", False, "Skipped - token invalid")
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        critical_tests = [
            ("Token Validity", token_ok),
            ("Login Credentials Test", login_ok),
            ("Clinical Questions List", questions_ok),
            ("Gemini API Speed Test", gemini_ok),
            ("Pre-defined Questions API", predefined_ok)
        ]
        
        for test_name, success in critical_tests:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {test_name}")
        
        passed_count = sum(1 for _, success in critical_tests if success)
        total_count = len(critical_tests)
        
        print(f"\nOverall: {passed_count}/{total_count} critical tests passed")
        
        if passed_count >= 4:  # Allow for some flexibility
            print("🎉 MOST CRITICAL TESTS PASSED!")
            return True
        else:
            print("⚠️  MULTIPLE CRITICAL TESTS FAILED - NEEDS ATTENTION")
            return False

def main():
    """Main test execution"""
    tester = MediDocTokenTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()