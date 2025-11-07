#!/usr/bin/env python3
"""
Comprehensive CDI Excel Upload Test
Tests the fix for PDX/After CDI indicator showing 0 values
"""

import requests
import io
import pandas as pd
from datetime import datetime

class CDIComprehensiveTest:
    def __init__(self):
        self.base_url = "https://medidoc-ai-1.preview.emergentagent.com"
        self.api_url = f"{self.base_url}/api"
        self.admin_credentials = {
            "email": "admin@cdi-center.sa",
            "password": "CDI@2024#Admin"
        }
        self.admin_token = None
        
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
                print(f"✅ Admin login successful: {self.admin_credentials['email']}")
                return True
            else:
                print(f"❌ Admin login failed: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Admin login error: {str(e)}")
            return False
    
    def create_test_excel_scenario_1(self):
        """Create Excel with mixed data including empty strings and whitespace"""
        data = {
            'Hospital Name': [
                'مستشفى الملك فهد الجامعي',
                'مستشفى الملك فيصل التخصصي',
                'مستشفى الملك فهد الجامعي',
                'مستشفى الأمير سلطان',
                'مستشفى الملك فيصل التخصصي'
            ],
            'PDX/After CDI': [
                'E11.9 - Type 2 diabetes mellitus',  # Valid data
                '',  # Empty string - should NOT count
                'I10 - Essential hypertension',  # Valid data
                '   ',  # Whitespace only - should NOT count
                'J44.1 - COPD with acute exacerbation'  # Valid data
            ],
            'ADX due to CDI': [
                'Z79.4 - Long term use of insulin',  # Valid data
                'E78.5 - Hyperlipidemia',  # Valid data
                '',  # Empty string - should NOT count
                '',  # Empty string - should NOT count
                'N25.81 - Secondary hyperparathyroidism'  # Valid data
            ],
            'DRG Before': ['641', '642', '643', '644', '645'],
            'DRG After': ['641', '643', '643', '645', '645']
        }
        
        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='CDI Data')
        excel_buffer.seek(0)
        return excel_buffer, 3, 3  # Expected PDX count, Expected ADX count
    
    def create_test_excel_scenario_2(self):
        """Create Excel with all empty PDX/ADX columns to test edge case"""
        data = {
            'Hospital Name': [
                'مستشفى الملك فهد',
                'مستشفى الملك فيصل'
            ],
            'PDX/After CDI': [
                '',  # Empty
                '   '  # Whitespace only
            ],
            'ADX due to CDI': [
                '',  # Empty
                ''   # Empty
            ],
            'DRG Before': ['641', '642'],
            'DRG After': ['641', '642']
        }
        
        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='CDI Data')
        excel_buffer.seek(0)
        return excel_buffer, 0, 0  # Expected PDX count, Expected ADX count
    
    def create_test_excel_scenario_3(self):
        """Create Excel with all valid PDX/ADX data"""
        data = {
            'Hospital Name': [
                'مستشفى الملك فهد',
                'مستشفى الملك فيصل',
                'مستشفى الأمير سلطان'
            ],
            'PDX/After CDI': [
                'E11.9 - Type 2 diabetes mellitus',
                'I10 - Essential hypertension',
                'J44.1 - COPD with acute exacerbation'
            ],
            'ADX due to CDI': [
                'Z79.4 - Long term use of insulin',
                'E78.5 - Hyperlipidemia',
                'N25.81 - Secondary hyperparathyroidism'
            ],
            'DRG Before': ['641', '642', '643'],
            'DRG After': ['641', '643', '645']
        }
        
        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='CDI Data')
        excel_buffer.seek(0)
        return excel_buffer, 3, 3  # Expected PDX count, Expected ADX count
    
    def test_cdi_upload(self, excel_file, expected_pdx, expected_adx, scenario_name):
        """Test CDI upload with specific scenario"""
        print(f"\n🧪 Testing Scenario: {scenario_name}")
        print(f"   Expected PDX/After CDI count: {expected_pdx}")
        print(f"   Expected ADX due to CDI count: {expected_adx}")
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            files = {
                'file': (f'{scenario_name.lower().replace(" ", "_")}.xlsx', excel_file, 
                        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            }
            
            response = requests.post(
                f"{self.api_url}/supervisor/upload-cdi-data",
                headers=headers,
                files=files,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Get metrics
                pdx_metrics = data.get('pdx_metrics', {})
                adx_metrics = data.get('adx_metrics', {})
                summary = data.get('summary', {})
                
                actual_pdx = pdx_metrics.get('total_after_cdi', 0)
                actual_adx = adx_metrics.get('total_added', 0)
                total_records = summary.get('total_records', 0)
                total_hospitals = summary.get('total_hospitals', 0)
                
                print(f"   Actual PDX/After CDI count: {actual_pdx}")
                print(f"   Actual ADX due to CDI count: {actual_adx}")
                print(f"   Total records: {total_records}")
                print(f"   Total hospitals: {total_hospitals}")
                
                # Validate results
                if actual_pdx == expected_pdx and actual_adx == expected_adx:
                    print(f"   ✅ {scenario_name}: PASSED")
                    return True
                else:
                    print(f"   ❌ {scenario_name}: FAILED - Expected PDX:{expected_pdx}, ADX:{expected_adx}, Got PDX:{actual_pdx}, ADX:{actual_adx}")
                    return False
            else:
                print(f"   ❌ {scenario_name}: Upload failed - {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ {scenario_name}: Exception - {str(e)}")
            return False
    
    def run_comprehensive_test(self):
        """Run all test scenarios"""
        print("🔬 COMPREHENSIVE CDI EXCEL UPLOAD TEST")
        print("=" * 60)
        print("Testing fix for: PDX/After CDI indicator showing 0 values")
        print("Fix: Added empty string filter in server.py line 1664")
        print("=" * 60)
        
        if not self.login_admin():
            return False
        
        results = []
        
        # Test Scenario 1: Mixed data with empty strings and whitespace
        excel1, exp_pdx1, exp_adx1 = self.create_test_excel_scenario_1()
        result1 = self.test_cdi_upload(excel1, exp_pdx1, exp_adx1, "Mixed Data with Empty Strings")
        results.append(result1)
        
        # Test Scenario 2: All empty data (edge case)
        excel2, exp_pdx2, exp_adx2 = self.create_test_excel_scenario_2()
        result2 = self.test_cdi_upload(excel2, exp_pdx2, exp_adx2, "All Empty Data")
        results.append(result2)
        
        # Test Scenario 3: All valid data
        excel3, exp_pdx3, exp_adx3 = self.create_test_excel_scenario_3()
        result3 = self.test_cdi_upload(excel3, exp_pdx3, exp_adx3, "All Valid Data")
        results.append(result3)
        
        # Summary
        passed = sum(results)
        total = len(results)
        
        print(f"\n📊 COMPREHENSIVE TEST RESULTS:")
        print(f"   Tests Passed: {passed}/{total}")
        print(f"   Success Rate: {(passed/total*100):.1f}%")
        
        if passed == total:
            print(f"\n🎉 ALL TESTS PASSED!")
            print(f"   ✅ The PDX/After CDI indicator fix is working correctly")
            print(f"   ✅ Empty strings and whitespace are properly filtered")
            print(f"   ✅ The reported user issue has been RESOLVED")
        else:
            print(f"\n❌ SOME TESTS FAILED!")
            print(f"   The fix may not be working correctly in all scenarios")
        
        return passed == total

if __name__ == "__main__":
    tester = CDIComprehensiveTest()
    tester.run_comprehensive_test()