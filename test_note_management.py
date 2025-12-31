#!/usr/bin/env python3
"""
Focused test for Note Management endpoints (PUT, DELETE, GET)
"""

import requests
import sys
import json
from datetime import datetime

class NoteManagementTester:
    def __init__(self, base_url="https://clinical-doc.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.admin_token = None
        
        # Admin credentials
        self.admin_credentials = {
            "email": "admin@cdi-center.sa",
            "password": "CDI@2024#Admin"
        }
        
        # Test user data
        self.test_user = {
            "email": f"note_test_{datetime.now().strftime('%H%M%S')}@hospital.com",
            "full_name": "د. اختبار إدارة الملاحظات",
            "phone_number": "966501111111",
            "password": "NoteTest123!"
        }

    def login_admin(self):
        """Login as admin"""
        try:
            response = requests.post(
                f"{self.api_url}/auth/login",
                json=self.admin_credentials,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get('access_token')
                print("✅ Admin login successful")
                return True
            else:
                print(f"❌ Admin login failed: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Admin login error: {str(e)}")
            return False

    def register_and_login_user(self):
        """Register and login test user"""
        try:
            # Register
            response = requests.post(
                f"{self.api_url}/auth/register",
                json=self.test_user,
                timeout=10
            )
            if response.status_code != 200:
                print(f"❌ User registration failed: {response.text}")
                return False
            
            # Login
            login_data = {
                "email": self.test_user["email"],
                "password": self.test_user["password"]
            }
            response = requests.post(
                f"{self.api_url}/auth/login",
                json=login_data,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                self.user_id = data.get('user', {}).get('id')
                print("✅ User registration and login successful")
                return True
            else:
                print(f"❌ User login failed: {response.text}")
                return False
        except Exception as e:
            print(f"❌ User registration/login error: {str(e)}")
            return False

    def create_test_note(self):
        """Create a test note"""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            note_data = {
                "title": "ملاحظة اختبار إدارة الملاحظات",
                "doctor_notes": [
                    {
                        "text": "هذه ملاحظة اختبار للتحقق من وظائف إدارة الملاحظات",
                        "specialty": "internal_medicine"
                    }
                ]
            }
            
            response = requests.post(
                f"{self.api_url}/notes",
                json=note_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                note_id = data.get('id')
                print(f"✅ Test note created: {note_id}")
                return note_id
            else:
                print(f"❌ Note creation failed: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Note creation error: {str(e)}")
            return None

    def test_get_note(self, note_id):
        """Test GET /api/notes/{note_id}"""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(
                f"{self.api_url}/notes/{note_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['id', 'user_id', 'title', 'doctor_notes', 'created_at']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    print(f"❌ GET note missing fields: {', '.join(missing_fields)}")
                    return False
                else:
                    print(f"✅ GET note successful: {data.get('title', '')}")
                    return True
            else:
                print(f"❌ GET note failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ GET note error: {str(e)}")
            return False

    def test_update_note(self, note_id):
        """Test PUT /api/notes/{note_id}"""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            updated_data = {
                "title": "ملاحظة محدثة - اختبار التحديث",
                "doctor_notes": [
                    {
                        "text": "هذه ملاحظة محدثة للتحقق من وظيفة التحديث",
                        "specialty": "internal_medicine"
                    },
                    {
                        "text": "ملاحظة إضافية بعد التحديث",
                        "specialty": "cardiology"
                    }
                ]
            }
            
            response = requests.put(
                f"{self.api_url}/notes/{note_id}",
                json=updated_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                title_updated = data.get('title') == updated_data['title']
                doctor_notes_count = len(data.get('doctor_notes', []))
                has_updated_at = 'updated_at' in data
                
                print(f"📊 Update results:")
                print(f"   Title updated: {title_updated}")
                print(f"   Doctor notes count: {doctor_notes_count}")
                print(f"   Has updated_at field: {has_updated_at}")
                print(f"   Updated_at value: {data.get('updated_at', 'None')}")
                
                if title_updated and doctor_notes_count == 2 and has_updated_at:
                    print("✅ PUT note successful")
                    return True
                else:
                    print("❌ PUT note validation failed")
                    return False
            else:
                print(f"❌ PUT note failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ PUT note error: {str(e)}")
            return False

    def test_update_invalid_note(self):
        """Test PUT with invalid note ID"""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            updated_data = {
                "title": "Invalid update",
                "doctor_notes": [
                    {
                        "text": "This should fail",
                        "specialty": "internal_medicine"
                    }
                ]
            }
            
            response = requests.put(
                f"{self.api_url}/notes/invalid-note-id",
                json=updated_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 404:
                print("✅ PUT invalid note correctly returned 404")
                return True
            else:
                print(f"❌ PUT invalid note expected 404, got {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ PUT invalid note error: {str(e)}")
            return False

    def test_delete_note(self, note_id):
        """Test DELETE /api/notes/{note_id}"""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            
            # First create an analysis to test cascade deletion
            analyze_data = {"note_id": note_id}
            analysis_response = requests.post(
                f"{self.api_url}/analyze",
                json=analyze_data,
                headers=headers,
                timeout=60
            )
            
            analysis_created = analysis_response.status_code == 200
            if analysis_created:
                print("📊 Created analysis for cascade deletion test")
            
            # Delete the note
            response = requests.delete(
                f"{self.api_url}/notes/{note_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                message = data.get('message', '')
                print(f"✅ DELETE note successful: {message}")
                
                # Verify note is deleted
                get_response = requests.get(
                    f"{self.api_url}/notes/{note_id}",
                    headers=headers,
                    timeout=10
                )
                
                if get_response.status_code == 404:
                    print("✅ Note confirmed deleted (404 on GET)")
                    
                    # Check if analyses were also deleted
                    if analysis_created:
                        analyses_response = requests.get(
                            f"{self.api_url}/analyses/{note_id}",
                            headers=headers,
                            timeout=10
                        )
                        if analyses_response.status_code == 200:
                            remaining_analyses = analyses_response.json()
                            if len(remaining_analyses) == 0:
                                print("✅ Related analyses also deleted")
                            else:
                                print(f"❌ {len(remaining_analyses)} analyses still exist")
                                return False
                    
                    return True
                else:
                    print(f"❌ Note still exists after deletion: {get_response.status_code}")
                    return False
            else:
                print(f"❌ DELETE note failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ DELETE note error: {str(e)}")
            return False

    def test_delete_invalid_note(self):
        """Test DELETE with invalid note ID"""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            
            response = requests.delete(
                f"{self.api_url}/notes/invalid-note-id",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 404:
                print("✅ DELETE invalid note correctly returned 404")
                return True
            else:
                print(f"❌ DELETE invalid note expected 404, got {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ DELETE invalid note error: {str(e)}")
            return False

    def cleanup(self):
        """Clean up test user"""
        if self.admin_token and hasattr(self, 'user_id'):
            try:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                response = requests.delete(
                    f"{self.api_url}/admin/users/{self.user_id}",
                    headers=headers,
                    timeout=10
                )
                if response.status_code == 200:
                    print("✅ Test user cleaned up")
                else:
                    print(f"⚠️ Cleanup failed: {response.text}")
            except Exception as e:
                print(f"⚠️ Cleanup error: {str(e)}")

    def run_tests(self):
        """Run all note management tests"""
        print("🚀 Starting Note Management Endpoint Tests")
        print("=" * 60)
        
        # Setup
        if not self.login_admin():
            return False
        
        if not self.register_and_login_user():
            return False
        
        # Test 1: Create a note
        print("\n📝 Test 1: Create Note")
        note_id = self.create_test_note()
        if not note_id:
            return False
        
        # Test 2: GET note
        print("\n📖 Test 2: GET Note")
        if not self.test_get_note(note_id):
            return False
        
        # Test 3: UPDATE note
        print("\n✏️ Test 3: PUT Note (Update)")
        if not self.test_update_note(note_id):
            return False
        
        # Test 4: GET updated note
        print("\n📖 Test 4: GET Updated Note")
        if not self.test_get_note(note_id):
            return False
        
        # Test 5: UPDATE invalid note
        print("\n❌ Test 5: PUT Invalid Note")
        if not self.test_update_invalid_note():
            return False
        
        # Test 6: DELETE invalid note
        print("\n❌ Test 6: DELETE Invalid Note")
        if not self.test_delete_invalid_note():
            return False
        
        # Test 7: DELETE note (with cascade)
        print("\n🗑️ Test 7: DELETE Note (with cascade)")
        if not self.test_delete_note(note_id):
            return False
        
        # Cleanup
        print("\n🧹 Cleanup")
        self.cleanup()
        
        print("\n🎉 All Note Management Tests Passed!")
        return True

if __name__ == "__main__":
    tester = NoteManagementTester()
    success = tester.run_tests()
    sys.exit(0 if success else 1)