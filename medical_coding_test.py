#!/usr/bin/env python3
"""
Medical Coding System Backend Testing
Tests the dual department implementation (CDI + Medical Coding)
"""

import requests
import sys
import json
from datetime import datetime
import time

class MedicalCodingTester:
    def __init__(self, base_url="https://medical-app-preview.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Test credentials from review request
        self.coding_credentials = {
            "supervisor": {"email": "supervisor@hospital.sa", "password": "Super123!"},
            "coder": {"email": "coder@hospital.sa", "password": "Coder123!"},
            "auditor": {"email": "auditor@hospital.sa", "password": "Auditor123!"}
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

    def test_medical_coding_system_comprehensive(self):
        """Comprehensive test for Medical Coding System - Dual Department Implementation"""
        print("\n🏥 MEDICAL CODING SYSTEM - DUAL DEPARTMENT TESTING")
        print("=" * 70)
        
        # Store tokens for each role
        tokens = {}
        user_ids = {}
        
        # ========== 1. Test User Registration with Department Selection ==========
        print("\n📝 1. Testing User Registration with Department Selection")
        print("-" * 50)
        
        # Test CDI department registration (default)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        cdi_user = {
            "email": f"cdi_test_{timestamp}@test.com",
            "full_name": "CDI Test User",
            "phone_number": f"96650123{timestamp[-4:]}",
            "password": "CDITestUser123!",
            "department": "cdi"
        }
        
        self.test_department_registration(cdi_user, "cdi", None)
        
        # Test coding department registration - coder
        coder_user = {
            "email": f"coder_test_{timestamp}@test.com",
            "full_name": "Coder Test User",
            "phone_number": f"96650124{timestamp[-4:]}",
            "password": "CoderTestUser123!",
            "department": "coding",
            "coding_role": "coder"
        }
        
        self.test_department_registration(coder_user, "coding", "coder")
        
        # Test coding department registration - auditor
        auditor_user = {
            "email": f"auditor_test_{timestamp}@test.com",
            "full_name": "Auditor Test User",
            "phone_number": f"96650125{timestamp[-4:]}",
            "password": "AuditorTestUser123!",
            "department": "coding",
            "coding_role": "auditor"
        }
        
        self.test_department_registration(auditor_user, "coding", "auditor")
        
        # ========== 2. Test Login for All Coding Roles ==========
        print("\n🔐 2. Testing Login for All Coding Roles")
        print("-" * 50)
        
        for role, creds in self.coding_credentials.items():
            success, token, user_data = self.test_coding_login(creds["email"], creds["password"], role)
            if success:
                tokens[role] = token
                user_ids[role] = user_data.get('id')
        
        # ========== 3. Test Coding Supervisor Endpoints ==========
        print("\n👑 3. Testing Coding Supervisor Endpoints")
        print("-" * 50)
        
        if 'supervisor' in tokens:
            supervisor_token = tokens['supervisor']
            
            # Test hospitals endpoints
            self.test_get_hospitals(supervisor_token)
            self.test_create_hospital(supervisor_token)
            
            # Test medical cases endpoints
            self.test_get_medical_cases(supervisor_token)
            self.test_assign_cases_to_coders(supervisor_token)
            
            # Test department KPIs
            self.test_get_department_kpis(supervisor_token)
            self.test_get_coder_statistics(supervisor_token)
        
        # ========== 4. Test Coder Endpoints ==========
        print("\n👨‍⚕️ 4. Testing Coder Endpoints")
        print("-" * 50)
        
        if 'coder' in tokens and 'coder' in user_ids:
            coder_token = tokens['coder']
            coder_id = user_ids['coder']
            
            # Test coder workflow
            self.test_get_my_cases(coder_token, coder_id)
            case_id = self.test_start_coding_case(coder_token, coder_id)
            if case_id:
                self.test_search_icd_codes(coder_token)
                self.test_submit_coding(coder_token, coder_id, case_id)
        
        # ========== 5. Test Auditor Endpoints ==========
        print("\n🔍 5. Testing Auditor Endpoints")
        print("-" * 50)
        
        if 'auditor' in tokens and 'auditor' in user_ids:
            auditor_token = tokens['auditor']
            auditor_id = user_ids['auditor']
            
            # Test auditor workflow
            self.test_get_cases_for_audit(auditor_token)
            self.test_submit_audit(auditor_token, auditor_id)
        
        # ========== 6. Test Department Management ==========
        print("\n🏢 6. Testing Department Management")
        print("-" * 50)
        
        # Test admin login first
        admin_token = self.test_admin_login()
        if admin_token:
            self.test_department_user_management(admin_token)
    
    def test_department_registration(self, user_data, expected_department, expected_coding_role):
        """Test user registration with department selection"""
        try:
            response = requests.post(
                f"{self.api_url}/auth/register",
                json=user_data,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                user = data.get('user', {})
                department = user.get('department')
                coding_role = user.get('coding_role')
                
                if department == expected_department and coding_role == expected_coding_role:
                    details = f"User registered with department='{department}', coding_role='{coding_role}'"
                else:
                    success = False
                    details = f"Expected department='{expected_department}', coding_role='{expected_coding_role}', got department='{department}', coding_role='{coding_role}'"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            test_name = f"Register {expected_department} user ({expected_coding_role or 'default'})"
            self.log_test(test_name, success, details, response.json() if success else None)
            return success
        except Exception as e:
            self.log_test(f"Register {expected_department} user", False, str(e))
            return False
    
    def test_coding_login(self, email, password, expected_role):
        """Test login for coding system users"""
        try:
            login_data = {"email": email, "password": password}
            response = requests.post(
                f"{self.api_url}/auth/login",
                json=login_data,
                timeout=10
            )
            success = response.status_code == 200
            token = None
            user_data = None
            
            if success:
                data = response.json()
                token = data.get('access_token')
                user_data = data.get('user', {})
                department = user_data.get('department')
                role = user_data.get('role')
                coding_role = user_data.get('coding_role')
                
                details = f"Login successful - Department: {department}, Role: {role}, Coding Role: {coding_role}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test(f"Login {expected_role}", success, details, response.json() if success else None)
            return success, token, user_data
        except Exception as e:
            self.log_test(f"Login {expected_role}", False, str(e))
            return False, None, None
    
    def test_admin_login(self):
        """Test admin login"""
        try:
            admin_credentials = {
                "email": "almaghthawi.cdi@gmail.com",
                "password": "CDI@2024#Admin"
            }
            response = requests.post(
                f"{self.api_url}/auth/login",
                json=admin_credentials,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                admin_token = data.get('access_token')
                details = f"Admin login successful"
                self.log_test("Admin Login", success, details)
                return admin_token
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
                self.log_test("Admin Login", False, details)
                return None
        except Exception as e:
            self.log_test("Admin Login", False, str(e))
            return None
    
    def test_get_hospitals(self, token):
        """Test GET /api/coding/hospitals"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(
                f"{self.api_url}/coding/hospitals",
                headers=headers,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                hospitals = data.get('hospitals', [])
                details = f"Retrieved {len(hospitals)} hospitals (expected: 3)"
                success = len(hospitals) >= 3
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Get Hospitals", success, details, response.json() if success else None)
            return success
        except Exception as e:
            self.log_test("Get Hospitals", False, str(e))
            return False
    
    def test_create_hospital(self, token):
        """Test POST /api/coding/hospitals"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            hospital_data = {
                "name": "مستشفى الاختبار",
                "code": f"TEST{datetime.now().strftime('%H%M%S')}",
                "location": "الرياض"
            }
            response = requests.post(
                f"{self.api_url}/coding/hospitals",
                json=hospital_data,
                headers=headers,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                details = f"Hospital created: {data.get('message', '')}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Create Hospital", success, details, response.json() if success else None)
            return success
        except Exception as e:
            self.log_test("Create Hospital", False, str(e))
            return False
    
    def test_get_medical_cases(self, token):
        """Test GET /api/coding/cases"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(
                f"{self.api_url}/coding/cases",
                headers=headers,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                cases = data.get('cases', [])
                details = f"Retrieved {len(cases)} medical cases (expected: 3)"
                success = len(cases) >= 3
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Get Medical Cases", success, details, response.json() if success else None)
            return success
        except Exception as e:
            self.log_test("Get Medical Cases", False, str(e))
            return False
    
    def test_assign_cases_to_coders(self, token):
        """Test POST /api/coding/cases/assign"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.post(
                f"{self.api_url}/coding/cases/assign",
                headers=headers,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                assigned = data.get('assigned', 0)
                coders = data.get('coders', 0)
                details = f"Assigned {assigned} cases to {coders} coders"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Assign Cases to Coders", success, details, response.json() if success else None)
            return success
        except Exception as e:
            self.log_test("Assign Cases to Coders", False, str(e))
            return False
    
    def test_get_department_kpis(self, token):
        """Test GET /api/coding/stats/department"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(
                f"{self.api_url}/coding/stats/department",
                headers=headers,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                total_cases = data.get('total_cases', 0)
                total_coders = data.get('total_coders', 0)
                details = f"KPIs retrieved - Cases: {total_cases}, Coders: {total_coders}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Get Department KPIs", success, details, response.json() if success else None)
            return success
        except Exception as e:
            self.log_test("Get Department KPIs", False, str(e))
            return False
    
    def test_get_coder_statistics(self, token):
        """Test GET /api/coding/stats/coders"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(
                f"{self.api_url}/coding/stats/coders",
                headers=headers,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                coders = data.get('coders', [])
                details = f"Retrieved statistics for {len(coders)} coders"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Get Coder Statistics", success, details, response.json() if success else None)
            return success
        except Exception as e:
            self.log_test("Get Coder Statistics", False, str(e))
            return False
    
    def test_get_my_cases(self, token, user_id):
        """Test GET /api/coding/my-cases"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(
                f"{self.api_url}/coding/my-cases?user_id={user_id}",
                headers=headers,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                cases = data.get('cases', [])
                details = f"Coder has {len(cases)} assigned cases"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Get My Cases (Coder)", success, details, response.json() if success else None)
            return success
        except Exception as e:
            self.log_test("Get My Cases (Coder)", False, str(e))
            return False
    
    def test_start_coding_case(self, token, user_id):
        """Test POST /api/coding/cases/{case_id}/start"""
        try:
            # First get a case assigned to this coder
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(
                f"{self.api_url}/coding/my-cases?user_id={user_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code != 200:
                self.log_test("Start Coding Case", False, "Could not get assigned cases")
                return None
            
            cases = response.json().get('cases', [])
            if not cases:
                self.log_test("Start Coding Case", False, "No cases assigned to coder")
                return None
            
            case_id = cases[0]['id']
            
            # Start coding the case
            response = requests.post(
                f"{self.api_url}/coding/cases/{case_id}/start?user_id={user_id}",
                headers=headers,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                details = f"Started coding case: {case_id}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Start Coding Case", success, details, response.json() if success else None)
            return case_id if success else None
        except Exception as e:
            self.log_test("Start Coding Case", False, str(e))
            return None
    
    def test_search_icd_codes(self, token):
        """Test GET /api/coding/icd-codes?search=diabetes"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(
                f"{self.api_url}/coding/icd-codes?search=diabetes",
                headers=headers,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                codes = data.get('codes', [])
                details = f"Found {len(codes)} ICD codes for 'diabetes'"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Search ICD Codes", success, details, response.json() if success else None)
            return success
        except Exception as e:
            self.log_test("Search ICD Codes", False, str(e))
            return False
    
    def test_submit_coding(self, token, user_id, case_id):
        """Test POST /api/coding/cases/{case_id}/submit"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            submission_data = {
                "case_id": case_id,
                "principal_diagnosis": {
                    "code": "E11.9",
                    "description": "Type 2 diabetes mellitus without complications",
                    "is_principal": True,
                    "is_complication": False
                },
                "secondary_diagnoses": [
                    {
                        "code": "I10",
                        "description": "Essential hypertension",
                        "is_principal": False,
                        "is_complication": False
                    }
                ],
                "drg_code": "DRG-641",
                "drg_description": "Diabetes with major complications",
                "financial_value": 25000.00
            }
            
            response = requests.post(
                f"{self.api_url}/coding/cases/{case_id}/submit?user_id={user_id}",
                json=submission_data,
                headers=headers,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                duration = data.get('duration_minutes', 0)
                details = f"Coding submitted successfully, duration: {duration} minutes"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Submit Coding", success, details, response.json() if success else None)
            return success
        except Exception as e:
            self.log_test("Submit Coding", False, str(e))
            return False
    
    def test_get_cases_for_audit(self, token):
        """Test GET /api/coding/cases/for-audit?sample_size=10"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(
                f"{self.api_url}/coding/cases/for-audit?sample_size=10",
                headers=headers,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                cases = data.get('cases', [])
                details = f"Retrieved {len(cases)} cases for audit (10% sample)"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Get Cases for Audit", success, details, response.json() if success else None)
            return success
        except Exception as e:
            self.log_test("Get Cases for Audit", False, str(e))
            return False
    
    def test_submit_audit(self, token, auditor_id):
        """Test POST /api/coding/audit/submit"""
        try:
            # First get cases for audit
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(
                f"{self.api_url}/coding/cases/for-audit?sample_size=1",
                headers=headers,
                timeout=10
            )
            
            if response.status_code != 200:
                self.log_test("Submit Audit", False, "Could not get cases for audit")
                return False
            
            cases = response.json().get('cases', [])
            if not cases:
                self.log_test("Submit Audit", False, "No cases available for audit")
                return False
            
            case_id = cases[0]['id']
            
            # Submit audit
            audit_data = {
                "case_id": case_id,
                "errors": [
                    {
                        "error_type": "undercoding",
                        "description": "Missing secondary diagnosis",
                        "icd_code": "I10",
                        "financial_impact": 2000.00,
                        "severity": "medium"
                    }
                ],
                "corrected_principal": "E11.9",
                "corrected_secondary": ["I10", "K29.7"],
                "corrected_drg": "DRG-641",
                "corrected_value": 27000.00,
                "recommendations": "Include all documented secondary diagnoses",
                "risk_level": "medium"
            }
            
            response = requests.post(
                f"{self.api_url}/coding/audit/submit?auditor_id={auditor_id}",
                json=audit_data,
                headers=headers,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                audit_id = data.get('audit_id')
                financial_impact = data.get('financial_impact', 0)
                details = f"Audit submitted - ID: {audit_id}, Financial Impact: {financial_impact} SAR"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Submit Audit", success, details, response.json() if success else None)
            return success
        except Exception as e:
            self.log_test("Submit Audit", False, str(e))
            return False
    
    def test_department_user_management(self, token):
        """Test admin can view users by department"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(
                f"{self.api_url}/admin/users-statistics",
                headers=headers,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                users = data.get('statistics', [])
                
                # Count users by department
                cdi_users = sum(1 for u in users if u.get('department') == 'cdi')
                coding_users = sum(1 for u in users if u.get('department') == 'coding')
                
                details = f"Users by department - CDI: {cdi_users}, Coding: {coding_users}"
                
                # Verify existing users have department field
                users_with_department = sum(1 for u in users if 'department' in u)
                if users_with_department != len(users):
                    success = False
                    details += f" - WARNING: {len(users) - users_with_department} users missing department field"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Department User Management", success, details, response.json() if success else None)
            return success
        except Exception as e:
            self.log_test("Department User Management", False, str(e))
            return False

    def run_tests(self):
        """Run all medical coding tests"""
        print("🚀 Starting Medical Coding System Backend Testing")
        print("=" * 80)
        print(f"🌐 Base URL: {self.base_url}")
        print(f"🔗 API URL: {self.api_url}")
        print("=" * 80)
        
        # Run comprehensive tests
        self.test_medical_coding_system_comprehensive()
        
        # Print final results
        print("\n" + "=" * 80)
        print("📊 MEDICAL CODING TEST RESULTS")
        print("=" * 80)
        print(f"✅ Tests Passed: {self.tests_passed}/{self.tests_run}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}/{self.tests_run}")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL MEDICAL CODING TESTS PASSED!")
        else:
            print("⚠️  Some tests failed - check logs above")
        
        print("=" * 80)
        
        return self.tests_passed, self.tests_run, self.test_results


if __name__ == "__main__":
    tester = MedicalCodingTester()
    tester.run_tests()