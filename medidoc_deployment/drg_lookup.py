"""
DRG Lookup Module - RAG Pipeline for DRG Pricing
Optimized for Saudi Arabia AR-DRG v9 Price List
100% Offline - No External API Dependencies
"""

import os
import json
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class DRGLookup:
    """
    DRG Price List Lookup with RAG capability
    Supports AR-DRG v9 Excel file format from Saudi Arabia
    Hospital Types:
        - Type A: Medical city & Tertiary type provider (الأعلى)
        - Type B: Non medical city type provider
        - Type C: Hospitals less than 50 beds (الأقل)
    """
    
    def __init__(self, price_list_path: str = None, hospital_type: str = "A"):
        """
        Initialize DRG Lookup
        
        Args:
            price_list_path: Path to DRG price list (Excel)
            hospital_type: "A", "B", or "C" (default: "A" for tertiary hospitals)
        """
        self.hospital_type = hospital_type.upper()
        self.drg_data = {}
        self.icd_to_drg_map = {}
        
        # Column indices for Excel file (0-indexed)
        # Based on actual file structure:
        # Col 1: AR-DRG Code
        # Col 2: Description
        # Col 3: ALOS
        # Col 4: Price C (< 50 beds)
        # Col 5: Price B (Non medical city)
        # Col 6: Price A (Medical city & Tertiary)
        self.price_columns = {
            "A": 6,  # Medical city & Tertiary
            "B": 5,  # Non medical city
            "C": 4   # < 50 beds
        }
        
        # Load default ICD-10-AM to DRG mappings
        self._load_default_mappings()
        
        # Load from file if provided
        if price_list_path and os.path.exists(price_list_path):
            self.load_from_file(price_list_path)
    
    def _load_default_mappings(self):
        """Load comprehensive ICD-10-AM to AR-DRG v9 mappings"""
        
        # ICD-10-AM to AR-DRG mapping (comprehensive)
        self.icd_to_drg_map = {
            # === Endocrine (Diabetes) ===
            "E11.9": "K60B",    # Type 2 diabetes unspecified
            "E11.65": "K60A",   # Type 2 diabetes with hyperglycemia
            "E11.40": "K60A",   # Type 2 diabetes with neuropathy
            "E11.41": "K60A",   # Type 2 diabetes with diabetic mononeuropathy
            "E11.42": "K60A",   # Type 2 diabetes with diabetic polyneuropathy
            "E11.21": "K60A",   # Type 2 diabetes with nephropathy
            "E11.22": "K60A",   # Type 2 diabetes with CKD
            "E11.29": "K60A",   # Type 2 diabetes with other kidney complication
            "E11.31": "K60A",   # Type 2 diabetes with retinopathy
            "E11.32": "K60A",   # Type 2 diabetes with mild NPDR
            "E11.33": "K60A",   # Type 2 diabetes with moderate NPDR
            "E11.34": "K60A",   # Type 2 diabetes with severe NPDR
            "E11.35": "K60A",   # Type 2 diabetes with PDR
            "E11.36": "K60A",   # Type 2 diabetes with diabetic cataract
            "E11.51": "K60A",   # Type 2 diabetes with peripheral angiopathy
            "E11.52": "K60A",   # Type 2 diabetes with peripheral angiopathy with gangrene
            "E11.59": "K60A",   # Type 2 diabetes with other circulatory complications
            "E11.61": "K60A",   # Type 2 diabetes with diabetic arthropathy
            "E11.62": "K60A",   # Type 2 diabetes with skin complications
            "E11.63": "K60A",   # Type 2 diabetes with oral complications
            "E11.64": "K60A",   # Type 2 diabetes with hypoglycemia
            "E11.69": "K60A",   # Type 2 diabetes with other specified complication
            "E11.8": "K60A",    # Type 2 diabetes with unspecified complications
            "E10.9": "K60B",    # Type 1 diabetes unspecified
            "E10.65": "K60A",   # Type 1 with hyperglycemia
            "E10.10": "K60A",   # Type 1 with ketoacidosis
            "E10.11": "K60A",   # Type 1 with ketoacidosis with coma
            
            # === Kidney & Urinary ===
            "N17.0": "L60B",    # Acute kidney failure with tubular necrosis
            "N17.1": "L60B",    # Acute kidney failure with cortical necrosis
            "N17.2": "L60B",    # Acute kidney failure with medullary necrosis
            "N17.8": "L60B",    # Other acute kidney failure
            "N17.9": "L60B",    # Acute kidney injury unspecified
            "N18.1": "L63B",    # CKD stage 1
            "N18.2": "L63B",    # CKD stage 2
            "N18.3": "L63A",    # CKD stage 3
            "N18.30": "L63A",   # CKD stage 3 unspecified
            "N18.31": "L63A",   # CKD stage 3a
            "N18.32": "L63A",   # CKD stage 3b
            "N18.4": "L60B",    # CKD stage 4
            "N18.5": "L60A",    # CKD stage 5 (ESKD)
            "N18.6": "L60A",    # End stage renal disease
            "N18.9": "L63B",    # CKD unspecified
            "N19": "L60B",      # Unspecified kidney failure
            "N39.0": "L63B",    # Urinary tract infection
            
            # === Cardiac ===
            "I50.1": "F62A",    # Left ventricular failure
            "I50.20": "F62A",   # Systolic heart failure unspecified
            "I50.21": "F62A",   # Acute systolic heart failure
            "I50.22": "F62A",   # Chronic systolic heart failure
            "I50.23": "F62A",   # Acute on chronic systolic heart failure
            "I50.30": "F62A",   # Diastolic heart failure unspecified
            "I50.31": "F62A",   # Acute diastolic heart failure
            "I50.32": "F62A",   # Chronic diastolic heart failure
            "I50.33": "F62A",   # Acute on chronic diastolic heart failure
            "I50.40": "F62A",   # Combined systolic and diastolic HF unspecified
            "I50.41": "F62A",   # Acute combined systolic and diastolic HF
            "I50.42": "F62A",   # Chronic combined systolic and diastolic HF
            "I50.43": "F62A",   # Acute on chronic combined systolic and diastolic HF
            "I50.9": "F62B",    # Heart failure unspecified
            "I10": "F74B",      # Essential hypertension
            "I11.0": "F62A",    # Hypertensive heart disease with heart failure
            "I11.9": "F62A",    # Hypertensive heart disease without heart failure
            "I12.0": "L63A",    # Hypertensive CKD with stage 5 CKD
            "I12.9": "L63A",    # Hypertensive CKD without stage 5 CKD
            "I13.0": "F62A",    # Hypertensive heart and CKD with HF
            "I13.10": "F62A",   # Hypertensive heart and CKD without HF
            "I13.11": "F62A",   # Hypertensive heart and CKD with HF and stage 5 CKD
            "I13.2": "F62A",    # Hypertensive heart and CKD with HF and CKD stage 5
            "I20.0": "F60A",    # Unstable angina
            "I20.1": "F74A",    # Angina with documented spasm
            "I20.8": "F74A",    # Other forms of angina
            "I20.9": "F74A",    # Angina pectoris unspecified
            "I21.0": "F60A",    # Acute STEMI of anterior wall
            "I21.1": "F60A",    # Acute STEMI of inferior wall
            "I21.2": "F60A",    # Acute STEMI of other sites
            "I21.3": "F60A",    # Acute STEMI unspecified site
            "I21.4": "F60B",    # Acute NSTEMI
            "I21.9": "F60B",    # Acute MI unspecified
            "I22.0": "F60A",    # Subsequent STEMI of anterior wall
            "I22.1": "F60A",    # Subsequent STEMI of inferior wall
            "I22.8": "F60A",    # Subsequent STEMI of other sites
            "I22.9": "F60A",    # Subsequent STEMI unspecified site
            "I25.10": "F74A",   # Atherosclerotic heart disease
            "I25.11": "F74A",   # Atherosclerotic heart disease with angina
            "I25.2": "F60B",    # Old myocardial infarction
            "I48.0": "F71A",    # Paroxysmal atrial fibrillation
            "I48.1": "F71A",    # Persistent atrial fibrillation
            "I48.2": "F71A",    # Chronic atrial fibrillation
            "I48.91": "F71A",   # Unspecified atrial fibrillation
            "R07.1": "F74B",    # Chest pain on breathing
            "R07.2": "F74B",    # Precordial pain
            "R07.89": "F74B",   # Other chest pain
            "R07.9": "F74B",    # Chest pain unspecified
            
            # === Respiratory ===
            "J18.0": "E62A",    # Bronchopneumonia, unspecified
            "J18.1": "E62B",    # Lobar pneumonia, unspecified
            "J18.8": "E62B",    # Other pneumonia
            "J18.9": "E62B",    # Pneumonia, unspecified
            "J13": "E62A",      # Pneumonia due to Streptococcus
            "J14": "E62A",      # Pneumonia due to Haemophilus
            "J15.0": "E62A",    # Pneumonia due to Klebsiella
            "J15.1": "E62A",    # Pneumonia due to Pseudomonas
            "J15.20": "E62A",   # Pneumonia due to staphylococcus
            "J15.21": "E62A",   # Pneumonia due to MSSA
            "J15.211": "E62A",  # Pneumonia due to MRSA
            "J15.29": "E62A",   # Pneumonia due to other staphylococcus
            "J15.9": "E62A",    # Bacterial pneumonia unspecified
            "J44.0": "E65A",    # COPD with acute lower respiratory infection
            "J44.1": "E65A",    # COPD with acute exacerbation
            "J44.9": "E65B",    # COPD unspecified
            "J45.20": "E69B",   # Mild intermittent asthma
            "J45.21": "E69A",   # Mild intermittent asthma with acute exacerbation
            "J45.30": "E69B",   # Mild persistent asthma
            "J45.31": "E69A",   # Mild persistent asthma with acute exacerbation
            "J45.40": "E69B",   # Moderate persistent asthma
            "J45.41": "E69A",   # Moderate persistent asthma with acute exacerbation
            "J45.50": "E69A",   # Severe persistent asthma
            "J45.51": "E69A",   # Severe persistent asthma with acute exacerbation
            "J96.00": "E62A",   # Acute respiratory failure unspecified
            "J96.01": "E62A",   # Acute respiratory failure with hypoxia
            "J96.02": "E62A",   # Acute respiratory failure with hypercapnia
            "J96.10": "E65A",   # Chronic respiratory failure unspecified
            "J96.11": "E65A",   # Chronic respiratory failure with hypoxia
            "J96.12": "E65A",   # Chronic respiratory failure with hypercapnia
            "J96.90": "E62B",   # Respiratory failure unspecified
            "J96.91": "E62B",   # Respiratory failure with hypoxia unspecified
            "J96.92": "E62B",   # Respiratory failure with hypercapnia unspecified
            
            # === Infectious Disease ===
            "A41.01": "T60A",   # Sepsis due to MSSA
            "A41.02": "T60A",   # Sepsis due to MRSA
            "A41.1": "T60A",    # Sepsis due to other staphylococcus
            "A41.2": "T60A",    # Sepsis due to unspecified staphylococcus
            "A41.3": "T60A",    # Sepsis due to Haemophilus
            "A41.4": "T60A",    # Sepsis due to anaerobes
            "A41.50": "T60A",   # Gram-negative sepsis unspecified
            "A41.51": "T60A",   # Sepsis due to E. coli
            "A41.52": "T60A",   # Sepsis due to Pseudomonas
            "A41.53": "T60A",   # Sepsis due to Serratia
            "A41.59": "T60A",   # Other Gram-negative sepsis
            "A41.81": "T60A",   # Sepsis due to Enterococcus
            "A41.89": "T60A",   # Other specified sepsis
            "A41.9": "T60A",    # Sepsis unspecified
            "A40.0": "T60A",    # Sepsis due to streptococcus group A
            "A40.1": "T60A",    # Sepsis due to streptococcus group B
            "A40.3": "T60A",    # Sepsis due to S. pneumoniae
            "A40.8": "T60A",    # Other streptococcal sepsis
            "A40.9": "T60A",    # Streptococcal sepsis unspecified
            "R65.20": "T60A",   # Severe sepsis without septic shock
            "R65.21": "T60A",   # Severe sepsis with septic shock
            
            # === Neurological ===
            "I63.0": "B70A",    # Cerebral infarction due to thrombosis of precerebral arteries
            "I63.1": "B70A",    # Cerebral infarction due to embolism of precerebral arteries
            "I63.2": "B70A",    # Cerebral infarction due to unspecified occlusion/stenosis of precerebral arteries
            "I63.3": "B70A",    # Cerebral infarction due to thrombosis of cerebral arteries
            "I63.4": "B70A",    # Cerebral infarction due to embolism of cerebral arteries
            "I63.5": "B70A",    # Cerebral infarction due to unspecified occlusion/stenosis of cerebral arteries
            "I63.8": "B70A",    # Other cerebral infarction
            "I63.9": "B70B",    # Cerebral infarction unspecified
            "I61.0": "B70A",    # Intracerebral hemorrhage in hemisphere subcortical
            "I61.1": "B70A",    # Intracerebral hemorrhage in hemisphere cortical
            "I61.2": "B70A",    # Intracerebral hemorrhage in hemisphere unspecified
            "I61.3": "B70A",    # Intracerebral hemorrhage in brain stem
            "I61.4": "B70A",    # Intracerebral hemorrhage in cerebellum
            "I61.5": "B70A",    # Intracerebral hemorrhage intraventricular
            "I61.6": "B70A",    # Intracerebral hemorrhage multiple localized
            "I61.8": "B70A",    # Other intracerebral hemorrhage
            "I61.9": "B70A",    # Intracerebral hemorrhage unspecified
            "G62.0": "B81A",    # Drug-induced polyneuropathy
            "G62.1": "B81A",    # Alcoholic polyneuropathy
            "G62.2": "B81A",    # Polyneuropathy due to other toxic agents
            "G62.81": "B81A",   # Critical illness polyneuropathy
            "G62.82": "B81A",   # Radiation-induced polyneuropathy
            "G62.89": "B81A",   # Other specified polyneuropathies
            "G62.9": "B81A",    # Polyneuropathy unspecified
            
            # === Eye ===
            "H35.30": "C63A",   # Unspecified macular degeneration
            "H35.31": "C63A",   # Nonexudative age-related macular degeneration
            "H35.32": "C63A",   # Exudative age-related macular degeneration
            "H36": "C63A",      # Retinal disorders in diseases classified elsewhere
            
            # === Gastrointestinal ===
            "K70.30": "G60B",   # Alcoholic cirrhosis of liver without ascites
            "K70.31": "G60A",   # Alcoholic cirrhosis of liver with ascites
            "K72.0": "G60A",    # Acute and subacute hepatic failure
            "K72.1": "G60A",    # Chronic hepatic failure
            "K72.9": "G60B",    # Hepatic failure unspecified
            "K74.0": "G60B",    # Hepatic fibrosis
            "K74.1": "G60B",    # Hepatic sclerosis
            "K74.2": "G60B",    # Hepatic fibrosis with hepatic sclerosis
            "K74.3": "G60A",    # Primary biliary cirrhosis
            "K74.4": "G60A",    # Secondary biliary cirrhosis
            "K74.5": "G60A",    # Biliary cirrhosis unspecified
            "K74.60": "G60B",   # Unspecified cirrhosis of liver
            "K74.69": "G60B",   # Other cirrhosis of liver
            "K92.0": "G61A",    # Hematemesis
            "K92.1": "G61A",    # Melena
            "K92.2": "G61A",    # GI hemorrhage unspecified
        }
        
        logger.info(f"✅ Loaded {len(self.icd_to_drg_map)} ICD-to-DRG mappings")
    
    def load_from_file(self, file_path: str) -> bool:
        """
        Load DRG price list from AR-DRG v9 Excel file
        
        Expected format (Saudi Arabia AR-DRG v9):
        - Row 0: Empty
        - Row 1: Headers
        - Row 2+: Data
        - Column 1: AR-DRG Code
        - Column 2: Description
        - Column 3: ALOS
        - Column 4: Price Type C (< 50 beds)
        - Column 5: Price Type B (Non medical city)
        - Column 6: Price Type A (Medical city & Tertiary)
        """
        try:
            import pandas as pd
            
            # Read Excel without headers (we'll parse manually)
            df = pd.read_excel(file_path, header=None)
            
            logger.info(f"📂 Loading DRG prices from: {file_path}")
            logger.info(f"📊 File shape: {df.shape}")
            
            # Get price column index based on hospital type
            price_col = self.price_columns.get(self.hospital_type, 6)
            
            # Skip header rows (first 2 rows are headers)
            data_start_row = 2
            
            loaded_count = 0
            for idx in range(data_start_row, len(df)):
                try:
                    drg_code = str(df.iloc[idx, 1]).strip()
                    
                    # Skip if not a valid DRG code
                    if not drg_code or drg_code == 'nan' or drg_code == 'AR-DRG v9':
                        continue
                    
                    description = str(df.iloc[idx, 2]).strip() if pd.notna(df.iloc[idx, 2]) else ""
                    alos = float(df.iloc[idx, 3]) if pd.notna(df.iloc[idx, 3]) else 0.0
                    price = float(df.iloc[idx, price_col]) if pd.notna(df.iloc[idx, price_col]) else 0.0
                    
                    if drg_code and description != 'nan':
                        self.drg_data[drg_code] = {
                            "description": description,
                            "alos": alos,
                            "price": price,
                            "hospital_type": self.hospital_type
                        }
                        loaded_count += 1
                        
                except Exception as row_error:
                    continue
            
            logger.info(f"✅ Loaded {loaded_count} DRG codes from file (Hospital Type: {self.hospital_type})")
            return True
            
        except ImportError:
            logger.error("❌ pandas not installed. Run: pip install pandas openpyxl")
            return False
        except Exception as e:
            logger.error(f"❌ Error loading DRG file: {str(e)}")
            return False
    
    def lookup_by_drg(self, drg_code: str) -> Optional[Dict]:
        """Look up DRG information by code"""
        drg_code = drg_code.upper().strip()
        
        if drg_code in self.drg_data:
            data = self.drg_data[drg_code]
            return {
                "drg_code": drg_code,
                "description": data.get("description", ""),
                "alos": data.get("alos", 0.0),
                "price": data.get("price", 0.0),
                "hospital_type": data.get("hospital_type", self.hospital_type),
                "estimated_cost": data.get("price", 0.0)
            }
        return None
    
    def lookup_by_icd(self, icd_code: str) -> Optional[Dict]:
        """Look up DRG information by ICD-10-AM code"""
        icd_code = icd_code.upper().strip()
        
        # Direct lookup
        if icd_code in self.icd_to_drg_map:
            drg_code = self.icd_to_drg_map[icd_code]
            result = self.lookup_by_drg(drg_code)
            if result:
                result['icd_code'] = icd_code
                return result
        
        # Try without decimal for partial match
        icd_base = icd_code.split('.')[0]
        for icd, drg in self.icd_to_drg_map.items():
            if icd.startswith(icd_base):
                result = self.lookup_by_drg(drg)
                if result:
                    result['icd_code'] = icd_code
                    result['matched_icd'] = icd
                    return result
        
        return None
    
    def calculate_cost(self, drg_code: str, cc_count: int = 0, los: float = 0) -> Dict:
        """
        Calculate estimated cost with CC adjustments and LOS consideration
        
        Args:
            drg_code: DRG code
            cc_count: Number of comorbidities/complications
            los: Actual length of stay (for outlier calculation)
        """
        drg_info = self.lookup_by_drg(drg_code)
        
        if not drg_info:
            return {
                "drg_code": drg_code,
                "base_price": 0.0,
                "cc_adjustment": 0.0,
                "los_adjustment": 0.0,
                "final_price": 0.0,
                "error": "رمز DRG غير موجود | DRG code not found"
            }
        
        base_price = drg_info["price"]
        alos = drg_info.get("alos", 1.0)
        
        # CC adjustment (simplified - each CC adds 10% to base)
        cc_adjustment = cc_count * (base_price * 0.10)
        
        # LOS adjustment (if actual LOS exceeds ALOS by more than 50%)
        los_adjustment = 0.0
        if los > 0 and alos > 0:
            if los > (alos * 1.5):
                # Per diem for additional days
                extra_days = los - alos
                per_diem = base_price / alos * 0.5  # 50% of daily rate
                los_adjustment = extra_days * per_diem
        
        final_price = base_price + cc_adjustment + los_adjustment
        
        return {
            "drg_code": drg_code,
            "description": drg_info["description"],
            "base_price": round(base_price, 2),
            "alos": alos,
            "actual_los": los,
            "cc_count": cc_count,
            "cc_adjustment": round(cc_adjustment, 2),
            "los_adjustment": round(los_adjustment, 2),
            "final_price": round(final_price, 2),
            "hospital_type": self.hospital_type,
            "currency": "SAR"
        }
    
    def get_all_drgs(self) -> List[Dict]:
        """Get all DRG codes with their information"""
        return [
            {
                "drg_code": code,
                "description": data.get("description", ""),
                "alos": data.get("alos", 0.0),
                "price": data.get("price", 0.0),
                "hospital_type": data.get("hospital_type", self.hospital_type)
            }
            for code, data in self.drg_data.items()
        ]
    
    def search_drg(self, query: str) -> List[Dict]:
        """Search DRG by description or code"""
        query = query.lower()
        results = []
        
        for code, data in self.drg_data.items():
            if query in code.lower() or query in data.get("description", "").lower():
                results.append({
                    "drg_code": code,
                    "description": data.get("description", ""),
                    "alos": data.get("alos", 0.0),
                    "price": data.get("price", 0.0)
                })
        
        return sorted(results, key=lambda x: x['drg_code'])
    
    def set_hospital_type(self, hospital_type: str):
        """Change hospital type (affects pricing)"""
        self.hospital_type = hospital_type.upper()
        logger.info(f"🏥 Hospital type changed to: {self.hospital_type}")
    
    def get_statistics(self) -> Dict:
        """Get statistics about loaded data"""
        prices = [d.get('price', 0) for d in self.drg_data.values() if d.get('price', 0) > 0]
        
        return {
            "total_drg_codes": len(self.drg_data),
            "total_icd_mappings": len(self.icd_to_drg_map),
            "hospital_type": self.hospital_type,
            "min_price": round(min(prices), 2) if prices else 0,
            "max_price": round(max(prices), 2) if prices else 0,
            "avg_price": round(sum(prices) / len(prices), 2) if prices else 0,
            "currency": "SAR"
        }


# Singleton instance
_drg_instance = None

def get_drg_lookup(price_list_path: str = None, hospital_type: str = "A") -> DRGLookup:
    """Get or create DRG lookup instance"""
    global _drg_instance
    
    if _drg_instance is None:
        _drg_instance = DRGLookup(price_list_path, hospital_type)
    
    return _drg_instance


def reload_drg_lookup(price_list_path: str, hospital_type: str = "A") -> DRGLookup:
    """Force reload DRG lookup with new file"""
    global _drg_instance
    _drg_instance = DRGLookup(price_list_path, hospital_type)
    return _drg_instance
