"""
AI-Powered Coding Assistant
Uses Gemini API to help medical coders with ICD-10-AM coding
"""
import os
import json
import google.generativeai as genai
from typing import List, Dict

# Configure Gemini
GEMINI_API_KEYS = [
    os.environ.get('GEMINI_API_KEY_1'),
    os.environ.get('GEMINI_API_KEY_2'),
    os.environ.get('GEMINI_API_KEY_3'),
    os.environ.get('GEMINI_API_KEY_4'),
    os.environ.get('GEMINI_API_KEY_5'),
]
current_key_index = 0

def get_next_api_key():
    global current_key_index
    key = GEMINI_API_KEYS[current_key_index]
    current_key_index = (current_key_index + 1) % len(GEMINI_API_KEYS)
    return key

async def analyze_case_for_coding(clinical_summary: str, chief_complaint: str, procedures: List[str], icd_codes: List[Dict]) -> Dict:
    """
    Analyze medical case and suggest ICD-10-AM codes
    """
    try:
        # Configure API
        api_key = get_next_api_key()
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Create ICD codes context
        icd_context = "\n".join([f"- {code['code']}: {code['description_ar']} ({code['description_en']})" 
                                 for code in icd_codes[:20]])  # Top 20 relevant codes
        
        prompt = f"""أنت مساعد ترميز طبي متخصص في ICD-10-AM الأسترالي (المستخدم في السعودية).

**معلومات الحالة:**
- الشكوى الرئيسية: {chief_complaint}
- الملخص السريري: {clinical_summary}
- الإجراءات: {', '.join(procedures) if procedures else 'لا يوجد'}

**أكواد ICD-10-AM المتاحة:**
{icd_context}

**المطلوب:**
1. حدد التشخيص الرئيسي (Principal Diagnosis) الأنسب
2. حدد التشخيصات الثانوية (Secondary Diagnoses) المهمة
3. حدد إذا كانت هناك مضاعفات (CC/MCC)
4. اقترح DRG المتوقع
5. قدم ملاحظات للمرمز

**الإجابة يجب أن تكون بصيغة JSON:**
{{
  "principal_diagnosis": {{
    "code": "كود ICD",
    "description": "الوصف بالعربية",
    "confidence": "عالي/متوسط/منخفض",
    "reasoning": "السبب"
  }},
  "secondary_diagnoses": [
    {{
      "code": "كود ICD",
      "description": "الوصف",
      "is_complication": true/false,
      "reasoning": "السبب"
    }}
  ],
  "suggested_drg": "DRG-XXX",
  "coding_notes": "ملاحظات مهمة للمرمز",
  "documentation_gaps": ["فجوات في التوثيق إن وجدت"]
}}

تأكد من استخدام أكواد ICD-10-AM الصحيحة من القائمة المتاحة."""

        # Generate response
        response = model.generate_content(prompt)
        result_text = response.text.strip()
        
        # Extract JSON from markdown if present
        if '```json' in result_text:
            result_text = result_text.split('```json')[1].split('```')[0].strip()
        elif '```' in result_text:
            result_text = result_text.split('```')[1].split('```')[0].strip()
        
        # Parse JSON
        result = json.loads(result_text)
        
        return {
            "success": True,
            "analysis": result,
            "raw_response": response.text
        }
        
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": "Failed to parse AI response",
            "raw_response": result_text if 'result_text' in locals() else ""
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

async def search_icd_smart(query: str, icd_codes: List[Dict]) -> List[Dict]:
    """
    Smart ICD code search with AI assistance
    """
    try:
        # First do basic search
        query_lower = query.lower()
        basic_results = [
            code for code in icd_codes
            if query_lower in code['code'].lower() 
            or query_lower in code['description_ar'].lower()
            or query_lower in code['description_en'].lower()
        ]
        
        if basic_results:
            return basic_results[:10]
        
        # If no results, use AI for semantic search
        api_key = get_next_api_key()
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        icd_context = "\n".join([f"{code['code']}: {code['description_ar']}" 
                                 for code in icd_codes[:100]])
        
        prompt = f"""من قائمة أكواد ICD-10-AM التالية، اختر أنسب 5 أكواد لـ: "{query}"

الأكواد المتاحة:
{icd_context}

أرجع الأكواد فقط كقائمة JSON:
["CODE1", "CODE2", "CODE3", "CODE4", "CODE5"]"""

        response = model.generate_content(prompt)
        result_text = response.text.strip()
        
        # Extract codes
        if '```json' in result_text:
            result_text = result_text.split('```json')[1].split('```')[0].strip()
        elif '```' in result_text:
            result_text = result_text.split('```')[1].split('```')[0].strip()
        
        suggested_codes = json.loads(result_text)
        
        # Find full details
        results = [code for code in icd_codes if code['code'] in suggested_codes]
        return results
        
    except Exception as e:
        print(f"Smart search error: {e}")
        return []

async def calculate_drg_value(principal_code: str, secondary_codes: List[str], drg_prices: List[Dict]) -> Dict:
    """
    Calculate DRG and estimated value based on diagnoses
    """
    try:
        # Simple DRG matching logic (can be enhanced)
        # For now, just match based on principal diagnosis category
        
        base_drg = None
        for drg in drg_prices:
            # Match DRG (simplified - real logic is more complex)
            if any(principal_code.startswith(prefix) for prefix in ['E11', 'E10']):
                if 'diabetes' in drg['description_en'].lower() or 'سكري' in drg['description_ar']:
                    base_drg = drg
                    break
            elif principal_code.startswith('I'):
                if 'cardiovascular' in drg['description_en'].lower() or 'قلب' in drg['description_ar']:
                    base_drg = drg
                    break
            elif principal_code.startswith('J'):
                if 'respiratory' in drg['description_en'].lower() or 'تنفس' in drg['description_ar']:
                    base_drg = drg
                    break
        
        if not base_drg and drg_prices:
            base_drg = drg_prices[0]  # Default to first DRG
        
        if base_drg:
            # Calculate value with complications adjustment
            has_complications = len(secondary_codes) > 2
            adjustment = 1.3 if has_complications else 1.0
            
            estimated_value = base_drg['base_price'] * base_drg['weight'] * adjustment
            
            return {
                "drg_code": base_drg['drg_code'],
                "description": base_drg['description_ar'],
                "weight": base_drg['weight'],
                "base_price": base_drg['base_price'],
                "adjustment": adjustment,
                "estimated_value": round(estimated_value, 2),
                "has_complications": has_complications
            }
        
        return {"error": "No matching DRG found"}
        
    except Exception as e:
        return {"error": str(e)}
