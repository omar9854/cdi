import re

with open("server.py", "r") as f:
    content = f.read()

# 1. Replace Ollama analyze section with local_llm call
old_ollama_analyze = '''                ollama_host = os.environ.get('OLLAMA_HOST', 'http://127.0.0.1:11434')
                ollama_model = os.environ.get('OLLAMA_MODEL', 'phi3:latest')
                
                # Build comprehensive prompt for Meditron
                prompt = f\"\"\"You are a Clinical Documentation Improvement (CDI) Specialist with deep medical knowledge.
                
Your role is to:
1. Identify the Principal Diagnosis (main reason for admission)
2. List all Secondary Diagnoses (comorbidities and complications)
3. Find documentation gaps
4. Generate physician queries

Clinical Notes:
{notes_text}

Doctor Specialties and Notes:
\"\"\"
                for note in doctor_notes:
                    prompt += f\"\\n{note['specialty']}: {note['text']}\"
                
                prompt += \"\"\"

Analyze these notes and provide:
1. Principal Diagnosis with ICD-10-AM code and evidence
2. Secondary Diagnoses (each with ICD code, category, and evidence)
3. Documentation gaps (what's missing: type, severity, stage?)
4. Physician queries (for undocumented diagnoses)

Respond in JSON format.\"\"\"
                
                logger.info(f"📤 Sending to {ollama_model}...")
                
                response = requests.post(
                    f"{ollama_host}/api/generate",
                    json={
                        "model": ollama_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.1,
                            "num_predict": 4000
                        }
                    },
                    timeout=300
                )
                
                if response.status_code == 200:
                    response_text = response.json().get("response", "")
                    logger.info(f"✅ {ollama_model} analysis successful")'''

new_local_analyze = '''                # Use vLLM local analysis
                logger.info("🚀 Using vLLM with Qwen2.5-32B for analysis...")
                result = await analyze_with_local_llm(notes_text, doctor_notes)
                return result'''

if old_ollama_analyze in content:
    content = content.replace(old_ollama_analyze, new_local_analyze)
    print("✅ Replaced Ollama analyze section")
else:
    print("⚠️ Ollama analyze section not found exactly, trying regex...")
    # Use regex to find and replace
    pattern = r"ollama_host = os\.environ\.get\('OLLAMA_HOST'.*?logger\.info\(f\"✅ \{ollama_model\} analysis successful\"\)"
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, new_local_analyze.strip(), content, flags=re.DOTALL)
        print("✅ Replaced Ollama with regex")

# 2. Replace Ollama chat section
old_chat_ollama = '''            ollama_host = os.environ.get('OLLAMA_HOST', 'http://localhost:11434')
            ollama_model = os.environ.get('OLLAMA_MODEL', 'meditron:70b')
            
            # Build conversation history
            conversation = f"{system_message}\\n\\n"
            for msg in previous_messages:
                if 'role' in msg and msg['role'] in ['user', 'assistant']:
                    role_label = "User" if msg['role'] == 'user' else "Assistant"
                    conversation += f"{role_label}: {msg['message']}\\n\\n"
            conversation += f"User: {chat_request.message}\\n\\nAssistant:"
            
            response = requests.post(
                f"{ollama_host}/api/generate",
                json={
                    "model": ollama_model,
                    "prompt": conversation,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 1000
                    }
                },
                timeout=120
            )
            
            if response.status_code == 200:
                response_text = response.json().get("response", "").strip()
                logger.info("✅ Meditron chat successful")
            else:
                raise Exception(f"Ollama error: {response.status_code}")'''

new_chat_local = '''            # Use vLLM for chat
            from local_llm import generate_text
            
            conversation = f"{system_message}\\n\\n"
            for msg in previous_messages:
                if 'role' in msg and msg['role'] in ['user', 'assistant']:
                    role_label = "المستخدم" if msg['role'] == 'user' else "المساعد"
                    conversation += f"{role_label}: {msg['message']}\\n\\n"
            conversation += f"المستخدم: {chat_request.message}\\n\\nالمساعد:"
            
            logger.info("🚀 Using vLLM for chat...")
            response_text = generate_text(conversation, max_tokens=1500, temperature=0.3, use_chat_prompt=True)
            logger.info("✅ vLLM chat successful")'''

if old_chat_ollama in content:
    content = content.replace(old_chat_ollama, new_chat_local)
    print("✅ Replaced Ollama chat section")

# 3. Change app name to "منصة نبيه"
content = content.replace(
    '"message":"مركز الترميز الطبي وتحسين التوثيق السريري"',
    '"message":"منصة نبيه - الذكاء الاصطناعي لتحسين التوثيق السريري"'
)
print("✅ Changed app name to منصة نبيه")

# Save
with open("server.py", "w") as f:
    f.write(content)

print("✅ All updates complete!")
