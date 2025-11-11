import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { toast } from 'sonner';
import { Shield, ArrowRight, RefreshCw } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';
import { getErrorMessage, logError } from '@/utils/errorHandler';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const MFAVerification = ({ setUser }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { language } = useLanguage();
  
  const [otpCode, setOtpCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [timer, setTimer] = useState(1800); // 30 minutes

  const email = location.state?.email;
  const tempToken = location.state?.tempToken;

  useEffect(() => {
    if (!email || !tempToken) {
      navigate('/login');
      return;
    }

    // Countdown timer (30 minutes = 1800 seconds)
    setTimer(1800);
    const interval = setInterval(() => {
      setTimer((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [email, tempToken, navigate]);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleVerify = async (e) => {
    e.preventDefault();
    
    if (otpCode.length !== 6) {
      toast.error(language === 'ar' ? 'يرجى إدخال رمز مكون من 6 أرقام' : 'Please enter a 6-digit code');
      return;
    }

    setLoading(true);

    try {
      // Complete login with step 2
      const loginResponse = await axios.post(`${API}/auth/login-step2`, {
        email: email,
        otp_code: otpCode
      });

      localStorage.setItem('token', loginResponse.data.access_token);
      localStorage.setItem('user', JSON.stringify(loginResponse.data.user));
      setUser(loginResponse.data.user);

      toast.success(language === 'ar' ? 'تم التحقق بنجاح! مرحباً بك' : 'Verification successful! Welcome');
      
      // Route based on department and role
      const user = loginResponse.data.user;
      if (user.department === 'coding') {
        if (user.coding_role === 'coder') {
          navigate('/coder');
        } else if (user.coding_role === 'auditor') {
          navigate('/auditor');
        } else if (user.role === 'supervisor' || user.role === 'admin') {
          navigate('/coding-supervisor');
        } else {
          navigate('/dashboard');
        }
      } else {
        navigate('/dashboard');
      }
    } catch (error) {
      logError('MFA Verification', error);
      const errorMessage = getErrorMessage(
        error,
        language === 'ar' ? 'رمز التحقق غير صحيح أو منتهي الصلاحية' : 'Invalid or expired OTP code'
      );
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setResending(true);
    try {
      await axios.post(`${API}/security/mfa/send-otp?email=${encodeURIComponent(email)}`);
      toast.success(language === 'ar' ? 'تم إرسال رمز جديد' : 'New code sent successfully');
      setTimer(1800); // Reset timer to 30 minutes
      setOtpCode('');
    } catch (error) {
      logError('Resend OTP', error);
      const errorMessage = getErrorMessage(
        error,
        language === 'ar' ? 'فشل إرسال الرمز' : 'Failed to send code'
      );
      toast.error(errorMessage);
    } finally {
      setResending(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 via-indigo-600 to-purple-700 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
            <Shield className="h-8 w-8 text-blue-600" />
          </div>
          <CardTitle className="text-2xl">
            {language === 'ar' ? 'التحقق الأمني' : 'Security Verification'}
          </CardTitle>
          <CardDescription className="text-base mt-2">
            {language === 'ar' 
              ? `تم إرسال رمز التحقق إلى بريدك الإلكتروني: ${email}. الرمز صالح لمدة 30 دقيقة.`
              : `Verification code sent to: ${email}. Valid for 30 minutes.`
            }
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleVerify} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                {language === 'ar' ? 'رمز التحقق (6 أرقام)' : 'Verification Code (6 digits)'}
              </label>
              <Input
                type="text"
                value={otpCode}
                onChange={(e) => {
                  const value = e.target.value.replace(/\D/g, '').slice(0, 6);
                  setOtpCode(value);
                }}
                placeholder="000000"
                className="text-center text-2xl font-bold tracking-widest"
                maxLength={6}
                autoFocus
              />
            </div>

            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">
                {language === 'ar' ? 'صالح لمدة:' : 'Valid for:'}
              </span>
              <span className={`font-bold ${timer < 60 ? 'text-red-600' : 'text-blue-600'}`}>
                {formatTime(timer)}
              </span>
            </div>

            {timer === 0 && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-800 text-center">
                {language === 'ar' ? 'انتهت صلاحية الرمز. يرجى طلب رمز جديد.' : 'Code expired. Please request a new one.'}
              </div>
            )}

            <Button
              type="submit"
              className="w-full bg-blue-600 hover:bg-blue-700 py-6 text-lg"
              disabled={loading || otpCode.length !== 6 || timer === 0}
            >
              {loading ? (
                <>
                  <RefreshCw className={`animate-spin h-5 w-5 ${language === 'ar' ? 'ml-2' : 'mr-2'}`} />
                  {language === 'ar' ? 'جاري التحقق...' : 'Verifying...'}
                </>
              ) : (
                <>
                  {language === 'ar' ? 'تحقق' : 'Verify'}
                  {language === 'ar' ? <ArrowRight className="mr-2" /> : <ArrowRight className="ml-2" />}
                </>
              )}
            </Button>

            <Button
              type="button"
              variant="outline"
              className="w-full"
              onClick={handleResend}
              disabled={resending || timer > 1740} // Allow resend after 1 minute (1800 - 60)
            >
              {resending ? (
                <>
                  <RefreshCw className={`animate-spin h-4 w-4 ${language === 'ar' ? 'ml-2' : 'mr-2'}`} />
                  {language === 'ar' ? 'جاري الإرسال...' : 'Sending...'}
                </>
              ) : (
                <>
                  <RefreshCw className={`h-4 w-4 ${language === 'ar' ? 'ml-2' : 'mr-2'}`} />
                  {language === 'ar' ? 'إعادة إرسال الرمز' : 'Resend Code'}
                </>
              )}
            </Button>

            <Button
              type="button"
              variant="ghost"
              className="w-full"
              onClick={() => navigate('/login')}
            >
              {language === 'ar' ? 'العودة لتسجيل الدخول' : 'Back to Login'}
            </Button>
          </form>

          <div className="mt-6 bg-amber-50 border border-amber-200 rounded-lg p-4">
            <p className="text-xs text-amber-800">
              <strong>{language === 'ar' ? 'ملاحظة أمنية:' : 'Security Note:'}</strong>
              {' '}
              {language === 'ar' 
                ? 'لا تشارك رمز التحقق مع أي شخص. لن يطلب فريق الدعم منك هذا الرمز أبداً.'
                : 'Never share your verification code. Support team will never ask for this code.'
              }
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default MFAVerification;
