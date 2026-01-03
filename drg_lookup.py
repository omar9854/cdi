"""
DRG Lookup Module
Provides ICD-10 to DRG code and pricing lookup
"""

import pandas as pd
import json
import logging
import os
from typing import Dict, Optional

logger = logging.getLogger(__name__)

_drg_lookup_instance = None


class DRGLookup:
    """DRG code and pricing lookup from Excel/JSON"""
    
    def __init__(self, price_list_path: str = None, hospital_type: str = "A"):
        self.hospital_type = hospital_type
        self.data = {}
        self.icd_to_drg = {}
        
        if price_list_path and os.path.exists(price_list_path):
            self._load_from_file(price_list_path)
        else:
            self._load_defaults()
    
    def _load_from_file(self, path: str):
        """Load DRG data from Excel or JSON file"""
        try:
            if path.endswith('.xlsx') or path.endswith('.xls'):
                df = pd.read_excel(path)
                for _, row in df.iterrows():
                    drg_code = str(row.get('DRG_Code', row.get('drg_code', '')))
                    if drg_code:
                        self.data[drg_code] = {
                            'drg_code': drg_code,
                            'description': row.get('Description', row.get('description', '')),
                            'price': row.get('Price', row.get('price', 0)),
                            'weight': row.get('Weight', row.get('weight', 1.0))
                        }
                        # Map ICD codes to DRG
                        icd_codes = str(row.get('ICD_Codes', row.get('icd_codes', ''))).split(',')
                        for icd in icd_codes:
                            icd = icd.strip()
                            if icd:
                                self.icd_to_drg[icd] = drg_code
                                
            elif path.endswith('.json'):
                with open(path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                    
            logger.info(f"✅ Loaded {len(self.data)} DRG entries from {path}")
            
        except Exception as e:
            logger.warning(f"⚠️ Could not load DRG file: {str(e)}")
            self._load_defaults()
    
    def _load_defaults(self):
        """Load common ICD-10 to DRG mappings"""
        # Common mappings
        self.icd_to_drg = {
            # Diabetes
            'E11.9': 'F60A', 'E11.65': 'F60A', 'E10.9': 'F60A',
            'E11.40': 'F60B', 'E11.21': 'F60B', 'E11.22': 'F60B',
            
            # CKD
            'N18.1': 'L60A', 'N18.2': 'L60A', 'N18.3': 'L60B',
            'N18.4': 'L60C', 'N18.5': 'L60D', 'N17.9': 'L60E',
            
            # Heart Failure
            'I50.9': 'F62A', 'I50.20': 'F62B', 'I50.21': 'F62B',
            'I50.22': 'F62B', 'I50.23': 'F62B',
            'I50.30': 'F62C', 'I50.31': 'F62C', 'I50.32': 'F62C',
            
            # Hypertension
            'I10': 'F70A', 'I11.0': 'F70B', 'I11.9': 'F70B',
            'I12.0': 'F70C', 'I12.9': 'F70C',
            
            # Sepsis
            'A41.9': 'T60A', 'A41.01': 'T60A', 'A41.02': 'T60A',
            'R65.20': 'T60B', 'R65.21': 'T60C',
            
            # Respiratory
            'J18.9': 'E62A', 'J44.1': 'E65A', 'J96.0': 'E63A',
        }
        
        # Default prices (SAR)
        self.data = {
            'F60A': {'drg_code': 'F60A', 'description': 'Diabetes without complications', 'price': 8500, 'weight': 0.85},
            'F60B': {'drg_code': 'F60B', 'description': 'Diabetes with complications', 'price': 15000, 'weight': 1.5},
            'L60A': {'drg_code': 'L60A', 'description': 'CKD Stage 1-2', 'price': 7000, 'weight': 0.7},
            'L60B': {'drg_code': 'L60B', 'description': 'CKD Stage 3', 'price': 12000, 'weight': 1.2},
            'L60C': {'drg_code': 'L60C', 'description': 'CKD Stage 4', 'price': 18000, 'weight': 1.8},
            'L60D': {'drg_code': 'L60D', 'description': 'CKD Stage 5', 'price': 25000, 'weight': 2.5},
            'L60E': {'drg_code': 'L60E', 'description': 'Acute Kidney Injury', 'price': 20000, 'weight': 2.0},
            'F62A': {'drg_code': 'F62A', 'description': 'Heart Failure unspecified', 'price': 15000, 'weight': 1.5},
            'F62B': {'drg_code': 'F62B', 'description': 'Systolic Heart Failure', 'price': 22000, 'weight': 2.2},
            'F62C': {'drg_code': 'F62C', 'description': 'Diastolic Heart Failure', 'price': 20000, 'weight': 2.0},
            'F70A': {'drg_code': 'F70A', 'description': 'Essential Hypertension', 'price': 5000, 'weight': 0.5},
            'F70B': {'drg_code': 'F70B', 'description': 'Hypertensive Heart Disease', 'price': 12000, 'weight': 1.2},
            'F70C': {'drg_code': 'F70C', 'description': 'Hypertensive CKD', 'price': 15000, 'weight': 1.5},
            'T60A': {'drg_code': 'T60A', 'description': 'Sepsis', 'price': 30000, 'weight': 3.0},
            'T60B': {'drg_code': 'T60B', 'description': 'Severe Sepsis', 'price': 50000, 'weight': 5.0},
            'T60C': {'drg_code': 'T60C', 'description': 'Septic Shock', 'price': 80000, 'weight': 8.0},
            'E62A': {'drg_code': 'E62A', 'description': 'Pneumonia', 'price': 12000, 'weight': 1.2},
            'E65A': {'drg_code': 'E65A', 'description': 'COPD Exacerbation', 'price': 15000, 'weight': 1.5},
            'E63A': {'drg_code': 'E63A', 'description': 'Respiratory Failure', 'price': 35000, 'weight': 3.5},
        }
        
        logger.info(f"✅ Loaded {len(self.icd_to_drg)} default ICD-to-DRG mappings")
    
    def lookup_by_icd(self, icd_code: str) -> Optional[Dict]:
        """Lookup DRG info by ICD-10 code"""
        if not icd_code:
            return None
        
        # Clean the code
        icd_code = icd_code.strip().upper()
        
        # Try exact match first
        drg_code = self.icd_to_drg.get(icd_code)
        
        # Try without decimal
        if not drg_code and '.' in icd_code:
            base_code = icd_code.split('.')[0]
            for stored_icd, stored_drg in self.icd_to_drg.items():
                if stored_icd.startswith(base_code):
                    drg_code = stored_drg
                    break
        
        if drg_code and drg_code in self.data:
            return self.data[drg_code]
        
        return None
    
    def lookup_by_drg(self, drg_code: str) -> Optional[Dict]:
        """Lookup DRG info by DRG code"""
        return self.data.get(drg_code)


def get_drg_lookup(price_list_path: str = None, hospital_type: str = "A") -> DRGLookup:
    """Get or create DRG lookup instance"""
    global _drg_lookup_instance
    
    if _drg_lookup_instance is None:
        # Try to find price list file
        if price_list_path is None:
            possible_paths = [
                'drg_prices.xlsx',
                'drg_prices.json',
                '/opt/medidoc/backend/drg_prices.xlsx',
                '/opt/medidoc/backend/drg_prices.json'
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    price_list_path = path
                    break
        
        _drg_lookup_instance = DRGLookup(price_list_path, hospital_type)
    
    return _drg_lookup_instance
