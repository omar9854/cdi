import re

with open("server.py", "r") as f:
    content = f.read()

# Find and update the chat system_message in both chat endpoints
old_system_message = '''system_message = f"""You are a Clinical Documentation Improvement (CDI) specialist. You have reviewed a clinical case and now the user wants to discuss the analysis with you.

Context:
{context}

Answer questions professionally, provide clarifications, and help improve the documentation. Respond in the same language as the user's question. 

IMPORTANT: Be VERY concise and direct. Give precise answers without unnecessary details. Focus only on the specific question asked. Maximum 3-4 sentences unless more detail is specifically requested."""'''

new_system_message = '''system_message = f"""أنت أخصائي تحسين التوثيق السريري (CDI Specialist).

## مهمتك في المناقشة:
1. اكتشاف التشخيصات غير الموثقة التي لها معطيات في الملاحظات
2. توليد استفسارات للطبيب مدعومة بالأدلة
3. طلب توضيح النوع والشدة والمرحلة لكل تشخيص

## سياق الحالة:
{context}

## قواعد الإجابة:
- إذا سُئلت عن تشخيص، ابحث عن معطيات تدعمه في الملاحظات
- إذا وجدت مؤشرات لتشخيص غير موثق، اقترح استفساراً للطبيب
- اذكر دائماً الدليل من الملاحظات
- اقترح الكود ICD-10 المناسب
- اطلب توضيح: النوع (Type)، الشدة (Severity)، المرحلة (Stage)، السبب (Etiology)

## مثال على صيغة الاستفسار:
"بناءً على: [المعطيات من الملاحظات]
التشخيص المحتمل: [التشخيص + الكود]
السؤال للطبيب: هل يمكن توثيق هذا التشخيص مع تحديد النوع/الشدة/المرحلة؟"

أجب بنفس لغة السؤال (عربي أو إنجليزي)."""'''

count = content.count(old_system_message)
if count > 0:
    content = content.replace(old_system_message, new_system_message)
    with open("server.py", "w") as f:
        f.write(content)
    print(f"SUCCESS: Updated {count} chat system_message(s)")
else:
    print("WARNING: Old system_message not found, trying partial match...")
    
    # Try to find and replace just the English part
    old_partial = '''Answer questions professionally, provide clarifications, and help improve the documentation. Respond in the same language as the user's question. 

IMPORTANT: Be VERY concise and direct. Give precise answers without unnecessary details. Focus only on the specific question asked. Maximum 3-4 sentences unless more detail is specifically requested."""'''
    
    new_partial = '''## قواعد الإجابة:
- إذا سُئلت عن تشخيص، ابحث عن معطيات تدعمه في الملاحظات
- إذا وجدت مؤشرات لتشخيص غير موثق، اقترح استفساراً للطبيب مدعوماً بالدليل
- اطلب توضيح: النوع (Type)، الشدة (Severity)، المرحلة (Stage)، السبب (Etiology)
- اذكر الكود ICD-10 المناسب

صيغة الاستفسار: "بناءً على [الدليل]، هل يمكن توثيق [التشخيص] مع تحديد [النوع/الشدة/المرحلة]؟"

أجب بنفس لغة السؤال."""'''
    
    if old_partial in content:
        content = content.replace(old_partial, new_partial)
        with open("server.py", "w") as f:
            f.write(content)
        print("SUCCESS: Updated chat prompts with partial match")
    else:
        print("INFO: Could not find exact match, manual update may be needed")
