import React, { useState } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { Lock } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';
import Footer from '@/components/Footer';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ResetPassword = () => {
  const navigate = useNavigate();
  const { language, t } = useLanguage();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  
  const [formData, setFormData] = useState({
    email: '',
    code: '',
    password: '',
    confirmPassword: ''
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (formData.password !== formData.confirmPassword) {
      toast.error(language === 'ar' ? 'كلمات المرور غير متطابقة' : 'Passwords do not match');
      return;
    }

    if (formData.password.length < 6) {
      toast.error(language === 'ar' ? 'كلمة المرور يجب أن تكون 6 أحرف على الأقل' : 'Password must be at least 6 characters');
      return;
    }

    setLoading(true);

    try {
      // Reset with token from email only
      await axios.post(`${API}/auth/reset-password`, {
        token,
        new_password: formData.password
      });
      
      toast.success(language === 'ar' ? 'تم إعادة تعيين كلمة المرور بنجاح!' : 'Password reset successfully!');
      setTimeout(() => navigate('/login'), 2000);
    } catch (error) {
      toast.error(error.response?.data?.detail || t('error'));
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    // Redirect to forgot password if no token
    return (
      <div className="min-h-screen flex flex-col">
        <div className="flex-1 flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-indigo-50 p-4">
          <Card className="w-full max-w-md medical-card fade-in">
            <CardHeader className="text-center space-y-4">
              <div className="mx-auto w-32 h-32 flex items-center justify-center">
                <img src="/download-2.png" alt="Logo" className="w-full h-full object-contain" />
              </div>
              <CardTitle className="text-3xl font-bold text-gray-800">{t('resetPasswordTitle')}</CardTitle>
              <CardDescription className="text-lg">
                {language === 'ar' 
                  ? 'رابط إعادة التعيين غير صالح. يرجى طلب رابط جديد.'
                  : 'Invalid reset link. Please request a new one.'
                }
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center space-y-4">
                <Button
                  onClick={() => navigate('/forgot-password')}
                  className="w-full medical-blue text-white py-6 text-lg font-semibold"
                >
                  {language === 'ar' ? 'طلب رابط جديد' : 'Request New Link'}
                </Button>
                <Link to="/login" className="block text-blue-600 font-semibold hover:underline">
                  {t('backToLogin')}
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col">
      <div className="flex-1 flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-indigo-50 p-4">
        <Card className="w-full max-w-md medical-card fade-in">
          <CardHeader className="text-center space-y-4">
            <div className="mx-auto w-32 h-32 flex items-center justify-center">
              <img src="/download-2.png" alt="Logo" className="w-full h-full object-contain" />
            </div>
            <CardTitle className="text-3xl font-bold text-gray-800">{t('resetPasswordTitle')}</CardTitle>
            <CardDescription className="text-lg">
              {language === 'ar' 
                ? 'أدخل كلمة المرور الجديدة' 
                : 'Enter your new password'
              }
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="password">{t('newPassword')}</Label>
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
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="confirmPassword">{t('confirmPassword')}</Label>
                <div className="relative">
                  <Lock className={`absolute ${language === 'ar' ? 'right-3' : 'left-3'} top-3 h-5 w-5 text-gray-400`} />
                  <Input
                    id="confirmPassword"
                    type="password"
                    placeholder="••••••••"
                    value={formData.confirmPassword}
                    onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                    className={language === 'ar' ? 'pr-10' : 'pl-10'}
                    required
                  />
                </div>
              </div>
              <Button
                type="submit"
                className="w-full medical-blue text-white py-6 text-lg font-semibold"
                disabled={loading}
              >
                {loading ? t('loading') : t('resetPassword')}
              </Button>
            </form>
            <div className="mt-6 text-center">
              <Link to="/login" className="text-blue-600 font-semibold hover:underline">
                {t('backToLogin')}
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default ResetPassword;
