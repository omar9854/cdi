import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { Lock, Mail } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';
import Footer from '@/components/Footer';
import Footer from '@/components/Footer';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Login = ({ setUser }) => {
  const navigate = useNavigate();
  const { language, t } = useLanguage();
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await axios.post(`${API}/auth/login`, formData);
      const { access_token, user } = response.data;
      
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(user));
      setUser(user);
      
      toast.success(t('loginSuccess'));
      navigate('/dashboard');
    } catch (error) {
      toast.error(error.response?.data?.detail || t('error'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <div className="flex-1 flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-indigo-50 p-4">
        <Card className="w-full max-w-md medical-card fade-in" data-testid="login-card">
        <CardHeader className="text-center space-y-4">
          <div className="mx-auto w-32 h-32 flex items-center justify-center">
            <img src="/download-2.png" alt="Logo" className="w-full h-full object-contain" />
          </div>
          <CardTitle className="text-3xl font-bold text-gray-800">{t('login')}</CardTitle>
          <CardDescription className="text-lg">{t('appName')}<br />{t('appSubtitle')}</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
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
                  data-testid="login-email-input"
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
                  data-testid="login-password-input"
                />
              </div>
            </div>
            <div className="text-right">
              <Link to="/forgot-password" className="text-sm text-blue-600 hover:underline">
                {t('forgotPassword')}
              </Link>
            </div>
            <Button
              type="submit"
              className="w-full medical-blue text-white py-6 text-lg font-semibold"
              disabled={loading}
              data-testid="login-submit-button"
            >
              {loading ? t('loading') : t('login')}
            </Button>
          </form>
          <div className="mt-6 text-center">
            <p className="text-gray-600">
              {t('dontHaveAccount')}{' '}
              <Link to="/register" className="text-blue-600 font-semibold hover:underline" data-testid="register-link">
                {t('signupNow')}
              </Link>
            </p>
          </div>
        </CardContent>
      </Card>
      </div>
    </div>
  );
};

export default Login;