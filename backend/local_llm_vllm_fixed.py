"""
Local LLM Integration with Ollama
This module provides functions for AI analysis and text generation using Ollama
Uses persistent configuration from nabih_config.py
"""

import os
import json
import requests
import logging
import re
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Import persistent configuration
try:
    from nabih_config import (
        AI_CONFIG, 
        CDI_ANALYSIS_SYSTEM_PROMPT, 
        CDI_CHAT_SYSTEM_PROMPT,
        get_analysis_prompt,
        get_chat_prompt
    )
    logger.info("✅ Loaded persistent configuration from nabih_config.py")
except ImportError:
    logger.warning("⚠️ nabih_config.py not found, using defaults")
    AI_CONFIG = {
        "analysis_model": "qwen2.5:32b",
        "chat_model": "qwen2.5:7b",
        "ollama_url": "http://localhost:11434",
        "temperature_analysis": 0.3,
        "temperature_chat": 0.7
    }
    CDI_ANALYSIS_SYSTEM_PROMPT = ""
    CDI_CHAT_SYSTEM_PROMPT = ""

# Ollama Configuration - from persistent config or environment
OLLAMA_URL = os.environ.get('OLLAMA_URL', AI_CONFIG.get('ollama_url', 'http://localhost:11434'))
ANALYSIS_MODEL = os.environ.get('OLLAMA_ANALYSIS_MODEL', AI_CONFIG.get('analysis_model', 'qwen2.5:32b'))
CHAT_MODEL = os.environ.get('OLLAMA_CHAT_MODEL', AI_CONFIG.get('chat_model', 'qwen2.5:7b'))


def analyze_clinical_notes(prompt: str, hospital_type: str = "A") -> Dict:
    """
    Analyze clinical notes using Ollama with Qwen2.5 model
    Uses hardcoded system prompt from nabih_config.py
    
    Args:
        prompt: The clinical notes to analyze
        hospital_type: Type of hospital (A, B, C)
    
    Returns:
        Dictionary containing analysis results
    """
    logger.info(f"🏥 Starting clinical notes analysis with Ollama ({ANALYSIS_MODEL})...")
    
    # Use persistent system prompt if available
    if CDI_ANALYSIS_SYSTEM_PROMPT:
        full_prompt = f"{CDI_ANALYSIS_SYSTEM_PROMPT}\n\n{prompt}"
        logger.info("📋 Using hardcoded system prompt from nabih_config.py")
    else:
        full_prompt = prompt
        logger.warning("⚠️ No system prompt configured, using raw prompt")
    
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": ANALYSIS_MODEL,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": AI_CONFIG.get('temperature_analysis', 0.3),
                    "num_predict": AI_CONFIG.get('max_tokens_analysis', 4096),
                    "top_p": 0.9
                }
            },
            timeout=AI_CONFIG.get('analysis_timeout', 300)  # 5 minutes timeout for analysis
        )
        
        if response.status_code != 200:
            logger.error(f"Ollama error: {response.status_code} - {response.text}")
            raise Exception(f"Ollama API error: {response.status_code}")
        
        result = response.json()
        response_text = result.get('response', '')
        
        logger.info(f"✅ Received response from Ollama ({len(response_text)} chars)")
        
        # Parse JSON from response
        parsed_result = parse_json_response(response_text)
        
        return parsed_result
        
    except requests.exceptions.Timeout:
        logger.error("❌ Ollama request timed out")
        raise Exception("تجاوز وقت الاستجابة. يرجى المحاولة مرة أخرى.")
    except requests.exceptions.ConnectionError:
        logger.error("❌ Cannot connect to Ollama")
        raise Exception("لا يمكن الاتصال بخدمة الذكاء الاصطناعي. تأكد من تشغيل Ollama.")
    except Exception as e:
        logger.error(f"❌ Analysis error: {str(e)}")
        raise


