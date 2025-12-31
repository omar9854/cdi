import re

with open("server.py", "r") as f:
    content = f.read()

# Find and replace the Gemini chat section in chat_with_ai_by_path
old_gemini_chat = '''        try:
            # Use Google Gemini API with automatic key rotation
            model = get_gemini_model('gemini-2.0-flash-exp', system_instruction=system_message)
            
            # Get chat history for context
            chat_history = []
            previous_messages = await db.chat_messages.find(
                {"analysis_id": analysis_id}
            ).sort("created_at", 1).to_list(100)
            
            # Build chat history
            for msg in previous_messages:
                # Handle both open chat messages (with 'role') and predefined questions (with 'question'/'answer')
                if 'role' in msg:
                    if msg['role'] == 'user':
                        chat_history.append({'role': 'user', 'parts': [msg['message']]})
                    else:
                        chat_history.append({'role': 'model', 'parts': [msg['message']]})
                elif 'question' in msg and 'answer' in msg:
                    # Predefined question format
                    chat_history.append({'role': 'user', 'parts': [msg['question']]})
                    chat_history.append({'role': 'model', 'parts': [msg['answer']]})
            
            # Start chat with history and retry logic
            max_retries = len(GEMINI_API_KEYS)
            response_text = None
            
            for attempt in range(max_retries):
                try:
                    chat = model.start_chat(history=chat_history)
                    response = chat.send_message(user_question)
                    response_text = response.text
                    break  # Success, exit retry loop
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Chat retry {attempt + 1}/{max_retries} with different API key")
                        model = get_gemini_model('gemini-2.0-flash-exp', system_instruction=system_message)
                    else:
                        raise e'''

new_local_chat = '''        try:
            # Use Local Qwen2.5-72B for chat (100% Offline)
            from local_llm import generate_text
            
            # Get chat history for context
            previous_messages = await db.chat_messages.find(
                {"analysis_id": analysis_id}
            ).sort("created_at", 1).to_list(100)
            
            # Build conversation with history
            conversation = f"{system_message}\\n\\n"
            for msg in previous_messages:
                if 'role' in msg and msg['role'] in ['user', 'assistant']:
                    role_label = "المستخدم" if msg['role'] == 'user' else "المساعد"
                    conversation += f"{role_label}: {msg['message']}\\n\\n"
                elif 'question' in msg and 'answer' in msg:
                    conversation += f"المستخدم: {msg['question']}\\n\\n"
                    conversation += f"المساعد: {msg['answer']}\\n\\n"
            
            conversation += f"المستخدم: {user_question}\\n\\nالمساعد:"
            
            logger.info("Using Qwen2.5-72B Local AI for enhanced chat...")
            response_text = generate_text(conversation, max_new_tokens=1500, temperature=0.3)
            logger.info("Local AI chat successful")'''

if old_gemini_chat in content:
    content = content.replace(old_gemini_chat, new_local_chat)
    with open("server.py", "w") as f:
        f.write(content)
    print("SUCCESS: Replaced Gemini chat with local_llm in chat_with_ai_by_path")
else:
    print("WARNING: Gemini chat pattern not found in chat_with_ai_by_path")
