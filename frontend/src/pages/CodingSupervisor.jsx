import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { toast } from 'sonner';
import { Hospital, FileText, Users, Upload, BarChart3 } from 'lucide-react';
import Navbar from '@/components/Navbar';
import { useLanguage } from '@/contexts/LanguageContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CodingSupervisor = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const { language } = useLanguage();
  const [hospitals, setHospitals] = useState([]);
  const [cases, setCases] = useState([]);
  const [kpis, setKPIs] = useState(null);
  const [coderStats, setCoderStats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newHospital, setNewHospital] = useState({ name: '', code: '', location: '' });
  const [showAddHospital, setShowAddHospital] = useState(false);

  useEffect(() => {
    if (user?.department !== 'coding' || (user?.role !== 'supervisor' && user?.role !== 'admin')) {
      navigate('/dashboard');
      return;
    }
    fetchData();
  }, [user]);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      const [hospitalsRes, casesRes, kpisRes, statsRes] = await Promise.all([
        axios.get(`${API}/coding/hospitals`, { headers }),
        axios.get(`${API}/coding/cases`, { headers }),
        axios.get(`${API}/coding/stats/department`, { headers }),
        axios.get(`${API}/coding/stats/coders`, { headers })
      ]);

      setHospitals(hospitalsRes.data.hospitals || []);
      setCases(casesRes.data.cases || []);
      setKPIs(kpisRes.data);
      setCoderStats(statsRes.data.coders || []);
    } catch (error) {
      console.error('Error:', error);
      toast.error(language === 'ar' ? 'فشل تحميل البيانات' : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleAddHospital = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/coding/hospitals`, newHospital, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(language === 'ar' ? 'تم إضافة المستشفى' : 'Hospital added');
      setNewHospital({ name: '', code: '', location: '' });
      setShowAddHospital(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || (language === 'ar' ? 'فشل الإضافة' : 'Failed'));
    }
  };

  const handleAssignCases = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await axios.post(`${API}/coding/cases/assign`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(res.data.message);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed');
    }
  };

  const handleFileUpload = async (e, type) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const token = localStorage.getItem('token');
      const endpoint = type === 'icd' ? 'icd-codes/upload' : 'drg-prices/upload';
      const res = await axios.post(`${API}/coding/${endpoint}`, formData, {
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });
      toast.success(res.data.message);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Upload failed');
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center min-h-screen">
      <div className="text-xl">{language === 'ar' ? 'جاري التحميل...' : 'Loading...'}</div>
    </div>;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar user={user} onLogout={onLogout} />
      <main className="max-w-7xl mx-auto p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-800">
              {language === 'ar' ? 'لوحة مشرف الترميز الطبي' : 'Coding Supervisor Dashboard'}
            </h1>
            <p className="text-gray-600 mt-1">
              {language === 'ar' ? 'إدارة المستشفيات والحالات والموظفين' : 'Manage hospitals, cases, and staff'}
            </p>
          </div>
        </div>

        {/* KPIs */}
        {kpis && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="bg-blue-50 border-blue-200">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-blue-800">
                  {language === 'ar' ? 'إجمالي الحالات' : 'Total Cases'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-blue-600">{kpis.total_cases}</div>
                <div className="text-xs text-blue-600 mt-1">
                  {language === 'ar' ? `مكتملة: ${kpis.completed_cases}` : `Completed: ${kpis.completed_cases}`}
                </div>
              </CardContent>
            </Card>

            <Card className="bg-green-50 border-green-200">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-green-800">
                  {language === 'ar' ? 'المرمزون النشطون' : 'Active Coders'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-green-600">
                  {kpis.active_coders_today}/{kpis.total_coders}
                </div>
                <div className="text-xs text-green-600 mt-1">
                  {language === 'ar' ? 'اليوم' : 'Today'}
                </div>
              </CardContent>
            </Card>

            <Card className="bg-purple-50 border-purple-200">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-purple-800">
                  {language === 'ar' ? 'القيمة المالية' : 'Financial Value'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-purple-600">
                  {Math.round(kpis.total_financial_value).toLocaleString()}
                </div>
                <div className="text-xs text-purple-600 mt-1">
                  {language === 'ar' ? 'ريال سعودي' : 'SAR'}
                </div>
              </CardContent>
            </Card>

            <Card className="bg-amber-50 border-amber-200">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-amber-800">
                  {language === 'ar' ? 'معدل الدقة' : 'Accuracy Rate'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-amber-600">
                  {kpis.financial_accuracy.toFixed(1)}%
                </div>
                <div className="text-xs text-amber-600 mt-1">
                  {language === 'ar' ? 'دقة مالية' : 'Financial'}
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Hospitals Management */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Hospital className="h-5 w-5" />
                {language === 'ar' ? 'إدارة المستشفيات' : 'Hospitals Management'}
              </CardTitle>
              <Button onClick={() => setShowAddHospital(!showAddHospital)} size="sm">
                {language === 'ar' ? 'إضافة مستشفى' : 'Add Hospital'}
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {showAddHospital && (
              <form onSubmit={handleAddHospital} className="mb-4 p-4 bg-gray-50 rounded-lg space-y-3">
                <Input
                  placeholder={language === 'ar' ? 'اسم المستشفى' : 'Hospital Name'}
                  value={newHospital.name}
                  onChange={(e) => setNewHospital({...newHospital, name: e.target.value})}
                  required
                />
                <div className="grid grid-cols-2 gap-3">
                  <Input
                    placeholder={language === 'ar' ? 'الكود' : 'Code'}
                    value={newHospital.code}
                    onChange={(e) => setNewHospital({...newHospital, code: e.target.value})}
                    required
                  />
                  <Input
                    placeholder={language === 'ar' ? 'الموقع' : 'Location'}
                    value={newHospital.location}
                    onChange={(e) => setNewHospital({...newHospital, location: e.target.value})}
                    required
                  />
                </div>
                <Button type="submit" className="w-full">
                  {language === 'ar' ? 'حفظ' : 'Save'}
                </Button>
              </form>
            )}
            <div className="space-y-2">
              {hospitals.map(hospital => (
                <div key={hospital.id} className="flex items-center justify-between p-3 bg-white border rounded-lg">
                  <div>
                    <div className="font-semibold">{hospital.name}</div>
                    <div className="text-sm text-gray-600">{hospital.code} - {hospital.location}</div>
                  </div>
                  <div className={`px-3 py-1 rounded-full text-xs ${
                    hospital.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                  }`}>
                    {hospital.is_active ? (language === 'ar' ? 'نشط' : 'Active') : (language === 'ar' ? 'معطل' : 'Inactive')}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Upload Files */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Upload className="h-5 w-5" />
                {language === 'ar' ? 'رفع أكواد ICD-10-AM' : 'Upload ICD-10-AM Codes'}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <label className="cursor-pointer">
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-500 transition">
                  <Upload className="mx-auto h-12 w-12 text-gray-400 mb-2" />
                  <p className="text-sm text-gray-600">
                    {language === 'ar' ? 'اضغط لاختيار ملف Excel' : 'Click to select Excel file'}
                  </p>
                </div>
                <input type="file" accept=".xlsx,.xls" className="hidden" onChange={(e) => handleFileUpload(e, 'icd')} />
              </label>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Upload className="h-5 w-5" />
                {language === 'ar' ? 'رفع أسعار DRG' : 'Upload DRG Prices'}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <label className="cursor-pointer">
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-green-500 transition">
                  <Upload className="mx-auto h-12 w-12 text-gray-400 mb-2" />
                  <p className="text-sm text-gray-600">
                    {language === 'ar' ? 'اضغط لاختيار ملف Excel' : 'Click to select Excel file'}
                  </p>
                </div>
                <input type="file" accept=".xlsx,.xls" className="hidden" onChange={(e) => handleFileUpload(e, 'drg')} />
              </label>
            </CardContent>
          </Card>
        </div>

        {/* Cases & Distribution */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                {language === 'ar' ? 'الحالات الطبية' : 'Medical Cases'}
              </CardTitle>
              <Button onClick={handleAssignCases}>
                {language === 'ar' ? 'توزيع على المرمزين' : 'Distribute to Coders'}
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {cases.slice(0, 5).map(c => (
                <div key={c.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <div className="font-semibold">{c.case_number}</div>
                    <div className="text-sm text-gray-600">{c.patient_id} - {c.chief_complaint}</div>
                  </div>
                  <div className={`px-3 py-1 rounded-full text-xs ${
                    c.status === 'completed' ? 'bg-green-100 text-green-700' :
                    c.status === 'in_progress' ? 'bg-blue-100 text-blue-700' :
                    'bg-gray-100 text-gray-700'
                  }`}>
                    {c.status === 'completed' ? (language === 'ar' ? 'مكتمل' : 'Completed') :
                     c.status === 'in_progress' ? (language === 'ar' ? 'جاري' : 'In Progress') :
                     (language === 'ar' ? 'معلق' : 'Pending')}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Coder Statistics */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              {language === 'ar' ? 'إحصائيات المرمزين' : 'Coder Statistics'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {coderStats.map(stat => (
                <div key={stat.user_id} className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <div className="font-semibold">{stat.full_name}</div>
                    <div className="text-sm text-gray-600">
                      {language === 'ar' ? 'اليوم:' : 'Today:'} {stat.completed_today}/{stat.daily_target}
                    </div>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-green-600 h-2 rounded-full transition-all"
                      style={{ width: `${Math.min(stat.completion_rate, 100)}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-gray-600 mt-1">
                    <span>{language === 'ar' ? 'متوسط الوقت:' : 'Avg time:'} {stat.avg_coding_time} {language === 'ar' ? 'دقيقة' : 'min'}</span>
                    <span>{stat.completion_rate.toFixed(1)}%</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
};

export default CodingSupervisor;