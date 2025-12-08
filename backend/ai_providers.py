"""
AI Providers Integration Module
Supports: Google Gemini, Grok (X.AI), Microsoft Azure OpenAI
"""
import os
import random
import logging
from typing import Optional, Dict, List
import google.generativeai as genai
from openai import AzureOpenAI
import anthropic

logger = logging.getLogger(__name__)

class AIProviderManager:
    """Manages multiple AI providers and their API keys"""
    
    def __init__(self, db):
        self.db = db
        self.providers = {
            'gemini': self._call_gemini,
            'azure': self._call_azure,
            'grok': self._call_grok
        }
    
    async def get_api_keys(self, provider: str) -> List[str]:
        """Get API keys for a specific provider from database"""
        settings = await self.db.ai_settings.find_one({"provider": provider})
        if settings and settings.get('api_keys'):
            return settings['api_keys']
        
        # Fallback to environment variables
        if provider == 'gemini':
            keys = [
                os.environ.get('GEMINI_API_KEY_1'),
                os.environ.get('GEMINI_API_KEY_2'),
                os.environ.get('GEMINI_API_KEY_3'),
                os.environ.get('GEMINI_API_KEY_4'),
                os.environ.get('GEMINI_API_KEY_5'),
                os.environ.get('GEMINI_API_KEY_6'),
                os.environ.get('GEMINI_API_KEY_7')
            ]
            return [key for key in keys if key]
        elif provider == 'azure':
            key = os.environ.get('AZURE_OPENAI_KEY')
            return [key] if key else []
        elif provider == 'grok':
            key = os.environ.get('GROK_API_KEY')
            return [key] if key else []
        
        return []
    
    async def save_api_keys(self, provider: str, api_keys: List[str]):
        """Save API keys for a specific provider to database"""
        await self.db.ai_settings.update_one(
            {"provider": provider},
            {"$set": {
                "provider": provider,
                "api_keys": api_keys,
                "updated_at": genai.datetime.now().isoformat()
            }},
            upsert=True
        )
        logger.info(f"Updated API keys for provider: {provider}")
    
    async def analyze_with_ai(self, provider: str, prompt: str, system_instruction: str) -> str:
        """Analyze using specified AI provider"""
        if provider not in self.providers:
            raise ValueError(f"Unsupported AI provider: {provider}")
        
        api_keys = await self.get_api_keys(provider)
        if not api_keys:
            raise ValueError(f"No API keys configured for provider: {provider}")
        
        # Use random key for load balancing
        api_key = random.choice(api_keys)
        
        return await self.providers[provider](api_key, prompt, system_instruction)
    
    async def _call_gemini(self, api_key: str, prompt: str, system_instruction: str) -> str:
        """Call Google Gemini API"""
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                'gemini-1.5-flash',
                system_instruction=system_instruction
            )
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            raise
    
    async def _call_azure(self, api_key: str, prompt: str, system_instruction: str) -> str:
        """Call Microsoft Azure OpenAI API"""
        try:
            endpoint = os.environ.get('AZURE_OPENAI_ENDPOINT', 'https://your-resource.openai.azure.com/')
            deployment = os.environ.get('AZURE_OPENAI_DEPLOYMENT', 'gpt-4')
            api_version = os.environ.get('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')
            
            client = AzureOpenAI(
                api_key=api_key,
                api_version=api_version,
                azure_endpoint=endpoint
            )
            
            messages = [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ]
            
            response = client.chat.completions.create(
                model=deployment,
                messages=messages,
                temperature=0.7,
                max_tokens=4000
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Azure OpenAI API error: {str(e)}")
            raise
    
    async def _call_grok(self, api_key: str, prompt: str, system_instruction: str) -> str:
        """Call Grok (X.AI) API"""
        try:
            # Grok uses OpenAI-compatible API
            from openai import OpenAI
            
            client = OpenAI(
                api_key=api_key,
                base_url="https://api.x.ai/v1"
            )
            
            messages = [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ]
            
            response = client.chat.completions.create(
                model="grok-beta",
                messages=messages,
                temperature=0.7,
                max_tokens=4000
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Grok API error: {str(e)}")
            raise
    
    async def get_available_providers(self) -> Dict[str, bool]:
        """Get list of available AI providers with their status"""
        providers = {}
        for provider in ['gemini', 'azure', 'grok']:
            keys = await self.get_api_keys(provider)
            providers[provider] = len(keys) > 0
        return providers
