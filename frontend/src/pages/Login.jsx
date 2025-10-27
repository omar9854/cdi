import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { Lock, Mail, ArrowRight, Activity, Shield, TrendingUp } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';

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
    <div className="min-h-screen flex">
      {/* Right Side - Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 lg:p-12 bg-white">
        <div className="w-full max-w-md space-y-8 animate-fade-in">
          {/* Logo and Title */}
          <div className="text-center space-y-4">
            <div className="mx-auto w-24 h-24 flex items-center justify-center bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl shadow-lg transform hover:scale-105 transition-transform duration-300">
              <img src="/logo.jpeg" alt="Logo" className="w-20 h-20 object-contain rounded-xl" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                {language === 'ar' ? 'مرحباً بك' : 'Welcome Back'}
              </h1>
              <p className="text-gray-600 text-lg">
                {language === 'ar' 
                  ? 'مركز الترميز الطبي وتحسين التوثيق السريري' 
                  : 'Medical Coding & CDI Center'}
              </p>
            </div>
          </div>

          {/* Login Form */}
          <Card className="border-0 shadow-xl bg-gradient-to-br from-white to-gray-50">
            <CardHeader className="space-y-1 pb-6">
              <CardTitle className="text-2xl font-bold text-center text-gray-800">
                {language === 'ar' ? 'تسجيل الدخول' : 'Sign In'}
              </CardTitle>
              <CardDescription className="text-center text-gray-600">
                {language === 'ar' 
                  ? 'أدخل بياناتك للوصول إلى حسابك' 
                  : 'Enter your credentials to access your account'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Email Field */}
                <div className="space-y-2">
                  <Label htmlFor="email" className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                    <Mail className="w-4 h-4 text-blue-600" />
                    {language === 'ar' ? 'البريد الإلكتروني' : 'Email Address'}
                  </Label>
                  <div className="relative">
                    <Input
                      id="email"
                      type="email"
                      placeholder={language === 'ar' ? 'example@domain.com' : 'example@domain.com'}
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      className="h-12 pl-4 pr-4 border-2 border-gray-200 focus:border-blue-500 rounded-xl transition-all duration-300 hover:border-blue-300"
                      required
                      data-testid="email-input"
                    />
                  </div>
                </div>

                {/* Password Field */}
                <div className="space-y-2">
                  <Label htmlFor="password" className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                    <Lock className="w-4 h-4 text-blue-600" />
                    {language === 'ar' ? 'كلمة المرور' : 'Password'}
                  </Label>
                  <div className="relative">
                    <Input
                      id="password"
                      type="password"
                      placeholder={language === 'ar' ? '••••••••' : '••••••••'}
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      className="h-12 pl-4 pr-4 border-2 border-gray-200 focus:border-blue-500 rounded-xl transition-all duration-300 hover:border-blue-300"
                      required
                      data-testid="password-input"
                    />
                  </div>
                </div>

                {/* Forgot Password Link */}
                <div className="flex justify-end">
                  <Link 
                    to="/forgot-password" 
                    className="text-sm text-blue-600 hover:text-blue-800 font-medium hover:underline transition-colors duration-300"
                  >
                    {language === 'ar' ? 'نسيت كلمة المرور؟' : 'Forgot Password?'}
                  </Link>
                </div>

                {/* Submit Button */}
                <Button
                  type="submit"
                  disabled={loading}
                  className="w-full h-12 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-300 flex items-center justify-center gap-2"
                  data-testid="login-button"
                >
                  {loading ? (
                    <Activity className="w-5 h-5 animate-spin" />
                  ) : (
                    <>
                      {language === 'ar' ? 'تسجيل الدخول' : 'Sign In'}
                      <ArrowRight className="w-5 h-5" />
                    </>
                  )}
                </Button>

                {/* Register Link */}
                <div className="text-center pt-4">
                  <p className="text-gray-600">
                    {language === 'ar' ? 'ليس لديك حساب؟' : "Don't have an account?"}{' '}
                    <Link 
                      to="/register" 
                      className="text-blue-600 hover:text-blue-800 font-semibold hover:underline transition-colors duration-300"
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
            <p className="mt-1 font-semibold text-gray-700">
              {language === 'ar' ? 'عمر المغذوي' : 'Omar Almaghthawi'}
            </p>
          </div>
        </div>
      </div>

      {/* Left Side - Image/Illustration */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-blue-600 via-indigo-600 to-purple-700 relative overflow-hidden">
        {/* Background Pattern */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 left-0 w-96 h-96 bg-white rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 right-0 w-96 h-96 bg-white rounded-full blur-3xl"></div>
        </div>

        {/* Content */}
        <div className="relative z-10 flex flex-col items-center justify-center p-12 text-white space-y-8">
          {/* Main Image */}
          <div className="w-full max-w-lg">
            <img 
              src="/download-2.png" 
              alt="Medical Illustration" 
              className="w-full h-auto drop-shadow-2xl animate-float"
            />
          </div>

          {/* Features */}
          <div className="space-y-6 w-full max-w-lg">
            <h2 className="text-4xl font-bold text-center mb-8">
              {language === 'ar' 
                ? 'نظام متكامل لتحسين التوثيق السريري' 
                : 'Complete CDI Management System'}
            </h2>
            
            <div className="space-y-4">
              <div className="flex items-start gap-4 bg-white/10 backdrop-blur-sm p-4 rounded-xl border border-white/20 hover:bg-white/20 transition-all duration-300">
                <div className="bg-white/20 p-3 rounded-lg">
                  <Activity className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="font-bold text-lg mb-1">
                    {language === 'ar' ? 'تحليل ذكي بالـ AI' : 'AI-Powered Analysis'}
                  </h3>
                  <p className="text-white/80 text-sm">
                    {language === 'ar' 
                      ? 'تحليل تلقائي للملفات الطبية مع اقتراحات دقيقة' 
                      : 'Automatic medical file analysis with precise suggestions'}
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4 bg-white/10 backdrop-blur-sm p-4 rounded-xl border border-white/20 hover:bg-white/20 transition-all duration-300">
                <div className="bg-white/20 p-3 rounded-lg">
                  <TrendingUp className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="font-bold text-lg mb-1">
                    {language === 'ar' ? 'تقارير احترافية' : 'Professional Reports'}
                  </h3>
                  <p className="text-white/80 text-sm">
                    {language === 'ar' 
                      ? 'رسوم بيانية وتقارير شاملة قابلة للتحميل' 
                      : 'Charts and comprehensive downloadable reports'}
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4 bg-white/10 backdrop-blur-sm p-4 rounded-xl border border-white/20 hover:bg-white/20 transition-all duration-300">
                <div className="bg-white/20 p-3 rounded-lg">
                  <Shield className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="font-bold text-lg mb-1">
                    {language === 'ar' ? 'أمان عالي' : 'High Security'}
                  </h3>
                  <p className="text-white/80 text-sm">
                    {language === 'ar' 
                      ? 'حماية متقدمة للبيانات الطبية الحساسة' 
                      : 'Advanced protection for sensitive medical data'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
