"""
Security Models for CDI Application
Includes: MFA, Audit Logs, Password Policies, Session Management
"""
from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid
import re

# ========== MFA Models ==========
class OTPRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    email: str
    otp_code: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime
    is_used: bool = False
    attempts: int = 0

class MFASetupRequest(BaseModel):
    user_id: str
    email: str

class MFAVerifyRequest(BaseModel):
    email: str
    otp_code: str

# ========== Audit Log Models ==========
class AuditLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    action: str  # login, logout, create_note, edit_note, delete_note, etc.
    resource_type: Optional[str] = None  # note, user, analysis, etc.
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    status: str  # success, failure
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AuditLogQuery(BaseModel):
    user_id: Optional[str] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None
    limit: int = 100
    skip: int = 0

# ========== Password Policy Models ==========
class PasswordHistory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    password_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str
    
    @validator('new_password')
    def validate_password_strength(cls, v):
        """Enforce strong password policy"""
        if len(v) < 12:
            raise ValueError('Password must be at least 12 characters long')
        
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit')
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        
        # Check for common weak passwords
        weak_passwords = ['Password123!', 'Welcome123!', 'Admin123!', 'User123456!']
        if v in weak_passwords:
            raise ValueError('This password is too common. Please choose a stronger password')
        
        return v

class PasswordResetWithOTP(BaseModel):
    email: EmailStr
    otp_code: str
    new_password: str

# ========== Session Management Models ==========
class SessionRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    token: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime
    is_active: bool = True

class ActiveSession(BaseModel):
    session_id: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime
    last_activity: datetime
    is_current: bool = False

# ========== Rate Limiting Models ==========
class LoginAttempt(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    ip_address: Optional[str] = None
    success: bool
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AccountLockout(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    email: str
    locked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    unlock_at: datetime
    reason: str

# ========== Security Settings Models ==========
class UserSecuritySettings(BaseModel):
    user_id: str
    mfa_enabled: bool = True
    mfa_method: str = "email"  # email, authenticator, sms
    password_last_changed: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    password_expires_at: datetime
    failed_login_attempts: int = 0
    account_locked: bool = False
    locked_until: Optional[datetime] = None

# ========== Security Dashboard Models ==========
class SecurityDashboardStats(BaseModel):
    total_users: int
    active_sessions: int
    failed_login_attempts_today: int
    locked_accounts: int
    audit_logs_today: int
    mfa_enabled_users: int
    password_expiring_soon: int

class SecurityAlert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    severity: str  # high, medium, low
    type: str  # multiple_failed_logins, suspicious_activity, etc.
    user_id: Optional[str] = None
    description: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved: bool = False
