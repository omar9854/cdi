import re

with open("server.py", "r") as f:
    content = f.read()

# New code to replace Ollama section
new_code = '''        # Use Local Qwen2.5-72B AI (100% Offline)
        if provider in ['meditron', 'phi3', 'azure', 'gemini', 'local']:
            # All providers now use local Qwen2.5-72B
            logger.info("Using Qwen2.5-72B Local AI...")
            
            try:
                # Use the wrapper that calls local_llm
                result = await analyze_with_local_llm(notes_text, doctor_notes)
                return result
                
            except Exception as e:
                logger.error(f"Local AI error: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")'''

# Find and replace the Ollama section
# Pattern: from "# Use Meditron" to the error handling
pattern = r'        # Use Meditron-70B via Ollama \(local medical AI\)\n.*?raise HTTPException\(status_code=500, detail=f"فشل التحليل: \{str\(e\)\}"\)'

new_content = re.sub(pattern, new_code, content, flags=re.DOTALL)

if new_content != content:
    with open("server.py", "w") as f:
        f.write(new_content)
    print("SUCCESS: Replaced Ollama with local_llm")
else:
    print("WARNING: Pattern not found, no changes made")
