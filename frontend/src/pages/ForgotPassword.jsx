import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { Mail, ArrowLeft } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';
import Footer from '@/components/Footer';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ForgotPassword = () => {
  const { language, t } = useLanguage();
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await axios.post(`${API}/auth/forgot-password`, { email });
      setSent(true);
      toast.success(t('resetLinkSent'));
    } catch (error) {
      toast.error(error.response?.data?.detail || t('error'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <div className="flex-1 flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-indigo-50 p-4">
        <Card className="w-full max-w-md medical-card fade-in">
          <CardHeader className="text-center space-y-4">
            <div className="mx-auto w-24 h-24 flex items-center justify-center">
              <img src="/download-2.png" alt="Logo" className="w-full h-full object-contain rounded-xl" />
            </div>
            <CardTitle className="text-3xl font-bold text-gray-800">{t('forgotPassword')}</CardTitle>
            <CardDescription className="text-lg">
              {sent 
                ? t('resetLinkSent')
                : language === 'ar' 
                  ? 'أدخل بريدك الإلكتروني وسنرسل لك رابط إعادة تعيين كلمة المرور'
                  : 'Enter your email and we will send you a password reset link'
              }
            </CardDescription>
          </CardHeader>
          <CardContent>
            {!sent ? (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="email">{t('email')}</Label>
                  <div className="relative">
                    <Mail className={`absolute ${language === 'ar' ? 'right-3' : 'left-3'} top-3 h-5 w-5 text-gray-400`} />
                    <Input
                      id="email"
                      type="email"
                      placeholder="example@hospital.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
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
                  {loading ? t('loading') : t('sendResetLink')}
                </Button>
              </form>
            ) : (
              <div className="text-center space-y-4">
                <div className="text-green-600 text-lg">
                  ✓ {t('resetLinkSent')}
                </div>
                <p className="text-gray-600">
                  {language === 'ar' 
                    ? 'يرجى التحقق من بريدك الإلكتروني واتباع التعليمات لإعادة تعيين كلمة المرور'
                    : 'Please check your email and follow the instructions to reset your password'
                  }
                </p>
              </div>
            )}
            <div className="mt-6 text-center">
              <Link to="/login" className="text-blue-600 font-semibold hover:underline inline-flex items-center gap-2">
                <ArrowLeft className="h-4 w-4" />
                {t('backToLogin')}
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
      <Footer />
    </div>
  );
};

export default ForgotPassword;
