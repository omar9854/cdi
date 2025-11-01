#!/usr/bin/env python3
"""
Backend API Testing for Arabic Medical Coding Application
Tests all endpoints including auth, notes, analysis, admin, supervisor, and CDI Excel upload functionality
"""

import requests
import sys
import json
from datetime import datetime
import time
import io
import pandas as pd
from openpyxl import Workbook

class MedicalCodingAPITester:
    def __init__(self, base_url="https://clinical-notes-pro-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.admin_token = None
        self.user_data = None
        self.admin_data = None
        self.test_user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Admin credentials from ADMIN_CREDENTIALS.txt
        self.admin_credentials = {
            "email": "admin@cdi-center.sa",
            "password": "CDI@2024#Admin"
        }
        
        # Test user data
        self.test_user = {
            "email": f"test_employee_{datetime.now().strftime('%H%M%S')}@hospital.com",
            "full_name": "د. سارة أحمد المختصة",
            "phone_number": "966501234567",
            "password": "TestPassword123!"
        }
        
        self.arabic_clinical_note = {
            "title": "ملاحظات سريرية - مريض السكري",
            "doctor_notes": [
                {
                    "text": """المريض: محمد أحمد، 45 سنة، ذكر

الشكوى الرئيسية:
- ارتفاع مستوى السكر في الدم
- تعب عام وإرهاق
- كثرة التبول والعطش

التاريخ المرضي:
- مصاب بداء السكري النوع الثاني منذ 5 سنوات
- ارتفاع ضغط الدم
- تاريخ عائلي لأمراض القلب""",
                    "specialty": "internal_medicine"
                },
                {
                    "text": """الفحص السريري:
- ضغط الدم: 150/90 mmHg
- نبضات القلب: 88 نبضة/دقيقة
- الوزن: 85 كغ، الطول: 170 سم
- BMI: 29.4

نتائج المختبر:
- سكر الدم الصائم: 180 mg/dl
- HbA1c: 8.5%
- الكوليسترول الكلي: 220 mg/dl
- وظائف الكلى: طبيعية""",
                    "specialty": "endocrinology"
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
                self.user_data = data.get('user')
                self.test_user_id = self.user_data.get('id')
                details = f"Login successful for: {data.get('user', {}).get('email')}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("User Login", success, details, response.json() if success else None)
            return success
        except Exception as e:
            self.log_test("User Login", False, str(e))
            return False

    def test_admin_login(self):
        """Test admin login"""
        try:
            response = requests.post(
                f"{self.api_url}/auth/login",
                json=self.admin_credentials,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                self.admin_token = data.get('access_token')
                self.admin_data = data.get('user')
                details = f"Admin login successful for: {data.get('user', {}).get('email')}, Role: {data.get('user', {}).get('role')}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Admin Login", success, details, response.json() if success else None)
            return success
        except Exception as e:
            self.log_test("Admin Login", False, str(e))
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

    # ========== ADMIN MANAGEMENT TESTS ==========
    
    def test_admin_users_statistics(self):
        """Test GET /api/admin/users-statistics - verify includes 'role' and 'is_active' fields"""
        if not self.admin_token:
            self.log_test("Admin Users Statistics", False, "No admin authentication token")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.get(
                f"{self.api_url}/admin/users-statistics",
                headers=headers,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                statistics = data.get('statistics', [])
                if statistics:
                    # Check if first user has required fields
                    first_user = statistics[0]
                    has_role = 'role' in first_user
                    has_is_active = 'is_active' in first_user
                    details = f"Retrieved {len(statistics)} users, has_role: {has_role}, has_is_active: {has_is_active}"
                    success = has_role and has_is_active
                else:
                    details = "No users found in statistics"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Admin Users Statistics", success, details, response.json() if success else None)
            return success
        except Exception as e:
            self.log_test("Admin Users Statistics", False, str(e))
            return False

    def test_assign_supervisor(self, user_id):
        """Test POST /api/admin/assign-supervisor/{user_id}"""
        if not self.admin_token or not user_id:
            self.log_test("Assign Supervisor", False, "No admin token or user ID")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.post(
                f"{self.api_url}/admin/assign-supervisor/{user_id}",
                headers=headers,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                details = f"User promoted to supervisor: {data.get('message', '')}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Assign Supervisor", success, details, response.json() if success else None)
            return success
        except Exception as e:
            self.log_test("Assign Supervisor", False, str(e))
            return False

    def test_remove_supervisor(self, user_id):
        """Test POST /api/admin/remove-supervisor/{user_id}"""
        if not self.admin_token or not user_id:
            self.log_test("Remove Supervisor", False, "No admin token or user ID")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.post(
                f"{self.api_url}/admin/remove-supervisor/{user_id}",
                headers=headers,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                details = f"Supervisor demoted to user: {data.get('message', '')}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Remove Supervisor", success, details, response.json() if success else None)
            return success
        except Exception as e:
            self.log_test("Remove Supervisor", False, str(e))
            return False

    def test_edit_user(self, user_id):
        """Test PUT /api/admin/users/{user_id} - edit user data"""
        if not self.admin_token or not user_id:
            self.log_test("Edit User", False, "No admin token or user ID")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            update_data = {
                "full_name": "د. سارة أحمد المحدثة",
                "email": f"updated_employee_{datetime.now().strftime('%H%M%S')}@hospital.com",
                "phone_number": "966509876543"
            }
            response = requests.put(
                f"{self.api_url}/admin/users/{user_id}",
                json=update_data,
                headers=headers,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                details = f"User updated: {data.get('message', '')}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Edit User", success, details, response.json() if success else None)
            return success
        except Exception as e:
            self.log_test("Edit User", False, str(e))
            return False

    def test_suspend_user(self, user_id):
        """Test POST /api/admin/suspend-user/{user_id}"""
        if not self.admin_token or not user_id:
            self.log_test("Suspend User", False, "No admin token or user ID")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.post(
                f"{self.api_url}/admin/suspend-user/{user_id}",
                headers=headers,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                details = f"User suspended: {data.get('message', '')}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Suspend User", success, details, response.json() if success else None)
            return success
        except Exception as e:
            self.log_test("Suspend User", False, str(e))
            return False

    def test_activate_user(self, user_id):
        """Test POST /api/admin/activate-user/{user_id}"""
        if not self.admin_token or not user_id:
            self.log_test("Activate User", False, "No admin token or user ID")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.post(
                f"{self.api_url}/admin/activate-user/{user_id}",
                headers=headers,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                details = f"User activated: {data.get('message', '')}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Activate User", success, details, response.json() if success else None)
            return success
        except Exception as e:
            self.log_test("Activate User", False, str(e))
            return False

    def test_delete_user(self, user_id):
        """Test DELETE /api/admin/users/{user_id}"""
        if not self.admin_token or not user_id:
            self.log_test("Delete User", False, "No admin token or user ID")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.delete(
                f"{self.api_url}/admin/users/{user_id}",
                headers=headers,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                details = f"User deleted: {data.get('message', '')}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Delete User", success, details, response.json() if success else None)
            return success
        except Exception as e:
            self.log_test("Delete User", False, str(e))
            return False

    # ========== SUPERVISOR TESTS ==========
    
    def test_supervisor_employees(self):
        """Test GET /api/supervisor/employees - verify includes 'notes_count' and 'analyses_count' fields"""
        if not self.admin_token:
            self.log_test("Supervisor Employees", False, "No admin authentication token")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.get(
                f"{self.api_url}/supervisor/employees",
                headers=headers,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                if data:
                    # Check if employees have required fields
                    first_employee = data[0] if data else {}
                    has_notes_count = 'notes_count' in first_employee
                    has_analyses_count = 'analyses_count' in first_employee
                    details = f"Retrieved {len(data)} employees, has_notes_count: {has_notes_count}, has_analyses_count: {has_analyses_count}"
                    success = has_notes_count and has_analyses_count
                else:
                    details = "No employees found"
                    success = True  # Empty list is valid
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Supervisor Employees", success, details, response.json() if success else None)
            return success
        except Exception as e:
            self.log_test("Supervisor Employees", False, str(e))
            return False

    # ========== CDI EXCEL UPLOAD TESTS ==========
    
    def create_sample_cdi_excel(self):
        """Create a sample Excel file with CDI data"""
        try:
            # Create sample data
            data = {
                'CDS Name': [
                    'د. أحمد محمد',
                    'د. فاطمة علي', 
                    'د. محمد حسن',
                    'د. نورا سالم',
                    'د. خالد أحمد'
                ],
                'Hospital Name': [
                    'مستشفى الملك فهد',
                    'مستشفى الملك فيصل',
                    'مستشفى الملك فهد',
                    'مستشفى الأمير سلطان',
                    'مستشفى الملك فيصل'
                ],
                'Admission Date': [
                    '2024-01-15',
                    '2024-01-16',
                    '2024-01-17',
                    '2024-01-18',
                    '2024-01-19'
                ],
                'Primary Diagnosis': [
                    'Diabetes Mellitus Type 2',
                    '',  # Empty to test undocumented detection
                    'Hypertension',
                    'Not documented',  # Explicit undocumented
                    'Pneumonia'
                ],
                'Secondary Diagnosis': [
                    'Hypertension',
                    'Diabetes',
                    '',  # Empty to test undocumented detection
                    'Diabetes Mellitus',
                    ''  # Empty
                ],
                'DRG Before': [
                    '641',
                    '642',
                    '643',
                    '644',
                    '645'
                ],
                'DRG After': [
                    '641',
                    '643',  # Changed
                    '643',
                    '645',  # Changed
                    '645'
                ],
                'DRG Change': [
                    '',
                    'Yes',
                    '',
                    'Yes',
                    ''
                ]
            }
            
            # Create DataFrame
            df = pd.DataFrame(data)
            
            # Save to BytesIO
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='CDI Data')
            
            excel_buffer.seek(0)
            return excel_buffer
            
        except Exception as e:
            print(f"Error creating sample Excel: {str(e)}")
            return None

    def test_upload_cdi_data(self):
        """Test POST /api/supervisor/upload-cdi-data with Excel file"""
        if not self.admin_token:
            self.log_test("Upload CDI Data", False, "No admin authentication token")
            return False
        
        try:
            # Create sample Excel file
            excel_file = self.create_sample_cdi_excel()
            if not excel_file:
                self.log_test("Upload CDI Data", False, "Failed to create sample Excel file")
                return False
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            files = {
                'file': ('cdi_sample_data.xlsx', excel_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            }
            
            response = requests.post(
                f"{self.api_url}/supervisor/upload-cdi-data",
                headers=headers,
                files=files,
                timeout=30
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                # Verify required fields in response
                required_fields = ['total_records', 'total_hospitals', 'drg_changes', 
                                 'undocumented_total', 'primary_undocumented', 
                                 'secondary_undocumented', 'hospitals_data']
                
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    details = f"CDI analysis complete - Records: {data.get('total_records')}, Hospitals: {data.get('total_hospitals')}, Undocumented: {data.get('undocumented_total')}"
                else:
                    success = False
                    details = f"Missing required fields: {', '.join(missing_fields)}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Upload CDI Data", success, details, response.json() if success else None)
            return success
        except Exception as e:
            self.log_test("Upload CDI Data", False, str(e))
            return False

    def run_all_tests(self):
        """Run all API tests including Admin and Supervisor functionality"""
        print("🚀 Starting CDI Medical Application API Tests")
        print(f"🔗 Testing API: {self.api_url}")
        print("=" * 80)
        
        # Basic connectivity
        if not self.test_health_check():
            print("❌ Health check failed - stopping tests")
            return self.generate_report()
        
        # Admin Authentication
        print("\n👑 Testing Admin Authentication...")
        if not self.test_admin_login():
            print("❌ Admin login failed - stopping admin tests")
            return self.generate_report()
        
        # Test user registration and login for admin management tests
        print("\n👤 Testing User Registration & Login...")
        if not self.test_user_registration():
            print("❌ User registration failed - stopping tests")
            return self.generate_report()
        
        if not self.test_user_login():
            print("❌ User login failed - stopping tests")
            return self.generate_report()
        
        # Admin User Management Tests
        print("\n🔧 Testing Admin User Management Endpoints...")
        
        # Test initial users statistics
        self.test_admin_users_statistics()
        
        # Test assign supervisor
        if self.test_user_id:
            self.test_assign_supervisor(self.test_user_id)
            
            # Test users statistics again to verify role change
            print("🔄 Verifying role change in statistics...")
            self.test_admin_users_statistics()
            
            # Test remove supervisor
            self.test_remove_supervisor(self.test_user_id)
            
            # Test edit user data
            self.test_edit_user(self.test_user_id)
            
            # Test suspend user
            self.test_suspend_user(self.test_user_id)
            
            # Test activate user
            self.test_activate_user(self.test_user_id)
        
        # Supervisor Employees Test
        print("\n👥 Testing Supervisor Endpoints...")
        self.test_supervisor_employees()
        
        # CDI Excel Upload Test
        print("\n📊 Testing CDI Excel Upload & Analysis...")
        self.test_upload_cdi_data()
        
        # Basic Notes and Analysis Tests (if time permits)
        print("\n📝 Testing Basic Notes & Analysis...")
        success, note_id = self.test_create_clinical_note()
        if success:
            self.test_get_notes()
            self.test_get_single_note(note_id)
            
            # AI Analysis tests (optional for this focused test)
            print("\n🤖 Testing AI Analysis (Optional)...")
            analysis_success, analysis_id = self.test_analyze_note(note_id)
            
            if analysis_success and analysis_id:
                self.test_get_analyses(note_id)
                self.test_get_history()
                
                # Export tests
                print("\n📄 Testing Export Functions...")
                self.test_export_pdf(analysis_id)
                self.test_export_excel(analysis_id)
        
        # Clean up - delete test user (optional, at the end)
        if self.test_user_id:
            print("\n🗑️ Cleaning up test data...")
            self.test_delete_user(self.test_user_id)
        
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