def generate_text(prompt: str, system_prompt: str = "", max_tokens: int = 2048) -> str:
    """
    Generate text using Ollama for chat functionality
    Uses hardcoded system prompt from nabih_config.py if not provided
    
    Args:
        prompt: User's message/question
        system_prompt: System instructions (optional, uses default if empty)
        max_tokens: Maximum tokens to generate
    
    Returns:
        Generated text response
    """
    logger.info(f"💬 Generating chat response with Ollama ({CHAT_MODEL})...")
    
    # Use provided system prompt, or fall back to hardcoded one
    effective_system_prompt = system_prompt if system_prompt else CDI_CHAT_SYSTEM_PROMPT
    
    if effective_system_prompt:
        full_prompt = f"{effective_system_prompt}\n\nسؤال المستخدم:\n{prompt}"
        logger.info("📋 Using system prompt for chat")
    else:
        full_prompt = prompt
    
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": CHAT_MODEL,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": AI_CONFIG.get('temperature_chat', 0.5),
                    "num_predict": AI_CONFIG.get('max_tokens_chat', 1024),
                    "num_ctx": AI_CONFIG.get('num_ctx_chat', 2048),
                    "top_p": 0.85,
                    "repeat_penalty": AI_CONFIG.get('repeat_penalty', 1.1)
                }
            },
            timeout=AI_CONFIG.get('chat_timeout', 60)
        )
        
        if response.status_code != 200:
            logger.error(f"Ollama chat error: {response.status_code}")
            raise Exception(f"Ollama API error: {response.status_code}")
        
        result = response.json()
        response_text = result.get('response', '')
        
        logger.info(f"✅ Chat response generated ({len(response_text)} chars)")
        
        return response_text
        
    except requests.exceptions.Timeout:
        logger.error("❌ Chat request timed out")
        raise Exception("تجاوز وقت الاستجابة. يرجى المحاولة مرة أخرى.")
    except requests.exceptions.ConnectionError:
        logger.error("❌ Cannot connect to Ollama for chat")
        raise Exception("لا يمكن الاتصال بخدمة الذكاء الاصطناعي.")
    except Exception as e:
        logger.error(f"❌ Chat error: {str(e)}")
        raise


def parse_json_response(text: str) -> Dict:
    """
    Parse JSON from AI response, handling common formatting issues
    """
    # Try to find JSON in the response
    json_patterns = [
        r'\{[\s\S]*\}',  # Match entire JSON object
        r'```json\s*([\s\S]*?)```',  # Match JSON in code block
        r'```\s*([\s\S]*?)```',  # Match any code block
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            try:
                # Clean up the match
                json_str = match.strip()
                if not json_str.startswith('{'):
                    continue
                    
                # Try to parse
                parsed = json.loads(json_str)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                continue
    
    # If no valid JSON found, return a structured response
    logger.warning("⚠️ Could not parse JSON from response, creating default structure")
    
    return {
        "principal_diagnosis": {
            "diagnosis_ar": "",
            "diagnosis_en": "",
            "icd_code": ""
        },
        "documented_diagnoses": [],
        "inferred_diagnoses": [],
        "documentation_gaps": [],
        "physician_queries": [],
        "recommendations_ar": [],
        "recommendations_en": [],
        "summary": {
            "summary_ar": text[:500] if text else "لم يتم التحليل",
            "summary_en": "Analysis could not be completed"
        }
    }


def check_ollama_status() -> Dict:
    """
    Check if Ollama is running and which models are available
    """
    try:
        # Check if Ollama is responding
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=10)
        
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [m.get('name', '') for m in models]
            
            return {
                "status": "running",
                "url": OLLAMA_URL,
                "models": model_names,
                "analysis_model": ANALYSIS_MODEL,
                "chat_model": CHAT_MODEL,
                "analysis_model_available": any(ANALYSIS_MODEL in m for m in model_names),
                "chat_model_available": any(CHAT_MODEL in m for m in model_names)
            }
        else:
            return {
                "status": "error",
                "message": f"Ollama returned status {response.status_code}"
            }
            
    except requests.exceptions.ConnectionError:
        return {
            "status": "offline",
            "message": "Cannot connect to Ollama. Make sure it's running."
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


# Test function
if __name__ == "__main__":
    print("Testing Ollama connection...")
    status = check_ollama_status()
    print(f"Status: {json.dumps(status, indent=2)}")
