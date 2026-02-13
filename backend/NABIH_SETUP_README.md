# NABIH Platform - Setup & Operations Guide

## 🚀 Quick Start

```bash
cd /app/backend
./start_nabih.sh
```

## 🛑 Stop Platform

```bash
cd /app/backend
./stop_nabih.sh
```

## 📁 File Structure

```
/app/backend/
├── server.py                 # Main FastAPI application
├── nabih_config.py           # Hardcoded system prompts & configuration
├── local_llm_vllm_fixed.py   # Ollama integration with persistent config
├── start_nabih.sh            # Startup script (ready-to-use)
├── stop_nabih.sh             # Shutdown script
└── .env                      # Environment variables
```

## ⚙️ Configuration

### AI Models (stored locally on disk)
- **Analysis**: qwen2.5:32b (19GB) - stored in ~/.ollama/models
- **Chat**: qwen2.5:7b (4.7GB) - stored in ~/.ollama/models

### System Prompts (hardcoded in nabih_config.py)
- CDI_ANALYSIS_SYSTEM_PROMPT: Clinical analysis instructions
- CDI_CHAT_SYSTEM_PROMPT: Chat assistant instructions

### Hospital Categories (DRG calculation)
- Category A: 25,000 SAR/case
- Category B: 21,250 SAR/case (0.85x)
- Category C: 17,500 SAR/case (0.70x)

## 🔧 Services

| Service | Port | Auto-start |
|---------|------|------------|
| MongoDB | 27017 | ✅ Yes |
| Ollama | 11434 | ✅ Yes |
| Backend | 8001 | ✅ Yes |
| Nginx | 80 | ✅ Yes |

## 📊 Monitoring

```bash
# View backend logs
sudo journalctl -u nabeeh_api -f

# Check service status
systemctl status nabeeh_api ollama mongod nginx

# Check AI models
ollama list
```

## 🔄 After Server Restart

Simply run:
```bash
./start_nabih.sh
```

The platform will:
1. Start MongoDB (if not running)
2. Start Ollama (if not running)
3. Load AI models from local disk (instant)
4. Start Backend API
5. Verify all services

**Expected startup time: ~10 seconds**
