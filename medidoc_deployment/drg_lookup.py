"""
DRG Lookup Module - RAG Pipeline for DRG Pricing
Supports loading from Excel/CSV and in-memory lookup
"""

import os
import json
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class DRGLookup:
    """
    DRG Price List Lookup with RAG capability
    Supports Excel/CSV file loading and ICD-to-DRG mapping
    """
    
    def __init__(self, price_list_path: str = None, base_rate: float = 5000.0):
        """
        Initialize DRG Lookup
        
        Args:
            price_list_path: Path to DRG price list (Excel or CSV)
            base_rate: Base rate for cost calculation (default: 5000 SAR)
        """
        self.base_rate = base_rate
        self.drg_data = {}
        self.icd_to_drg_map = {}
        
        # Load default ICD-10-AM to DRG mappings
        self._load_default_mappings()
        
        # Load from file if provided
        if price_list_path and os.path.exists(price_list_path):
            self.load_from_file(price_list_path)
    
    def _load_default_mappings(self):
        """Load default ICD-10-AM to DRG mappings"""
        
        # Common DRG codes with relative weights
        self.drg_data = {
            # Endocrine DRGs (Diabetes)
            "K60A": {"description": "Diabetes with Complications", "weight": 1.45, "mdc": "10"},
            "K60B": {"description": "Diabetes without Complications", "weight": 0.85, "mdc": "10"},
            "K60C": {"description": "Diabetes Minor Complexity", "weight": 0.55, "mdc": "10"},
            
            # Kidney DRGs
            "L60A": {"description": "Renal Failure with Dialysis", "weight": 3.20, "mdc": "11"},
            "L60B": {"description": "Renal Failure without Dialysis", "weight": 1.85, "mdc": "11"},
            "L63A": {"description": "Kidney & UTI with CC", "weight": 1.25, "mdc": "11"},
            "L63B": {"description": "Kidney & UTI without CC", "weight": 0.75, "mdc": "11"},
            
            # Cardiac DRGs
            "F60A": {"description": "Circulatory Disorders with AMI & CC", "weight": 2.85, "mdc": "05"},
            "F60B": {"description": "Circulatory Disorders with AMI", "weight": 1.95, "mdc": "05"},
            "F62A": {"description": "Heart Failure & Shock with CC", "weight": 1.65, "mdc": "05"},
            "F62B": {"description": "Heart Failure & Shock without CC", "weight": 1.05, "mdc": "05"},
            "F74A": {"description": "Chest Pain with CC", "weight": 0.95, "mdc": "05"},
            "F74B": {"description": "Chest Pain without CC", "weight": 0.55, "mdc": "05"},
            
            # Respiratory DRGs
            "E62A": {"description": "Respiratory Infections with CC", "weight": 2.15, "mdc": "04"},
            "E62B": {"description": "Respiratory Infections without CC", "weight": 1.35, "mdc": "04"},
            "E65A": {"description": "COPD with CC", "weight": 1.45, "mdc": "04"},
            "E65B": {"description": "COPD without CC", "weight": 0.95, "mdc": "04"},
            
            # Nervous System DRGs
            "B70A": {"description": "Stroke with CC", "weight": 2.45, "mdc": "01"},
            "B70B": {"description": "Stroke without CC", "weight": 1.55, "mdc": "01"},
            "B81A": {"description": "Other Nervous System with CC", "weight": 1.25, "mdc": "01"},
            
            # Infectious Disease DRGs
            "T60A": {"description": "Septicaemia with CC", "weight": 3.85, "mdc": "18"},
            "T60B": {"description": "Septicaemia without CC", "weight": 2.45, "mdc": "18"},
            
            # Eye DRGs
            "C60A": {"description": "Major Eye Procedures", "weight": 1.85, "mdc": "02"},
            "C63A": {"description": "Other Eye Disorders", "weight": 0.65, "mdc": "02"},
        }
        
        # ICD-10-AM to DRG mapping
        self.icd_to_drg_map = {
            # Diabetes codes
            "E11.9": "K60B",   # Type 2 diabetes unspecified
            "E11.65": "K60A",  # Type 2 diabetes with hyperglycemia
            "E11.40": "K60A",  # Type 2 diabetes with neuropathy
            "E11.21": "K60A",  # Type 2 diabetes with nephropathy
            "E11.31": "K60A",  # Type 2 diabetes with retinopathy
            "E11.22": "K60A",  # Type 2 diabetes with CKD
            "E10.9": "K60B",   # Type 1 diabetes
            "E10.65": "K60A",  # Type 1 with complications
            
            # Kidney codes
            "N17.9": "L60B",   # Acute kidney injury
            "N18.1": "L63B",   # CKD stage 1
            "N18.2": "L63B",   # CKD stage 2
            "N18.3": "L63A",   # CKD stage 3
            "N18.4": "L60B",   # CKD stage 4
            "N18.5": "L60A",   # CKD stage 5
            "N18.9": "L63B",   # CKD unspecified
            
            # Cardiac codes
            "I50.9": "F62B",   # Heart failure unspecified
            "I50.1": "F62A",   # Left heart failure
            "I50.20": "F62A",  # Systolic heart failure
            "I50.30": "F62A",  # Diastolic heart failure
            "I50.40": "F62A",  # Combined heart failure
            "I10": "F74B",     # Essential hypertension
            "I11.9": "F62A",   # Hypertensive heart disease
            "I12.9": "L63A",   # Hypertensive CKD
            "I20.9": "F74A",   # Angina
            "R07.9": "F74B",   # Chest pain
            
            # Respiratory codes
            "J18.9": "E62B",   # Pneumonia unspecified
            "J15.9": "E62A",   # Bacterial pneumonia
            "J44.9": "E65B",   # COPD
            "J44.1": "E65A",   # COPD with exacerbation
            
            # Infectious codes
            "A41.9": "T60A",   # Sepsis
            
            # Neurological codes
            "G62.9": "B81A",   # Polyneuropathy
        }
        
        logger.info(f"✅ Loaded {len(self.drg_data)} DRG codes and {len(self.icd_to_drg_map)} ICD mappings")
    
    def load_from_file(self, file_path: str) -> bool:
        """
        Load DRG price list from Excel or CSV file
        
        Expected columns: DRG_Code, Description, Relative_Weight, MDC (optional)
        """
        try:
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext in ['.xlsx', '.xls']:
                import pandas as pd
                df = pd.read_excel(file_path)
            elif ext == '.csv':
                import pandas as pd
                df = pd.read_csv(file_path)
            else:
                logger.error(f"Unsupported file format: {ext}")
                return False
            
            # Normalize column names
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
            
            # Map to expected columns
            code_col = next((c for c in df.columns if 'drg' in c and 'code' in c), 
                           next((c for c in df.columns if 'code' in c), None))
            desc_col = next((c for c in df.columns if 'desc' in c), None)
            weight_col = next((c for c in df.columns if 'weight' in c), None)
            
            if not code_col or not weight_col:
                logger.error("Required columns not found in file")
                return False
            
            # Load data
            for _, row in df.iterrows():
                drg_code = str(row[code_col]).strip()
                if drg_code and drg_code != 'nan':
                    self.drg_data[drg_code] = {
                        "description": str(row.get(desc_col, '')).strip() if desc_col else "",
                        "weight": float(row[weight_col]) if row[weight_col] else 1.0,
                        "mdc": str(row.get('mdc', '')).strip() if 'mdc' in df.columns else ""
                    }
            
            logger.info(f"✅ Loaded {len(self.drg_data)} DRG codes from file")
            return True
            
        except Exception as e:
            logger.error(f"Error loading DRG file: {str(e)}")
            return False
    
    def load_icd_mapping(self, mapping_file: str) -> bool:
        """Load ICD-to-DRG mapping from file"""
        try:
            ext = os.path.splitext(mapping_file)[1].lower()
            
            if ext == '.json':
                with open(mapping_file, 'r') as f:
                    self.icd_to_drg_map.update(json.load(f))
            elif ext in ['.xlsx', '.xls', '.csv']:
                import pandas as pd
                if ext == '.csv':
                    df = pd.read_csv(mapping_file)
                else:
                    df = pd.read_excel(mapping_file)
                
                df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
                
                icd_col = next((c for c in df.columns if 'icd' in c), None)
                drg_col = next((c for c in df.columns if 'drg' in c), None)
                
                if icd_col and drg_col:
                    for _, row in df.iterrows():
                        icd = str(row[icd_col]).strip()
                        drg = str(row[drg_col]).strip()
                        if icd and drg and icd != 'nan':
                            self.icd_to_drg_map[icd] = drg
            
            logger.info(f"✅ Loaded {len(self.icd_to_drg_map)} ICD-DRG mappings")
            return True
            
        except Exception as e:
            logger.error(f"Error loading ICD mapping: {str(e)}")
            return False
    
    def lookup_by_drg(self, drg_code: str) -> Optional[Dict]:
        """Look up DRG information by code"""
        drg_code = drg_code.upper().strip()
        
        if drg_code in self.drg_data:
            data = self.drg_data[drg_code]
            return {
                "drg_code": drg_code,
                "description": data.get("description", ""),
                "relative_weight": data.get("weight", 1.0),
                "mdc": data.get("mdc", ""),
                "base_rate": self.base_rate,
                "estimated_cost": data.get("weight", 1.0) * self.base_rate
            }
        return None
    
    def lookup_by_icd(self, icd_code: str) -> Optional[Dict]:
        """Look up DRG information by ICD-10-AM code"""
        icd_code = icd_code.upper().strip()
        
        # Direct lookup
        if icd_code in self.icd_to_drg_map:
            drg_code = self.icd_to_drg_map[icd_code]
            return self.lookup_by_drg(drg_code)
        
        # Try without decimal for partial match
        icd_base = icd_code.split('.')[0]
        for icd, drg in self.icd_to_drg_map.items():
            if icd.startswith(icd_base):
                return self.lookup_by_drg(drg)
        
        return None
    
    def calculate_cost(self, drg_code: str, cc_count: int = 0) -> Dict:
        """
        Calculate estimated cost with CC adjustments
        
        Args:
            drg_code: DRG code
            cc_count: Number of comorbidities/complications
        """
        drg_info = self.lookup_by_drg(drg_code)
        
        if not drg_info:
            return {
                "drg_code": drg_code,
                "base_weight": 1.0,
                "cc_adjustment": 0.0,
                "final_weight": 1.0,
                "base_rate": self.base_rate,
                "estimated_cost": self.base_rate,
                "error": "DRG code not found"
            }
        
        base_weight = drg_info["relative_weight"]
        cc_adjustment = cc_count * 0.1  # Simplified CC adjustment
        final_weight = base_weight + cc_adjustment
        
        return {
            "drg_code": drg_code,
            "description": drg_info["description"],
            "base_weight": base_weight,
            "cc_adjustment": cc_adjustment,
            "final_weight": final_weight,
            "base_rate": self.base_rate,
            "estimated_cost": final_weight * self.base_rate
        }
    
    def get_all_drgs(self) -> List[Dict]:
        """Get all DRG codes with their information"""
        return [
            {
                "drg_code": code,
                "description": data.get("description", ""),
                "relative_weight": data.get("weight", 1.0),
                "mdc": data.get("mdc", ""),
                "estimated_cost": data.get("weight", 1.0) * self.base_rate
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
                    "relative_weight": data.get("weight", 1.0),
                    "estimated_cost": data.get("weight", 1.0) * self.base_rate
                })
        
        return results
    
    def set_base_rate(self, rate: float):
        """Update base rate for cost calculations"""
        self.base_rate = rate
        logger.info(f"Base rate updated to {rate}")


# Singleton instance
_drg_instance = None

def get_drg_lookup(price_list_path: str = None, base_rate: float = 5000.0) -> DRGLookup:
    """Get or create DRG lookup instance"""
    global _drg_instance
    
    if _drg_instance is None:
        _drg_instance = DRGLookup(price_list_path, base_rate)
    
    return _drg_instance
