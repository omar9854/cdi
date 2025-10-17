import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { FileText, Lock, Mail, User } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Register = ({ setUser }) => {
  const navigate = useNavigate();
  const { language, t } = useLanguage();
  const [formData, setFormData] = useState({ email: '', full_name: '', password: '' });
  const [loading, setLoading] = useState(false);

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
      toast.error(error.response?.data?.detail || t('error'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-indigo-50 p-4">
      <Card className="w-full max-w-md medical-card fade-in" data-testid="register-card">
        <CardHeader className="text-center space-y-4">
          <div className="mx-auto w-16 h-16 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-2xl flex items-center justify-center">
            <FileText className="w-8 h-8 text-white" />
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
  );
};

export default Register;