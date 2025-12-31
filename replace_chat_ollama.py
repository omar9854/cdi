import re

with open("server.py", "r") as f:
    content = f.read()

# Find and replace chat Ollama section
old_chat_pattern = r'''        # Use Meditron-70B via Ollama for chat
        logger\.info\("🏥 Using Meditron-70B for chat\.\.\."\)
        
        try:
            import requests
            
            ollama_host = os\.environ\.get\('OLLAMA_HOST', 'http://localhost:11434'\)
            ollama_model = os\.environ\.get\('OLLAMA_MODEL', 'meditron:70b'\)
            
            # Build conversation history
            conversation = f"\{system_message\}\\n\\n"
            for msg in previous_messages:
                if 'role' in msg and msg\['role'\] in \['user', 'assistant'\]:
                    role_label = "User" if msg\['role'\] == 'user' else "Assistant"
                    conversation \+= f"\{role_label\}: \{msg\['message'\]\}\\n\\n"
            conversation \+= f"User: \{chat_request\.message\}\\n\\nAssistant:"
            
            response = requests\.post\(
                f"\{ollama_host\}/api/generate",
                json=\{
                    "model": ollama_model,
                    "prompt": conversation,
                    "stream": False,
                    "options": \{
                        "temperature": 0\.7,
                        "num_predict": 1000
                    \}
                \},
                timeout=120
            \)
            
            if response\.status_code == 200:
                response_text = response\.json\(\)\.get\("response", ""\)\.strip\(\)
                logger\.info\("✅ Meditron chat successful"\)
            else:
                raise Exception\(f"Ollama error: \{response\.status_code\}"\)
                
        except Exception as e:
            logger\.error\(f"❌ Meditron chat error: \{str\(e\)\}"\)
            raise HTTPException\(status_code=500, detail=f"فشلت الدردشة: \{str\(e\)\}"\)'''

new_chat_code = '''        # Use Local Qwen2.5-72B for chat
        logger.info("Using Qwen2.5-72B Local AI for chat...")
        
        try:
            from local_llm import generate_text
            
            # Build conversation history
            conversation = f"{system_message}\\n\\n"
            for msg in previous_messages:
                if 'role' in msg and msg['role'] in ['user', 'assistant']:
                    role_label = "User" if msg['role'] == 'user' else "Assistant"
                    conversation += f"{role_label}: {msg['message']}\\n\\n"
            conversation += f"User: {chat_request.message}\\n\\nAssistant:"
            
            response_text = generate_text(conversation, max_new_tokens=1000, temperature=0.7)
            logger.info("Local AI chat successful")
                
        except Exception as e:
            logger.error(f"Local AI chat error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")'''

# Use simpler string matching
old_section = '''        # Use Meditron-70B via Ollama for chat
        logger.info("🏥 Using Meditron-70B for chat...")
        
        try:
            import requests
            
            ollama_host = os.environ.get('OLLAMA_HOST', 'http://localhost:11434')
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
                raise Exception(f"Ollama error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Meditron chat error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"فشلت الدردشة: {str(e)}")'''

if old_section in content:
    content = content.replace(old_section, new_chat_code)
    with open("server.py", "w") as f:
        f.write(content)
    print("SUCCESS: Replaced chat Ollama with local_llm")
else:
    print("WARNING: Chat Ollama pattern not found")
