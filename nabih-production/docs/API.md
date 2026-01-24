# Nabih Platform - API Documentation

## Base URL
```
http://your-server-ip/api
```

## Authentication

### Login Step 1 - Request OTP
```http
POST /api/auth/login-step1
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "yourpassword"
}
```

**Response:**
```json
{
    "requires_mfa": true,
    "message": "OTP sent to your email",
    "email": "user@example.com"
}
```

### Login Step 2 - Verify OTP
```http
POST /api/auth/login-step2
Content-Type: application/json

{
    "email": "user@example.com",
    "otp_code": "123456"
}
```

**Response:**
```json
{
    "access_token": "eyJ...",
    "token_type": "bearer",
    "user": {
        "id": "uuid",
        "email": "user@example.com",
        "role": "user"
    }
}
```

---

## Notes

### Create Note
```http
POST /api/notes
Authorization: Bearer {token}
Content-Type: application/json

{
    "title": "Patient Case #123",
    "content": "Clinical notes text...",
    "doctor_notes": [
        {
            "specialty": "Internal Medicine",
            "text": "Patient presents with..."
        }
    ]
}
```

### Get Notes
```http
GET /api/notes
Authorization: Bearer {token}
```

---

## Analysis

### Analyze Note
```http
POST /api/analyze
Authorization: Bearer {token}
Content-Type: application/json

{
    "note_id": "note-uuid"
}
```

**Response:**
```json
{
    "id": "analysis-uuid",
    "principal_diagnosis": {
        "diagnosis_ar": "التهاب رئوي",
        "diagnosis_en": "Pneumonia",
        "icd_code": "J18.9",
        "evidence": "Patient admitted with pneumonia..."
    },
    "secondary_diagnoses": [...],
    "inferred_diagnoses": [...],
    "documentation_gaps": [...],
    "queries_ar": [...],
    "case_summary": {...}
}
```

### Get Analysis
```http
GET /api/analysis/{note_id}
Authorization: Bearer {token}
```

---

## Chat

### Ask Question
```http
POST /api/chat/ask-question/{question_id}
Authorization: Bearer {token}
Content-Type: application/json

{
    "analysis_id": "analysis-uuid",
    "message": "What about the patient's potassium level?",
    "language": "ar"
}
```

---

## Error Responses

```json
{
    "detail": "Error message"
}
```

| Status Code | Description |
|-------------|-------------|
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 500 | Internal Server Error |
