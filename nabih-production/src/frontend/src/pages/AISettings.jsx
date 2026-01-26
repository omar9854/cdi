import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { useLanguage } from '@/contexts/LanguageContext';
import { Brain, Server, Shield, Cpu, Database, Lock } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

export default function AISettings({ user, onLogout }) {
  const { language } = useLanguage();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <div className="container mx-auto p-6 max-w-6xl">
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <Brain className="h-8 w-8 text-blue-600" />
            <h1 className="text-3xl font-bold text-gray-800">
              {language === 'ar' ? 'إعدادات الذكاء الاصطناعي' : 'AI Settings'}
            </h1>
          </div>
          <p className="text-gray-600">
            {language === 'ar' ? 
              'نظام ذكاء اصطناعي محلي آمن 100% - بدون تبعيات خارجية' : 
              '100% Secure Local AI System - No External Dependencies'
            }
          </p>
        </div>

        {/* Offline AI Notice */}
        <Card className="mb-6 bg-green-50 border-green-200">
          <CardHeader>
            <div className="flex items-center gap-3">
              <Shield className="h-8 w-8 text-green-600" />
              <div>
                <CardTitle className="text-xl text-green-800">
                  {language === 'ar' ? 'نظام آمن 100%' : '100% Secure System'}
                </CardTitle>
                <CardDescription className="text-green-700">
                  {language === 'ar' ? 
                    'هذا النظام يعمل بالكامل محلياً بدون إرسال أي بيانات لخوادم خارجية' : 
                    'This system operates entirely locally without sending any data to external servers'
                  }
                </CardDescription>
              </div>
            </div>
          </CardHeader>
        </Card>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Local LLM Card */}
          <Card className="medical-card">
            <CardHeader>
              <div className="flex items-center gap-3">
                <Cpu className="h-8 w-8 text-blue-600" />
                <div>
                  <CardTitle className="text-xl">
                    {language === 'ar' ? 'نموذج الذكاء الاصطناعي المحلي' : 'Local AI Model'}
                  </CardTitle>
                  <CardDescription>
                    Qwen2.5-72B-Instruct
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
                  <span className="text-sm font-medium">
                    {language === 'ar' ? 'الحالة' : 'Status'}
                  </span>
                  <span className="text-green-600 font-semibold flex items-center gap-2">
                    <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                    {language === 'ar' ? 'نشط' : 'Active'}
                  </span>
                </div>
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm font-medium">
                    {language === 'ar' ? 'نوع التكميم' : 'Quantization'}
                  </span>
                  <span className="text-gray-700">4-bit NF4</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm font-medium">
                    {language === 'ar' ? 'الجهاز' : 'Device'}
                  </span>
                  <span className="text-gray-700">NVIDIA A100 GPU</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Security Card */}
          <Card className="medical-card">
            <CardHeader>
              <div className="flex items-center gap-3">
                <Lock className="h-8 w-8 text-purple-600" />
                <div>
                  <CardTitle className="text-xl">
                    {language === 'ar' ? 'أمان البيانات' : 'Data Security'}
                  </CardTitle>
                  <CardDescription>
                    {language === 'ar' ? 'حماية البيانات الطبية' : 'Medical Data Protection'}
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center gap-3 p-3 bg-green-50 rounded-lg">
                  <span className="text-green-600">✓</span>
                  <span className="text-sm">
                    {language === 'ar' ? 'لا يتم إرسال بيانات لخوادم خارجية' : 'No data sent to external servers'}
                  </span>
                </div>
                <div className="flex items-center gap-3 p-3 bg-green-50 rounded-lg">
                  <span className="text-green-600">✓</span>
                  <span className="text-sm">
                    {language === 'ar' ? 'معالجة محلية 100%' : '100% Local Processing'}
                  </span>
                </div>
                <div className="flex items-center gap-3 p-3 bg-green-50 rounded-lg">
                  <span className="text-green-600">✓</span>
                  <span className="text-sm">
                    {language === 'ar' ? 'متوافق مع HIPAA' : 'HIPAA Compliant'}
                  </span>
                </div>
                <div className="flex items-center gap-3 p-3 bg-green-50 rounded-lg">
                  <span className="text-green-600">✓</span>
                  <span className="text-sm">
                    {language === 'ar' ? 'تشفير البيانات في الراحة والنقل' : 'Data encrypted at rest and in transit'}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* DRG Pricing Card */}
          <Card className="medical-card">
            <CardHeader>
              <div className="flex items-center gap-3">
                <Database className="h-8 w-8 text-orange-600" />
                <div>
                  <CardTitle className="text-xl">
                    {language === 'ar' ? 'قاعدة بيانات DRG' : 'DRG Database'}
                  </CardTitle>
                  <CardDescription>
                    AR-DRG v9 - Saudi Arabia
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between items-center p-3 bg-orange-50 rounded-lg">
                  <span className="text-sm font-medium">
                    {language === 'ar' ? 'عدد أكواد DRG' : 'DRG Codes'}
                  </span>
                  <span className="text-orange-700 font-semibold">800+</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm font-medium">
                    {language === 'ar' ? 'تعيينات ICD-10-AM' : 'ICD-10-AM Mappings'}
                  </span>
                  <span className="text-gray-700">150+</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm font-medium">
                    {language === 'ar' ? 'نوع المستشفى' : 'Hospital Type'}
                  </span>
                  <span className="text-gray-700">
                    {language === 'ar' ? 'مدينة طبية (A)' : 'Medical City (A)'}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* System Info Card */}
          <Card className="medical-card">
            <CardHeader>
              <div className="flex items-center gap-3">
                <Server className="h-8 w-8 text-gray-600" />
                <div>
                  <CardTitle className="text-xl">
                    {language === 'ar' ? 'معلومات النظام' : 'System Information'}
                  </CardTitle>
                  <CardDescription>
                    {language === 'ar' ? 'تفاصيل السيرفر' : 'Server Details'}
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm font-medium">
                    {language === 'ar' ? 'دور المستخدم' : 'User Role'}
                  </span>
                  <span className="text-gray-700">
                    {language === 'ar' ? 'مدقق طبي أول' : 'Senior Medical Auditor'}
                  </span>
                </div>
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm font-medium">
                    {language === 'ar' ? 'معايير الترميز' : 'Coding Standards'}
                  </span>
                  <span className="text-gray-700">ICD-10-AM</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm font-medium">
                    {language === 'ar' ? 'الاتصال بالإنترنت' : 'Internet Connection'}
                  </span>
                  <span className="text-red-600 font-medium">
                    {language === 'ar' ? 'غير مطلوب' : 'Not Required'}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Important Notice */}
        <Card className="mt-6 bg-blue-50 border-blue-200">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <Shield className="h-5 w-5 text-blue-600 mt-1" />
              <div className="space-y-2">
                <p className="font-semibold text-blue-900">
                  {language === 'ar' ? 'ملاحظات الأمان' : 'Security Notes'}
                </p>
                <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
                  <li>
                    {language === 'ar' ? 
                      'هذا النظام مصمم للعمل بدون اتصال بالإنترنت' : 
                      'This system is designed to work without internet connection'
                    }
                  </li>
                  <li>
                    {language === 'ar' ? 
                      'جميع البيانات الطبية تبقى داخل الشبكة المحلية' : 
                      'All medical data stays within the local network'
                    }
                  </li>
                  <li>
                    {language === 'ar' ? 
                      'لا توجد مفاتيح API خارجية - النظام آمن 100%' : 
                      'No external API keys - System is 100% secure'
                    }
                  </li>
                  <li>
                    {language === 'ar' ? 
                      'التحليلات تتم محلياً باستخدام نموذج Qwen2.5-72B' : 
                      'Analysis is performed locally using Qwen2.5-72B model'
                    }
                  </li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
