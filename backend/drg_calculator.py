"""
DRG Price Loader and Calculator
Loads DRG prices from Excel and calculates financial impact
"""

import pandas as pd
import os
import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Global cache for DRG prices
_drg_prices_cache: Dict[str, Dict[str, float]] = {}
_drg_prices_loaded = False


def load_drg_prices(excel_path: str = "/app/backend/data/drg_prices.xlsx") -> Dict[str, Dict[str, float]]:
    """
    Load DRG prices from Excel file
    
    Structure:
    - Column B (index 1): DRG codes
    - Column E (index 4): Category C prices (< 50 beds)
    - Column F (index 5): Category B prices (> 50 beds)
    - Column G (index 6): Category A prices (Medical cities)
    
    Returns:
        Dictionary: {drg_code: {'A': price, 'B': price, 'C': price}}
    """
    global _drg_prices_cache, _drg_prices_loaded
    
    if _drg_prices_loaded and _drg_prices_cache:
        logger.info("📊 Using cached DRG prices")
        return _drg_prices_cache
    
    try:
        if not os.path.exists(excel_path):
            logger.warning(f"⚠️ DRG prices file not found: {excel_path}")
            return {}
        
        logger.info(f"📖 Loading DRG prices from {excel_path}")
        df = pd.read_excel(excel_path, header=None)
        
        prices = {}
        
        # Skip header row (row 0)
        for idx in range(1, len(df)):
            drg_code = str(df.iloc[idx, 1]).strip() if pd.notna(df.iloc[idx, 1]) else None
            
            if not drg_code or drg_code == 'nan':
                continue
            
            # Get prices for each category
            price_c = df.iloc[idx, 4]  # Column E - Category C
            price_b = df.iloc[idx, 5]  # Column F - Category B
            price_a = df.iloc[idx, 6]  # Column G - Category A
            
            # Convert to float, handle non-numeric values
            def safe_float(val):
                try:
                    if pd.isna(val):
                        return 0.0
                    return float(val)
                except (ValueError, TypeError):
                    return 0.0
            
            prices[drg_code] = {
                'A': safe_float(price_a),
                'B': safe_float(price_b),
                'C': safe_float(price_c)
            }
        
        _drg_prices_cache = prices
        _drg_prices_loaded = True
        
        logger.info(f"✅ Loaded {len(prices)} DRG codes with prices")
        return prices
        
    except Exception as e:
        logger.error(f"❌ Error loading DRG prices: {str(e)}")
        return {}


def get_drg_price(drg_code: str, category: str) -> float:
    """
    Get price for a specific DRG code and hospital category
    
    Args:
        drg_code: The DRG code (e.g., '801A', 'A13A')
        category: Hospital category ('A', 'B', or 'C')
    
    Returns:
        Price in SAR
    """
    prices = load_drg_prices()
    
    if not prices:
        logger.warning("⚠️ DRG prices not loaded")
        return 0.0
    
    drg_code = str(drg_code).strip().upper()
    category = str(category).strip().upper()
    
    if drg_code not in prices:
        logger.warning(f"⚠️ DRG code {drg_code} not found in price list")
        return 0.0
    
    if category not in ['A', 'B', 'C']:
        logger.warning(f"⚠️ Invalid category {category}, defaulting to A")
        category = 'A'
    
    return prices[drg_code].get(category, 0.0)


def calculate_drg_difference(old_drg: str, new_drg: str, category: str) -> Tuple[float, float, float]:
    """
    Calculate financial difference between old and new DRG
    
    Args:
        old_drg: Previous DRG code
        new_drg: New DRG code after CDI intervention
        category: Hospital category ('A', 'B', 'C')
    
    Returns:
        Tuple: (old_price, new_price, difference)
    """
    old_price = get_drg_price(old_drg, category)
    new_price = get_drg_price(new_drg, category)
    difference = new_price - old_price
    
    return old_price, new_price, difference


