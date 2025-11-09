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

  const [resetCode, setResetCode] = useState('');
  const [phoneDigits, setPhoneDigits] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await axios.post(`${API}/auth/forgot-password`, { email });
      
      if (response.data.has_phone && response.data.reset_code) {
        // عرض الكود للمستخدم
        setResetCode(response.data.reset_code);
        setPhoneDigits(response.data.phone_last_digits);
        setSent(true);
        toast.success(
          language === 'ar' 
            ? 'تم إرسال كود الاستعادة إلى واتساب والبريد الإلكتروني' 
            : 'Reset code sent to WhatsApp and email'
        );
      } else {
        setSent(true);
        toast.success(t('resetLinkSent'));
      }
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
            <div className="mx-auto w-32 h-32 flex items-center justify-center">
              <img src="/download-2.png" alt="Logo" className="w-full h-full object-contain" />
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
              <div className="text-center space-y-6">
                <div className="text-green-600 text-lg font-semibold">
                  ✓ {language === 'ar' ? 'تم إرسال كود الاستعادة' : 'Reset Code Sent'}
                </div>
                
                {resetCode && (
                  <div className="bg-blue-50 border-2 border-blue-300 rounded-lg p-6 space-y-3">
                    <p className="text-sm text-gray-700">
                      {language === 'ar' 
                        ? `تم إرسال الكود إلى واتساب (***${phoneDigits}) وبريدك الإلكتروني`
                        : `Code sent to WhatsApp (***${phoneDigits}) and your email`
                      }
                    </p>
                    <div className="bg-white rounded-lg p-4 shadow-sm">
                      <p className="text-xs text-gray-500 mb-2">
                        {language === 'ar' ? 'كود الاستعادة:' : 'Reset Code:'}
                      </p>
                      <div className="text-3xl font-bold text-blue-600 tracking-wider" style={{letterSpacing: '0.5em'}}>
                        {resetCode}
                      </div>
                    </div>
                    <p className="text-xs text-gray-500">
                      {language === 'ar' 
                        ? 'استخدم هذا الكود في صفحة إعادة تعيين كلمة المرور'
                        : 'Use this code on the password reset page'
                      }
                    </p>
                  </div>
                )}
                
                <p className="text-gray-600 text-sm">
                  {language === 'ar' 
                    ? 'تحقق من واتساب وبريدك الإلكتروني واتبع التعليمات لإعادة تعيين كلمة المرور'
                    : 'Check your WhatsApp and email and follow the instructions to reset your password'
                  }
                </p>
                
                <Button
                  onClick={() => window.location.href = '/reset-password'}
                  className="w-full medical-blue"
                >
                  {language === 'ar' ? 'أدخل الكود الآن' : 'Enter Code Now'}
                </Button>
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
