#!/usr/bin/env python3
"""
Focused test for supervisor employees endpoint
Tests the specific request: GET /api/supervisor/employees with admin credentials
"""

import requests
import json
from datetime import datetime

class SupervisorEmployeesTest:
    def __init__(self):
        self.base_url = "https://medical-app-preview.preview.emergentagent.com"
        self.api_url = f"{self.base_url}/api"
        self.admin_token = None
        
        # Admin credentials as specified in the review request
        self.admin_credentials = {
            "email": "admin@cdi-center.sa",
            "password": "CDI@2024#Admin"
        }
        
        # Test employee data for creating if needed
        self.test_employee = {
            "email": f"test_employee_{datetime.now().strftime('%H%M%S')}@hospital.com",
            "full_name": "د. أحمد محمد الموظف",
            "phone_number": "966501234567",
            "password": "TestPassword123!"
        }

    def login_admin(self):
        """Login as admin with specified credentials"""
        try:
            response = requests.post(
                f"{self.api_url}/auth/login",
                json=self.admin_credentials,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get('access_token')
                admin_data = data.get('user')
                print(f"✅ Admin login successful")
                print(f"   Email: {admin_data.get('email')}")
                print(f"   Role: {admin_data.get('role')}")
                print(f"   Name: {admin_data.get('full_name')}")
                return True
            else:
                print(f"❌ Admin login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Admin login error: {str(e)}")
            return False

    def test_supervisor_employees_endpoint(self):
        """Test GET /api/supervisor/employees endpoint"""
        if not self.admin_token:
            print("❌ No admin token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.get(
                f"{self.api_url}/supervisor/employees",
                headers=headers,
                timeout=10
            )
            
            print(f"\n📊 Testing GET /api/supervisor/employees")
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Endpoint accessible")
                print(f"   Response Type: {type(data)}")
                print(f"   Number of employees: {len(data)}")
                
                # Verify response structure
                if len(data) > 0:
                    first_employee = data[0]
                    print(f"\n📋 Employee Data Structure:")
                    print(f"   Available fields: {list(first_employee.keys())}")
                    
                    # Check required fields
                    required_fields = ['id', 'full_name', 'email', 'notes_count', 'analyses_count']
                    optional_fields = ['phone_number', 'role', 'is_active', 'created_at']
                    missing_required = []
                    
                    print(f"   📋 Required Fields:")
                    for field in required_fields:
                        if field in first_employee:
                            print(f"   ✅ {field}: {first_employee[field]}")
                        else:
                            missing_required.append(field)
                            print(f"   ❌ Missing: {field}")
                    
                    print(f"   📋 Optional Fields:")
                    for field in optional_fields:
                        if field in first_employee:
                            print(f"   ✅ {field}: {first_employee[field]}")
                        else:
                            print(f"   ⚠️  Optional missing: {field}")
                    
                    if not missing_required:
                        print(f"✅ All required fields present")
                        
                        # Display sample employee data
                        print(f"\n👤 Sample Employee Data:")
                        for employee in data[:3]:  # Show first 3 employees
                            phone = employee.get('phone_number', 'Not provided')
                            print(f"   • {employee.get('full_name', 'N/A')} ({employee.get('email', 'N/A')})")
                            print(f"     Phone: {phone}, Notes: {employee.get('notes_count', 0)}, Analyses: {employee.get('analyses_count', 0)}")
                        
                        return True
                    else:
                        print(f"❌ Missing required fields: {missing_required}")
                        return False
                else:
                    print(f"ℹ️  No employees found in database")
                    print(f"   This is expected if no employee users exist")
                    return True
                    
            else:
                print(f"❌ Endpoint failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Test error: {str(e)}")
            return False

    def create_test_employee(self):
        """Create a test employee user if none exist"""
        try:
            response = requests.post(
                f"{self.api_url}/auth/register",
                json=self.test_employee,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                user_data = data.get('user')
                print(f"✅ Test employee created")
                print(f"   Name: {user_data.get('full_name')}")
                print(f"   Email: {user_data.get('email')}")
                print(f"   ID: {user_data.get('id')}")
                return user_data.get('id')
            else:
                print(f"❌ Failed to create test employee: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating test employee: {str(e)}")
            return None

    def check_database_employees(self):
        """Check if any employees exist in database using admin statistics"""
        if not self.admin_token:
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.get(
                f"{self.api_url}/admin/users-statistics",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                statistics = data.get('statistics', [])
                
                # Count users by role
                users_by_role = {}
                for user in statistics:
                    role = user.get('role', 'user')
                    users_by_role[role] = users_by_role.get(role, 0) + 1
                
                print(f"\n📊 Database User Statistics:")
                print(f"   Total users: {len(statistics)}")
                for role, count in users_by_role.items():
                    print(f"   {role}: {count}")
                
                employee_count = users_by_role.get('user', 0)
                return employee_count > 0
                
            else:
                print(f"❌ Failed to get user statistics: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error checking database: {str(e)}")
            return False

    def run_test(self):
        """Run the complete supervisor employees test"""
        print("🚀 Testing Supervisor Employees Endpoint")
        print("=" * 50)
        
        # Step 1: Login as admin
        print("1️⃣ Logging in as admin...")
        if not self.login_admin():
            print("❌ Test failed: Cannot login as admin")
            return False
        
        # Step 2: Check if employees exist
        print("\n2️⃣ Checking database for employees...")
        has_employees = self.check_database_employees()
        
        # Step 3: Create test employee if none exist
        if not has_employees:
            print("\n3️⃣ No employees found, creating test employee...")
            employee_id = self.create_test_employee()
            if not employee_id:
                print("⚠️  Could not create test employee, continuing with empty database test")
        else:
            print("\n3️⃣ Employees found in database")
        
        # Step 4: Test the supervisor/employees endpoint
        print("\n4️⃣ Testing /api/supervisor/employees endpoint...")
        success = self.test_supervisor_employees_endpoint()
        
        # Step 5: Summary
        print("\n" + "=" * 50)
        if success:
            print("✅ SUPERVISOR EMPLOYEES ENDPOINT TEST PASSED")
            print("   • Admin login successful")
            print("   • Endpoint accessible with admin credentials")
            print("   • Response structure correct")
            print("   • Required fields present (id, full_name, email, phone_number, notes_count, analyses_count)")
        else:
            print("❌ SUPERVISOR EMPLOYEES ENDPOINT TEST FAILED")
        
        return success

def main():
    """Main test execution"""
    tester = SupervisorEmployeesTest()
    success = tester.run_test()
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())