def analyze_monthly_drg_impact(df: pd.DataFrame, 
                                drg_old_col: str = None,
                                drg_new_col: str = None,
                                category_col: str = None,
                                hospital_col: str = None,
                                department_col: str = None,
                                specialist_col: str = None) -> Dict:
    """
    Analyze monthly DRG financial impact from uploaded Excel
    
    Expected columns (by letter):
    - T: DRG change indicator
    - V: Old DRG code
    - (next after V): New DRG code
    - X: Hospital category
    
    Args:
        df: DataFrame from uploaded Excel
        drg_old_col: Column name/index for old DRG (default: column V = index 21)
        drg_new_col: Column name/index for new DRG (default: column after V)
        category_col: Column name/index for hospital category (default: column X = index 23)
    
    Returns:
        Dictionary with comprehensive DRG analysis
    """
    logger.info("📊 Starting monthly DRG impact analysis...")
    
    # Load DRG prices
    prices = load_drg_prices()
    if not prices:
        return {"error": "DRG prices not loaded", "total_impact": 0}
    
    # Column indices (0-based): T=19, V=21, X=23
    # Adjust based on actual file structure
    columns = df.columns.tolist()
    
    # Try to find columns by index or name
    def get_column(df, col_index_or_name, default_index):
        if col_index_or_name is not None:
            if isinstance(col_index_or_name, int):
                return df.iloc[:, col_index_or_name] if col_index_or_name < len(df.columns) else None
            elif col_index_or_name in df.columns:
                return df[col_index_or_name]
        if default_index < len(df.columns):
            return df.iloc[:, default_index]
        return None
    
    # Get relevant columns
    drg_change_col = get_column(df, None, 19)  # Column T (index 19)
    old_drg_series = get_column(df, drg_old_col, 21)  # Column V (index 21)
    new_drg_series = get_column(df, drg_new_col, 22)  # Column W (index 22)
    category_series = get_column(df, category_col, 23)  # Column X (index 23)
    
    # Results containers
    total_impact = 0.0
    total_cases_with_drg_change = 0
    hospital_impacts = {}
    department_impacts = {}
    specialist_impacts = {}
    drg_changes_detail = []
    
    # Process each row
    for idx in range(len(df)):
        try:
            # Check if there's a DRG change
            drg_change = drg_change_col.iloc[idx] if drg_change_col is not None else None
            
            # Skip if no DRG change
            if pd.isna(drg_change) or str(drg_change).strip().lower() not in ['yes', 'نعم', '1', 'true', 'y']:
                continue
            
            # Get DRG codes
            old_drg = str(old_drg_series.iloc[idx]).strip() if old_drg_series is not None and pd.notna(old_drg_series.iloc[idx]) else None
            new_drg = str(new_drg_series.iloc[idx]).strip() if new_drg_series is not None and pd.notna(new_drg_series.iloc[idx]) else None
            category = str(category_series.iloc[idx]).strip().upper() if category_series is not None and pd.notna(category_series.iloc[idx]) else 'A'
            
            if not old_drg or not new_drg or old_drg == 'nan' or new_drg == 'nan':
                continue
            
            # Calculate price difference
            old_price, new_price, difference = calculate_drg_difference(old_drg, new_drg, category)
            
            if difference == 0:
                continue
            
            total_cases_with_drg_change += 1
            total_impact += difference
            
            # Get hospital name
            hospital_name = "Unknown"
            if hospital_col and hospital_col in df.columns:
                hospital_name = str(df.iloc[idx][hospital_col])
            elif len(df.columns) > 0:
                # Try first column as hospital name
                hospital_name = str(df.iloc[idx, 0]) if pd.notna(df.iloc[idx, 0]) else "Unknown"
            
            # Get department
            department = "Unknown"
            if department_col and department_col in df.columns:
                department = str(df.iloc[idx][department_col])
            
            # Get specialist
            specialist = "Unknown"
            if specialist_col and specialist_col in df.columns:
                specialist = str(df.iloc[idx][specialist_col])
            
            # Aggregate by hospital
            if hospital_name not in hospital_impacts:
                hospital_impacts[hospital_name] = {
                    'total_impact': 0.0,
                    'cases': 0,
                    'positive_changes': 0,
                    'negative_changes': 0
                }
            hospital_impacts[hospital_name]['total_impact'] += difference
            hospital_impacts[hospital_name]['cases'] += 1
            if difference > 0:
                hospital_impacts[hospital_name]['positive_changes'] += 1
            else:
                hospital_impacts[hospital_name]['negative_changes'] += 1
            
            # Aggregate by department
            if department not in department_impacts:
                department_impacts[department] = {'total_impact': 0.0, 'cases': 0}
            department_impacts[department]['total_impact'] += difference
            department_impacts[department]['cases'] += 1
            
            # Aggregate by specialist
            if specialist not in specialist_impacts:
                specialist_impacts[specialist] = {'total_impact': 0.0, 'cases': 0}
            specialist_impacts[specialist]['total_impact'] += difference
            specialist_impacts[specialist]['cases'] += 1
            
            # Store detail
            drg_changes_detail.append({
                'row': idx + 1,
                'hospital': hospital_name,
                'department': department,
                'specialist': specialist,
                'old_drg': old_drg,
                'new_drg': new_drg,
                'category': category,
                'old_price': round(old_price, 2),
                'new_price': round(new_price, 2),
                'difference': round(difference, 2)
            })
            
        except Exception as e:
            logger.warning(f"⚠️ Error processing row {idx}: {str(e)}")
            continue
    
    # Format results
    result = {
        'summary': {
            'total_cases_analyzed': len(df),
            'cases_with_drg_change': total_cases_with_drg_change,
            'total_financial_impact_sar': round(total_impact, 2),
            'total_impact_formatted': f"{total_impact:,.2f} ريال",
            'average_impact_per_case': round(total_impact / total_cases_with_drg_change, 2) if total_cases_with_drg_change > 0 else 0
        },
        'by_hospital': [
            {
                'hospital_name': name,
                'total_impact_sar': round(data['total_impact'], 2),
                'impact_formatted': f"{data['total_impact']:,.2f} ريال",
                'cases': data['cases'],
                'positive_changes': data['positive_changes'],
                'negative_changes': data['negative_changes']
            }
            for name, data in sorted(hospital_impacts.items(), key=lambda x: x[1]['total_impact'], reverse=True)
        ],
        'by_department': [
            {
                'department': name,
                'total_impact_sar': round(data['total_impact'], 2),
                'impact_formatted': f"{data['total_impact']:,.2f} ريال",
                'cases': data['cases']
            }
            for name, data in sorted(department_impacts.items(), key=lambda x: x[1]['total_impact'], reverse=True)
        ],
        'by_specialist': [
            {
                'specialist': name,
                'total_impact_sar': round(data['total_impact'], 2),
                'impact_formatted': f"{data['total_impact']:,.2f} ريال",
                'cases': data['cases']
            }
            for name, data in sorted(specialist_impacts.items(), key=lambda x: x[1]['total_impact'], reverse=True)
        ],
        'drg_changes_detail': drg_changes_detail[:100]  # Limit to first 100 for API response
    }
    
    logger.info(f"✅ DRG analysis complete: {total_cases_with_drg_change} changes, {total_impact:,.2f} SAR impact")
    
    return result


# Test function
if __name__ == "__main__":
    print("Testing DRG Price Loader...")
    prices = load_drg_prices("/tmp/drg_prices.xlsx")
    print(f"Loaded {len(prices)} DRG codes")
    
    # Test specific codes
    test_codes = ['801A', '801B', 'A13A', 'B02A']
    for code in test_codes:
        if code in prices:
            print(f"\n{code}:")
            print(f"  Category A: {prices[code]['A']:,.2f} SAR")
            print(f"  Category B: {prices[code]['B']:,.2f} SAR")
            print(f"  Category C: {prices[code]['C']:,.2f} SAR")
