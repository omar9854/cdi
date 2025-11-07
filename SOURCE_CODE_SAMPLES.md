# عينات من الكود البرمجي - CDI System
# Source Code Samples

**نظام تحسين التوثيق السريري**  
**التاريخ:** نوفمبر 2025

---

## 📋 جدول المحتويات

1. [Backend - Python/FastAPI](#backend)
2. [Frontend - React/JavaScript](#frontend)
3. [قاعدة البيانات - MongoDB](#database)
4. [الأمان - Security](#security)
5. [الذكاء الاصطناعي - AI](#ai)

---

<a name="backend"></a>
# 1️⃣ Backend - Python/FastAPI

## server.py - الملف الرئيسي

### الإعدادات الأساسية

```python
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from slowapi import Limiter
import os
import bcrypt
import jwt
import google.generativeai as genai
from datetime import datetime, timezone, timedelta
import uuid

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create FastAPI app
app = FastAPI()

# JWT Settings
SECRET_KEY = os.environ.get('JWT_SECRET', 'your-secret-key')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Gemini API Keys (multiple for rotation)
GEMINI_API_KEYS = [
    os.environ.get('GEMINI_API_KEY_1'),
    os.environ.get('GEMINI_API_KEY_2'),
    os.environ.get('GEMINI_API_KEY_3')
]
```

---

### نظام تلقائي لإنشاء حساب الأدمن

```python
async def ensure_admin_account():
    """Automatically ensure admin account exists on startup"""
    try:
        admin_email = "almaghthawi.cdi@gmail.com"
        admin_password = "CDI@2024#Admin"
        
        print(f"🔍 Checking admin account...")
        
        # Delete ALL admin accounts first
        deleted = await db.users.delete_many({'role': 'admin'})
        if deleted.deleted_count > 0:
            print(f"🗑️  Deleted {deleted.deleted_count} old admin account(s)")
        
        # Create fresh admin account
        print(f"👤 Creating admin account: {admin_email}")
        hashed = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt())
        
        admin_user = {
            'id': str(uuid.uuid4()),
            'email': admin_email,
            'password_hash': hashed.decode('utf-8'),
            'full_name': 'مدير النظام - System Administrator',
            'phone_number': '+966500000000',
            'role': 'admin',
            'mfa_enabled': True,
            'is_active': True,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'failed_login_attempts': 0,
            'account_locked_until': None
        }
        
        await db.users.insert_one(admin_user)
        print(f"✅ Admin account ready: {admin_email}")
        
        # Clean up old OTP and login attempts
        await db.otp_records.delete_many({})
        await db.login_attempts.delete_many({})
        print(f"🧹 Cleaned old OTP and login attempts")
        
    except Exception as e:
        print(f"❌ Error ensuring admin account: {e}")

# Run on startup
@app.on_event("startup")
async def startup_event():
    await ensure_admin_account()
```

---

### وظائف المساعدة - Helper Functions

```python
def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(
        password.encode('utf-8'), 
        bcrypt.gensalt()
    ).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(
        password.encode('utf-8'), 
        hashed.encode('utf-8')
    )

def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    """Decode and verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

---

### API Endpoints - المصادقة

```python
@api_router.post("/auth/login-step1")
@limiter.limit("5/minute")
async def login_step1(
    credentials: UserLogin, 
    request: Request
):
    """Login Step 1: Verify credentials and send OTP"""
    
    # Find user
    user = await db.users.find_one(
        {"email": credentials.email},
        {"_id": 0}
    )
    
    if not user:
        raise HTTPException(
            status_code=401, 
            detail="Invalid credentials"
        )
    
    # Check if account is locked
    if user.get('account_locked_until'):
        locked_until = datetime.fromisoformat(
            user['account_locked_until']
        )
        if datetime.now(timezone.utc) < locked_until:
            raise HTTPException(
                status_code=423,
                detail="Account is locked"
            )
    
    # Verify password
    if not verify_password(
        credentials.password, 
        user['password_hash']
    ):
        # Increment failed attempts
        await db.users.update_one(
            {"id": user['id']},
            {
                "$inc": {"failed_login_attempts": 1},
                "$set": {"last_failed_login": datetime.now(timezone.utc)}
            }
        )
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )
    
    # Generate OTP
    otp_code = ''.join(random.choices('0123456789', k=6))
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
    
    # Save OTP to database
    await db.otp_records.insert_one({
        "email": credentials.email,
        "otp_code": otp_code,
        "expires_at": expires_at,
        "is_used": False,
        "created_at": datetime.now(timezone.utc)
    })
    
    # Send OTP via email
    await send_otp_email(credentials.email, user['full_name'], otp_code)
    
    return {
        "message": "OTP sent to your email",
        "mfa_required": True
    }

@api_router.post("/auth/login-step2")
async def login_step2(verification: OTPVerification):
    """Login Step 2: Verify OTP and issue token"""
    
    # Find OTP record
    otp_record = await db.otp_records.find_one({
        "email": verification.email,
        "otp_code": verification.otp_code,
        "is_used": False
    })
    
    if not otp_record:
        raise HTTPException(
            status_code=401,
            detail="Invalid OTP"
        )
    
    # Check expiration
    if datetime.now(timezone.utc) > otp_record['expires_at']:
        raise HTTPException(
            status_code=401,
            detail="OTP expired"
        )
    
    # Mark OTP as used
    await db.otp_records.update_one(
        {"_id": otp_record['_id']},
        {"$set": {"is_used": True}}
    )
    
    # Get user
    user = await db.users.find_one(
        {"email": verification.email},
        {"_id": 0}
    )
    
    # Reset failed attempts
    await db.users.update_one(
        {"id": user['id']},
        {
            "$set": {
                "failed_login_attempts": 0,
                "last_login": datetime.now(timezone.utc)
            }
        }
    )
    
    # Create access token
    token = create_access_token({"user_id": user['id']})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }
```

---

### API Endpoints - تحليل الملاحظات

```python
@api_router.post("/analysis/analyze")
async def analyze_note(
    request: AnalyzeRequest,
    current_user: dict = Depends(get_current_user)
):
    """Analyze clinical note using AI"""
    
    # Get note
    note = await db.clinical_notes.find_one(
        {"id": request.note_id},
        {"_id": 0}
    )
    
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Prepare combined text from all doctor notes
    combined_text = "\n\n".join([
        f"التخصص: {n.get('specialty', 'غير محدد')}\n{n['text']}"
        for n in note['doctor_notes']
    ])
    
    # Call AI analysis
    analysis_result = await analyze_clinical_note_advanced(combined_text)
    
    # Save analysis to database
    analysis = {
        "id": str(uuid.uuid4()),
        "note_id": note['id'],
        "user_id": current_user['id'],
        "diagnoses_to_document": analysis_result['diagnoses'],
        "missing_documentation": analysis_result['missing_docs'],
        "gaps_ar": analysis_result['gaps_ar'],
        "gaps_en": analysis_result['gaps_en'],
        "queries_ar": analysis_result['queries_ar'],
        "queries_en": analysis_result['queries_en'],
        "recommendations_ar": analysis_result['recommendations_ar'],
        "recommendations_en": analysis_result['recommendations_en'],
        "summary_ar": analysis_result['summary_ar'],
        "summary_en": analysis_result['summary_en'],
        "created_at": datetime.now(timezone.utc)
    }
    
    await db.analyses.insert_one(analysis)
    
    return analysis
```

---

### تكامل الذكاء الاصطناعي - AI Integration

```python
def get_gemini_model(model_name='gemini-flash-latest', system_instruction=None):
    """Get Gemini model with load balancing"""
    api_key = random.choice(GEMINI_API_KEYS)
    genai.configure(api_key=api_key)
    
    if system_instruction:
        return genai.GenerativeModel(
            model_name, 
            system_instruction=system_instruction
        )
    else:
        return genai.GenerativeModel(model_name)

async def analyze_clinical_note_advanced(note_text: str):
    """Advanced AI analysis of clinical notes"""
    
    system_instruction = """
    أنت متخصص في تحسين التوثيق السريري (CDI Specialist) وخبير في:
    1. تحليل الملاحظات الطبية السريرية
    2. تحديد الثغرات في التوثيق
    3. تخصيص أكواد ICD-10-CM
    4. توليد استفسارات دقيقة للأطباء
    
    المهام:
    - تحليل شامل للملاحظات
    - تحديد التشخيصات الناقصة
    - اقتراح تحسينات للتوثيق
    """
    
    prompt = f"""
    حلل هذه الملاحظة الطبية بشكل شامل:
    
    {note_text}
    
    قدم النتائج بصيغة JSON مع:
    1. diagnoses: قائمة التشخيصات (عربي، إنجليزي، ICD-10-CM)
    2. gaps_ar: الثغرات بالعربية
    3. gaps_en: الثغرات بالإنجليزية
    4. queries_ar: استفسارات للطبيب بالعربية
    5. queries_en: استفسارات بالإنجليزية
    6. recommendations_ar: توصيات بالعربية
    7. recommendations_en: توصيات بالإنجليزية
    8. summary_ar: ملخص بالعربية
    9. summary_en: ملخص بالإنجليزية
    """
    
    model = get_gemini_model(system_instruction=system_instruction)
    response = model.generate_content(prompt)
    
    # Parse JSON response
    result = json.loads(response.text)
    
    return result
```

---

<a name="frontend"></a>
# 2️⃣ Frontend - React/JavaScript

## App.js - التطبيق الرئيسي

```javascript
import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { LanguageProvider, useLanguage } from '@/contexts/LanguageContext';
import { Toaster } from 'sonner';

// Import pages
import Login from '@/pages/Login';
import Dashboard from '@/pages/Dashboard';
import AdminDashboard from '@/pages/AdminDashboard';
import NewNote from '@/pages/NewNote';
import Analysis from '@/pages/Analysis';

function AppContent() {
  const { t } = useLanguage();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const userData = localStorage.getItem('user');
    
    if (token && userData) {
      setUser(JSON.parse(userData));
    }
    setLoading(false);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl">{t('loading')}</div>
      </div>
    );
  }

  return (
    <div className="App">
      <Toaster position="top-center" richColors closeButton />
      <BrowserRouter>
        <Routes>
          <Route 
            path="/login" 
            element={!user ? <Login setUser={setUser} /> : <Navigate to="/dashboard" />} 
          />
          <Route 
            path="/dashboard" 
            element={user ? <Dashboard user={user} onLogout={handleLogout} /> : <Navigate to="/login" />} 
          />
          <Route 
            path="/admin" 
            element={user && user.role === 'admin' ? <AdminDashboard user={user} /> : <Navigate to="/dashboard" />} 
          />
          <Route 
            path="/" 
            element={<Navigate to={user ? "/dashboard" : "/login"} />} 
          />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

function App() {
  return (
    <LanguageProvider>
      <AppContent />
    </LanguageProvider>
  );
}

export default App;
```

---

## Login.jsx - صفحة تسجيل الدخول

```javascript
import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { useLanguage } from '@/contexts/LanguageContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardHeader, CardContent } from '@/components/ui/card';

const Login = ({ setUser }) => {
  const navigate = useNavigate();
  const { t, language } = useLanguage();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL;
      
      // Step 1: Send credentials
      const response = await axios.post(
        `${backendUrl}/api/auth/login-step1`,
        { email, password }
      );

      if (response.data.mfa_required) {
        // Navigate to MFA verification
        navigate('/mfa-verify', { 
          state: { email } 
        });
        toast.success(
          language === 'ar' 
            ? 'تم إرسال رمز التحقق إلى بريدك الإلكتروني' 
            : 'Verification code sent to your email'
        );
      }
    } catch (error) {
      console.error('Login error:', error);
      const message = error.response?.data?.detail || 'Login failed';
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <Card className="w-full max-w-md shadow-xl">
        <CardHeader>
          <h2 className="text-2xl font-bold text-center">
            {t('login')}
          </h2>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                {t('email')}
              </label>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="example@email.com"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">
                {t('password')}
              </label>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="••••••••"
              />
            </div>

            <Button 
              type="submit" 
              className="w-full"
              disabled={loading}
            >
              {loading ? t('loading') : t('login')}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default Login;
```

---

## MFAVerification.jsx - التحقق الثنائي

```javascript
import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate, useLocation } from 'react-router-dom';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

const MFAVerification = ({ setUser }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const email = location.state?.email;
  
  const [otpCode, setOtpCode] = useState('');
  const [loading, setLoading] = useState(false);

  const handleVerifyOTP = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL;
      
      const response = await axios.post(
        `${backendUrl}/api/auth/login-step2`,
        { 
          email, 
          otp_code: otpCode 
        }
      );

      // Save token and user data
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
      
      setUser(response.data.user);
      toast.success('Login successful!');
      navigate('/dashboard');
      
    } catch (error) {
      console.error('OTP verification error:', error);
      toast.error('Invalid or expired OTP');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="w-full max-w-md p-8">
        <h2 className="text-2xl font-bold mb-6">Enter Verification Code</h2>
        
        <form onSubmit={handleVerifyOTP}>
          <Input
            type="text"
            value={otpCode}
            onChange={(e) => setOtpCode(e.target.value)}
            placeholder="Enter 6-digit code"
            maxLength={6}
            required
          />
          
          <Button 
            type="submit" 
            className="w-full mt-4"
            disabled={loading}
          >
            {loading ? 'Verifying...' : 'Verify'}
          </Button>
        </form>
      </div>
    </div>
  );
};

export default MFAVerification;
```

---

## Dashboard.jsx - لوحة التحكم

```javascript
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import Navbar from '@/components/Navbar';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

const Dashboard = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    totalNotes: 0,
    totalAnalyses: 0,
    recentNotes: []
  });

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL;
      const token = localStorage.getItem('token');
      
      const response = await axios.get(
        `${backendUrl}/api/dashboard/stats`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar user={user} onLogout={onLogout} />
      
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-8">
          Welcome, {user.full_name}
        </h1>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card>
            <CardHeader>Total Notes</CardHeader>
            <CardContent>
              <p className="text-4xl font-bold">{stats.totalNotes}</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>Analyses</CardHeader>
            <CardContent>
              <p className="text-4xl font-bold">{stats.totalAnalyses}</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>Quick Actions</CardHeader>
            <CardContent>
              <Button 
                onClick={() => navigate('/new-note')}
                className="w-full"
              >
                Create New Note
              </Button>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>Recent Notes</CardHeader>
          <CardContent>
            <div className="space-y-4">
              {stats.recentNotes.map((note) => (
                <div 
                  key={note.id}
                  className="p-4 border rounded-lg hover:bg-gray-50 cursor-pointer"
                  onClick={() => navigate(`/analysis/${note.id}`)}
                >
                  <h3 className="font-semibold">{note.title}</h3>
                  <p className="text-sm text-gray-500">
                    {new Date(note.created_at).toLocaleDateString()}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;
```

---

<a name="database"></a>
# 3️⃣ قاعدة البيانات - MongoDB

## MongoDB Schemas

### Users Collection
```javascript
{
  _id: ObjectId,
  id: "uuid-string",
  email: "user@example.com",
  password_hash: "bcrypt-hashed-password",
  full_name: "John Doe",
  phone_number: "+966500000000",
  role: "admin" | "supervisor" | "user",
  mfa_enabled: true,
  is_active: true,
  created_at: ISODate("2025-11-07T..."),
  last_login: ISODate("2025-11-07T..."),
  failed_login_attempts: 0,
  account_locked_until: null,
  supervisor_id: "uuid-string" // for regular users
}
```

### Clinical Notes Collection
```javascript
{
  _id: ObjectId,
  id: "uuid-string",
  user_id: "uuid-string",
  title: "Patient Case Note",
  doctor_notes: [
    {
      text: "Clinical note text...",
      specialty: "cardiology"
    }
  ],
  created_at: ISODate("2025-11-07T..."),
  updated_at: ISODate("2025-11-07T...")
}
```

### Analyses Collection
```javascript
{
  _id: ObjectId,
  id: "uuid-string",
  note_id: "uuid-string",
  user_id: "uuid-string",
  diagnoses_to_document: [
    {
      diagnosis_ar: "فشل القلب الاحتقاني",
      diagnosis_en: "Congestive Heart Failure",
      icd_code: "I50.9"
    }
  ],
  gaps_ar: ["معلومات ناقصة عن..."],
  gaps_en: ["Missing information about..."],
  queries_ar: ["هل يعاني المريض من...؟"],
  queries_en: ["Does the patient have...?"],
  summary_ar: "ملخص التحليل...",
  summary_en: "Analysis summary...",
  created_at: ISODate("2025-11-07T...")
}
```

---

<a name="security"></a>
# 4️⃣ الأمان - Security

## Password Hashing with Bcrypt

```python
import bcrypt

def hash_password(password: str) -> str:
    """
    Hash password using bcrypt with 12 rounds
    """
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash
    """
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )
```

---

## JWT Token Management

```python
import jwt
from datetime import datetime, timedelta, timezone

SECRET_KEY = os.environ['JWT_SECRET']
ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: timedelta = None):
    """
    Create JWT access token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=7)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt

def verify_token(token: str):
    """
    Verify and decode JWT token
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")
```

---

## Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/auth/login-step1")
@limiter.limit("5/minute")  # 5 attempts per minute
async def login(request: Request, credentials: UserLogin):
    # Login logic
    pass

@app.post("/api/analysis/analyze")
@limiter.limit("10/minute")  # 10 analyses per minute
async def analyze(request: Request, data: AnalyzeRequest):
    # Analysis logic
    pass
```

---

<a name="ai"></a>
# 5️⃣ الذكاء الاصطناعي - AI Integration

## Google Gemini Integration

```python
import google.generativeai as genai
import random

# Configure multiple API keys for load balancing
GEMINI_API_KEYS = [
    os.environ.get('GEMINI_API_KEY_1'),
    os.environ.get('GEMINI_API_KEY_2'),
    os.environ.get('GEMINI_API_KEY_3')
]

def get_gemini_model(system_instruction=None):
    """
    Get Gemini model with random API key for load balancing
    """
    api_key = random.choice(GEMINI_API_KEYS)
    genai.configure(api_key=api_key)
    
    if system_instruction:
        return genai.GenerativeModel(
            'gemini-2.0-flash-exp',
            system_instruction=system_instruction
        )
    return genai.GenerativeModel('gemini-2.0-flash-exp')

async def analyze_clinical_note(note_text: str, language: str = 'ar'):
    """
    Analyze clinical note using AI
    """
    system_instruction = """
    أنت متخصص في تحسين التوثيق السريري (CDI Specialist).
    مهمتك:
    1. تحليل الملاحظات الطبية
    2. تحديد الثغرات في التوثيق
    3. تخصيص أكواد ICD-10-CM
    4. توليد استفسارات للأطباء
    """
    
    prompt = f"""
    حلل الملاحظة الطبية التالية:
    
    {note_text}
    
    قدم:
    1. التشخيصات المحتملة مع أكواد ICD-10-CM
    2. الثغرات في التوثيق
    3. استفسارات للطبيب لتحسين التوثيق
    4. توصيات CDI
    
    الرد بصيغة JSON
    """
    
    model = get_gemini_model(system_instruction=system_instruction)
    
    try:
        response = model.generate_content(prompt)
        result = json.loads(response.text)
        return result
    except Exception as e:
        print(f"AI Analysis Error: {e}")
        raise HTTPException(500, "AI analysis failed")
```

---

## معلومات الحساب الافتراضي

```
البريد الإلكتروني: almaghthawi.cdi@gmail.com
كلمة المرور: CDI@2024#Admin
الدور: admin
```

---

**© 2025 CDI System - Source Code Samples**
**جميع الحقوق محفوظة**
