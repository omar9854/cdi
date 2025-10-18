# Email Configuration Guide | دليل إعداد البريد الإلكتروني

## Current Status | الحالة الحالية

✅ **Implemented Features:**
- Login page updated with new logo (`download-2.png`)
- "Forgot Password" link added to login page
- Password reset flow (frontend + backend)
- Welcome email system for new users
- Password reset email system

## Email Configuration Required | التكوين المطلوب للبريد الإلكتروني

### Gmail App Password Setup (for almaghthawi.cdi@gmail.com)

To enable email sending, you need to generate a Gmail **App Password**:

#### Steps to Generate App Password:

1. **Go to your Google Account:**
   - Visit: https://myaccount.google.com/

2. **Enable 2-Step Verification** (if not already enabled):
   - Go to Security → 2-Step Verification
   - Follow the setup process

3. **Generate App Password:**
   - Go to Security → 2-Step Verification → App passwords
   - Select "Mail" as the app
   - Select "Other" as the device and name it "CDI Platform"
   - Click "Generate"
   - **Copy the 16-character password** (e.g., "abcd efgh ijkl mnop")

4. **Update Backend Configuration:**
   - Open file: `/app/backend/.env`
   - Find the line: `SMTP_PASSWORD=""`
   - Replace with: `SMTP_PASSWORD="your-16-character-app-password"`
   - Remove spaces from the password
   - Restart backend: `sudo supervisorctl restart backend`

### Example Configuration:

```
EMAIL_FROM="almaghthawi.cdi@gmail.com"
SMTP_HOST="smtp.gmail.com"
SMTP_PORT=587
SMTP_USER="almaghthawi.cdi@gmail.com"
SMTP_PASSWORD="abcdefghijklmnop"
```

## Current Behavior | السلوك الحالي

**Without SMTP Password:**
- Registration works ✅
- Login works ✅
- Password reset works ✅
- **Emails are NOT sent** ⚠️ (logged as warning in backend logs)

**With SMTP Password Configured:**
- Registration works ✅
- Login works ✅
- Password reset works ✅
- **Welcome emails are sent** 📧
- **Password reset emails are sent** 📧

## Email Templates | قوالب البريد الإلكتروني

### 1. Welcome Email (Sent on Registration)
- **Subject:** "مرحباً بك في مركز الترميز الطبي | Welcome to Medical Coding Center"
- **Content:** Bilingual (Arabic/English) welcome message
- **Includes:** Platform features overview

### 2. Password Reset Email
- **Subject:** "إعادة تعيين كلمة المرور | Password Reset"
- **Content:** Bilingual password reset instructions
- **Includes:** 
  - Reset link (valid for 1 hour)
  - Security notice
  - From: almaghthawi.cdi@gmail.com

## Testing Without Email (Current State)

The application is **fully functional** without email configuration:

1. **Registration:** Works, but no welcome email
2. **Login:** Works normally
3. **Forgot Password:** Frontend displays success message, but no email sent
4. **Password Reset:** Cannot test end-to-end without email

## Next Steps | الخطوات التالية

### Option 1: Configure Gmail (Recommended)
Follow the steps above to enable email sending

### Option 2: Test Without Email
Continue using the app - email failures won't break functionality

### Option 3: Use Alternative Email Service
- Update `.env` with different SMTP provider (e.g., SendGrid, AWS SES)

---

## Technical Details | التفاصيل التقنية

**Backend Files Modified:**
- `/app/backend/server.py` - Added email functions and password reset endpoints
- `/app/backend/.env` - Added email configuration variables
- `/app/backend/requirements.txt` - Added `aiosmtplib` package

**Frontend Files Created:**
- `/app/frontend/src/pages/ForgotPassword.jsx` - Forgot password page
- `/app/frontend/src/pages/ResetPassword.jsx` - Reset password page

**Frontend Files Modified:**
- `/app/frontend/src/App.js` - Added routes for password reset pages
- `/app/frontend/src/pages/Login.jsx` - Added "Forgot Password" link and updated logo
- `/app/frontend/src/contexts/LanguageContext.jsx` - Added password reset translations

**API Endpoints Added:**
- `POST /api/auth/forgot-password` - Request password reset
- `POST /api/auth/reset-password` - Reset password with token
- Modified: `POST /api/auth/register` - Now sends welcome email

---

© 2025 جميع الحقوق محفوظة | عمر المغذوي
