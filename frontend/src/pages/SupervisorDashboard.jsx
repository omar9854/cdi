import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { toast } from 'sonner';
import { 
  Upload, FileSpreadsheet, TrendingUp, AlertTriangle, Activity, Hospital, 
  Users, Award, BarChart3, Stethoscope, Download, PieChart, Eye, Lock, MessageSquare, FileText, DollarSign
} from 'lucide-react';
import {
  BarChart, Bar, PieChart as RePieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import Navbar from '@/components/Navbar';
import { useLanguage } from '@/contexts/LanguageContext';
import Footer from '@/components/Footer';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82ca9d'];

const SupervisorDashboard = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const { language, t } = useLanguage();
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [employees, setEmployees] = useState([]);
  const [selectedHospital, setSelectedHospital] = useState(null);
  const [changePasswordUser, setChangePasswordUser] = useState(null);
  const [newPassword, setNewPassword] = useState('');

  useEffect(() => {
    if (user.role !== 'supervisor' && user.role !== 'admin') {
      navigate('/dashboard');
      return;
    }
    fetchEmployees();
  }, []);

  const fetchEmployees = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/supervisor/employees`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      console.log('Employees fetched:', response.data);
      console.log('Number of employees:', response.data?.length);
      setEmployees(response.data || []);
    } catch (error) {
      console.error('Failed to fetch employees:', error);
      toast.error(language === 'ar' ? 'فشل تحميل قائمة الموظفين' : 'Failed to load employees');
    }
  };

  const handleImpersonateEmployee = async (employeeId, employeeName) => {
    if (!window.confirm(language === 'ar' ? `هل تريد الدخول إلى حساب ${employeeName}؟` : `Do you want to access ${employeeName}'s account?`)) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API}/admin/impersonate/${employeeId}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );

      console.log('Impersonation response:', response.data);

      // Store original token (works for both admin and supervisor)
      const currentUser = JSON.parse(localStorage.getItem('user'));
      if (currentUser?.role === 'admin') {
        localStorage.setItem('admin_token_backup', token);
      } else {
        localStorage.setItem('supervisor_token_backup', token);
      }
      localStorage.setItem('is_impersonating', 'true');
      
      // Set the impersonated user's token
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
      
      toast.success(language === 'ar' ? `تم الدخول إلى حساب ${employeeName}` : `Now viewing ${employeeName}'s account`);
      
      // Reload to dashboard
      setTimeout(() => {
        window.location.href = '/dashboard';
      }, 500);
    } catch (error) {
      console.error('Impersonation error:', error);
      toast.error(language === 'ar' ? 'فشل الدخول للحساب' : 'Failed to impersonate user');
    }
  };

  const handleChangePassword = async () => {
    if (!newPassword || newPassword.length < 6) {
      toast.error(language === 'ar' ? 'كلمة المرور يجب أن تكون 6 أحرف على الأقل' : 'Password must be at least 6 characters');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/admin/change-user-password/${changePasswordUser.id}`,
        null,
        {
          params: { new_password: newPassword },
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      toast.success(language === 'ar' ? 'تم تغيير كلمة المرور بنجاح' : 'Password changed successfully');
      setChangePasswordUser(null);
      setNewPassword('');
    } catch (error) {
      toast.error(language === 'ar' ? 'فشل تغيير كلمة المرور' : 'Failed to change password');
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
      toast.error(language === 'ar' ? 'يرجى رفع ملف Excel فقط' : 'Please upload Excel file only');
      return;
    }

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/supervisor/upload-cdi-data`, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });

      setAnalysis(response.data);
      toast.success(language === 'ar' ? 'تم تحليل البيانات بنجاح ✅' : 'Data analyzed successfully ✅');
    } catch (error) {
      toast.error(
        error.response?.data?.detail || 
        (language === 'ar' ? 'فشل تحليل البيانات' : 'Failed to analyze data')
      );
    } finally {
      setUploading(false);
    }
  };

  const handleDownloadExcel = async () => {
    if (!analysis) return;
    
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API}/supervisor/generate-excel-report`,
        analysis,
        {
          headers: { Authorization: `Bearer ${token}` },
          responseType: 'blob'
        }
      );

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `CDI_Report_${new Date().toISOString().split('T')[0]}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      toast.success(language === 'ar' ? 'تم تحميل التقرير بنجاح ✅' : 'Report downloaded successfully ✅');
    } catch (error) {
      toast.error(language === 'ar' ? 'فشل تحميل التقرير' : 'Failed to download report');
    }
  };

  const renderSummaryCards = () => {
    if (!analysis) return null;

    return (
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card className="medical-card bg-gradient-to-br from-blue-50 to-blue-100">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              {language === 'ar' ? 'إجمالي الحالات' : 'Total Cases'}
            </CardTitle>
            <FileSpreadsheet className="h-5 w-5 text-[#0066a1]" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-700">{analysis.summary.total_records}</div>
            <p className="text-xs text-[#0066a1] mt-1">
              {analysis.summary.total_hospitals} {language === 'ar' ? 'مستشفى' : 'hospitals'}
            </p>
          </CardContent>
        </Card>

        <Card className="medical-card bg-gradient-to-br from-purple-50 to-purple-100">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              {language === 'ar' ? 'تغييرات DRG' : 'DRG Changes'}
            </CardTitle>
            <TrendingUp className="h-5 w-5 text-[#0066a1]" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-purple-700">{analysis.drg_metrics.total_changes}</div>
            <p className="text-xs text-[#0066a1] mt-1">
              {analysis.drg_metrics.change_rate}% {language === 'ar' ? 'معدل التغيير' : 'change rate'}
            </p>
          </CardContent>
        </Card>


        {/* Financial Impact Card */}
        {analysis.drg_financial_impact && (
          <Card className="medical-card bg-gradient-to-br from-green-50 to-emerald-100">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {language === 'ar' ? 'الأثر المالي' : 'Financial Impact'}
              </CardTitle>
              <DollarSign className="h-5 w-5 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className={`text-2xl font-bold ${analysis.drg_financial_impact.summary.total_financial_impact_sar >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                {analysis.drg_financial_impact.summary.total_impact_formatted}
              </div>
              <p className="text-xs text-green-600 mt-1">
                {analysis.drg_financial_impact.summary.total_drg_changes} {language === 'ar' ? 'حالة' : 'cases'}
              </p>
            </CardContent>
          </Card>
        )}
        <Card className="medical-card bg-gradient-to-br from-blue-50 to-indigo-100">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              {language === 'ar' ? 'PDX/After CDI' : 'PDX/After CDI'}
            </CardTitle>
            <Stethoscope className="h-5 w-5 text-[#0066a1]" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-[#0066a1]">{analysis.pdx_metrics.total_after_cdi}</div>
            <p className="text-xs text-[#0066a1] mt-1">
              {analysis.pdx_metrics.changes} {language === 'ar' ? 'تغييرات' : 'changes'} | {analysis.pdx_metrics.newly_added} {language === 'ar' ? 'جديد' : 'new'}
            </p>
          </CardContent>
        </Card>

        <Card className="medical-card bg-gradient-to-br from-orange-50 to-orange-100">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              {language === 'ar' ? 'ADX due to CDI' : 'ADX due to CDI'}
            </CardTitle>
            <AlertTriangle className="h-5 w-5 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-orange-700">{analysis.adx_metrics.total_added}</div>
            <p className="text-xs text-orange-600 mt-1">
              {analysis.adx_metrics.addition_rate}% {language === 'ar' ? 'معدل الإضافة' : 'addition rate'}
            </p>
          </CardContent>
        </Card>

        <Card className="medical-card bg-gradient-to-br from-cyan-50 to-cyan-100">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              {language === 'ar' ? 'عدد الاستفسارات' : 'Numbers of Query'}
            </CardTitle>
            <MessageSquare className="h-5 w-5 text-cyan-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-cyan-700">{analysis.query_metrics?.total_queries || 0}</div>
            <p className="text-xs text-cyan-600 mt-1">
              {language === 'ar' ? 'إجمالي الاستفسارات' : 'Total queries'}
            </p>
          </CardContent>
        </Card>

        <Card className="medical-card bg-gradient-to-br from-teal-50 to-teal-100">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              {language === 'ar' ? 'عدد المراجعات' : 'Numbers of Review'}
            </CardTitle>
            <FileText className="h-5 w-5 text-teal-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-teal-700">{analysis.review_metrics?.total_reviews || 0}</div>
            <p className="text-xs text-teal-600 mt-1">
              {language === 'ar' ? 'إجمالي المراجعات' : 'Total reviews'}
            </p>
          </CardContent>
        </Card>

        <Card className="medical-card bg-gradient-to-br from-indigo-50 to-indigo-100">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              {language === 'ar' ? 'عدد الردود' : 'Numbers of Response'}
            </CardTitle>
            <Award className="h-5 w-5 text-indigo-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-indigo-700">{analysis.response_metrics?.total_responses || 0}</div>
            <p className="text-xs text-indigo-600 mt-1">
              {language === 'ar' ? 'إجمالي الردود' : 'Total responses'}
            </p>
          </CardContent>
        </Card>
      </div>
    );
  };

  const renderHospitalsAnalysis = () => {
    if (!analysis || !analysis.hospitals_analysis) return null;

    return (
      <Card className="medical-card mb-8">
        <CardHeader>
          <CardTitle className="text-2xl text-gray-800">
            {language === 'ar' ? 'تحليل المستشفيات التفصيلي' : 'Detailed Hospital Analysis'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {analysis.hospitals_analysis.map((hospital, index) => (
              <div key={index} className="border rounded-lg p-4 bg-gradient-to-r from-gray-50 to-white">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                    <Hospital className="h-5 w-5 text-[#0066a1]" />
                    {hospital.hospital_name}
                  </h3>
                  <div className="text-sm text-gray-600">
                    {hospital.total_cases} {language === 'ar' ? 'حالة' : 'cases'}
                  </div>
                </div>

                <div className="grid md:grid-cols-6 gap-4 mb-4">
                  <div className="bg-purple-50 p-3 rounded-lg">
                    <div className="text-xs text-[#0066a1] mb-1">{language === 'ar' ? 'تغييرات DRG' : 'DRG Changes'}</div>
                    <div className="text-2xl font-bold text-purple-700">{hospital.drg_changes}</div>
                    <div className="text-xs text-[#0066a1]">{hospital.drg_impact_rate}%</div>
                  </div>
                  
                  <div className="bg-green-50 p-3 rounded-lg">
                    <div className="text-xs text-green-600 mb-1">{language === 'ar' ? 'PDX المضافة' : 'PDX Added'}</div>
                    <div className="text-2xl font-bold text-green-700">{hospital.pdx_added}</div>
                  </div>
                  
                  <div className="bg-orange-50 p-3 rounded-lg">
                    <div className="text-xs text-orange-600 mb-1">{language === 'ar' ? 'ADX المضافة' : 'ADX Added'}</div>
                    <div className="text-2xl font-bold text-orange-700">{hospital.adx_added}</div>
                  </div>
                  
                  <div className="bg-cyan-50 p-3 rounded-lg">
                    <div className="text-xs text-cyan-600 mb-1">{language === 'ar' ? 'الاستفسارات' : 'Queries'}</div>
                    <div className="text-2xl font-bold text-cyan-700">{hospital.total_queries || 0}</div>
                  </div>
                  
                  <div className="bg-teal-50 p-3 rounded-lg">
                    <div className="text-xs text-teal-600 mb-1">{language === 'ar' ? 'المراجعات' : 'Reviews'}</div>
                    <div className="text-2xl font-bold text-teal-700">{hospital.total_reviews || 0}</div>
                  </div>
                  
                  <div className="bg-indigo-50 p-3 rounded-lg">
                    <div className="text-xs text-indigo-600 mb-1">{language === 'ar' ? 'الردود' : 'Responses'}</div>
                    <div className="text-2xl font-bold text-indigo-700">{hospital.total_responses || 0}</div>
                  </div>
                </div>

                <div className="grid md:grid-cols-2 gap-4">
                  {hospital.top_pdx_diagnoses && hospital.top_pdx_diagnoses.length > 0 && (
                    <div className="bg-blue-50 p-3 rounded-lg">
                      <h4 className="font-semibold text-blue-800 mb-2 text-sm">
                        {language === 'ar' ? 'أكثر تشخيصات PDX/After CDI' : 'Top PDX/After CDI Diagnoses'}
                      </h4>
                      <div className="space-y-1 max-h-48 overflow-y-auto">
                        {hospital.top_pdx_diagnoses.slice(0, 5).map((diag, i) => (
                          <div key={i} className="flex justify-between text-xs bg-white p-2 rounded">
                            <span className="text-gray-700 truncate flex-1">{diag.diagnosis}</span>
                            <span className="font-bold text-[#0066a1] ml-2">{diag.count}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {hospital.top_adx_diagnoses && hospital.top_adx_diagnoses.length > 0 && (
                    <div className="bg-orange-50 p-3 rounded-lg">
                      <h4 className="font-semibold text-orange-800 mb-2 text-sm">
                        {language === 'ar' ? 'أكثر تشخيصات ADX due to CDI' : 'Top ADX due to CDI Diagnoses'}
                      </h4>
                      <div className="space-y-1 max-h-48 overflow-y-auto">
                        {hospital.top_adx_diagnoses.slice(0, 5).map((diag, i) => (
                          <div key={i} className="flex justify-between text-xs bg-white p-2 rounded">
                            <span className="text-gray-700 truncate flex-1">{diag.diagnosis}</span>
                            <span className="font-bold text-orange-600 ml-2">{diag.count}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderTopDiagnoses = () => {
    if (!analysis || !analysis.top_diagnoses) return null;

    return (
      <div className="grid md:grid-cols-3 gap-6 mb-8">
        {analysis.top_diagnoses.pdx_after_cdi && analysis.top_diagnoses.pdx_after_cdi.length > 0 && (
          <Card className="medical-card">
            <CardHeader>
              <CardTitle className="text-xl text-gray-800">
                {language === 'ar' ? 'أكثر التشخيصات PDX/After CDI' : 'Top PDX/After CDI Diagnoses'}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {analysis.top_diagnoses.pdx_after_cdi.map((diag, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-blue-50 rounded-lg hover:bg-blue-100 transition">
                    <div className="flex-1">
                      <div className="font-medium text-gray-800 text-sm">{diag.diagnosis}</div>
                      <div className="text-xs text-gray-600">{diag.percentage}%</div>
                    </div>
                    <div className="text-xl font-bold text-[#0066a1]">{diag.count}</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {analysis.top_diagnoses.pdx_due_to_cdi && analysis.top_diagnoses.pdx_due_to_cdi.length > 0 && (
          <Card className="medical-card">
            <CardHeader>
              <CardTitle className="text-xl text-gray-800">
                {language === 'ar' ? 'أكثر التشخيصات PDX due to CDI' : 'Top PDX due to CDI Diagnoses'}
              </CardTitle>
              <CardDescription className="text-xs">
                {language === 'ar' ? '(التشخيصات الرئيسية المضافة فقط)' : '(Newly added primary diagnoses only)'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {analysis.top_diagnoses.pdx_due_to_cdi.map((diag, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-blue-50 rounded-lg hover:bg-blue-100 transition">
                    <div className="flex-1">
                      <div className="font-medium text-gray-800 text-sm">{diag.diagnosis}</div>
                      <div className="text-xs text-gray-600">{diag.percentage}%</div>
                    </div>
                    <div className="text-xl font-bold text-[#0066a1]">{diag.count}</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {analysis.top_diagnoses.adx_due_to_cdi && analysis.top_diagnoses.adx_due_to_cdi.length > 0 && (
          <Card className="medical-card">
            <CardHeader>
              <CardTitle className="text-xl text-gray-800">
                {language === 'ar' ? 'أكثر التشخيصات ADX due to CDI' : 'Top ADX due to CDI Diagnoses'}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {analysis.top_diagnoses.adx_due_to_cdi.map((diag, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-orange-50 rounded-lg hover:bg-orange-100 transition">
                    <div className="flex-1">
                      <div className="font-medium text-gray-800 text-sm">{diag.diagnosis}</div>
                      <div className="text-xs text-gray-600">{diag.percentage}%</div>
                    </div>
                    <div className="text-xl font-bold text-orange-600">{diag.count}</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    );
  };

  const renderSpecialtyAnalysis = () => {
    if (!analysis || !analysis.specialty_analysis || analysis.specialty_analysis.length === 0) return null;

    return (
      <Card className="medical-card mb-8">
        <CardHeader>
          <CardTitle className="text-2xl text-gray-800">
            {language === 'ar' ? 'تحليل التخصصات' : 'Specialty Analysis'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-center">{language === 'ar' ? 'التخصص' : 'Specialty'}</TableHead>
                  <TableHead className="text-center">{language === 'ar' ? 'الحالات' : 'Cases'}</TableHead>
                  <TableHead className="text-center">{language === 'ar' ? 'DRG' : 'DRG'}</TableHead>
                  <TableHead className="text-center">{language === 'ar' ? 'PDX' : 'PDX'}</TableHead>
                  <TableHead className="text-center">{language === 'ar' ? 'ADX' : 'ADX'}</TableHead>
                  <TableHead className="text-center">{language === 'ar' ? 'معدل التأثير' : 'Impact Rate'}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {analysis.specialty_analysis.map((spec, index) => (
                  <TableRow key={index} className={index % 2 === 0 ? 'bg-gray-50' : ''}>
                    <TableCell className="text-center font-medium">{spec.specialty}</TableCell>
                    <TableCell className="text-center">{spec.total_cases}</TableCell>
                    <TableCell className="text-center">
                      <span className="font-bold text-[#0066a1]">{spec.drg_changes}</span>
                    </TableCell>
                    <TableCell className="text-center">
                      <span className="font-bold text-[#0066a1]">{spec.pdx_changes}</span>
                    </TableCell>
                    <TableCell className="text-center">
                      <span className="font-bold text-orange-600">{spec.adx_added}</span>
                    </TableCell>
                    <TableCell className="text-center">
                      <span className="font-bold text-[#0066a1]">{spec.impact_rate}%</span>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderCDSPerformance = () => {
    if (!analysis || !analysis.cds_performance || analysis.cds_performance.length === 0) return null;

    const hasStatusData = analysis.data_flags?.has_status_data;

    return (
      <Card className="medical-card mb-8">
        <CardHeader>
          <CardTitle className="text-2xl text-gray-800">
            {language === 'ar' ? 'أداء أخصائيي التوثيق السريري (CDS)' : 'CDS Specialists Performance'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-center">{language === 'ar' ? 'الاسم' : 'Name'}</TableHead>
                  <TableHead className="text-center">{language === 'ar' ? 'الحالات' : 'Cases'}</TableHead>
                  <TableHead className="text-center">{language === 'ar' ? 'تأثير DRG' : 'DRG Impact'}</TableHead>
                  <TableHead className="text-center">{language === 'ar' ? 'PDX' : 'PDX'}</TableHead>
                  <TableHead className="text-center">{language === 'ar' ? 'ADX' : 'ADX'}</TableHead>
                  <TableHead className="text-center">{language === 'ar' ? 'مجموع الاستفسارات' : 'Total Queries'}</TableHead>
                  {hasStatusData && (
                    <>
                      <TableHead className="text-center">{language === 'ar' ? 'تم ✅' : 'Done ✅'}</TableHead>
                      <TableHead className="text-center">{language === 'ar' ? 'للبدء 🔵' : 'To Start 🔵'}</TableHead>
                      <TableHead className="text-center">{language === 'ar' ? 'جاري 🔄' : 'Working 🔄'}</TableHead>
                      <TableHead className="text-center">{language === 'ar' ? 'فارغ ⚪' : 'Empty ⚪'}</TableHead>
                    </>
                  )}
                  <TableHead className="text-center">{language === 'ar' ? 'النجاح %' : 'Success %'}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {analysis.cds_performance.map((cds, index) => (
                  <TableRow key={index} className={index % 2 === 0 ? 'bg-gray-50' : ''}>
                    <TableCell className="text-center font-medium">
                      {cds.cds_name}
                      {cds.validation_passed === false && (
                        <span className="ml-2 text-xs text-red-600" title="تحذير: عدم تطابق في العد">⚠️</span>
                      )}
                    </TableCell>
                    <TableCell className="text-center">
                      <span className="font-bold text-gray-800">{cds.total_cases}</span>
                      {hasStatusData && cds.status_total && (
                        <div className="text-xs text-gray-500">({cds.status_total})</div>
                      )}
                    </TableCell>
                    <TableCell className="text-center">
                      <span className="font-bold text-[#0066a1]">{cds.drg_impact}</span>
                    </TableCell>
                    <TableCell className="text-center">
                      <span className="font-bold text-[#0066a1]">{cds.pdx_queries}</span>
                    </TableCell>
                    <TableCell className="text-center">
                      <span className="font-bold text-orange-600">{cds.adx_queries}</span>
                    </TableCell>
                    <TableCell className="text-center">
                      <span className="inline-block bg-cyan-600 text-white px-3 py-1.5 rounded-full text-sm font-bold">
                        {cds.total_queries || 0}
                      </span>
                    </TableCell>
                    {hasStatusData && (
                      <>
                        <TableCell className="text-center">
                          <span className="inline-block bg-green-600 text-white px-2 py-1 rounded-full text-xs font-bold">
                            {cds.status_done || 0}
                          </span>
                        </TableCell>
                        <TableCell className="text-center">
                          <span className="inline-block bg-[#0066a1] text-white px-2 py-1 rounded-full text-xs font-bold">
                            {cds.status_to_start || 0}
                          </span>
                        </TableCell>
                        <TableCell className="text-center">
                          <span className="inline-block bg-yellow-600 text-white px-2 py-1 rounded-full text-xs font-bold">
                            {cds.status_working || 0}
                          </span>
                        </TableCell>
                        <TableCell className="text-center">
                          <span className="inline-block bg-gray-400 text-white px-2 py-1 rounded-full text-xs font-bold">
                            {cds.status_empty || 0}
                          </span>
                        </TableCell>
                      </>
                    )}
                    <TableCell className="text-center">
                      <span className="font-bold text-[#0066a1]">{cds.success_rate}%</span>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {/* CDS Status Chart if available */}
          {hasStatusData && analysis.cds_performance.length > 0 && (
            <div className="mt-8">
              <h3 className="text-xl font-bold text-gray-800 mb-4 text-center">
                {language === 'ar' ? 'توزيع حالة الملفات لكل أخصائي' : 'File Status Distribution per Specialist'}
              </h3>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {analysis.cds_performance.slice(0, 6).map((cds, index) => {
                  const statusData = [
                    { name: language === 'ar' ? 'تم' : 'Done', value: cds.status_done || 0, color: '#16a34a' },
                    { name: language === 'ar' ? 'للبدء' : 'To Start', value: cds.status_to_start || 0, color: '#2563eb' },
                    { name: language === 'ar' ? 'جاري' : 'Working', value: cds.status_working || 0, color: '#ca8a04' },
                    { name: language === 'ar' ? 'فارغ' : 'Empty', value: cds.status_empty || 0, color: '#9ca3af' }
                  ];

                  return (
                    <Card key={index} className="bg-gradient-to-br from-gray-50 to-blue-50">
                      <CardHeader>
                        <CardTitle className="text-sm font-medium text-center">{cds.cds_name}</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <ResponsiveContainer width="100%" height={200}>
                          <RePieChart>
                            <Pie
                              data={statusData}
                              cx="50%"
                              cy="50%"
                              labelLine={false}
                              label={(entry) => entry.value > 0 ? `${entry.value}` : ''}
                              outerRadius={70}
                              dataKey="value"
                            >
                              {statusData.map((entry, idx) => (
                                <Cell key={`cell-${idx}`} fill={entry.color} />
                              ))}
                            </Pie>
                            <Tooltip />
                          </RePieChart>
                        </ResponsiveContainer>
                        <div className="grid grid-cols-2 gap-2 mt-2 text-xs">
                          <div className="flex items-center gap-1">
                            <div className="w-3 h-3 bg-green-600 rounded"></div>
                            <span>{language === 'ar' ? 'تم' : 'Done'}: {cds.status_done || 0}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <div className="w-3 h-3 bg-[#0066a1] rounded"></div>
                            <span>{language === 'ar' ? 'للبدء' : 'Start'}: {cds.status_to_start || 0}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <div className="w-3 h-3 bg-yellow-600 rounded"></div>
                            <span>{language === 'ar' ? 'جاري' : 'Work'}: {cds.status_working || 0}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <div className="w-3 h-3 bg-gray-400 rounded"></div>
                            <span>{language === 'ar' ? 'فارغ' : 'Empty'}: {cds.status_empty || 0}</span>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </div>
          )}

          {/* Data Accuracy Notice */}
          <div className="mt-6 p-4 bg-green-50 border-l-4 border-green-500 rounded">
            <div className="flex items-start gap-3">
              <div className="text-green-600 text-2xl">✅</div>
              <div>
                <h4 className="font-bold text-green-800 mb-1">
                  {language === 'ar' ? 'ضمان دقة البيانات' : 'Data Accuracy Guarantee'}
                </h4>
                <p className="text-sm text-green-700">
                  {language === 'ar' 
                    ? 'تم حساب جميع الإحصائيات بدقة 100% مع التحقق التلقائي. إجمالي الحالات = Done + To Start + Working + Empty. أي تحذير (⚠️) يعني وجود خلل في بيانات الملف المصدر.'
                    : 'All statistics calculated with 100% precision and automatic validation. Total cases = Done + To Start + Working + Empty. Any warning (⚠️) indicates an issue in the source file data.'}
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderCharts = () => {
    if (!analysis || !analysis.hospitals_analysis) return null;

    const hospitalsData = analysis.hospitals_analysis.slice(0, 10).map(h => ({
      name: h.hospital_name.length > 20 ? h.hospital_name.substring(0, 17) + '...' : h.hospital_name,
      DRG: h.drg_changes,
      PDX: h.pdx_changes + h.pdx_added,
      ADX: h.adx_added
    }));

    const drgPieData = [
      { name: language === 'ar' ? 'تغييرات DRG' : 'DRG Changes', value: analysis.drg_metrics.total_changes },
      { name: language === 'ar' ? 'بدون تغيير' : 'No Change', value: analysis.drg_metrics.no_change }
    ];

    return (
      <div className="grid md:grid-cols-2 gap-6 mb-8">
        <Card className="medical-card">
          <CardHeader>
            <CardTitle className="text-xl text-gray-800 flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-[#0066a1]" />
              {language === 'ar' ? 'مقارنة المستشفيات (Top 10)' : 'Hospitals Comparison (Top 10)'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={hospitalsData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} fontSize={10} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="DRG" fill="#8b5cf6" name="DRG Changes" />
                <Bar dataKey="PDX" fill="#3b82f6" name="PDX" />
                <Bar dataKey="ADX" fill="#f97316" name="ADX" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card className="medical-card">
          <CardHeader>
            <CardTitle className="text-xl text-gray-800 flex items-center gap-2">
              <PieChart className="h-5 w-5 text-[#0066a1]" />
              {language === 'ar' ? 'توزيع تأثير DRG' : 'DRG Impact Distribution'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <RePieChart>
                <Pie
                  data={drgPieData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry) => `${entry.name}: ${entry.value}`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {drgPieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </RePieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    );
  };

  const renderRecommendations = () => {
    if (!analysis) return null;

    const recommendations = [];
    const drgRate = analysis.drg_metrics?.change_rate || 0;
    const pdxRate = analysis.pdx_metrics?.change_rate || 0;
    const hospitals = analysis.hospitals_analysis || [];
    
    if (drgRate < 20) {
      recommendations.push({
        category: '⚠️ معدل تأثير DRG منخفض',
        recommendation: `معدل تغيير DRG الحالي ${drgRate}% أقل من المتوقع. يُنصح بتكثيف جهود CDI والتركيز على المراجعة الدقيقة للملفات قبل الترميز النهائي.`
      });
    } else if (drgRate > 60) {
      recommendations.push({
        category: '✅ معدل تأثير DRG ممتاز',
        recommendation: `معدل تغيير DRG الحالي ${drgRate}% يعتبر ممتازاً. استمروا في تطبيق نفس المعايير والممارسات الحالية.`
      });
    }

    if (pdxRate > 30) {
      recommendations.push({
        category: '📋 تحسين التوثيق الرئيسي مطلوب',
        recommendation: `نسبة ${pdxRate}% من التشخيصات الرئيسية تم تعديلها. يجب تدريب الأطباء على توثيق التشخيص الرئيسي بدقة منذ البداية.`
      });
    }

    if (hospitals.length > 0) {
      const lowPerformers = hospitals.filter(h => (h.drg_impact_rate || 0) < 20);
      if (lowPerformers.length > 0) {
        const names = lowPerformers.slice(0, 3).map(h => h.hospital_name).join(', ');
        recommendations.push({
          category: '🏥 مستشفيات تحتاج تحسين',
          recommendation: `المستشفيات التالية تحتاج إلى تحسين في التوثيق: ${names}. يُنصح بعقد ورش عمل تدريبية وزيادة التواصل مع فريق التوثيق.`
        });
      }

      const sorted = [...hospitals].sort((a, b) => 
        ((b.pdx_added || 0) + (b.adx_added || 0)) - ((a.pdx_added || 0) + (a.adx_added || 0))
      );
      if (sorted.length > 0 && ((sorted[0].pdx_added || 0) + (sorted[0].adx_added || 0)) > 50) {
        recommendations.push({
          category: '📝 نقص في التوثيق',
          recommendation: `المستشفى ${sorted[0].hospital_name} يحتاج إلى تحسين كبير في توثيق التشخيصات. تم إضافة ${sorted[0].pdx_added || 0} تشخيص رئيسي و ${sorted[0].adx_added || 0} تشخيص إضافي بعد مراجعة CDI.`
        });
      }
    }

    const topPdx = analysis.top_diagnoses?.pdx_after_cdi || [];
    if (topPdx.length > 0) {
      const top3 = topPdx.slice(0, 3).map(d => d.diagnosis).join(', ');
      recommendations.push({
        category: '🎯 التشخيصات الأكثر شيوعاً',
        recommendation: `التشخيصات الأكثر شيوعاً بعد CDI: ${top3}. يُنصح بإنشاء بروتوكولات توثيق محددة لهذه الحالات لتقليل الحاجة للتعديل مستقبلاً.`
      });
    }

    recommendations.push({
      category: '💡 أفضل الممارسات',
      recommendation: 'استمروا في المراجعة الدورية للملفات، وتحديث البروتوكولات بناءً على أحدث إرشادات ICD-10، وعقد اجتماعات دورية بين فريق CDI والأطباء.'
    });

    return (
      <Card className="medical-card mb-8 bg-gradient-to-br from-yellow-50 to-orange-50">
        <CardHeader>
          <CardTitle className="text-2xl text-gray-800 flex items-center gap-2">
            <Award className="h-6 w-6 text-orange-600" />
            {language === 'ar' ? 'التوصيات والتوجيهات للتحسين' : 'Recommendations & Improvement Guidelines'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {recommendations.map((rec, index) => (
              <div key={index} className="bg-white p-4 rounded-lg border-l-4 border-orange-500 shadow-sm hover:shadow-md transition">
                <h3 className="font-bold text-gray-800 mb-2">{rec.category}</h3>
                <p className="text-gray-700 text-sm leading-relaxed">{rec.recommendation}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderFinancialImpactDetails = () => {
    if (!analysis || !analysis.drg_financial_impact) return null;

    const fi = analysis.drg_financial_impact;

    return (
      <Card className="medical-card mb-8 bg-gradient-to-br from-green-50 to-emerald-100">
        <CardHeader>
          <CardTitle className="text-2xl text-gray-800 flex items-center gap-2">
            <DollarSign className="h-6 w-6 text-green-600" />
            {language === 'ar' ? 'تفاصيل الأثر المالي لتغييرات DRG' : 'Financial Impact Details of DRG Changes'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/* Summary Row */}
          <div className="grid md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white p-4 rounded-lg text-center border-l-4 border-green-500">
              <div className="text-sm text-green-600 mb-1">{language === 'ar' ? 'إجمالي الأثر المالي' : 'Total Financial Impact'}</div>
              <div className={`text-2xl font-bold ${fi.summary.total_financial_impact_sar >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                {fi.summary.total_impact_formatted}
              </div>
            </div>
            <div className="bg-white p-4 rounded-lg text-center border-l-4 border-blue-500">
              <div className="text-sm text-blue-600 mb-1">{language === 'ar' ? 'عدد الحالات' : 'Number of Cases'}</div>
              <div className="text-2xl font-bold text-blue-700">{fi.summary.total_drg_changes}</div>
            </div>
            <div className="bg-white p-4 rounded-lg text-center border-l-4 border-purple-500">
              <div className="text-sm text-purple-600 mb-1">{language === 'ar' ? 'متوسط الأثر للحالة' : 'Avg Impact per Case'}</div>
              <div className="text-2xl font-bold text-purple-700">{fi.summary.average_impact_per_case?.toLocaleString()} {language === 'ar' ? 'ريال' : 'SAR'}</div>
            </div>
            <div className="bg-white p-4 rounded-lg text-center border-l-4 border-orange-500">
              <div className="text-sm text-orange-600 mb-1">{language === 'ar' ? 'إيجابي / سلبي' : 'Positive / Negative'}</div>
              <div className="text-lg font-bold">
                <span className="text-green-600">{fi.summary.positive_impact_cases || 0}</span>
                {' / '}
                <span className="text-red-600">{fi.summary.negative_impact_cases || 0}</span>
              </div>
            </div>
          </div>

          {/* By Hospital */}
          {fi.by_hospital && fi.by_hospital.length > 0 && (
            <div className="mb-6">
              <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                <Hospital className="h-5 w-5 text-blue-600" />
                {language === 'ar' ? 'الأثر المالي حسب المستشفى' : 'Financial Impact by Hospital'}
              </h3>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="text-center">{language === 'ar' ? 'المستشفى' : 'Hospital'}</TableHead>
                      <TableHead className="text-center">{language === 'ar' ? 'الأثر المالي' : 'Financial Impact'}</TableHead>
                      <TableHead className="text-center">{language === 'ar' ? 'الحالات' : 'Cases'}</TableHead>
                      <TableHead className="text-center">{language === 'ar' ? 'إيجابي' : 'Positive'}</TableHead>
                      <TableHead className="text-center">{language === 'ar' ? 'سلبي' : 'Negative'}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {fi.by_hospital.map((h, index) => (
                      <TableRow key={index} className={index % 2 === 0 ? 'bg-gray-50' : ''}>
                        <TableCell className="font-medium">{h.hospital_name}</TableCell>
                        <TableCell className={`text-center font-bold ${h.total_impact_sar >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {h.impact_formatted}
                        </TableCell>
                        <TableCell className="text-center">{h.cases}</TableCell>
                        <TableCell className="text-center text-green-600">{h.positive_changes}</TableCell>
                        <TableCell className="text-center text-red-600">{h.negative_changes}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </div>
          )}

          {/* By Department */}
          {fi.by_department && fi.by_department.length > 0 && (
            <div className="mb-6">
              <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                <Stethoscope className="h-5 w-5 text-purple-600" />
                {language === 'ar' ? 'الأثر المالي حسب القسم' : 'Financial Impact by Department'}
              </h3>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3">
                {fi.by_department.map((d, index) => (
                  <div key={index} className="bg-white p-3 rounded-lg border hover:shadow-md transition">
                    <div className="font-medium text-gray-800 mb-1">{d.department}</div>
                    <div className={`text-lg font-bold ${d.total_impact_sar >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {d.impact_formatted}
                    </div>
                    <div className="text-xs text-gray-500">{d.cases} {language === 'ar' ? 'حالة' : 'cases'}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* By Specialist */}
          {fi.by_specialist && fi.by_specialist.length > 0 && (
            <div className="mb-6">
              <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                <Users className="h-5 w-5 text-orange-600" />
                {language === 'ar' ? 'الأثر المالي حسب أخصائي CDI' : 'Financial Impact by CDI Specialist'}
              </h3>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="text-center">{language === 'ar' ? 'الأخصائي' : 'Specialist'}</TableHead>
                      <TableHead className="text-center">{language === 'ar' ? 'الأثر المالي' : 'Financial Impact'}</TableHead>
                      <TableHead className="text-center">{language === 'ar' ? 'الحالات' : 'Cases'}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {fi.by_specialist.map((s, index) => (
                      <TableRow key={index} className={index % 2 === 0 ? 'bg-gray-50' : ''}>
                        <TableCell className="font-medium">{s.specialist}</TableCell>
                        <TableCell className={`text-center font-bold ${s.total_impact_sar >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {s.impact_formatted}
                        </TableCell>
                        <TableCell className="text-center">{s.cases}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </div>
          )}

          {/* Sample Changes */}
          {fi.sample_changes && fi.sample_changes.length > 0 && (
            <div>
              <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-cyan-600" />
                {language === 'ar' ? 'عينة من تغييرات DRG' : 'Sample DRG Changes'}
              </h3>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="text-center">{language === 'ar' ? 'المستشفى' : 'Hospital'}</TableHead>
                      <TableHead className="text-center">{language === 'ar' ? 'DRG قبل' : 'Old DRG'}</TableHead>
                      <TableHead className="text-center">{language === 'ar' ? 'DRG بعد' : 'New DRG'}</TableHead>
                      <TableHead className="text-center">{language === 'ar' ? 'الفئة' : 'Category'}</TableHead>
                      <TableHead className="text-center">{language === 'ar' ? 'السعر القديم' : 'Old Price'}</TableHead>
                      <TableHead className="text-center">{language === 'ar' ? 'السعر الجديد' : 'New Price'}</TableHead>
                      <TableHead className="text-center">{language === 'ar' ? 'الفرق' : 'Difference'}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {fi.sample_changes.slice(0, 10).map((c, index) => (
                      <TableRow key={index} className={index % 2 === 0 ? 'bg-gray-50' : ''}>
                        <TableCell className="text-sm">{c.hospital}</TableCell>
                        <TableCell className="text-center font-mono text-sm">{c.old_drg}</TableCell>
                        <TableCell className="text-center font-mono text-sm">{c.new_drg}</TableCell>
                        <TableCell className="text-center">{c.category}</TableCell>
                        <TableCell className="text-center">{c.old_price?.toLocaleString()}</TableCell>
                        <TableCell className="text-center">{c.new_price?.toLocaleString()}</TableCell>
                        <TableCell className={`text-center font-bold ${c.difference >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {c.difference?.toLocaleString()} {language === 'ar' ? 'ريال' : 'SAR'}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

  const renderHospitalDetailedAnalysis = () => {
    if (!analysis || !analysis.hospitals_analysis || analysis.hospitals_analysis.length === 0) return null;

    const hospitalsList = analysis.hospitals_analysis;
    const currentHospital = selectedHospital || hospitalsList[0];

    return (
      <Card className="medical-card mb-8 bg-gradient-to-br from-indigo-50 to-blue-50">
        <CardHeader>
          <CardTitle className="text-2xl text-gray-800 flex items-center gap-2">
            <Hospital className="h-6 w-6 text-[#0066a1]" />
            {language === 'ar' ? 'تحليل تفصيلي لكل مستشفى - التشخيصات والتكرار' : 'Detailed Hospital Analysis - Diagnoses & Frequency'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/* Hospital Selector */}
          <div className="mb-6">
            <Label className="text-lg mb-2 block font-semibold">
              {language === 'ar' ? 'اختر المستشفى:' : 'Select Hospital:'}
            </Label>
            <select
              value={currentHospital?.hospital_name || ''}
              onChange={(e) => {
                const hospital = hospitalsList.find(h => h.hospital_name === e.target.value);
                setSelectedHospital(hospital);
              }}
              className="w-full md:w-1/2 p-3 border border-gray-300 rounded-lg bg-white shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {hospitalsList.map((hospital, index) => (
                <option key={index} value={hospital.hospital_name}>
                  {hospital.hospital_name}
                </option>
              ))}
            </select>
          </div>

          {currentHospital && (
            <div className="space-y-6">
              {/* Hospital Summary - Enhanced with PDX/After and ADX/After */}
              <div className="grid md:grid-cols-3 gap-4 mb-6">
                <div className="bg-blue-100 p-4 rounded-lg text-center">
                  <div className="text-sm text-[#0066a1] mb-1">{language === 'ar' ? 'إجمالي الحالات' : 'Total Cases'}</div>
                  <div className="text-3xl font-bold text-blue-700">{currentHospital.total_cases}</div>
                </div>
                <div className="bg-purple-100 p-4 rounded-lg text-center">
                  <div className="text-sm text-[#0066a1] mb-1">{language === 'ar' ? 'تغييرات DRG' : 'DRG Changes'}</div>
                  <div className="text-3xl font-bold text-purple-700">{currentHospital.drg_changes}</div>
                </div>
                <div className="bg-indigo-100 p-4 rounded-lg text-center">
                  <div className="text-sm text-indigo-600 mb-1">{language === 'ar' ? 'معدل التأثير' : 'Impact Rate'}</div>
                  <div className="text-3xl font-bold text-indigo-700">{currentHospital.drg_impact_rate}%</div>
                </div>
              </div>

              {/* Diagnosis Indicators Grid - 2 Main Indicators */}
              <div className="grid md:grid-cols-2 gap-6 mb-6">
                <div className="bg-purple-100 p-4 rounded-lg text-center border-l-4 border-purple-500">
                  <div className="text-xs text-[#0066a1] mb-1">{language === 'ar' ? 'PDX/After CDI' : 'PDX/After CDI'}</div>
                  <div className="text-2xl font-bold text-purple-700">
                    {currentHospital.top_pdx_diagnoses ? currentHospital.top_pdx_diagnoses.reduce((sum, d) => sum + d.count, 0) : 0}
                  </div>
                  <div className="text-xs text-[#0066a1] mt-1">{language === 'ar' ? 'جميع التشخيصات الرئيسية' : 'All primary diagnoses'}</div>
                </div>
                
                <div className="bg-orange-100 p-4 rounded-lg text-center border-l-4 border-orange-500">
                  <div className="text-xs text-orange-600 mb-1">{language === 'ar' ? 'ADX due to CDI' : 'ADX due to CDI'}</div>
                  <div className="text-2xl font-bold text-orange-700">
                    {currentHospital.top_adx_diagnoses ? currentHospital.top_adx_diagnoses.reduce((sum, d) => sum + d.count, 0) : 0}
                  </div>
                  <div className="text-xs text-orange-600 mt-1">{language === 'ar' ? 'جميع التشخيصات الإضافية' : 'All additional diagnoses'}</div>
                </div>
              </div>

              {/* PDX/After CDI Diagnoses Chart & Table */}
              {currentHospital.top_pdx_diagnoses && currentHospital.top_pdx_diagnoses.length > 0 && (
                <div className="grid md:grid-cols-2 gap-6 mt-6">
                  {/* PDX/After CDI Chart */}
                  <Card className="bg-purple-50">
                    <CardHeader>
                      <CardTitle className="text-lg text-gray-800">
                        {language === 'ar' ? '📊 رسم بياني - تشخيصات PDX/After CDI' : '📊 Chart - PDX/After CDI Diagnoses'}
                      </CardTitle>
                      <CardDescription className="text-xs">
                        {language === 'ar' ? '(جميع التشخيصات الرئيسية بعد CDI)' : '(All primary diagnoses after CDI)'}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={currentHospital.top_pdx_diagnoses.slice(0, 10)}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis 
                            dataKey="diagnosis" 
                            angle={-45} 
                            textAnchor="end" 
                            height={120} 
                            fontSize={9}
                            interval={0}
                          />
                          <YAxis />
                          <Tooltip />
                          <Bar dataKey="count" fill="#a855f7" name={language === 'ar' ? 'التكرار' : 'Count'} />
                        </BarChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>

                  {/* PDX/After CDI Table */}
                  <Card className="bg-purple-50">
                    <CardHeader>
                      <CardTitle className="text-lg text-gray-800">
                        {language === 'ar' ? '📋 جدول - تشخيصات PDX/After CDI' : '📋 Table - PDX/After CDI Diagnoses'}
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="max-h-96 overflow-y-auto">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead className="text-center">{language === 'ar' ? 'التشخيص' : 'Diagnosis'}</TableHead>
                              <TableHead className="text-center">{language === 'ar' ? 'العدد' : 'Count'}</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {currentHospital.top_pdx_diagnoses.map((diag, index) => (
                              <TableRow key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-purple-100/30'}>
                                <TableCell className="text-sm">{diag.diagnosis}</TableCell>
                                <TableCell className="text-center">
                                  <span className="inline-block bg-purple-600 text-white px-3 py-1 rounded-full font-bold">
                                    {diag.count}
                                  </span>
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              )}

              {/* ADX due to CDI Diagnoses Chart & Table */}
              {currentHospital.top_adx_diagnoses && currentHospital.top_adx_diagnoses.length > 0 && (
                <div className="grid md:grid-cols-2 gap-6 mt-6">
                  {/* ADX due to CDI Chart */}
                  <Card className="bg-orange-50">
                    <CardHeader>
                      <CardTitle className="text-lg text-gray-800">
                        {language === 'ar' ? '📊 رسم بياني - تشخيصات ADX due to CDI' : '📊 Chart - ADX due to CDI Diagnoses'}
                      </CardTitle>
                      <CardDescription className="text-xs">
                        {language === 'ar' ? '(التشخيصات الإضافية المضافة بسبب CDI)' : '(Secondary diagnoses added due to CDI)'}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={currentHospital.top_adx_diagnoses.slice(0, 10)}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis 
                            dataKey="diagnosis" 
                            angle={-45} 
                            textAnchor="end" 
                            height={120} 
                            fontSize={9}
                            interval={0}
                          />
                          <YAxis />
                          <Tooltip />
                          <Bar dataKey="count" fill="#f97316" name={language === 'ar' ? 'التكرار' : 'Count'} />
                        </BarChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>

                  {/* ADX due to CDI Table */}
                  <Card className="bg-orange-50">
                    <CardHeader>
                      <CardTitle className="text-lg text-gray-800">
                        {language === 'ar' ? '📋 جدول - تشخيصات ADX due to CDI' : '📋 Table - ADX due to CDI Diagnoses'}
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="max-h-96 overflow-y-auto">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead className="text-center">{language === 'ar' ? 'التشخيص' : 'Diagnosis'}</TableHead>
                              <TableHead className="text-center">{language === 'ar' ? 'العدد' : 'Count'}</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {currentHospital.top_adx_diagnoses.map((diag, index) => (
                              <TableRow key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-orange-100/30'}>
                                <TableCell className="text-sm">{diag.diagnosis}</TableCell>
                                <TableCell className="text-center">
                                  <span className="inline-block bg-orange-600 text-white px-3 py-1 rounded-full font-bold">
                                    {diag.count}
                                  </span>
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              )}

              {/* No Data Message */}
              {(!currentHospital.top_pdx_diagnoses || currentHospital.top_pdx_diagnoses.length === 0) && 
               (!currentHospital.top_adx_diagnoses || currentHospital.top_adx_diagnoses.length === 0) && (
                <div className="text-center py-8 text-gray-500">
                  <AlertTriangle className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                  <p>{language === 'ar' ? 'لا توجد بيانات تشخيص متاحة لهذا المستشفى' : 'No diagnosis data available for this hospital'}</p>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#f0f9ff] via-[#e0f2fe] to-[#f0fdfa]">
      <Navbar user={user} onLogout={onLogout} />
      <main className="container mx-auto px-4 py-8">
        <div className="mb-8 animate-fade-in">
          <h1 className="text-4xl font-bold gradient-text mb-2">
            {language === 'ar' ? 'لوحة تحكم المشرف' : 'Supervisor Dashboard'}
          </h1>
          <p className="text-gray-600 text-lg">
            {language === 'ar' ? 'أداة تحليل CDI الاحترافية والمتابعة الشاملة' : 'Professional CDI Analysis & Comprehensive Monitoring Tool'}
          </p>
        </div>

        {/* Employees Section - Moved to top */}
        <Card className="professional-card mb-8 animate-slide-in">
          <CardHeader>
            <CardTitle className="text-2xl text-gray-800 flex items-center gap-2">
              <Users className="h-6 w-6" />
              {language === 'ar' ? 'الموظفون - الاطلاع على الحسابات' : 'Employees - View Accounts'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {employees.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Users className="h-16 w-16 mx-auto mb-4 text-gray-300" />
                <p className="text-lg">{language === 'ar' ? 'لا يوجد موظفون حالياً' : 'No employees found'}</p>
                <p className="text-sm mt-2">{language === 'ar' ? 'سيظهر الموظفون هنا عند إضافتهم' : 'Employees will appear here when added'}</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="text-center">{language === 'ar' ? 'الاسم' : 'Name'}</TableHead>
                      <TableHead className="text-center">{language === 'ar' ? 'البريد' : 'Email'}</TableHead>
                      <TableHead className="text-center">{language === 'ar' ? 'الجوال' : 'Phone'}</TableHead>
                      <TableHead className="text-center">{language === 'ar' ? 'الملاحظات' : 'Notes'}</TableHead>
                      <TableHead className="text-center">{language === 'ar' ? 'التحليلات' : 'Analyses'}</TableHead>
                      <TableHead className="text-center">{language === 'ar' ? 'الإجراءات' : 'Actions'}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {employees.map((emp, index) => (
                      <TableRow key={emp.id} className={index % 2 === 0 ? 'bg-gray-50' : ''}>
                        <TableCell className="text-center font-medium">{emp.full_name}</TableCell>
                        <TableCell className="text-center text-sm">{emp.email}</TableCell>
                        <TableCell className="text-center text-sm">{emp.phone_number || '-'}</TableCell>
                        <TableCell className="text-center">
                          <span className="font-bold text-[#0066a1]">{emp.notes_count || 0}</span>
                        </TableCell>
                        <TableCell className="text-center">
                          <span className="font-bold text-[#0066a1]">{emp.analyses_count || 0}</span>
                        </TableCell>
                        <TableCell className="text-center">
                          <div className="flex items-center justify-center gap-2">
                            <Button
                              size="sm"
                              variant="outline"
                              className="text-orange-600 hover:bg-orange-50 border-orange-300"
                              onClick={() => setChangePasswordUser(emp)}
                              title={language === 'ar' ? 'تغيير كلمة المرور' : 'Change Password'}
                            >
                              <Lock className="h-4 w-4" />
                            </Button>
                            
                            <Button
                              size="sm"
                              className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white shadow-md hover:shadow-lg transition-all duration-300"
                              onClick={() => handleImpersonateEmployee(emp.id, emp.full_name)}
                              title={language === 'ar' ? 'الدخول للحساب' : 'View Account'}
                            >
                              <Eye className="h-4 w-4 mr-1" />
                              {language === 'ar' ? 'عرض' : 'View'}
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Upload Section */}
        <Card className="medical-card mb-8">
          <CardHeader>
            <CardTitle className="text-2xl text-gray-800">
              {language === 'ar' ? 'رفع ملف التحليل الشهري' : 'Upload Monthly Analysis File'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <Label className="text-lg mb-2 block">
                  {language === 'ar' 
                    ? 'قم برفع ملف Excel يحتوي على: Hospital Name, PDX/After CDI, ADX due to CDI, DRG Change, Specialty' 
                    : 'Upload Excel file containing: Hospital Name, PDX/After CDI, ADX due to CDI, DRG Change, Specialty'}
                </Label>
                <Input
                  type="file"
                  accept=".xlsx,.xls"
                  onChange={handleFileUpload}
                  disabled={uploading}
                  className="cursor-pointer"
                />
              </div>
              {uploading && (
                <div className="flex items-center gap-2 text-[#0066a1]">
                  <Activity className="animate-spin" />
                  <span>{language === 'ar' ? 'جاري التحليل...' : 'Analyzing...'}</span>
                </div>
              )}
              {analysis && (
                <div className="flex gap-3 mt-4">
                  <Button 
                    onClick={handleDownloadExcel}
                    className="medical-blue flex items-center gap-2"
                  >
                    <FileSpreadsheet className="h-4 w-4" />
                    {language === 'ar' ? 'تحميل تقرير Excel شامل' : 'Download Comprehensive Excel Report'}
                  </Button>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Analysis Results */}
        {analysis && (
          <>
            {renderSummaryCards()}
            {renderCharts()}
            {renderRecommendations()}
            {renderHospitalDetailedAnalysis()}
            {renderHospitalsAnalysis()}
            {renderTopDiagnoses()}
            {renderSpecialtyAnalysis()}
            {renderCDSPerformance()}
          </>
        )}
      </main>
      
      {/* Change Password Dialog */}
      {changePasswordUser && (
        <Dialog open={!!changePasswordUser} onOpenChange={() => setChangePasswordUser(null)}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>
                {language === 'ar' ? 'تغيير كلمة المرور' : 'Change Password'}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div>
                <Label className="text-sm font-medium text-gray-700">
                  {language === 'ar' ? 'المستخدم:' : 'User:'} <span className="font-bold">{changePasswordUser.full_name}</span>
                </Label>
              </div>
              <div>
                <Label htmlFor="new-password">{language === 'ar' ? 'كلمة المرور الجديدة' : 'New Password'}</Label>
                <Input
                  id="new-password"
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder={language === 'ar' ? 'أدخل كلمة المرور الجديدة (6 أحرف على الأقل)' : 'Enter new password (min 6 characters)'}
                  className="mt-2"
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => {
                  setChangePasswordUser(null);
                  setNewPassword('');
                }}
              >
                {language === 'ar' ? 'إلغاء' : 'Cancel'}
              </Button>
              <Button
                onClick={handleChangePassword}
                className="bg-[#0066a1] hover:bg-[#005588]"
              >
                {language === 'ar' ? 'تغيير كلمة المرور' : 'Change Password'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
      
      <Footer />
    </div>
  );
};

export default SupervisorDashboard;
