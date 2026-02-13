import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import { Lock, Mail, User, Phone, Activity, ArrowRight, Eye, EyeOff } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const Register = ({ setUser }) => {
  const navigate = useNavigate();
  const { language, t } = useLanguage();
  const [formData, setFormData] = useState({ 
    email: '', 
    full_name: '', 
    phone_number: '',
    password: '',
    department: 'cdi',
    admin_code: '' 
  });
  const [loading, setLoading] = useState(false);
  const [showAdminCode, setShowAdminCode] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await axios.post(`${API}/auth/register`, formData);
      const { access_token, user } = response.data;
      
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(user));
      setUser(user);
      
      toast.success(t('registerSuccess'));
      navigate('/dashboard');
    } catch (error) {
      toast.error(error.response?.data?.detail || t('error'), {
        duration: 4000,
        style: {
          background: '#ef4444',
          color: '#fff',
          fontSize: '16px',
          fontWeight: 'bold'
        }
      });
      setLoading(false);
    }
  };

  return (
    <div 
      className="min-h-screen flex items-center justify-end relative overflow-hidden py-8"
      dir={language === 'ar' ? 'rtl' : 'ltr'}
    >
      {/* Full Background Image */}
      <div 
        className="absolute inset-0 z-0"
        style={{
          backgroundImage: `url('https://customer-assets.emergentagent.com/job_e770b79e-b869-458f-8e5a-632dba9ea2b3/artifacts/j4zvqtlv_IMG_2950.jpeg')`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundRepeat: 'no-repeat'
        }}
      />
      
      {/* Dark Overlay */}
      <div className="absolute inset-0 bg-gradient-to-l from-[#0a1628]/95 via-[#0a1628]/70 to-transparent z-10" />

      {/* Content - Right Side */}
      <div className="relative z-20 w-full max-w-md mx-8 lg:mx-16">
        {/* Logo and Title */}
        <div className="text-center mb-6">
          <div className="mx-auto w-24 h-24 flex items-center justify-center mb-4">
            <img src="/nabeeh-logo.png" alt="نبيه Logo" className="w-full h-full object-contain drop-shadow-2xl" />
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white mb-1 drop-shadow-lg">
            نـبـيـه | NABEEH
          </h1>
          <p className="text-cyan-300 text-xs sm:text-sm">
            {language === 'ar' 
              ? 'منصة الذكاء الاصطناعي لتحسين التوثيق السريري' 
              : 'AI Platform for Clinical Documentation Improvement'}
          </p>
        </div>

        {/* Register Card */}
        <div className="bg-white/10 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/20 overflow-hidden">
          {/* Card Header */}
          <div className="bg-gradient-to-r from-[#0066a1] to-[#00a99d] px-6 py-4">
            <h2 className="text-xl sm:text-2xl font-bold text-center text-white">
              {language === 'ar' ? 'إنشاء حساب جديد' : 'Create Account'}
            </h2>
            <p className="text-center text-white/80 text-sm mt-1">
              {language === 'ar' 
                ? 'أدخل بياناتك لإنشاء حسابك' 
                : 'Enter your details to create your account'}
            </p>
          </div>

          {/* Card Content */}
          <div className="p-6">
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Full Name Field */}
              <div className="space-y-1">
                <Label htmlFor="full_name" className="text-sm font-semibold text-white/90 flex items-center gap-2">
                  <User className="w-4 h-4 text-cyan-400" />
                  {language === 'ar' ? 'الاسم الكامل' : 'Full Name'}
                </Label>
                <Input
                  id="full_name"
                  type="text"
                  placeholder={language === 'ar' ? 'أحمد محمد' : 'John Doe'}
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  className="h-11 bg-white/10 border-2 border-white/20 focus:border-emerald-400 rounded-xl text-white placeholder:text-white/40 transition-all duration-300"
                  required
                  data-testid="register-name-input"
                />
              </div>

              {/* Email Field */}
              <div className="space-y-1">
                <Label htmlFor="email" className="text-sm font-semibold text-white/90 flex items-center gap-2">
                  <Mail className="w-4 h-4 text-emerald-400" />
                  {language === 'ar' ? 'البريد الإلكتروني' : 'Email Address'}
                </Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="example@domain.com"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="h-11 bg-white/10 border-2 border-white/20 focus:border-emerald-400 rounded-xl text-white placeholder:text-white/40 transition-all duration-300"
                  required
                  data-testid="register-email-input"
                />
              </div>

              {/* Phone Field */}
              <div className="space-y-1">
                <Label htmlFor="phone_number" className="text-sm font-semibold text-white/90 flex items-center gap-2">
                  <Phone className="w-4 h-4 text-emerald-400" />
                  {language === 'ar' ? 'رقم الهاتف' : 'Phone Number'}
                </Label>
                <Input
                  id="phone_number"
                  type="tel"
                  placeholder="+966500000000"
                  value={formData.phone_number}
                  onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })}
                  className="h-11 bg-white/10 border-2 border-white/20 focus:border-emerald-400 rounded-xl text-white placeholder:text-white/40 transition-all duration-300"
                  required
                  data-testid="register-phone-input"
                />
              </div>

              {/* Password Field */}
              <div className="space-y-1">
                <Label htmlFor="password" className="text-sm font-semibold text-white/90 flex items-center gap-2">
                  <Lock className="w-4 h-4 text-emerald-400" />
                  {language === 'ar' ? 'كلمة المرور' : 'Password'}
                </Label>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="••••••••••••"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    className="h-11 bg-white/10 border-2 border-white/20 focus:border-emerald-400 rounded-xl text-white placeholder:text-white/40 transition-all duration-300 pe-12"
                    required
                    data-testid="register-password-input"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute top-1/2 -translate-y-1/2 end-4 text-white/50 hover:text-white transition-colors"
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
                <p className="text-xs text-white/50 mt-1">
                  {language === 'ar' ? 'كلمة المرور يجب أن تكون 12 حرف على الأقل' : 'Password must be at least 12 characters'}
                </p>
              </div>

              {/* Admin Code Toggle */}
              <div className="text-center">
                <button
                  type="button"
                  onClick={() => setShowAdminCode(!showAdminCode)}
                  className="text-sm text-emerald-400 hover:text-emerald-300 hover:underline transition-colors"
                >
                  {showAdminCode ? 
                    (language === 'ar' ? 'إخفاء كود الأدمن' : 'Hide Admin Code') : 
                    (language === 'ar' ? 'هل أنت أدمن؟ أدخل الكود' : 'Are you an admin? Enter code')
                  }
                </button>
              </div>

              {/* Admin Code Field */}
              {showAdminCode && (
                <div className="space-y-1">
                  <Label htmlFor="admin_code" className="text-sm font-semibold text-white/90">
                    {language === 'ar' ? 'كود الأدمن (اختياري)' : 'Admin Code (Optional)'}
                  </Label>
                  <Input
                    id="admin_code"
                    type="text"
                    placeholder={language === 'ar' ? 'أدخل كود الأدمن' : 'Enter admin code'}
                    value={formData.admin_code}
                    onChange={(e) => setFormData({ ...formData, admin_code: e.target.value })}
                    className="h-11 bg-white/10 border-2 border-white/20 focus:border-emerald-400 rounded-xl text-white placeholder:text-white/40 transition-all duration-300"
                    data-testid="register-admin-code-input"
                  />
                </div>
              )}

              {/* Submit Button */}
              <Button
                type="submit"
                disabled={loading}
                className="w-full h-12 bg-gradient-to-r from-emerald-600 to-cyan-500 hover:from-emerald-700 hover:to-cyan-600 text-white font-bold rounded-xl shadow-lg hover:shadow-2xl transform hover:scale-[1.02] transition-all duration-300 flex items-center justify-center gap-2 mt-4"
                data-testid="register-submit-button"
              >
                {loading ? (
                  <Activity className="w-5 h-5 animate-spin" />
                ) : (
                  <>
                    {language === 'ar' ? 'إنشاء حساب' : 'Create Account'}
                    <ArrowRight className="w-5 h-5 rtl:rotate-180" />
                  </>
                )}
              </Button>

              {/* Divider */}
              <div className="relative my-3">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-white/20"></div>
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-4 bg-transparent text-white/50">
                    {language === 'ar' ? 'أو' : 'OR'}
                  </span>
                </div>
              </div>

              {/* Login Link */}
              <div className="text-center">
                <p className="text-white/70">
                  {language === 'ar' ? 'لديك حساب بالفعل؟' : 'Already have an account?'}{' '}
                  <Link 
                    to="/login" 
                    className="text-emerald-400 hover:text-emerald-300 font-semibold hover:underline transition-colors duration-300"
                    data-testid="login-link"
                  >
                    {language === 'ar' ? 'تسجيل الدخول' : 'Sign In'}
                  </Link>
                </p>
              </div>
            </form>
          </div>
        </div>

        {/* Footer Text */}
        <div className="text-center text-sm text-white/50 mt-4">
          <p>© 2025 {language === 'ar' ? 'جميع الحقوق محفوظة' : 'All Rights Reserved'}</p>
          <p className="mt-1 font-semibold text-white/60">
            {language === 'ar' ? 'عمر المغذوي و سامي المعدوي' : 'Omar Almaghthawi & Sami Almaadawi'}
          </p>
        </div>
      </div>
    </div>
  );
};

export default Register;
