import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { Lock, Mail, ArrowRight, Activity, Eye, EyeOff } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';
import { getErrorMessage } from '@/utils/errorHandler';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Login = ({ setUser }) => {
  const navigate = useNavigate();
  const { language, t } = useLanguage();
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Try new MFA flow first
      const response = await axios.post(`${API}/auth/login-step1`, formData);
      
      if (response.data.requires_mfa) {
        // Navigate to MFA verification page
        toast.success(
          language === 'ar' 
            ? '✅ تم إرسال رمز التحقق إلى بريدك الإلكتروني' 
            : '✅ Verification code sent to your email'
        );
        navigate('/mfa-verify', {
          state: {
            email: response.data.email,
            tempToken: formData.password
          }
        });
      } else {
        // MFA disabled, login directly
        const { access_token, user } = response.data;
        localStorage.setItem('token', access_token);
        localStorage.setItem('user', JSON.stringify(user));
        setUser(user);
        
        toast.success(t('loginSuccess'));
        
        // Route based on role
        if (user.role === 'supervisor' || user.role === 'admin') {
          navigate('/supervisor');
        } else {
          navigate('/dashboard');
        }
      }
    } catch (error) {
      let errorMessage;
      
      if (error.response?.status === 429) {
        errorMessage = language === 'ar'
          ? '⚠️ تم قفل الحساب مؤقتاً بسبب محاولات فاشلة متعددة. حاول لاحقاً.'
          : '⚠️ Account temporarily locked due to multiple failed attempts. Try again later.';
      } else if (error.response?.status === 403) {
        errorMessage = language === 'ar'
          ? '⚠️ الحساب مقفل. يرجى الاتصال بالدعم الفني.'
          : '⚠️ Account is locked. Please contact support.';
      } else if (error.response?.status === 401) {
        errorMessage = language === 'ar' 
          ? 'البريد الإلكتروني أو كلمة المرور غير صحيحة' 
          : 'Invalid email or password';
      } else {
        const defaultMsg = language === 'ar' ? 'حدث خطأ في تسجيل الدخول' : 'Login error';
        errorMessage = getErrorMessage(error, defaultMsg);
      }
      
      toast.error(errorMessage, {
        duration: 4000,
        style: {
          background: '#ef4444',
          color: '#fff',
          fontSize: '16px',
          fontWeight: 'bold'
        }
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col lg:flex-row" dir={language === 'ar' ? 'rtl' : 'ltr'}>
      {/* Right Side - Image/Illustration (appears on left in RTL) */}
      <div 
        className="hidden lg:flex lg:w-3/5 relative overflow-hidden"
        style={{
          backgroundImage: `url('https://customer-assets.emergentagent.com/job_696a10ac-e29e-498a-b073-aa134e8b40d7/artifacts/o61m4nq4_IMG_2949.jpeg')`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundRepeat: 'no-repeat'
        }}
      >
        {/* Overlay for better text readability */}
        <div className="absolute inset-0 bg-gradient-to-l from-[#0a1628]/80 via-[#0a1628]/40 to-transparent"></div>
        
        {/* Content over image */}
        <div className="relative z-10 flex flex-col items-center justify-center w-full p-12 text-white">
          {/* Logo and Title */}
          <div className="text-center space-y-6">
            <div className="mx-auto w-32 h-32 flex items-center justify-center bg-white/10 backdrop-blur-md rounded-3xl shadow-2xl border border-white/20">
              <img src="/login-logo.png" alt="نبيه Logo" className="w-28 h-28 object-contain" />
            </div>
            <div>
              <h1 className="text-5xl font-bold mb-3 drop-shadow-lg">
                نـبـيـه | NABIH
              </h1>
              <p className="text-xl text-white/90 font-medium">
                {language === 'ar' 
                  ? 'منصة الذكاء الاصطناعي لتحسين التوثيق السريري' 
                  : 'AI Platform for Clinical Documentation Improvement'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Left Side - Login Form (appears on right in RTL) */}
      <div className="w-full lg:w-2/5 flex items-center justify-center p-6 lg:p-12 bg-[#0a1628]">
        <div className="w-full max-w-md space-y-8">
          {/* Mobile Logo - only shown on small screens */}
          <div className="lg:hidden text-center space-y-4 mb-8">
            <div className="mx-auto w-20 h-20 flex items-center justify-center bg-white/10 backdrop-blur-md rounded-2xl shadow-xl border border-white/20">
              <img src="/login-logo.png" alt="نبيه Logo" className="w-16 h-16 object-contain" />
            </div>
            <h1 className="text-2xl font-bold text-white">نـبـيـه | NABIH</h1>
          </div>

          {/* Login Card */}
          <Card className="border-0 shadow-2xl bg-[#111d32] rounded-3xl overflow-hidden">
            <CardHeader className="space-y-2 pb-6 pt-8 bg-gradient-to-r from-blue-600 to-cyan-500">
              <CardTitle className="text-2xl font-bold text-center text-white">
                {language === 'ar' ? 'تسجيل الدخول' : 'Sign In'}
              </CardTitle>
              <p className="text-center text-white/80 text-sm">
                {language === 'ar' 
                  ? 'أدخل بياناتك للوصول إلى حسابك' 
                  : 'Enter your credentials to access your account'}
              </p>
            </CardHeader>
            <CardContent className="p-8">
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Email Field */}
                <div className="space-y-2">
                  <Label htmlFor="email" className="text-sm font-semibold text-gray-300 flex items-center gap-2">
                    <Mail className="w-4 h-4 text-blue-400" />
                    {language === 'ar' ? 'البريد الإلكتروني' : 'Email Address'}
                  </Label>
                  <div className="relative">
                    <Input
                      id="email"
                      type="email"
                      placeholder={language === 'ar' ? 'example@domain.com' : 'example@domain.com'}
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      className="h-12 bg-[#1a2942] border-2 border-[#2a3f5f] focus:border-blue-500 rounded-xl text-white placeholder:text-gray-500 transition-all duration-300"
                      required
                      data-testid="email-input"
                    />
                  </div>
                </div>

                {/* Password Field */}
                <div className="space-y-2">
                  <Label htmlFor="password" className="text-sm font-semibold text-gray-300 flex items-center gap-2">
                    <Lock className="w-4 h-4 text-blue-400" />
                    {language === 'ar' ? 'كلمة المرور' : 'Password'}
                  </Label>
                  <div className="relative">
                    <Input
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      placeholder="••••••••••••"
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      className="h-12 bg-[#1a2942] border-2 border-[#2a3f5f] focus:border-blue-500 rounded-xl text-white placeholder:text-gray-500 transition-all duration-300 pe-12"
                      required
                      data-testid="password-input"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute top-1/2 -translate-y-1/2 end-4 text-gray-400 hover:text-white transition-colors"
                    >
                      {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                </div>

                {/* Forgot Password Link */}
                <div className="flex justify-end">
                  <Link 
                    to="/forgot-password" 
                    className="text-sm text-blue-400 hover:text-blue-300 font-medium hover:underline transition-colors duration-300"
                  >
                    {language === 'ar' ? 'نسيت كلمة المرور؟' : 'Forgot Password?'}
                  </Link>
                </div>

                {/* Submit Button */}
                <Button
                  type="submit"
                  disabled={loading}
                  className="w-full h-12 bg-gradient-to-r from-blue-600 to-cyan-500 hover:from-blue-700 hover:to-cyan-600 text-white font-bold rounded-xl shadow-lg hover:shadow-2xl transform hover:scale-[1.02] transition-all duration-300 flex items-center justify-center gap-2"
                  data-testid="login-button"
                >
                  {loading ? (
                    <Activity className="w-5 h-5 animate-spin" />
                  ) : (
                    <>
                      {language === 'ar' ? 'تسجيل الدخول' : 'Sign In'}
                      <ArrowRight className="w-5 h-5 rtl:rotate-180" />
                    </>
                  )}
                </Button>

                {/* Divider */}
                <div className="relative my-6">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-[#2a3f5f]"></div>
                  </div>
                  <div className="relative flex justify-center text-sm">
                    <span className="px-4 bg-[#111d32] text-gray-400">
                      {language === 'ar' ? 'أو' : 'OR'}
                    </span>
                  </div>
                </div>

                {/* Register Link */}
                <div className="text-center">
                  <p className="text-gray-400">
                    {language === 'ar' ? 'ليس لديك حساب؟' : "Don't have an account?"}{' '}
                    <Link 
                      to="/register" 
                      className="text-blue-400 hover:text-blue-300 font-semibold hover:underline transition-colors duration-300"
                    >
                      {language === 'ar' ? 'إنشاء حساب جديد' : 'Create Account'}
                    </Link>
                  </p>
                </div>
              </form>
            </CardContent>
          </Card>

          {/* Footer Text */}
          <div className="text-center text-sm text-gray-500 pt-4">
            <p>© 2025 {language === 'ar' ? 'جميع الحقوق محفوظة' : 'All Rights Reserved'}</p>
            <p className="mt-1 font-semibold text-gray-400">
              {language === 'ar' ? 'عمر المغذوي' : 'Omar Almaghthawi'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
