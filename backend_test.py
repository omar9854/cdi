#!/usr/bin/env python3
"""
Backend API Testing for Arabic Medical Coding Application
Tests all endpoints including auth, notes, analysis, and export functionality
"""

import requests
import sys
import json
from datetime import datetime
import time

class MedicalCodingAPITester:
    def __init__(self, base_url="https://clinical-doc-ai.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_data = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Arabic test data
        self.test_user = {
            "email": f"test_doctor_{datetime.now().strftime('%H%M%S')}@hospital.com",
            "full_name": "د. أحمد محمد الطبيب",
            "password": "TestPassword123!"
        }
        
        self.arabic_clinical_note = {
            "title": "ملاحظات سريرية - مريض السكري",
            "notes_text": """المريض: محمد أحمد، 45 سنة، ذكر

الشكوى الرئيسية:
- ارتفاع مستوى السكر في الدم
- تعب عام وإرهاق
- كثرة التبول والعطش

التاريخ المرضي:
- مصاب بداء السكري النوع الثاني منذ 5 سنوات
- ارتفاع ضغط الدم
- تاريخ عائلي لأمراض القلب

الفحص السريري:
- ضغط الدم: 150/90 mmHg
- نبضات القلب: 88 نبضة/دقيقة
- الوزن: 85 كغ، الطول: 170 سم
- BMI: 29.4

نتائج المختبر:
- سكر الدم الصائم: 180 mg/dl
- HbA1c: 8.5%
- الكوليسترول الكلي: 220 mg/dl
- وظائف الكلى: طبيعية

التشخيص:
- داء السكري النوع الثاني غير المنضبط
- ارتفاع ضغط الدم الأساسي
- السمنة

العلاج:
- تعديل جرعة الميتفورمين
- إضافة دواء ضغط الدم
- نصائح غذائية وممارسة الرياضة
- متابعة بعد شهر"""
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

    def test_user_registration(self):
        """Test user registration"""
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
                details = f"User registered: {self.user_data.get('email')}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("User Registration", success, details, response.json() if success else None)
            return success
        except Exception as e:
            self.log_test("User Registration", False, str(e))
            return False

    def test_user_login(self):
        """Test user login"""
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
            success = response.status_code == 200
            if success:
                data = response.json()
                self.token = data.get('access_token')
                details = f"Login successful for: {data.get('user', {}).get('email')}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("User Login", success, details, response.json() if success else None)
            return success
        except Exception as e:
            self.log_test("User Login", False, str(e))
            return False

    def test_create_clinical_note(self):
        """Test creating a clinical note"""
        if not self.token:
            self.log_test("Create Clinical Note", False, "No authentication token")
            return False, None
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.post(
                f"{self.api_url}/notes",
                json=self.arabic_clinical_note,
                headers=headers,
                timeout=10
            )
            success = response.status_code == 200
            note_id = None
            if success:
                data = response.json()
                note_id = data.get('id')
                details = f"Note created with ID: {note_id}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Create Clinical Note", success, details, response.json() if success else None)
            return success, note_id
        except Exception as e:
            self.log_test("Create Clinical Note", False, str(e))
            return False, None

    def test_get_notes(self):
        """Test retrieving user's notes"""
        if not self.token:
            self.log_test("Get Notes", False, "No authentication token")
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
                details = f"Retrieved {len(data)} notes"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Get Notes", success, details, response.json() if success else None)
            return success
        except Exception as e:
            self.log_test("Get Notes", False, str(e))
            return False

    def test_get_single_note(self, note_id):
        """Test retrieving a single note"""
        if not self.token or not note_id:
            self.log_test("Get Single Note", False, "No authentication token or note ID")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(
                f"{self.api_url}/notes/{note_id}",
                headers=headers,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                details = f"Retrieved note: {data.get('title', '')}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Get Single Note", success, details, response.json() if success else None)
            return success
        except Exception as e:
            self.log_test("Get Single Note", False, str(e))
            return False

    def test_analyze_note(self, note_id):
        """Test AI analysis of clinical note"""
        if not self.token or not note_id:
            self.log_test("Analyze Note", False, "No authentication token or note ID")
            return False, None
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            analyze_data = {"note_id": note_id}
            
            print("🔄 Starting AI analysis (this may take 10-30 seconds)...")
            response = requests.post(
                f"{self.api_url}/analyze",
                json=analyze_data,
                headers=headers,
                timeout=60  # Longer timeout for AI processing
            )
            success = response.status_code == 200
            analysis_id = None
            if success:
                data = response.json()
                analysis_id = data.get('id')
                primary_count = len(data.get('primary_diagnoses', []))
                secondary_count = len(data.get('secondary_diagnoses', []))
                gaps_count = len(data.get('gaps', []))
                queries_count = len(data.get('queries_for_doctor', []))
                details = f"Analysis completed - Primary: {primary_count}, Secondary: {secondary_count}, Gaps: {gaps_count}, Queries: {queries_count}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Analyze Note", success, details, response.json() if success else None)
            return success, analysis_id
        except Exception as e:
            self.log_test("Analyze Note", False, str(e))
            return False, None

    def test_get_analyses(self, note_id):
        """Test retrieving analyses for a note"""
        if not self.token or not note_id:
            self.log_test("Get Analyses", False, "No authentication token or note ID")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(
                f"{self.api_url}/analyses/{note_id}",
                headers=headers,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                details = f"Retrieved {len(data)} analyses"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Get Analyses", success, details, response.json() if success else None)
            return success
        except Exception as e:
            self.log_test("Get Analyses", False, str(e))
            return False

    def test_get_history(self):
        """Test retrieving analysis history"""
        if not self.token:
            self.log_test("Get History", False, "No authentication token")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(
                f"{self.api_url}/history",
                headers=headers,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                details = f"Retrieved {len(data)} history items"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Get History", success, details, response.json() if success else None)
            return success
        except Exception as e:
            self.log_test("Get History", False, str(e))
            return False

    def test_export_pdf(self, analysis_id):
        """Test PDF export"""
        if not self.token or not analysis_id:
            self.log_test("Export PDF", False, "No authentication token or analysis ID")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(
                f"{self.api_url}/export/pdf/{analysis_id}",
                headers=headers,
                timeout=30
            )
            success = response.status_code == 200
            if success:
                content_type = response.headers.get('content-type', '')
                content_length = len(response.content)
                details = f"PDF generated - Type: {content_type}, Size: {content_length} bytes"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Export PDF", success, details)
            return success
        except Exception as e:
            self.log_test("Export PDF", False, str(e))
            return False

    def test_export_excel(self, analysis_id):
        """Test Excel export"""
        if not self.token or not analysis_id:
            self.log_test("Export Excel", False, "No authentication token or analysis ID")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(
                f"{self.api_url}/export/excel/{analysis_id}",
                headers=headers,
                timeout=30
            )
            success = response.status_code == 200
            if success:
                content_type = response.headers.get('content-type', '')
                content_length = len(response.content)
                details = f"Excel generated - Type: {content_type}, Size: {content_length} bytes"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Export Excel", success, details)
            return success
        except Exception as e:
            self.log_test("Export Excel", False, str(e))
            return False

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Arabic Medical Coding API Tests")
        print(f"🔗 Testing API: {self.api_url}")
        print("=" * 60)
        
        # Basic connectivity
        if not self.test_health_check():
            print("❌ Health check failed - stopping tests")
            return self.generate_report()
        
        # Authentication tests
        if not self.test_user_registration():
            print("❌ User registration failed - stopping tests")
            return self.generate_report()
        
        if not self.test_user_login():
            print("❌ User login failed - stopping tests")
            return self.generate_report()
        
        # Notes tests
        success, note_id = self.test_create_clinical_note()
        if not success:
            print("❌ Note creation failed - stopping tests")
            return self.generate_report()
        
        self.test_get_notes()
        self.test_get_single_note(note_id)
        
        # AI Analysis tests (most critical)
        print("\n🤖 Testing AI Analysis (Gemini 2.5-pro)...")
        analysis_success, analysis_id = self.test_analyze_note(note_id)
        
        if analysis_success and analysis_id:
            self.test_get_analyses(note_id)
            self.test_get_history()
            
            # Export tests
            print("\n📄 Testing Export Functions...")
            self.test_export_pdf(analysis_id)
            self.test_export_excel(analysis_id)
        else:
            print("⚠️ AI Analysis failed - skipping export tests")
        
        return self.generate_report()

    def generate_report(self):
        """Generate test report"""
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        print(f"✅ Tests Passed: {self.tests_passed}/{self.tests_run}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}/{self.tests_run}")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        # Critical issues
        failed_tests = [test for test in self.test_results if not test['success']]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  • {test['test_name']}: {test['details']}")
        
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "failed_tests": self.tests_run - self.tests_passed,
            "success_rate": success_rate,
            "test_results": self.test_results,
            "critical_failures": failed_tests
        }

def main():
    """Main test execution"""
    tester = MedicalCodingAPITester()
    results = tester.run_all_tests()
    
    # Return appropriate exit code
    return 0 if results["failed_tests"] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())