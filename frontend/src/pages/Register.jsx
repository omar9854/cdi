import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { FileText, Lock, Mail, User, Phone } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Register = ({ setUser }) => {
  const navigate = useNavigate();
  const { language, t } = useLanguage();
  const [formData, setFormData] = useState({ 
    email: '', 
    full_name: '', 
    phone_number: '',
    password: '',
    admin_code: '' 
  });
  const [loading, setLoading] = useState(false);
  const [showAdminCode, setShowAdminCode] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await axios.post(`${API}/auth/register`, formData);
      const { access_token, user, whatsapp_welcome_link } = response.data;
      
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(user));
      setUser(user);
      
      toast.success(t('registerSuccess'));
      
      // فتح واتساب مع رسالة الترحيب - استخدام location بدلاً من window.open
      if (whatsapp_welcome_link) {
        // حفظ الرابط وفتحه مباشرة
        window.location.href = whatsapp_welcome_link;
        
        // الانتظار قليلاً ثم التوجيه للداشبورد
        setTimeout(() => {
          navigate('/dashboard');
        }, 3000);
      } else {
        navigate('/dashboard');
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || t('error'));
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <div className="flex-1 flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-indigo-50 p-4">
        <Card className="w-full max-w-md medical-card fade-in" data-testid="register-card">
        <CardHeader className="text-center space-y-4">
          <div className="mx-auto w-32 h-32 flex items-center justify-center">
            <img src="/download-2.png" alt="Logo" className="w-full h-full object-contain" />
          </div>
          <CardTitle className="text-3xl font-bold text-gray-800">{t('register')}</CardTitle>
          <CardDescription className="text-lg">{t('appName')}<br />{t('appSubtitle')}</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="full_name">{t('fullName')}</Label>
              <div className="relative">
                <User className={`absolute ${language === 'ar' ? 'right-3' : 'left-3'} top-3 h-5 w-5 text-gray-400`} />
                <Input
                  id="full_name"
                  type="text"
                  placeholder={language === 'ar' ? 'أحمد محمد' : 'John Doe'}
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  className={language === 'ar' ? 'pr-10' : 'pl-10'}
                  required
                  data-testid="register-name-input"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">{t('email')}</Label>
              <div className="relative">
                <Mail className={`absolute ${language === 'ar' ? 'right-3' : 'left-3'} top-3 h-5 w-5 text-gray-400`} />
                <Input
                  id="email"
                  type="email"
                  placeholder="example@hospital.com"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className={language === 'ar' ? 'pr-10' : 'pl-10'}
                  required
                  data-testid="register-email-input"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="phone_number">{t('phoneNumber')}</Label>
              <div className="relative">
                <Phone className={`absolute ${language === 'ar' ? 'right-3' : 'left-3'} top-3 h-5 w-5 text-gray-400`} />
                <Input
                  id="phone_number"
                  type="tel"
                  placeholder="966502468148"
                  value={formData.phone_number}
                  onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })}
                  className={language === 'ar' ? 'pr-10' : 'pl-10'}
                  required
                  data-testid="register-phone-input"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">{t('password')}</Label>
              <div className="relative">
                <Lock className={`absolute ${language === 'ar' ? 'right-3' : 'left-3'} top-3 h-5 w-5 text-gray-400`} />
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className={language === 'ar' ? 'pr-10' : 'pl-10'}
                  required
                  data-testid="register-password-input"
                />
              </div>
            </div>
            
            {/* Admin Code Toggle */}
            <div className="text-center">
              <button
                type="button"
                onClick={() => setShowAdminCode(!showAdminCode)}
                className="text-sm text-blue-600 hover:underline"
              >
                {showAdminCode ? 
                  (language === 'ar' ? 'إخفاء كود الأدمن' : 'Hide Admin Code') : 
                  (language === 'ar' ? 'هل أنت أدمن؟ أدخل الكود' : 'Are you an admin? Enter code')
                }
              </button>
            </div>

            {/* Admin Code Field */}
            {showAdminCode && (
              <div className="space-y-2 fade-in">
                <Label htmlFor="admin_code">
                  {language === 'ar' ? 'كود الأدمن (اختياري)' : 'Admin Code (Optional)'}
                </Label>
                <Input
                  id="admin_code"
                  type="text"
                  placeholder={language === 'ar' ? 'أدخل كود الأدمن' : 'Enter admin code'}
                  value={formData.admin_code}
                  onChange={(e) => setFormData({ ...formData, admin_code: e.target.value })}
                  data-testid="register-admin-code-input"
                />
              </div>
            )}
            <Button
              type="submit"
              className="w-full medical-blue text-white py-6 text-lg font-semibold"
              disabled={loading}
              data-testid="register-submit-button"
            >
              {loading ? t('loading') : t('register')}
            </Button>
          </form>
          <div className="mt-6 text-center">
            <p className="text-gray-600">
              {t('alreadyHaveAccount')}{' '}
              <Link to="/login" className="text-blue-600 font-semibold hover:underline" data-testid="login-link">
                {t('loginNow')}
              </Link>
            </p>
          </div>
        </CardContent>
      </Card>
      </div>
    </div>
  );
};

export default Register;