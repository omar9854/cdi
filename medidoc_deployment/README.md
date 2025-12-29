# MediDoc AI - Clinical Documentation Improvement System

## 🏥 Overview

MediDoc AI is an advanced Clinical Documentation Improvement (CDI) system powered by **Qwen2.5-72B** large language model. It acts as a **Senior Medical Auditor** to analyze clinical notes and provide:

- **Principal & Secondary Diagnosis Identification**
- **ICD-10-AM Code Assignment**
- **Evidence-Based Clinical Reasoning**
- **DRG Cost Estimation with RAG Pipeline**
- **Physician Query Generation**

## 🖥️ System Requirements

### Hardware
- **GPU**: NVIDIA A100 40GB (required for 72B model)
- **RAM**: 64GB minimum
- **Storage**: 500GB SSD
- **CPU**: 8+ cores

### Software
- Ubuntu 22.04 LTS
- Python 3.11+
- NVIDIA CUDA 11.8+
- MongoDB 6.0+
- Nginx

## 📦 Installation

### 1. Clone and Setup

```bash
# Run setup script
chmod +x setup_server.sh
./setup_server.sh
```

### 2. Configure Environment

```bash
cp .env.example .env
nano .env  # Edit with your settings
```

### 3. Load DRG Price List (Optional)

Place your DRG price list file at:
```
/opt/medidoc-ai/backend/data/drg_prices.xlsx
```

Expected columns:
- `DRG_Code`: DRG code (e.g., K60A)
- `Description`: DRG description
- `Relative_Weight`: Relative weight for cost calculation

## 🚀 Usage

### Start Services

```bash
sudo systemctl start medidoc-backend
sudo systemctl start nginx
```

### Check Status

```bash
sudo systemctl status medidoc-backend
sudo journalctl -u medidoc-backend -f  # View logs
```

## 📊 API Endpoints

### Analysis

```http
POST /api/analyze
Content-Type: application/json
Authorization: Bearer <token>

{
    "note_id": "uuid"
}
```

**Response:**
```json
{
    "principal_diagnosis": {
        "diagnosis_en": "Type 2 Diabetes with poor control",
        "diagnosis_ar": "داء السكري النوع 2 مع سوء التحكم",
        "icd_code": "E11.65",
        "evidence": "HbA1c 9.5% indicating poor glycemic control",
        "drg_code": "K60A",
        "relative_weight": 1.45,
        "estimated_cost": 7250.0
    },
    "secondary_diagnoses": [...],
    "physician_queries": [...],
    "drg_summary": {
        "estimated_drg": "K60A",
        "base_drg_weight": 1.45,
        "cc_adjustment": 0.3,
        "final_weight": 1.75,
        "base_rate": 5000.0,
        "total_estimated_cost": 8750.0
    }
}
```

### Chat (CDI-Focused)

```http
POST /api/chat/{analysis_id}
Content-Type: application/json
Authorization: Bearer <token>

{
    "message": "What is the evidence for diabetic nephropathy?"
}
```

## 🔧 Configuration

### Model Settings

In `local_llm.py`:
```python
DEFAULT_MODEL = "Qwen/Qwen2.5-72B-Instruct"  # Main model
FALLBACK_MODEL = "Qwen/Qwen2.5-7B-Instruct"  # Fallback if 72B fails
```

### DRG Base Rate

In `.env`:
```
DRG_BASE_RATE=5000.0  # SAR
```

### Load Custom DRG Price List

```python
from drg_lookup import DRGLookup

drg = DRGLookup()
drg.load_from_file("/path/to/drg_prices.xlsx")
drg.set_base_rate(5000.0)
```

## 📋 ICD-10-AM Codes

The system uses **ICD-10-AM (Australian Modification)** codes. Key mappings:

| Code | Description | DRG | Weight |
|------|-------------|-----|--------|
| E11.65 | Type 2 DM with hyperglycemia | K60A | 1.45 |
| E11.40 | Type 2 DM with neuropathy | K60A | 1.45 |
| E11.21 | Type 2 DM with nephropathy | K60A | 1.45 |
| I10 | Essential hypertension | F74B | 0.55 |
| I50.9 | Heart failure | F62B | 1.05 |
| N18.3 | CKD Stage 3 | L63A | 1.25 |
| N18.5 | CKD Stage 5 | L60A | 3.20 |

## 🔒 Security Notes

1. Change `JWT_SECRET_KEY` in production
2. Use HTTPS with SSL certificate
3. Configure firewall rules
4. Regular security updates

## 📞 Support

For issues or questions, contact:
- Email: support@medidoc.ai

## 📄 License

Proprietary - All rights reserved.
