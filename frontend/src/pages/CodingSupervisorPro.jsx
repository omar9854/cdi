import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import { Hospital, FileText, Users, Upload, BarChart3, Plus, Edit, Trash2, Power } from 'lucide-react';
import Navbar from '@/components/Navbar';
import { useLanguage } from '@/contexts/LanguageContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CodingSupervisorPro = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const { language } = useLanguage();
  const [hospitals, setHospitals] = useState([]);
  const [cases, setCases] = useState([]);
  const [kpis, setKPIs] = useState(null);
  const [coderStats, setCoderStats] = useState([]);
  const [coders, setCoders] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Hospital management
  const [editingHospital, setEditingHospital] = useState(null);
  const [newHospital, setNewHospital] = useState({ name: '', code: '', location: '' });
  const [showAddHospital, setShowAddHospital] = useState(false);
  
  // Manual case creation
  const [showManualCase, setShowManualCase] = useState(false);
  const [manualCase, setManualCase] = useState({
    case_number: '',
    hospital_id: '',
    admission_days: 1,
    assigned_coder_id: ''
  });
  
  // Excel upload
  const [showExcelUpload, setShowExcelUpload] = useState(false);

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

      const [hospitalsRes, casesRes, kpisRes, statsRes, codersRes] = await Promise.all([
        axios.get(`${API}/coding/hospitals`, { headers }),
        axios.get(`${API}/coding/cases`, { headers }),
        axios.get(`${API}/coding/stats/department`, { headers }),
        axios.get(`${API}/coding/stats/coders`, { headers }),
        axios.get(`${API}/users?department=coding&coding_role=coder`, { headers })
      ]);

      setHospitals(hospitalsRes.data.hospitals || []);
      setCases(casesRes.data.cases || []);
      setKPIs(kpisRes.data);
      setCoderStats(statsRes.data.coders || []);
      setCoders(codersRes.data.users || []);
    } catch (error) {
      console.error('Error:', error);
      toast.error(language === 'ar' ? 'فشل تحميل البيانات' : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveHospital = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      if (editingHospital) {
        await axios.put(`${API}/coding/hospitals/${editingHospital.id}`, newHospital, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success(language === 'ar' ? 'تم التحديث' : 'Updated');
      } else {
        await axios.post(`${API}/coding/hospitals`, newHospital, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success(language === 'ar' ? 'تم الإضافة' : 'Added');
      }
      setNewHospital({ name: '', code: '', location: '' });
      setEditingHospital(null);
      setShowAddHospital(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed');
    }
  };

  const handleDeleteHospital = async (id) => {
    if (!confirm(language === 'ar' ? 'تأكيد الحذف؟' : 'Confirm delete?')) return;
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API}/coding/hospitals/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(language === 'ar' ? 'تم التعطيل' : 'Deactivated');
      fetchData();
    } catch (error) {
      toast.error('Failed');
    }
  };

  const handleActivateHospital = async (id) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/coding/hospitals/${id}/activate`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(language === 'ar' ? 'تم التفعيل' : 'Activated');
      fetchData();
    } catch (error) {
      toast.error('Failed');
    }
  };

  const handleCreateManualCase = async (e) => {
    e.preventDefault();
    if (!manualCase.case_number || !manualCase.hospital_id || !manualCase.assigned_coder_id) {
      toast.error(language === 'ar' ? 'املأ جميع الحقول' : 'Fill all fields');
      return;
    }
    
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API}/coding/cases/manual?case_number=${manualCase.case_number}&hospital_id=${manualCase.hospital_id}&admission_days=${manualCase.admission_days}&assigned_coder_id=${manualCase.assigned_coder_id}&user_id=${user.id}`,
        {},
        { headers: { Authorization: `Bearer ${token}` }}
      );
      toast.success(response.data.message);
      setManualCase({ case_number: '', hospital_id: '', admission_days: 1, assigned_coder_id: '' });
      setShowManualCase(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed');
    }
  };

  const handleUploadExcel = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_id', user.id);

    try {
      const token = localStorage.getItem('token');
      const res = await axios.post(`${API}/coding/cases/upload-excel?user_id=${user.id}`, formData, {
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });
      toast.success(res.data.message);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Upload failed');
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
              <Button onClick={() => { setShowAddHospital(!showAddHospital); setEditingHospital(null); setNewHospital({ name: '', code: '', location: '' }); }} size="sm">
                <Plus className="h-4 w-4 mr-1" />
                {language === 'ar' ? 'إضافة مستشفى' : 'Add Hospital'}
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {showAddHospital && (
              <form onSubmit={handleSaveHospital} className="mb-4 p-4 bg-gray-50 rounded-lg space-y-3">
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
                <div className="flex gap-2">
                  <Button type="submit" className="flex-1">
                    {editingHospital ? (language === 'ar' ? 'تحديث' : 'Update') : (language === 'ar' ? 'حفظ' : 'Save')}
                  </Button>
                  <Button type="button" variant="outline" onClick={() => { setShowAddHospital(false); setEditingHospital(null); }}>
                    {language === 'ar' ? 'إلغاء' : 'Cancel'}
                  </Button>
                </div>
              </form>
            )}
            <div className="space-y-2">
              {hospitals.map(hospital => (
                <div key={hospital.id} className="flex items-center justify-between p-3 bg-white border rounded-lg">
                  <div>
                    <div className="font-semibold">{hospital.name}</div>
                    <div className="text-sm text-gray-600">{hospital.code} - {hospital.location}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className={`px-3 py-1 rounded-full text-xs ${
                      hospital.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                    }`}>
                      {hospital.is_active ? (language === 'ar' ? 'نشط' : 'Active') : (language === 'ar' ? 'معطل' : 'Inactive')}
                    </div>
                    <Button 
                      size="sm" 
                      variant="outline"
                      onClick={() => { setEditingHospital(hospital); setNewHospital({ name: hospital.name, code: hospital.code, location: hospital.location }); setShowAddHospital(true); }}
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                    {hospital.is_active ? (
                      <Button size="sm" variant="destructive" onClick={() => handleDeleteHospital(hospital.id)}>
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    ) : (
                      <Button size="sm" variant="default" onClick={() => handleActivateHospital(hospital.id)}>
                        <Power className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Case Assignment Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Manual Case Creation */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Plus className="h-5 w-5" />
                {language === 'ar' ? 'إضافة حالة يدوياً' : 'Add Case Manually'}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {!showManualCase ? (
                <Button onClick={() => setShowManualCase(true)} className="w-full">
                  {language === 'ar' ? 'إنشاء حالة جديدة' : 'Create New Case'}
                </Button>
              ) : (
                <form onSubmit={handleCreateManualCase} className="space-y-3">
                  <Input
                    placeholder={language === 'ar' ? 'رقم الملف' : 'Case Number'}
                    value={manualCase.case_number}
                    onChange={(e) => setManualCase({...manualCase, case_number: e.target.value})}
                    required
                  />
                  <Select value={manualCase.hospital_id} onValueChange={(v) => setManualCase({...manualCase, hospital_id: v})}>
                    <SelectTrigger>
                      <SelectValue placeholder={language === 'ar' ? 'اختر المستشفى' : 'Select Hospital'} />
                    </SelectTrigger>
                    <SelectContent>
                      {hospitals.filter(h => h.is_active).map(h => (
                        <SelectItem key={h.id} value={h.id}>{h.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Input
                    type="number"
                    placeholder={language === 'ar' ? 'مدة التنويم (أيام)' : 'Admission Days'}
                    value={manualCase.admission_days}
                    onChange={(e) => setManualCase({...manualCase, admission_days: parseInt(e.target.value)})}
                    min="1"
                    required
                  />
                  <Select value={manualCase.assigned_coder_id} onValueChange={(v) => setManualCase({...manualCase, assigned_coder_id: v})}>
                    <SelectTrigger>
                      <SelectValue placeholder={language === 'ar' ? 'اختر المرمز' : 'Select Coder'} />
                    </SelectTrigger>
                    <SelectContent>
                      {coders.map(c => (
                        <SelectItem key={c.id} value={c.id}>{c.full_name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <div className="flex gap-2">
                    <Button type="submit" className="flex-1">
                      {language === 'ar' ? 'إرسال' : 'Submit'}
                    </Button>
                    <Button type="button" variant="outline" onClick={() => setShowManualCase(false)}>
                      {language === 'ar' ? 'إلغاء' : 'Cancel'}
                    </Button>
                  </div>
                </form>
              )}
            </CardContent>
          </Card>

          {/* Excel Upload */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Upload className="h-5 w-5" />
                {language === 'ar' ? 'رفع ملف Excel' : 'Upload Excel File'}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <p className="text-sm text-gray-600">
                  {language === 'ar' 
                    ? 'رفع ملف Excel للتوزيع التلقائي حسب عدد الملفات المحدد لكل مرمز' 
                    : 'Upload Excel for automatic distribution based on coder targets'}
                </p>
                <div className="text-xs text-gray-500 bg-gray-50 p-3 rounded">
                  <div className="font-semibold mb-1">{language === 'ar' ? 'الأعمدة المطلوبة:' : 'Required columns:'}</div>
                  <ul className="list-disc list-inside space-y-1">
                    <li>case_number</li>
                    <li>hospital_code</li>
                    <li>admission_days</li>
                  </ul>
                </div>
                <label className="cursor-pointer">
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-500 transition">
                    <Upload className="mx-auto h-12 w-12 text-gray-400 mb-2" />
                    <p className="text-sm text-gray-600">
                      {language === 'ar' ? 'اضغط لاختيار ملف Excel' : 'Click to select Excel file'}
                    </p>
                  </div>
                  <input type="file" accept=".xlsx,.xls" className="hidden" onChange={handleUploadExcel} />
                </label>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Upload ICD & DRG Files */}
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

export default CodingSupervisorPro;
