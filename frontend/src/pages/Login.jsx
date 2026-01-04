import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
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
      const response = await axios.post(`${API}/auth/login-step1`, formData);
      
      if (response.data.requires_mfa) {
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
        const { access_token, user } = response.data;
        localStorage.setItem('token', access_token);
        localStorage.setItem('user', JSON.stringify(user));
        setUser(user);
        
        toast.success(t('loginSuccess'));
        
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
    <div 
      className="min-h-screen flex items-center relative overflow-hidden"
      dir={language === 'ar' ? 'rtl' : 'ltr'}
    >
      {/* Full Page Background Image */}
      <div 
        className="absolute inset-0 z-0"
        style={{
          backgroundImage: `url('https://customer-assets.emergentagent.com/job_e770b79e-b869-458f-8e5a-632dba9ea2b3/artifacts/j4zvqtlv_IMG_2950.jpeg')`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundRepeat: 'no-repeat'
        }}
      />
      
      {/* Dark Overlay for better readability */}
      <div className="absolute inset-0 bg-gradient-to-r from-[#0a1628]/95 via-[#0a1628]/70 to-transparent z-10" />

      {/* Login Form - Left Side */}
      <div className="relative z-20 w-full max-w-md mx-8 lg:mx-16">
        {/* Logo and Title */}
        <div className="text-center mb-8">
          <div className="mx-auto w-28 h-28 flex items-center justify-center mb-6">
            <img src="/nabeeh-logo.png" alt="نبيه Logo" className="w-full h-full object-contain drop-shadow-2xl" />
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-white mb-2 drop-shadow-lg">
            نـبـيـه | NABEEH
          </h1>
          <p className="text-cyan-300 text-sm sm:text-base drop-shadow-md">
            {language === 'ar' 
              ? 'منصة الذكاء الاصطناعي لتحسين التوثيق السريري' 
              : 'AI Platform for Clinical Documentation Improvement'}
          </p>
        </div>

        {/* Login Card */}
        <div className="bg-white/10 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/20 overflow-hidden">
          {/* Card Header */}
          <div className="bg-gradient-to-r from-[#0066a1] to-[#00a99d] px-6 py-5">
            <h2 className="text-xl sm:text-2xl font-bold text-center text-white">
              {language === 'ar' ? 'تسجيل الدخول' : 'Sign In'}
            </h2>
            <p className="text-center text-white/80 text-sm mt-1">
              {language === 'ar' 
                ? 'أدخل بياناتك للوصول إلى حسابك' 
                : 'Enter your credentials to access your account'}
            </p>
          </div>

          {/* Card Content */}
          <div className="p-6 sm:p-8">
            <form onSubmit={handleSubmit} className="space-y-5">
              {/* Email Field */}
              <div className="space-y-2">
                <Label htmlFor="email" className="text-sm font-semibold text-white/90 flex items-center gap-2">
                  <Mail className="w-4 h-4 text-cyan-400" />
                  {language === 'ar' ? 'البريد الإلكتروني' : 'Email Address'}
                </Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="example@domain.com"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="h-12 bg-white/10 border-2 border-white/20 focus:border-cyan-400 rounded-xl text-white placeholder:text-white/40 transition-all duration-300"
                  required
                  data-testid="email-input"
                />
              </div>

              {/* Password Field */}
              <div className="space-y-2">
                <Label htmlFor="password" className="text-sm font-semibold text-white/90 flex items-center gap-2">
                  <Lock className="w-4 h-4 text-cyan-400" />
                  {language === 'ar' ? 'كلمة المرور' : 'Password'}
                </Label>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="••••••••••••"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    className="h-12 bg-white/10 border-2 border-white/20 focus:border-cyan-400 rounded-xl text-white placeholder:text-white/40 transition-all duration-300 pe-12"
                    required
                    data-testid="password-input"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute top-1/2 -translate-y-1/2 end-4 text-white/50 hover:text-white transition-colors"
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>

              {/* Forgot Password Link */}
              <div className="flex justify-end">
                <Link 
                  to="/forgot-password" 
                  className="text-sm text-cyan-400 hover:text-cyan-300 font-medium hover:underline transition-colors duration-300"
                >
                  {language === 'ar' ? 'نسيت كلمة المرور؟' : 'Forgot Password?'}
                </Link>
              </div>

              {/* Submit Button */}
              <Button
                type="submit"
                disabled={loading}
                className="w-full h-12 bg-gradient-to-r from-[#0066a1] to-[#00a99d] hover:from-[#005588] hover:to-[#008877] text-white font-bold rounded-xl shadow-lg hover:shadow-2xl transform hover:scale-[1.02] transition-all duration-300 flex items-center justify-center gap-2"
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
              <div className="relative my-4">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-white/20"></div>
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-4 bg-transparent text-white/50">
                    {language === 'ar' ? 'أو' : 'OR'}
                  </span>
                </div>
              </div>

              {/* Register Link */}
              <div className="text-center">
                <p className="text-white/70">
                  {language === 'ar' ? 'ليس لديك حساب؟' : "Don't have an account?"}{' '}
                  <Link 
                    to="/register" 
                    className="text-cyan-400 hover:text-cyan-300 font-semibold hover:underline transition-colors duration-300"
                  >
                    {language === 'ar' ? 'إنشاء حساب جديد' : 'Create Account'}
                  </Link>
                </p>
              </div>
            </form>
          </div>
        </div>

        {/* Footer Text */}
        <div className="text-center text-sm text-white/50 mt-6">
          <p>© 2025 {language === 'ar' ? 'جميع الحقوق محفوظة' : 'All Rights Reserved'}</p>
          <p className="mt-1 font-semibold text-white/60">
            {language === 'ar' ? 'عمر المغذوي' : 'Omar Almaghthawi'}
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
