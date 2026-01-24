"""
DRG Pricing Lookup Module
Supports Hospital Categories: A (MAJC), B (INTC), C (MINC)
Saudi Arabia DRG Pricing System
"""

import logging
import pandas as pd
from typing import Dict, List, Optional
import os

logger = logging.getLogger(__name__)

# Hospital Category Mapping
HOSPITAL_CATEGORIES = {
    "A": {"code": "MAJC", "name_ar": "مستشفيات الفئة أ (كبرى)", "name_en": "Category A (Major)"},
    "B": {"code": "INTC", "name_ar": "مستشفيات الفئة ب (متوسطة)", "name_en": "Category B (Intermediate)"},
    "C": {"code": "MINC", "name_ar": "مستشفيات الفئة ج (صغرى)", "name_en": "Category C (Minor)"},
}


class DRGLookup:
    """DRG Pricing Lookup System"""
    
    def __init__(self, excel_path: str = None):
        self.excel_path = excel_path or "/opt/medidoc/backend/reference_data/drg_prices.xlsx"
        self.data = None
        self.loaded = False
        self._load_data()
    
    def _load_data(self):
        """Load DRG pricing data from Excel file"""
        try:
            if os.path.exists(self.excel_path):
                # Try to load the Excel file
                self.data = pd.read_excel(self.excel_path)
                self.loaded = True
                logger.info(f"✅ Loaded DRG pricing data: {len(self.data)} records")
                logger.info(f"📊 Columns: {list(self.data.columns)}")
            else:
                logger.warning(f"⚠️ DRG pricing file not found: {self.excel_path}")
                self._init_fallback_data()
        except Exception as e:
            logger.error(f"❌ Error loading DRG data: {str(e)}")
            self._init_fallback_data()
    
    def _init_fallback_data(self):
        """Initialize with fallback/sample data"""
        self.data = pd.DataFrame({
            "DRG_Code": [],
            "Description": [],
            "Category_A": [],
            "Category_B": [],
            "Category_C": []
        })
        self.loaded = False
    
    def lookup_by_drg(self, drg_code: str, hospital_category: str = "A") -> Optional[Dict]:
        """
        Look up DRG pricing by DRG code
        
        Args:
            drg_code: The DRG code to look up
            hospital_category: Hospital category (A, B, or C)
            
        Returns:
            Dict with pricing information or None
        """
        if not self.loaded or self.data is None:
            return None
        
        try:
            code = drg_code.upper().strip()
            
            # Try to find the DRG code
            mask = self.data.iloc[:, 0].astype(str).str.upper().str.contains(code, na=False)
            matches = self.data[mask]
            
            if len(matches) > 0:
                row = matches.iloc[0]
                
                # Get price based on category
                category_col_map = {
                    "A": "MAJC",
                    "B": "INTC", 
                    "C": "MINC"
                }
                
                price = None
                for col in row.index:
                    if category_col_map.get(hospital_category, "MAJC") in str(col).upper():
                        price = row[col]
                        break
                
                return {
                    "drg_code": code,
                    "description": str(row.iloc[1]) if len(row) > 1 else "",
                    "hospital_category": hospital_category,
                    "price": float(price) if price and pd.notna(price) else None,
                    "category_info": HOSPITAL_CATEGORIES.get(hospital_category, {})
                }
                
        except Exception as e:
            logger.error(f"Error looking up DRG {drg_code}: {str(e)}")
        
        return None
    
    def lookup_by_icd(self, icd_code: str, hospital_category: str = "A") -> Optional[Dict]:
        """
        Look up DRG pricing by ICD-10 code
        Note: This requires ICD-to-DRG mapping which may not be available
        
        Args:
            icd_code: The ICD-10 code to look up
            hospital_category: Hospital category (A, B, or C)
            
        Returns:
            Dict with pricing information or None
        """
        if not self.loaded or self.data is None:
            return None
        
        try:
            code = icd_code.upper().strip()
            
            # Search for ICD code in description or any column
            for col in self.data.columns:
                mask = self.data[col].astype(str).str.upper().str.contains(code, na=False)
                if mask.any():
                    matches = self.data[mask]
                    if len(matches) > 0:
                        row = matches.iloc[0]
                        drg_code = str(row.iloc[0])
                        return self.lookup_by_drg(drg_code, hospital_category)
                        
        except Exception as e:
            logger.error(f"Error looking up ICD {icd_code}: {str(e)}")
        
        return None
    
    def get_all_categories_pricing(self, drg_code: str) -> Dict:
        """Get pricing for all hospital categories"""
        result = {
            "drg_code": drg_code,
            "pricing": {}
        }
        
        for cat in ["A", "B", "C"]:
            lookup = self.lookup_by_drg(drg_code, cat)
            if lookup:
                result["pricing"][cat] = {
                    "price": lookup.get("price"),
                    "category_name_ar": HOSPITAL_CATEGORIES[cat]["name_ar"],
                    "category_name_en": HOSPITAL_CATEGORIES[cat]["name_en"]
                }
        
        return result
    
    def estimate_case_value(self, diagnoses: List[Dict], hospital_category: str = "A") -> Dict:
        """
        Estimate total case value based on diagnoses
        
        Args:
            diagnoses: List of diagnosis dicts with 'icd_code' or 'drg_code'
            hospital_category: Hospital category
            
        Returns:
            Dict with estimated values
        """
        result = {
            "hospital_category": hospital_category,
            "category_info": HOSPITAL_CATEGORIES.get(hospital_category, {}),
            "diagnoses_with_pricing": [],
            "total_estimated": 0.0,
            "pricing_available": False
        }
        
        for diag in diagnoses:
            diag_result = {
                "diagnosis_ar": diag.get("diagnosis_ar", ""),
                "diagnosis_en": diag.get("diagnosis_en", ""),
                "icd_code": diag.get("icd_code", ""),
                "drg_code": None,
                "price": None
            }
            
            # Try DRG lookup first, then ICD
            drg_code = diag.get("drg_code")
            if drg_code:
                lookup = self.lookup_by_drg(drg_code, hospital_category)
            else:
                icd_code = diag.get("icd_code", "")
                lookup = self.lookup_by_icd(icd_code, hospital_category)
            
            if lookup:
                diag_result["drg_code"] = lookup.get("drg_code")
                diag_result["price"] = lookup.get("price")
                if lookup.get("price"):
                    result["total_estimated"] += lookup["price"]
                    result["pricing_available"] = True
            
            result["diagnoses_with_pricing"].append(diag_result)
        
        return result


# Global instance
_drg_lookup = None


def get_drg_lookup(excel_path: str = None, hospital_type: str = "A") -> DRGLookup:
    """Get or create DRG lookup instance"""
    global _drg_lookup
    if _drg_lookup is None:
        _drg_lookup = DRGLookup(excel_path)
    return _drg_lookup


def lookup_drg_price(drg_code: str, hospital_category: str = "A") -> Optional[Dict]:
    """Quick lookup function for DRG pricing"""
    lookup = get_drg_lookup()
    return lookup.lookup_by_drg(drg_code, hospital_category)


def lookup_icd_price(icd_code: str, hospital_category: str = "A") -> Optional[Dict]:
    """Quick lookup function for ICD pricing"""
    lookup = get_drg_lookup()
    return lookup.lookup_by_icd(icd_code, hospital_category)
