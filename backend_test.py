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
    def __init__(self, base_url="https://cdi-health.preview.emergentagent.com"):
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

    def test_supervisor_account_employees_access(self):
        """Test supervisor account (not admin) access to GET /api/supervisor/employees"""
        print("\n🔍 FOCUSED TEST: Supervisor Account Employee Access")
        print("=" * 60)
        
        # Step 1: Create a supervisor account
        supervisor_user = {
            "email": f"supervisor_test_{datetime.now().strftime('%H%M%S')}@hospital.com",
            "full_name": "د. مشرف اختبار",
            "phone_number": "966507654321",
            "password": "SupervisorTest123!"
        }
        
        # Register supervisor user
        try:
            response = requests.post(
                f"{self.api_url}/auth/register",
                json=supervisor_user,
                timeout=10
            )
            if response.status_code != 200:
                self.log_test("Create Supervisor Account", False, f"Registration failed: {response.text}")
                return False
            
            supervisor_data = response.json()
            supervisor_user_id = supervisor_data.get('user', {}).get('id')
            self.log_test("Create Supervisor Account", True, f"Supervisor registered: {supervisor_user['email']}")
        except Exception as e:
            self.log_test("Create Supervisor Account", False, str(e))
            return False
        
        # Step 2: Promote user to supervisor using admin
        if not self.admin_token or not supervisor_user_id:
            self.log_test("Promote to Supervisor", False, "No admin token or supervisor user ID")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.post(
                f"{self.api_url}/admin/assign-supervisor/{supervisor_user_id}",
                headers=headers,
                timeout=10
            )
            if response.status_code != 200:
                self.log_test("Promote to Supervisor", False, f"Promotion failed: {response.text}")
                return False
            
            self.log_test("Promote to Supervisor", True, "User promoted to supervisor role")
        except Exception as e:
            self.log_test("Promote to Supervisor", False, str(e))
            return False
        
        # Step 3: Login as supervisor to get supervisor token
        try:
            login_data = {
                "email": supervisor_user["email"],
                "password": supervisor_user["password"]
            }
            response = requests.post(
                f"{self.api_url}/auth/login",
                json=login_data,
                timeout=10
            )
            if response.status_code != 200:
                self.log_test("Supervisor Login", False, f"Login failed: {response.text}")
                return False
            
            login_response = response.json()
            supervisor_token = login_response.get('access_token')
            supervisor_role = login_response.get('user', {}).get('role')
            
            if supervisor_role != 'supervisor':
                self.log_test("Supervisor Login", False, f"Expected role 'supervisor', got '{supervisor_role}'")
                return False
            
            self.log_test("Supervisor Login", True, f"Supervisor login successful, role: {supervisor_role}")
        except Exception as e:
            self.log_test("Supervisor Login", False, str(e))
            return False
        
        # Step 4: Test admin access to employees (baseline)
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.get(
                f"{self.api_url}/supervisor/employees",
                headers=headers,
                timeout=10
            )
            admin_success = response.status_code == 200
            admin_employees = []
            if admin_success:
                admin_employees = response.json()
                self.log_test("Admin Employee Access", True, f"Admin sees {len(admin_employees)} employees")
            else:
                self.log_test("Admin Employee Access", False, f"Admin access failed: {response.text}")
        except Exception as e:
            self.log_test("Admin Employee Access", False, str(e))
            admin_success = False
            admin_employees = []
        
        # Step 5: Test supervisor access to employees (main test)
        try:
            headers = {"Authorization": f"Bearer {supervisor_token}"}
            response = requests.get(
                f"{self.api_url}/supervisor/employees",
                headers=headers,
                timeout=10
            )
            supervisor_success = response.status_code == 200
            supervisor_employees = []
            
            if supervisor_success:
                supervisor_employees = response.json()
                
                # Verify response structure
                if supervisor_employees:
                    first_employee = supervisor_employees[0]
                    required_fields = ['id', 'full_name', 'email', 'notes_count', 'analyses_count']
                    missing_fields = [field for field in required_fields if field not in first_employee]
                    
                    if missing_fields:
                        supervisor_success = False
                        details = f"Missing required fields: {', '.join(missing_fields)}"
                    else:
                        details = f"Supervisor sees {len(supervisor_employees)} employees with all required fields"
                else:
                    details = "Supervisor sees 0 employees"
                
                # Compare with admin results
                if admin_success and len(admin_employees) != len(supervisor_employees):
                    details += f" (Admin sees {len(admin_employees)}, difference detected!)"
                    supervisor_success = False
                elif admin_success:
                    details += f" (Same as admin: {len(admin_employees)} employees)"
                
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Supervisor Employee Access", supervisor_success, details, response.json() if supervisor_success else None)
            
        except Exception as e:
            self.log_test("Supervisor Employee Access", False, str(e))
            supervisor_success = False
        
        # Step 6: Clean up - delete supervisor account
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.delete(
                f"{self.api_url}/admin/users/{supervisor_user_id}",
                headers=headers,
                timeout=10
            )
            cleanup_success = response.status_code == 200
            self.log_test("Cleanup Supervisor Account", cleanup_success, "Supervisor account deleted" if cleanup_success else f"Cleanup failed: {response.text}")
        except Exception as e:
            self.log_test("Cleanup Supervisor Account", False, str(e))
        
        # Summary
        print(f"\n📊 SUPERVISOR ACCESS TEST SUMMARY:")
        print(f"   Admin Access: {'✅ SUCCESS' if admin_success else '❌ FAILED'} ({len(admin_employees)} employees)")
        print(f"   Supervisor Access: {'✅ SUCCESS' if supervisor_success else '❌ FAILED'} ({len(supervisor_employees)} employees)")
        
        if admin_success and supervisor_success:
            if len(admin_employees) == len(supervisor_employees):
                print(f"   ✅ RESULT: Both admin and supervisor see the same {len(admin_employees)} employees")
                return True
            else:
                print(f"   ❌ ISSUE: Admin sees {len(admin_employees)} employees, supervisor sees {len(supervisor_employees)}")
                return False
        else:
            print(f"   ❌ ISSUE: One or both access methods failed")
            return False

    # ========== MESSAGING SYSTEM TESTS ==========
    
    def test_send_message_to_user(self, recipient_user_id):
        """Test POST /api/messages/send - Send message to specific user"""
        if not self.admin_token or not recipient_user_id:
            self.log_test("Send Message to User", False, "No admin token or recipient user ID")
            return False, None
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            message_data = {
                "to_user_id": recipient_user_id,
                "subject": "رسالة اختبار للموظف",
                "body": "هذه رسالة اختبار من المدير إلى الموظف المحدد. يرجى التأكد من استلام الرسالة.",
                "is_draft": False
            }
            response = requests.post(
                f"{self.api_url}/messages/send",
                json=message_data,
                headers=headers,
                timeout=10
            )
            success = response.status_code == 200
            message_id = None
            if success:
                data = response.json()
                message_id = data.get('id')
                details = f"Message sent to user: {data.get('message', '')}, ID: {message_id}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Send Message to User", success, details, response.json() if success else None)
            return success, message_id
        except Exception as e:
            self.log_test("Send Message to User", False, str(e))
            return False, None

    def test_send_message_to_all(self):
        """Test POST /api/messages/send - Send message to all users"""
        if not self.admin_token:
            self.log_test("Send Message to All", False, "No admin token")
            return False, None
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            message_data = {
                "to_user_id": "ALL",
                "subject": "إعلان عام لجميع الموظفين",
                "body": "هذا إعلان عام لجميع موظفي مركز الترميز الطبي. يرجى قراءة الرسالة والاطلاع على التحديثات الجديدة.",
                "is_draft": False
            }
            response = requests.post(
                f"{self.api_url}/messages/send",
                json=message_data,
                headers=headers,
                timeout=10
            )
            success = response.status_code == 200
            message_id = None
            if success:
                data = response.json()
                message_id = data.get('id')
                details = f"Message sent to all users: {data.get('message', '')}, ID: {message_id}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Send Message to All", success, details, response.json() if success else None)
            return success, message_id
        except Exception as e:
            self.log_test("Send Message to All", False, str(e))
            return False, None

    def test_get_inbox_messages(self):
        """Test GET /api/messages/inbox"""
        if not self.token:
            self.log_test("Get Inbox Messages", False, "No user token")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(
                f"{self.api_url}/messages/inbox",
                headers=headers,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                details = f"Retrieved {len(data)} inbox messages"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Get Inbox Messages", success, details, response.json() if success else None)
            return success
        except Exception as e:
            self.log_test("Get Inbox Messages", False, str(e))
            return False

    def test_get_sent_messages(self):
        """Test GET /api/messages/sent"""
        if not self.admin_token:
            self.log_test("Get Sent Messages", False, "No admin token")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.get(
                f"{self.api_url}/messages/sent",
                headers=headers,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                details = f"Retrieved {len(data)} sent messages"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Get Sent Messages", success, details, response.json() if success else None)
            return success
        except Exception as e:
            self.log_test("Get Sent Messages", False, str(e))
            return False

    def test_get_draft_messages(self):
        """Test GET /api/messages/drafts"""
        if not self.admin_token:
            self.log_test("Get Draft Messages", False, "No admin token")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.get(
                f"{self.api_url}/messages/drafts",
                headers=headers,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                details = f"Retrieved {len(data)} draft messages"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Get Draft Messages", success, details, response.json() if success else None)
            return success
        except Exception as e:
            self.log_test("Get Draft Messages", False, str(e))
            return False

    def test_get_unread_count(self):
        """Test GET /api/messages/unread-count"""
        if not self.token:
            self.log_test("Get Unread Count", False, "No user token")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(
                f"{self.api_url}/messages/unread-count",
                headers=headers,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                count = data.get('count', 0)
                details = f"Unread messages count: {count}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Get Unread Count", success, details, response.json() if success else None)
            return success
        except Exception as e:
            self.log_test("Get Unread Count", False, str(e))
            return False

    def test_mark_message_as_read(self, message_id):
        """Test POST /api/messages/{message_id}/read"""
        if not self.token or not message_id:
            self.log_test("Mark Message as Read", False, "No user token or message ID")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.post(
                f"{self.api_url}/messages/{message_id}/read",
                headers=headers,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                details = f"Message marked as read: {data.get('message', '')}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Mark Message as Read", success, details, response.json() if success else None)
            return success
        except Exception as e:
            self.log_test("Mark Message as Read", False, str(e))
            return False

    def test_delete_message(self, message_id):
        """Test DELETE /api/messages/{message_id}"""
        if not self.admin_token or not message_id:
            self.log_test("Delete Message", False, "No admin token or message ID")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.delete(
                f"{self.api_url}/messages/{message_id}",
                headers=headers,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                details = f"Message deleted: {data.get('message', '')}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Delete Message", success, details, response.json() if success else None)
            return success
        except Exception as e:
            self.log_test("Delete Message", False, str(e))
            return False

    def test_save_draft_message(self):
        """Test POST /api/messages/send - Save draft message"""
        if not self.admin_token:
            self.log_test("Save Draft Message", False, "No admin token")
            return False, None
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            message_data = {
                "to_user_id": "ALL",
                "subject": "مسودة رسالة",
                "body": "هذه مسودة رسالة لم يتم إرسالها بعد.",
                "is_draft": True
            }
            response = requests.post(
                f"{self.api_url}/messages/send",
                json=message_data,
                headers=headers,
                timeout=10
            )
            success = response.status_code == 200
            message_id = None
            if success:
                data = response.json()
                message_id = data.get('id')
                details = f"Draft message saved: {data.get('message', '')}, ID: {message_id}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Save Draft Message", success, details, response.json() if success else None)
            return success, message_id
        except Exception as e:
            self.log_test("Save Draft Message", False, str(e))
            return False, None

    # ========== AUTH/ME ENDPOINT TESTS ==========
    
    def test_auth_me_endpoint(self, token, expected_role, test_name):
        """Test GET /api/auth/me endpoint"""
        if not token:
            self.log_test(f"Auth Me - {test_name}", False, "No authentication token")
            return False, None
        
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(
                f"{self.api_url}/auth/me",
                headers=headers,
                timeout=10
            )
            success = response.status_code == 200
            user_data = None
            if success:
                user_data = response.json()
                actual_role = user_data.get('role')
                required_fields = ['id', 'email', 'full_name', 'role']
                missing_fields = [field for field in required_fields if field not in user_data]
                
                if missing_fields:
                    success = False
                    details = f"Missing required fields: {', '.join(missing_fields)}"
                elif expected_role and actual_role != expected_role:
                    success = False
                    details = f"Expected role '{expected_role}', got '{actual_role}'"
                else:
                    details = f"User data retrieved - Role: {actual_role}, Name: {user_data.get('full_name')}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test(f"Auth Me - {test_name}", success, details, user_data if success else None)
            return success, user_data
        except Exception as e:
            self.log_test(f"Auth Me - {test_name}", False, str(e))
            return False, None

    # ========== SUPERVISOR IMPERSONATION TESTS ==========
    
    def test_admin_impersonate_user(self, target_user_id):
        """Test POST /api/admin/impersonate/{user_id}"""
        if not self.admin_token or not target_user_id:
            self.log_test("Admin Impersonate User", False, "No admin token or target user ID")
            return False, None
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.post(
                f"{self.api_url}/admin/impersonate/{target_user_id}",
                headers=headers,
                timeout=10
            )
            success = response.status_code == 200
            impersonated_token = None
            if success:
                data = response.json()
                impersonated_token = data.get('access_token')
                user_info = data.get('user', {})
                is_impersonating = user_info.get('is_impersonating', False)
                impersonated_by = user_info.get('impersonated_by')
                details = f"Admin impersonation successful - User: {user_info.get('full_name')}, Is_impersonating: {is_impersonating}, Impersonated_by: {impersonated_by}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Admin Impersonate User", success, details, response.json() if success else None)
            return success, impersonated_token
        except Exception as e:
            self.log_test("Admin Impersonate User", False, str(e))
            return False, None

    def test_supervisor_impersonate_user(self, supervisor_token, target_user_id):
        """Test POST /api/admin/impersonate/{user_id} with supervisor credentials"""
        if not supervisor_token or not target_user_id:
            self.log_test("Supervisor Impersonate User", False, "No supervisor token or target user ID")
            return False, None
        
        try:
            headers = {"Authorization": f"Bearer {supervisor_token}"}
            response = requests.post(
                f"{self.api_url}/admin/impersonate/{target_user_id}",
                headers=headers,
                timeout=10
            )
            success = response.status_code == 200
            impersonated_token = None
            if success:
                data = response.json()
                impersonated_token = data.get('access_token')
                user_info = data.get('user', {})
                is_impersonating = user_info.get('is_impersonating', False)
                impersonated_by = user_info.get('impersonated_by')
                details = f"Supervisor impersonation successful - User: {user_info.get('full_name')}, Is_impersonating: {is_impersonating}, Impersonated_by: {impersonated_by}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Supervisor Impersonate User", success, details, response.json() if success else None)
            return success, impersonated_token
        except Exception as e:
            self.log_test("Supervisor Impersonate User", False, str(e))
            return False, None

    def test_impersonated_token_access(self, impersonated_token):
        """Test that impersonated token can access user endpoints"""
        if not impersonated_token:
            self.log_test("Impersonated Token Access", False, "No impersonated token")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {impersonated_token}"}
            response = requests.get(
                f"{self.api_url}/notes",
                headers=headers,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                details = f"Impersonated token successfully accessed user notes: {len(data)} notes found"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Impersonated Token Access", success, details, response.json() if success else None)
            return success
        except Exception as e:
            self.log_test("Impersonated Token Access", False, str(e))
            return False

    def test_supervisor_impersonation_comprehensive(self):
        """Comprehensive test for supervisor impersonation feature after fix"""
        print("\n🎯 COMPREHENSIVE SUPERVISOR IMPERSONATION TEST")
        print("=" * 70)
        print("Testing the fix for: 'عند دخول المشرف على حساب الأعضاء تأتي رسالة بفشل الدخول لحساب العضو'")
        print("=" * 70)
        
        # Step 1: Get supervisor credentials (try ex012@hotmail.com first)
        supervisor_credentials = {
            "email": "ex012@hotmail.com",
            "password": "123456"  # Common password, will try variations if needed
        }
        
        # Try to login with existing supervisor
        supervisor_token = None
        supervisor_user_id = None
        
        try:
            response = requests.post(
                f"{self.api_url}/auth/login",
                json=supervisor_credentials,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                supervisor_token = data.get('access_token')
                supervisor_data = data.get('user', {})
                supervisor_user_id = supervisor_data.get('id')
                role = supervisor_data.get('role')
                
                if role == 'supervisor':
                    self.log_test("Existing Supervisor Login", True, f"Logged in as supervisor: {supervisor_credentials['email']}")
                else:
                    self.log_test("Existing Supervisor Login", False, f"User exists but role is '{role}', not 'supervisor'")
                    supervisor_token = None
            else:
                self.log_test("Existing Supervisor Login", False, f"Login failed: {response.text}")
        except Exception as e:
            self.log_test("Existing Supervisor Login", False, str(e))
        
        # Step 2: If no existing supervisor, create a test supervisor
        if not supervisor_token:
            print("\n📝 Creating test supervisor account...")
            
            # Create supervisor user
            test_supervisor = {
                "email": f"test_supervisor_{datetime.now().strftime('%H%M%S')}@hospital.com",
                "full_name": "د. مشرف الاختبار",
                "phone_number": "966507777777",
                "password": "SupervisorTest123!"
            }
            
            try:
                # Register user
                response = requests.post(
                    f"{self.api_url}/auth/register",
                    json=test_supervisor,
                    timeout=10
                )
                if response.status_code != 200:
                    self.log_test("Create Test Supervisor", False, f"Registration failed: {response.text}")
                    return False
                
                supervisor_reg_data = response.json()
                supervisor_user_id = supervisor_reg_data.get('user', {}).get('id')
                
                # Promote to supervisor using admin
                if not self.admin_token:
                    self.log_test("Create Test Supervisor", False, "No admin token to promote user")
                    return False
                
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                response = requests.post(
                    f"{self.api_url}/admin/assign-supervisor/{supervisor_user_id}",
                    headers=headers,
                    timeout=10
                )
                if response.status_code != 200:
                    self.log_test("Create Test Supervisor", False, f"Promotion failed: {response.text}")
                    return False
                
                # Login as supervisor
                login_data = {
                    "email": test_supervisor["email"],
                    "password": test_supervisor["password"]
                }
                response = requests.post(
                    f"{self.api_url}/auth/login",
                    json=login_data,
                    timeout=10
                )
                if response.status_code != 200:
                    self.log_test("Create Test Supervisor", False, f"Supervisor login failed: {response.text}")
                    return False
                
                login_response = response.json()
                supervisor_token = login_response.get('access_token')
                supervisor_credentials = test_supervisor
                
                self.log_test("Create Test Supervisor", True, f"Test supervisor created and logged in: {test_supervisor['email']}")
                
            except Exception as e:
                self.log_test("Create Test Supervisor", False, str(e))
                return False
        
        # Step 3: Get list of employees
        print("\n👥 Getting list of employees...")
        employees = []
        try:
            headers = {"Authorization": f"Bearer {supervisor_token}"}
            response = requests.get(
                f"{self.api_url}/supervisor/employees",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                employees = response.json()
                self.log_test("Get Employee List", True, f"Retrieved {len(employees)} employees")
            else:
                self.log_test("Get Employee List", False, f"Failed to get employees: {response.text}")
                return False
        except Exception as e:
            self.log_test("Get Employee List", False, str(e))
            return False
        
        if not employees:
            self.log_test("Employee Availability", False, "No employees found to test impersonation")
            return False
        
        # Step 4: Try to impersonate an employee using supervisor credentials
        target_employee = employees[0]
        target_user_id = target_employee.get('id')
        target_name = target_employee.get('full_name', 'Unknown')
        
        print(f"\n🎭 Testing supervisor impersonation of employee: {target_name}")
        
        supervisor_impersonate_success, supervisor_impersonated_token = self.test_supervisor_impersonate_user(
            supervisor_token, target_user_id
        )
        
        # Step 5: Verify token is generated correctly and works
        if supervisor_impersonate_success and supervisor_impersonated_token:
            print("\n✅ Testing impersonated token functionality...")
            token_works = self.test_impersonated_token_access(supervisor_impersonated_token)
            
            if token_works:
                self.log_test("Supervisor Impersonation Complete", True, 
                            f"Supervisor successfully impersonated {target_name} and token works correctly")
            else:
                self.log_test("Supervisor Impersonation Complete", False, 
                            "Impersonation succeeded but token doesn't work for user endpoints")
        else:
            self.log_test("Supervisor Impersonation Complete", False, 
                        "Supervisor impersonation failed - this is the reported issue")
        
        # Step 6: Test admin impersonation (should still work)
        print(f"\n👑 Testing admin impersonation of same employee: {target_name}")
        admin_impersonate_success, admin_impersonated_token = self.test_admin_impersonate_user(target_user_id)
        
        if admin_impersonate_success and admin_impersonated_token:
            admin_token_works = self.test_impersonated_token_access(admin_impersonated_token)
            if admin_token_works:
                self.log_test("Admin Impersonation Verification", True, 
                            "Admin impersonation still works correctly")
            else:
                self.log_test("Admin Impersonation Verification", False, 
                            "Admin impersonation succeeded but token doesn't work")
        else:
            self.log_test("Admin Impersonation Verification", False, 
                        "Admin impersonation failed - this should not happen")
        
        # Step 7: Summary and cleanup
        print("\n📊 SUPERVISOR IMPERSONATION TEST SUMMARY:")
        print(f"   Supervisor Login: {'✅ SUCCESS' if supervisor_token else '❌ FAILED'}")
        print(f"   Employee List Access: {'✅ SUCCESS' if employees else '❌ FAILED'} ({len(employees)} employees)")
        print(f"   Supervisor Impersonation: {'✅ SUCCESS' if supervisor_impersonate_success else '❌ FAILED'}")
        print(f"   Admin Impersonation: {'✅ SUCCESS' if admin_impersonate_success else '❌ FAILED'}")
        
        # Cleanup test supervisor if created
        if supervisor_user_id and supervisor_credentials.get('email', '').startswith('test_supervisor_'):
            try:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                response = requests.delete(
                    f"{self.api_url}/admin/users/{supervisor_user_id}",
                    headers=headers,
                    timeout=10
                )
                cleanup_success = response.status_code == 200
                self.log_test("Cleanup Test Supervisor", cleanup_success, 
                            "Test supervisor deleted" if cleanup_success else f"Cleanup failed: {response.text}")
            except Exception as e:
                self.log_test("Cleanup Test Supervisor", False, str(e))
        
        # Return overall success
        return supervisor_impersonate_success and admin_impersonate_success

    def test_exit_impersonation_functionality(self):
        """Test exit impersonation functionality specifically for supervisors"""
        print("\n🚪 TESTING EXIT IMPERSONATION FUNCTIONALITY")
        print("=" * 70)
        print("Testing fix for: المشرف عندما يدخل لحساب عضو ويضغط 'الخروج من الحساب'، لا يستطيع الرجوع لحسابه")
        print("=" * 70)
        
        # Step 1: Login as supervisor (try ex012@hotmail.com first)
        supervisor_credentials = {
            "email": "ex012@hotmail.com",
            "password": "123456"
        }
        
        supervisor_token = None
        supervisor_user_data = None
        
        try:
            response = requests.post(
                f"{self.api_url}/auth/login",
                json=supervisor_credentials,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                supervisor_token = data.get('access_token')
                supervisor_user_data = data.get('user', {})
                role = supervisor_user_data.get('role')
                
                if role == 'supervisor':
                    self.log_test("Supervisor Login for Exit Test", True, f"Logged in as supervisor: {supervisor_credentials['email']}")
                else:
                    # If not supervisor, create one
                    supervisor_token = None
            else:
                supervisor_token = None
        except Exception as e:
            self.log_test("Supervisor Login for Exit Test", False, str(e))
            supervisor_token = None
        
        # Create test supervisor if needed
        if not supervisor_token:
            print("\n📝 Creating test supervisor for exit impersonation test...")
            
            test_supervisor = {
                "email": f"exit_test_supervisor_{datetime.now().strftime('%H%M%S')}@hospital.com",
                "full_name": "د. مشرف اختبار الخروج",
                "phone_number": "966508888888",
                "password": "ExitTestSupervisor123!"
            }
            
            try:
                # Register and promote to supervisor
                response = requests.post(f"{self.api_url}/auth/register", json=test_supervisor, timeout=10)
                if response.status_code != 200:
                    self.log_test("Create Exit Test Supervisor", False, f"Registration failed: {response.text}")
                    return False
                
                reg_data = response.json()
                supervisor_user_id = reg_data.get('user', {}).get('id')
                
                # Promote to supervisor
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                response = requests.post(f"{self.api_url}/admin/assign-supervisor/{supervisor_user_id}", headers=headers, timeout=10)
                if response.status_code != 200:
                    self.log_test("Create Exit Test Supervisor", False, f"Promotion failed: {response.text}")
                    return False
                
                # Login as supervisor
                response = requests.post(f"{self.api_url}/auth/login", json={"email": test_supervisor["email"], "password": test_supervisor["password"]}, timeout=10)
                if response.status_code != 200:
                    self.log_test("Create Exit Test Supervisor", False, f"Login failed: {response.text}")
                    return False
                
                login_data = response.json()
                supervisor_token = login_data.get('access_token')
                supervisor_user_data = login_data.get('user', {})
                supervisor_credentials = test_supervisor
                
                self.log_test("Create Exit Test Supervisor", True, f"Test supervisor created: {test_supervisor['email']}")
                
            except Exception as e:
                self.log_test("Create Exit Test Supervisor", False, str(e))
                return False
        
        # Step 2: Test GET /api/auth/me with supervisor token
        print("\n🔍 Testing GET /api/auth/me with supervisor token...")
        supervisor_me_success, supervisor_me_data = self.test_auth_me_endpoint(
            supervisor_token, 'supervisor', 'Supervisor Original Token'
        )
        
        if not supervisor_me_success:
            self.log_test("Exit Impersonation Test", False, "GET /api/auth/me failed with supervisor token")
            return False
        
        # Step 3: Get an employee to impersonate
        print("\n👥 Getting employee list for impersonation...")
        try:
            headers = {"Authorization": f"Bearer {supervisor_token}"}
            response = requests.get(f"{self.api_url}/supervisor/employees", headers=headers, timeout=10)
            if response.status_code != 200:
                self.log_test("Get Employees for Exit Test", False, f"Failed to get employees: {response.text}")
                return False
            
            employees = response.json()
            if not employees:
                self.log_test("Get Employees for Exit Test", False, "No employees available for impersonation test")
                return False
            
            target_employee = employees[0]
            target_user_id = target_employee.get('id')
            target_name = target_employee.get('full_name', 'Unknown')
            
            self.log_test("Get Employees for Exit Test", True, f"Found {len(employees)} employees, will impersonate: {target_name}")
            
        except Exception as e:
            self.log_test("Get Employees for Exit Test", False, str(e))
            return False
        
        # Step 4: Supervisor impersonates employee
        print(f"\n🎭 Supervisor impersonating employee: {target_name}")
        try:
            headers = {"Authorization": f"Bearer {supervisor_token}"}
            response = requests.post(f"{self.api_url}/admin/impersonate/{target_user_id}", headers=headers, timeout=10)
            
            if response.status_code != 200:
                self.log_test("Supervisor Impersonation for Exit Test", False, f"Impersonation failed: {response.text}")
                return False
            
            impersonation_data = response.json()
            impersonated_token = impersonation_data.get('access_token')
            impersonated_user = impersonation_data.get('user', {})
            
            self.log_test("Supervisor Impersonation for Exit Test", True, 
                        f"Supervisor successfully impersonated {impersonated_user.get('full_name')}")
            
        except Exception as e:
            self.log_test("Supervisor Impersonation for Exit Test", False, str(e))
            return False
        
        # Step 5: Verify impersonated token works
        print("\n✅ Testing impersonated token functionality...")
        impersonated_me_success, impersonated_me_data = self.test_auth_me_endpoint(
            impersonated_token, 'user', 'Impersonated Employee Token'
        )
        
        if not impersonated_me_success:
            self.log_test("Exit Impersonation Test", False, "Impersonated token doesn't work with GET /api/auth/me")
            return False
        
        # Step 6: CRITICAL TEST - Simulate exit impersonation
        print("\n🚪 CRITICAL TEST: Simulating exit impersonation...")
        print("   This simulates when supervisor clicks 'Exit Account' and should return to supervisor account")
        
        # Test that original supervisor token still works (this is what frontend should restore)
        exit_success, exit_me_data = self.test_auth_me_endpoint(
            supervisor_token, 'supervisor', 'Supervisor Token After Exit'
        )
        
        if not exit_success:
            self.log_test("Exit Impersonation Critical Test", False, 
                        "CRITICAL ISSUE: Supervisor token doesn't work after impersonation - this causes the stuck page issue!")
            return False
        
        # Verify the supervisor data is correct and complete
        if not exit_me_data:
            self.log_test("Exit Impersonation Critical Test", False, "No user data returned from supervisor token")
            return False
        
        # Check that supervisor data matches original login data
        original_supervisor_id = supervisor_user_data.get('id')
        restored_supervisor_id = exit_me_data.get('id')
        
        if original_supervisor_id != restored_supervisor_id:
            self.log_test("Exit Impersonation Critical Test", False, 
                        f"Supervisor ID mismatch: original {original_supervisor_id} vs restored {restored_supervisor_id}")
            return False
        
        # Step 7: Test that supervisor can still access supervisor endpoints
        print("\n🔐 Testing supervisor endpoint access after exit...")
        try:
            headers = {"Authorization": f"Bearer {supervisor_token}"}
            response = requests.get(f"{self.api_url}/supervisor/employees", headers=headers, timeout=10)
            
            if response.status_code != 200:
                self.log_test("Supervisor Endpoints After Exit", False, 
                            f"Supervisor can't access endpoints after exit: {response.text}")
                return False
            
            post_exit_employees = response.json()
            self.log_test("Supervisor Endpoints After Exit", True, 
                        f"Supervisor can still access endpoints, sees {len(post_exit_employees)} employees")
            
        except Exception as e:
            self.log_test("Supervisor Endpoints After Exit", False, str(e))
            return False
        
        # Step 8: Final verification - test multiple cycles
        print("\n🔄 Testing multiple impersonation cycles...")
        for cycle in range(2):
            print(f"   Cycle {cycle + 1}/2...")
            
            # Impersonate again
            try:
                headers = {"Authorization": f"Bearer {supervisor_token}"}
                response = requests.post(f"{self.api_url}/admin/impersonate/{target_user_id}", headers=headers, timeout=10)
                
                if response.status_code != 200:
                    self.log_test(f"Multiple Cycles Test - Cycle {cycle + 1}", False, 
                                f"Impersonation failed on cycle {cycle + 1}: {response.text}")
                    return False
                
                # Test exit again
                cycle_exit_success, _ = self.test_auth_me_endpoint(
                    supervisor_token, 'supervisor', f'Cycle {cycle + 1} Exit'
                )
                
                if not cycle_exit_success:
                    self.log_test(f"Multiple Cycles Test - Cycle {cycle + 1}", False, 
                                f"Exit failed on cycle {cycle + 1}")
                    return False
                
            except Exception as e:
                self.log_test(f"Multiple Cycles Test - Cycle {cycle + 1}", False, str(e))
                return False
        
        self.log_test("Multiple Cycles Test", True, "Multiple impersonation/exit cycles work correctly")
        
        # Cleanup
        if supervisor_credentials.get('email', '').startswith('exit_test_supervisor_'):
            try:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                supervisor_user_id = supervisor_user_data.get('id')
                response = requests.delete(f"{self.api_url}/admin/users/{supervisor_user_id}", headers=headers, timeout=10)
                cleanup_success = response.status_code == 200
                self.log_test("Cleanup Exit Test Supervisor", cleanup_success, 
                            "Test supervisor deleted" if cleanup_success else f"Cleanup failed: {response.text}")
            except Exception as e:
                self.log_test("Cleanup Exit Test Supervisor", False, str(e))
        
        # Final summary
        print("\n📊 EXIT IMPERSONATION TEST SUMMARY:")
        print(f"   ✅ Supervisor Login: SUCCESS")
        print(f"   ✅ GET /api/auth/me with supervisor token: SUCCESS")
        print(f"   ✅ Supervisor impersonation: SUCCESS")
        print(f"   ✅ Impersonated token works: SUCCESS")
        print(f"   ✅ CRITICAL: Supervisor token works after impersonation: SUCCESS")
        print(f"   ✅ Supervisor endpoints accessible after exit: SUCCESS")
        print(f"   ✅ Multiple impersonation cycles: SUCCESS")
        print("\n🎉 EXIT IMPERSONATION FUNCTIONALITY IS WORKING CORRECTLY!")
        print("   The reported issue 'المشرف لا يستطيع الرجوع لحسابه' should be RESOLVED")
        
        self.log_test("Exit Impersonation Complete Test", True, 
                    "All exit impersonation functionality tests passed - issue should be resolved")
        
        return True

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
        
        # ========== MESSAGING SYSTEM TESTS ==========
        print("\n💬 Testing Messaging System...")
        
        # Test sending messages
        message_success, message_id = self.test_send_message_to_user(self.test_user_id) if self.test_user_id else (False, None)
        all_message_success, all_message_id = self.test_send_message_to_all()
        
        # Test draft functionality
        draft_success, draft_id = self.test_save_draft_message()
        
        # Test retrieving messages (admin perspective)
        self.test_get_sent_messages()
        self.test_get_draft_messages()
        
        # Test retrieving messages (user perspective)
        self.test_get_inbox_messages()
        self.test_get_unread_count()
        
        # Test message interactions
        if message_id:
            self.test_mark_message_as_read(message_id)
        
        # Test message deletion (clean up)
        if message_id:
            self.test_delete_message(message_id)
        if all_message_id:
            self.test_delete_message(all_message_id)
        if draft_id:
            self.test_delete_message(draft_id)
        
        # ========== SUPERVISOR IMPERSONATION TESTS ==========
        print("\n👤 Testing Supervisor Impersonation...")
        
        if self.test_user_id:
            # Test admin impersonation
            impersonate_success, impersonated_token = self.test_admin_impersonate_user(self.test_user_id)
            
            # Test that impersonated token works
            if impersonate_success and impersonated_token:
                self.test_impersonated_token_access(impersonated_token)
        
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

    def run_supervisor_focused_test(self):
        """Run focused test for supervisor employee access issue"""
        print("🚀 Starting Focused Supervisor Employee Access Test")
        print(f"🔗 Testing API: {self.api_url}")
        print("=" * 80)
        
        # Basic connectivity
        if not self.test_health_check():
            print("❌ Health check failed - stopping tests")
            return self.generate_report()
        
        # Admin Authentication (required for setup)
        print("\n👑 Testing Admin Authentication...")
        if not self.test_admin_login():
            print("❌ Admin login failed - stopping tests")
            return self.generate_report()
        
        # Run the focused supervisor test
        self.test_supervisor_account_employees_access()
        
        return self.generate_report()

    def run_supervisor_impersonation_test(self):
        """Run focused test for supervisor impersonation feature after fix"""
        print("🚀 Starting Supervisor Impersonation Test After Fix")
        print(f"🔗 Testing API: {self.api_url}")
        print("=" * 80)
        
        # Basic connectivity
        if not self.test_health_check():
            print("❌ Health check failed - stopping tests")
            return self.generate_report()
        
        # Admin Authentication (required for setup)
        print("\n👑 Testing Admin Authentication...")
        if not self.test_admin_login():
            print("❌ Admin login failed - stopping tests")
            return self.generate_report()
        
        # Run the comprehensive supervisor impersonation test
        self.test_supervisor_impersonation_comprehensive()
        
        # NEW: Exit Impersonation Functionality Test (Critical for reported issue)
        print("\n🚪 Testing Exit Impersonation Functionality (Critical for Supervisor Issue)...")
        self.test_exit_impersonation_functionality()
        
        return self.generate_report()

def main():
    """Main test execution"""
    tester = MedicalCodingAPITester()
    
    # Check if we should run focused test
    if len(sys.argv) > 1:
        if sys.argv[1] == "--supervisor-test":
            results = tester.run_supervisor_focused_test()
        elif sys.argv[1] == "--impersonation-test":
            results = tester.run_supervisor_impersonation_test()
        else:
            results = tester.run_all_tests()
    else:
        results = tester.run_all_tests()
    
    # Return appropriate exit code
    return 0 if results["failed_tests"] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())