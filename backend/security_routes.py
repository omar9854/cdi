"""
Security Routes for CDI Application
Includes: MFA, Audit Logs, Session Management, Security Dashboard
"""
from fastapi import APIRouter, HTTPException, Depends, Header, Request
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
from motor.motor_asyncio import AsyncIOMotorDatabase
import os

from security_models import (
    MFASetupRequest, MFAVerifyRequest, OTPRecord,
    AuditLog, AuditLogQuery,
    PasswordChangeRequest, PasswordResetWithOTP,
    SessionRecord, ActiveSession,
    SecurityDashboardStats, SecurityAlert,
    UserSecuritySettings
)
from security_utils import (
    generate_otp, send_otp_email, send_security_alert_email,
    log_audit, check_rate_limit, record_login_attempt,
    unlock_account_if_expired, check_password_history, is_password_expired
)

security_router = APIRouter(prefix="/security")

SECRET_KEY = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"

# ========== Helper Functions ==========
def get_client_ip(request: Request) -> Optional[str]:
    """Extract client IP address"""
    if request.client:
        return request.client.host
    return None

def get_user_agent(request: Request) -> Optional[str]:
    """Extract user agent"""
    return request.headers.get("user-agent")

async def get_current_user_from_token(authorization: Optional[str] = Header(None)):
    """Get current user from JWT token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

async def require_admin(user: dict = Depends(get_current_user_from_token)):
    """Require admin role"""
    if user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

# ========== MFA Endpoints ==========
@security_router.post("/mfa/send-otp")
async def send_mfa_otp(
    request: Request,
    email: str,
    db: AsyncIOMotorDatabase = Depends(lambda: None)  # Will be injected
):
    """Send OTP code for MFA"""
    try:
        # Get database from app state
        from server import db as database
        db = database
        
        # Check if user exists
        user = await db.users.find_one({"email": email}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Generate OTP
        otp_code = generate_otp()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        
        # Save OTP to database
        otp_record = OTPRecord(
            user_id=user['id'],
            email=email,
            otp_code=otp_code,
            expires_at=expires_at
        )
        
        doc = otp_record.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        doc['expires_at'] = doc['expires_at'].isoformat()
        
        await db.otp_records.insert_one(doc)
        
        # Send OTP via email
        user_name = user.get('full_name', 'المستخدم')
        email_sent = await send_otp_email(email, otp_code, user_name)
        
        if not email_sent:
            raise HTTPException(status_code=500, detail="Failed to send OTP email")
        
        # Log audit
        await log_audit(
            db,
            action="mfa_otp_sent",
            user_id=user['id'],
            user_email=email,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            status="success"
        )
        
        return {
            "message": "OTP sent successfully",
            "expires_in_minutes": 10
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error sending OTP: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send OTP")

@security_router.post("/mfa/verify-otp")
async def verify_mfa_otp(
    request: Request,
    verify_request: MFAVerifyRequest
):
    """Verify OTP code for MFA"""
    try:
        from server import db
        
        # Find OTP record
        otp_record = await db.otp_records.find_one({
            "email": verify_request.email,
            "otp_code": verify_request.otp_code,
            "is_used": False
        }, {"_id": 0})
        
        if not otp_record:
            # Log failed attempt
            await log_audit(
                db,
                action="mfa_verification_failed",
                user_email=verify_request.email,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                status="failure",
                details={"reason": "Invalid or expired OTP"}
            )
            raise HTTPException(status_code=400, detail="Invalid or expired OTP code")
        
        # Check expiration
        expires_at = datetime.fromisoformat(otp_record['expires_at'])
        if datetime.now(timezone.utc) > expires_at:
            await log_audit(
                db,
                action="mfa_verification_failed",
                user_email=verify_request.email,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                status="failure",
                details={"reason": "OTP expired"}
            )
            raise HTTPException(status_code=400, detail="OTP code has expired")
        
        # Mark OTP as used
        await db.otp_records.update_one(
            {"id": otp_record['id']},
            {"$set": {"is_used": True}}
        )
        
        # Log successful verification
        await log_audit(
            db,
            action="mfa_verification_success",
            user_id=otp_record['user_id'],
            user_email=verify_request.email,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            status="success"
        )
        
        return {
            "message": "OTP verified successfully",
            "user_id": otp_record['user_id']
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error verifying OTP: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to verify OTP")

# ========== Audit Log Endpoints ==========
@security_router.get("/audit-logs")
async def get_audit_logs(
    request: Request,
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    skip: int = 0,
    current_user: dict = Depends(require_admin)
):
    """Get audit logs (Admin only)"""
    try:
        from server import db
        
        # Build query
        query = {}
        if user_id:
            query['user_id'] = user_id
        if action:
            query['action'] = action
        if status:
            query['status'] = status
        
        if start_date or end_date:
            query['timestamp'] = {}
            if start_date:
                query['timestamp']['$gte'] = start_date
            if end_date:
                query['timestamp']['$lte'] = end_date
        
        # Get logs
        logs = await db.audit_logs.find(
            query,
            {"_id": 0}
        ).sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)
        
        # Get total count
        total = await db.audit_logs.count_documents(query)
        
        return {
            "logs": logs,
            "total": total,
            "limit": limit,
            "skip": skip
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting audit logs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get audit logs")

@security_router.get("/audit-logs/actions")
async def get_audit_log_actions(
    current_user: dict = Depends(require_admin)
):
    """Get list of all audit log action types"""
    try:
        from server import db
        
        actions = await db.audit_logs.distinct("action")
        return {"actions": sorted(actions)}
    
    except Exception as e:
        print(f"Error getting actions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get actions")

@security_router.get("/audit-logs/user/{user_id}")
async def get_user_audit_logs(
    user_id: str,
    limit: int = 50,
    current_user: dict = Depends(get_current_user_from_token)
):
    """Get audit logs for specific user (user can see their own, admin can see all)"""
    try:
        from server import db
        
        # Check authorization
        if current_user.get('id') != user_id and current_user.get('role') != 'admin':
            raise HTTPException(status_code=403, detail="Not authorized")
        
        logs = await db.audit_logs.find(
            {"user_id": user_id},
            {"_id": 0}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        
        return {"logs": logs}
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting user audit logs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get logs")

# ========== Password Management Endpoints ==========
@security_router.post("/password/change")
async def change_password(
    request: Request,
    password_request: PasswordChangeRequest,
    current_user: dict = Depends(get_current_user_from_token)
):
    """Change user password"""
    try:
        from server import db
        
        user_id = current_user['id']
        
        # Get user
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify old password
        if not bcrypt.checkpw(password_request.old_password.encode('utf-8'), user['password'].encode('utf-8')):
            await log_audit(
                db,
                action="password_change_failed",
                user_id=user_id,
                user_email=user['email'],
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                status="failure",
                details={"reason": "Incorrect old password"}
            )
            raise HTTPException(status_code=400, detail="Incorrect old password")
        
        # Get password history
        history = await db.password_history.find(
            {"user_id": user_id},
            {"_id": 0}
        ).sort("created_at", -1).limit(5).to_list(5)
        
        # Hash new password
        new_password_hash = bcrypt.hashpw(
            password_request.new_password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')
        
        # Check if password was used before
        password_hashes = [h['password_hash'] for h in history]
        if not check_password_history(password_request.new_password, password_hashes):
            raise HTTPException(
                status_code=400,
                detail="This password was used recently. Please choose a different password."
            )
        
        # Update password
        password_changed_at = datetime.now(timezone.utc)
        password_expires_at = password_changed_at + timedelta(days=90)
        
        await db.users.update_one(
            {"id": user_id},
            {
                "$set": {
                    "password": new_password_hash,
                    "password_last_changed": password_changed_at.isoformat(),
                    "password_expires_at": password_expires_at.isoformat()
                }
            }
        )
        
        # Save to password history
        await db.password_history.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "password_hash": new_password_hash,
            "created_at": password_changed_at.isoformat()
        })
        
        # Log audit
        await log_audit(
            db,
            action="password_changed",
            user_id=user_id,
            user_email=user['email'],
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            status="success"
        )
        
        # Send security alert
        await send_security_alert_email(
            user['email'],
            'password_changed',
            'تم تغيير كلمة المرور الخاصة بحسابك بنجاح.'
        )
        
        return {"message": "Password changed successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error changing password: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to change password")

# ========== Session Management Endpoints ==========
@security_router.get("/sessions/active")
async def get_active_sessions(
    current_user: dict = Depends(get_current_user_from_token)
):
    """Get all active sessions for current user"""
    try:
        from server import db
        
        user_id = current_user['id']
        
        sessions = await db.user_sessions.find(
            {"user_id": user_id, "is_active": True},
            {"_id": 0}
        ).sort("last_activity", -1).to_list(100)
        
        return {"sessions": sessions}
    
    except Exception as e:
        print(f"Error getting sessions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get sessions")

@security_router.post("/sessions/revoke/{session_id}")
async def revoke_session(
    session_id: str,
    current_user: dict = Depends(get_current_user_from_token)
):
    """Revoke a specific session"""
    try:
        from server import db
        
        # Update session
        result = await db.user_sessions.update_one(
            {"id": session_id, "user_id": current_user['id']},
            {"$set": {"is_active": False}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"message": "Session revoked successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error revoking session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to revoke session")

@security_router.post("/sessions/revoke-all")
async def revoke_all_sessions(
    request: Request,
    current_user: dict = Depends(get_current_user_from_token)
):
    """Revoke all sessions except current one"""
    try:
        from server import db
        
        # Get current token
        auth_header = request.headers.get("authorization", "")
        current_token = auth_header.split(" ")[1] if " " in auth_header else ""
        
        # Revoke all sessions except current
        await db.user_sessions.update_many(
            {
                "user_id": current_user['id'],
                "token": {"$ne": current_token},
                "is_active": True
            },
            {"$set": {"is_active": False}}
        )
        
        # Log audit
        await log_audit(
            db,
            action="all_sessions_revoked",
            user_id=current_user['id'],
            user_email=current_user.get('email'),
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            status="success"
        )
        
        return {"message": "All other sessions revoked successfully"}
    
    except Exception as e:
        print(f"Error revoking sessions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to revoke sessions")

# ========== Security Dashboard Endpoints ==========
@security_router.get("/dashboard/stats")
async def get_security_dashboard_stats(
    current_user: dict = Depends(require_admin)
):
    """Get security dashboard statistics (Admin only)"""
    try:
        from server import db
        
        # Total users
        total_users = await db.users.count_documents({})
        
        # Active sessions
        active_sessions = await db.user_sessions.count_documents({"is_active": True})
        
        # Failed logins today
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        failed_logins_today = await db.login_attempts.count_documents({
            "success": False,
            "timestamp": {"$gte": today_start.isoformat()}
        })
        
        # Locked accounts
        locked_accounts = await db.users.count_documents({"account_locked": True})
        
        # Audit logs today
        audit_logs_today = await db.audit_logs.count_documents({
            "timestamp": {"$gte": today_start.isoformat()}
        })
        
        # MFA enabled users
        mfa_enabled = await db.users.count_documents({"mfa_enabled": True})
        
        # Passwords expiring soon (within 30 days)
        thirty_days_from_now = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        password_expiring_soon = await db.users.count_documents({
            "password_expires_at": {
                "$lte": thirty_days_from_now,
                "$gte": datetime.now(timezone.utc).isoformat()
            }
        })
        
        stats = SecurityDashboardStats(
            total_users=total_users,
            active_sessions=active_sessions,
            failed_login_attempts_today=failed_logins_today,
            locked_accounts=locked_accounts,
            audit_logs_today=audit_logs_today,
            mfa_enabled_users=mfa_enabled,
            password_expiring_soon=password_expiring_soon
        )
        
        return stats.model_dump()
    
    except Exception as e:
        print(f"Error getting dashboard stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")

@security_router.get("/dashboard/recent-activities")
async def get_recent_security_activities(
    limit: int = 20,
    current_user: dict = Depends(require_admin)
):
    """Get recent security activities (Admin only)"""
    try:
        from server import db
        
        activities = await db.audit_logs.find(
            {"action": {"$in": [
                "login", "logout", "mfa_otp_sent", "mfa_verification_failed",
                "password_changed", "account_locked", "all_sessions_revoked"
            ]}},
            {"_id": 0}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        
        return {"activities": activities}
    
    except Exception as e:
        print(f"Error getting activities: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get activities")

import uuid
