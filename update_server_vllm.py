import re

with open("server.py", "r") as f:
    content = f.read()

# 1. Make Gemini optional
old_gemini_check = '''if not GEMINI_API_KEYS:
    raise ValueError("No Gemini API keys found in environment variables")

print(f"✅ Loaded {len(GEMINI_API_KEYS)} Gemini API keys for rotation")'''

new_gemini_check = '''# Gemini is optional - using local vLLM
if GEMINI_API_KEYS:
    print(f"✅ Loaded {len(GEMINI_API_KEYS)} Gemini API keys")
else:
    print("🚀 Running with LOCAL vLLM (Qwen2.5-32B on 4x V100)")'''

if old_gemini_check in content:
    content = content.replace(old_gemini_check, new_gemini_check)
    print("✅ Made Gemini optional")

# 2. Add import for local_llm wrapper
if "from analysis_wrapper import" not in content:
    content = content.replace(
        "import aiosmtplib",
        "import aiosmtplib\nfrom analysis_wrapper import analyze_with_local_llm"
    )
    print("✅ Added analysis_wrapper import")

# 3. Replace Ollama calls with local_llm
old_ollama = '''        # Use Meditron-70B via Ollama (local medical AI)
        if provider in ['meditron', 'phi3', 'azure', 'gemini']:'''

new_local = '''        # Use Local vLLM (Qwen2.5-32B on 4x V100)
        if provider in ['meditron', 'phi3', 'azure', 'gemini', 'local']:'''

if old_ollama in content:
    content = content.replace(old_ollama, new_local)
    print("✅ Updated provider check")

# Save
with open("server.py", "w") as f:
    f.write(content)

print("✅ server.py updated for vLLM!")
