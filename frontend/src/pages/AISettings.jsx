import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useLanguage } from '@/contexts/LanguageContext';
import { toast } from 'sonner';
import axios from 'axios';
import { Key, Plus, Trash2, Save, Brain, Server } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
const API = `${BACKEND_URL}/api`;

export default function AISettings({ user, onLogout }) {
  const { language, t } = useLanguage();
  const [loading, setLoading] = useState(false);
  const [providers, setProviders] = useState({
    gemini: { name: 'Google Gemini', name_ar: 'جوجل جيميناي', keys_count: 0, api_keys: [] },
    azure: { name: 'Microsoft Azure', name_ar: 'مايكروسوفت أزور', keys_count: 0, api_keys: [] },
    deepseek: { name: 'DeepSeek', name_ar: 'ديب سيك', keys_count: 0, api_keys: [] }
  });
  
  const [editingProvider, setEditingProvider] = useState(null);
  const [newKeys, setNewKeys] = useState({});

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/admin/ai-settings`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProviders(response.data);
    } catch (error) {
      toast.error(language === 'ar' ? 'فشل تحميل الإعدادات' : 'Failed to load settings');
    }
  };

  const handleAddKey = (provider) => {
    setNewKeys(prev => ({
      ...prev,
      [provider]: [...(prev[provider] || providers[provider].api_keys), '']
    }));
  };

  const handleKeyChange = (provider, index, value) => {
    setNewKeys(prev => {
      const keys = [...(prev[provider] || providers[provider].api_keys)];
      keys[index] = value;
      return { ...prev, [provider]: keys };
    });
  };

  const handleRemoveKey = (provider, index) => {
    setNewKeys(prev => {
      const keys = [...(prev[provider] || providers[provider].api_keys)];
      keys.splice(index, 1);
      return { ...prev, [provider]: keys };
    });
  };

  const handleSave = async (provider) => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const keys = (newKeys[provider] || providers[provider].api_keys).filter(k => k.trim() !== '');
      
      if (keys.length === 0) {
        toast.error(language === 'ar' ? 'يجب إضافة مفتاح واحد على الأقل' : 'At least one key is required');
        setLoading(false);
        return;
      }

      await axios.put(
        `${API}/admin/ai-settings`,
        {
          provider: provider,
          api_keys: keys
        },
        { headers: { Authorization: `Bearer ${token}` }}
      );

      toast.success(language === 'ar' ? 'تم حفظ المفاتيح بنجاح' : 'Keys saved successfully');
      setEditingProvider(null);
      setNewKeys(prev => ({ ...prev, [provider]: undefined }));
      await fetchSettings();
    } catch (error) {
      toast.error(error.response?.data?.detail || (language === 'ar' ? 'فشل الحفظ' : 'Failed to save'));
    }
    setLoading(false);
  };

  const renderProviderCard = (providerId) => {
    const provider = providers[providerId];
    const isEditing = editingProvider === providerId;
    const currentKeys = newKeys[providerId] || provider.api_keys;

    const getProviderIcon = () => {
      if (providerId === 'gemini') return '🤖';
      if (providerId === 'azure') return '☁️';
      if (providerId === 'deepseek') return '🧠';
      return '🔑';
    };

    return (
      <Card key={providerId} className="medical-card">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-3xl">{getProviderIcon()}</span>
              <div>
                <CardTitle className="text-xl">
                  {language === 'ar' ? provider.name_ar : provider.name}
                </CardTitle>
                <CardDescription>
                  {language === 'ar' ? 
                    `${provider.keys_count} مفتاح نشط` : 
                    `${provider.keys_count} active key${provider.keys_count !== 1 ? 's' : ''}`
                  }
                </CardDescription>
              </div>
            </div>
            {!isEditing && (
              <Button
                onClick={() => setEditingProvider(providerId)}
                variant="outline"
                size="sm"
              >
                <Key className="h-4 w-4 mr-2" />
                {language === 'ar' ? 'إدارة المفاتيح' : 'Manage Keys'}
              </Button>
            )}
          </div>
        </CardHeader>

        {isEditing && (
          <CardContent className="space-y-4">
            <div className="space-y-3">
              <Label className="text-sm font-semibold">
                {language === 'ar' ? 'مفاتيح API' : 'API Keys'}
              </Label>
              
              {currentKeys.map((key, index) => (
                <div key={index} className="flex gap-2">
                  <Input
                    type="password"
                    value={key}
                    onChange={(e) => handleKeyChange(providerId, index, e.target.value)}
                    placeholder={language === 'ar' ? 'أدخل مفتاح API' : 'Enter API key'}
                    className="flex-1"
                  />
                  <Button
                    onClick={() => handleRemoveKey(providerId, index)}
                    variant="destructive"
                    size="icon"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}

              <Button
                onClick={() => handleAddKey(providerId)}
                variant="outline"
                className="w-full"
                size="sm"
              >
                <Plus className="h-4 w-4 mr-2" />
                {language === 'ar' ? 'إضافة مفتاح' : 'Add Key'}
              </Button>
            </div>

            <div className="flex gap-2 pt-4 border-t">
              <Button
                onClick={() => handleSave(providerId)}
                disabled={loading}
                className="flex-1"
              >
                <Save className="h-4 w-4 mr-2" />
                {language === 'ar' ? 'حفظ' : 'Save'}
              </Button>
              <Button
                onClick={() => {
                  setEditingProvider(null);
                  setNewKeys(prev => ({ ...prev, [providerId]: undefined }));
                }}
                variant="outline"
                className="flex-1"
              >
                {language === 'ar' ? 'إلغاء' : 'Cancel'}
              </Button>
            </div>
          </CardContent>
        )}
      </Card>
    );
  };

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
              'إدارة مفاتيح API لمزودي الذكاء الاصطناعي المختلفين' : 
              'Manage API keys for different AI providers'
            }
          </p>
        </div>

        <div className="grid grid-cols-1 gap-6">
          {renderProviderCard('gemini')}
          {renderProviderCard('azure')}
          {renderProviderCard('deepseek')}
        </div>

        <Card className="mt-6 bg-blue-50 border-blue-200">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <Server className="h-5 w-5 text-blue-600 mt-1" />
              <div className="space-y-2">
                <p className="font-semibold text-blue-900">
                  {language === 'ar' ? 'ملاحظات مهمة' : 'Important Notes'}
                </p>
                <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
                  <li>
                    {language === 'ar' ? 
                      'سيتم استخدام المفاتيح بالتناوب تلقائياً لتوزيع الحمل' : 
                      'Keys will be automatically rotated for load balancing'
                    }
                  </li>
                  <li>
                    {language === 'ar' ? 
                      'تأكد من صحة المفاتيح قبل الحفظ' : 
                      'Ensure keys are valid before saving'
                    }
                  </li>
                  <li>
                    {language === 'ar' ? 
                      'يمكن للمستخدمين اختيار مزود الذكاء الاصطناعي عند التحليل' : 
                      'Users can choose AI provider during analysis'
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
