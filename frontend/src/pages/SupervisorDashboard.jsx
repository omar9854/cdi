import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';
import { 
  Upload, FileSpreadsheet, TrendingUp, AlertTriangle, Activity, Hospital, 
  Users, Award, BarChart3, Stethoscope, Download, PieChart, Eye 
} from 'lucide-react';
import {
  BarChart, Bar, PieChart as RePieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import Navbar from '@/components/Navbar';
import { useLanguage } from '@/contexts/LanguageContext';
import Footer from '@/components/Footer';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
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

      // Store original supervisor token
      localStorage.setItem('supervisor_token_backup', token);
      localStorage.setItem('is_impersonating', 'true');
      
      // Set the impersonated user's token
      localStorage.setItem('token', response.data.access_token);
      
      toast.success(language === 'ar' ? `تم الدخول إلى حساب ${employeeName}` : `Now viewing ${employeeName}'s account`);
      
      // Reload to dashboard
      window.location.href = '/dashboard';
    } catch (error) {
      toast.error(language === 'ar' ? 'فشل الدخول للحساب' : 'Failed to impersonate user');
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
            <FileSpreadsheet className="h-5 w-5 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-700">{analysis.summary.total_records}</div>
            <p className="text-xs text-blue-600 mt-1">
              {analysis.summary.total_hospitals} {language === 'ar' ? 'مستشفى' : 'hospitals'}
            </p>
          </CardContent>
        </Card>

        <Card className="medical-card bg-gradient-to-br from-purple-50 to-purple-100">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              {language === 'ar' ? 'تغييرات DRG' : 'DRG Changes'}
            </CardTitle>
            <TrendingUp className="h-5 w-5 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-purple-700">{analysis.drg_metrics.total_changes}</div>
            <p className="text-xs text-purple-600 mt-1">
              {analysis.drg_metrics.change_rate}% {language === 'ar' ? 'معدل التغيير' : 'change rate'}
            </p>
          </CardContent>
        </Card>

        <Card className="medical-card bg-gradient-to-br from-blue-50 to-indigo-100">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              {language === 'ar' ? 'PDX/After CDI' : 'PDX/After CDI'}
            </CardTitle>
            <Stethoscope className="h-5 w-5 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-600">{analysis.pdx_metrics.total_after_cdi}</div>
            <p className="text-xs text-blue-600 mt-1">
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
                    <Hospital className="h-5 w-5 text-blue-600" />
                    {hospital.hospital_name}
                  </h3>
                  <div className="text-sm text-gray-600">
                    {hospital.total_cases} {language === 'ar' ? 'حالة' : 'cases'}
                  </div>
                </div>

                <div className="grid md:grid-cols-4 gap-4 mb-4">
                  <div className="bg-purple-50 p-3 rounded-lg">
                    <div className="text-xs text-purple-600 mb-1">{language === 'ar' ? 'تغييرات DRG' : 'DRG Changes'}</div>
                    <div className="text-2xl font-bold text-purple-700">{hospital.drg_changes}</div>
                    <div className="text-xs text-purple-600">{hospital.drg_impact_rate}%</div>
                  </div>
                  
                  <div className="bg-blue-50 p-3 rounded-lg">
                    <div className="text-xs text-blue-600 mb-1">{language === 'ar' ? 'PDX المتغيرة' : 'PDX Changes'}</div>
                    <div className="text-2xl font-bold text-blue-700">{hospital.pdx_changes}</div>
                  </div>
                  
                  <div className="bg-green-50 p-3 rounded-lg">
                    <div className="text-xs text-blue-600 mb-1">{language === 'ar' ? 'PDX المضافة' : 'PDX Added'}</div>
                    <div className="text-2xl font-bold text-green-700">{hospital.pdx_added}</div>
                  </div>
                  
                  <div className="bg-orange-50 p-3 rounded-lg">
                    <div className="text-xs text-orange-600 mb-1">{language === 'ar' ? 'ADX المضافة' : 'ADX Added'}</div>
                    <div className="text-2xl font-bold text-orange-700">{hospital.adx_added}</div>
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
                            <span className="font-bold text-blue-600 ml-2">{diag.count}</span>
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
                    <div className="text-xl font-bold text-blue-600">{diag.count}</div>
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
                    <div className="text-xl font-bold text-blue-600">{diag.count}</div>
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
                      <span className="font-bold text-purple-600">{spec.drg_changes}</span>
                    </TableCell>
                    <TableCell className="text-center">
                      <span className="font-bold text-blue-600">{spec.pdx_changes}</span>
                    </TableCell>
                    <TableCell className="text-center">
                      <span className="font-bold text-orange-600">{spec.adx_added}</span>
                    </TableCell>
                    <TableCell className="text-center">
                      <span className="font-bold text-blue-600">{spec.impact_rate}%</span>
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
                      <span className="font-bold text-purple-600">{cds.drg_impact}</span>
                    </TableCell>
                    <TableCell className="text-center">
                      <span className="font-bold text-blue-600">{cds.pdx_queries}</span>
                    </TableCell>
                    <TableCell className="text-center">
                      <span className="font-bold text-orange-600">{cds.adx_queries}</span>
                    </TableCell>
                    {hasStatusData && (
                      <>
                        <TableCell className="text-center">
                          <span className="inline-block bg-green-600 text-white px-2 py-1 rounded-full text-xs font-bold">
                            {cds.status_done || 0}
                          </span>
                        </TableCell>
                        <TableCell className="text-center">
                          <span className="inline-block bg-blue-600 text-white px-2 py-1 rounded-full text-xs font-bold">
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
                      <span className="font-bold text-green-600">{cds.success_rate}%</span>
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
                            <div className="w-3 h-3 bg-blue-600 rounded"></div>
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
              <BarChart3 className="h-5 w-5 text-blue-600" />
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
              <PieChart className="h-5 w-5 text-purple-600" />
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

  const renderHospitalDetailedAnalysis = () => {
    if (!analysis || !analysis.hospitals_analysis || analysis.hospitals_analysis.length === 0) return null;

    const hospitalsList = analysis.hospitals_analysis;
    const currentHospital = selectedHospital || hospitalsList[0];

    return (
      <Card className="medical-card mb-8 bg-gradient-to-br from-indigo-50 to-blue-50">
        <CardHeader>
          <CardTitle className="text-2xl text-gray-800 flex items-center gap-2">
            <Hospital className="h-6 w-6 text-blue-600" />
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
              {/* Hospital Summary */}
              <div className="grid md:grid-cols-4 gap-4 mb-6">
                <div className="bg-blue-100 p-4 rounded-lg text-center">
                  <div className="text-sm text-blue-600 mb-1">{language === 'ar' ? 'إجمالي الحالات' : 'Total Cases'}</div>
                  <div className="text-3xl font-bold text-blue-700">{currentHospital.total_cases}</div>
                </div>
                <div className="bg-purple-100 p-4 rounded-lg text-center">
                  <div className="text-sm text-purple-600 mb-1">{language === 'ar' ? 'تغييرات DRG' : 'DRG Changes'}</div>
                  <div className="text-3xl font-bold text-purple-700">{currentHospital.drg_changes}</div>
                </div>
                <div className="bg-green-100 p-4 rounded-lg text-center">
                  <div className="text-sm text-green-600 mb-1">{language === 'ar' ? 'PDX المضافة' : 'PDX Added'}</div>
                  <div className="text-3xl font-bold text-green-700">{currentHospital.pdx_added}</div>
                </div>
                <div className="bg-orange-100 p-4 rounded-lg text-center">
                  <div className="text-sm text-orange-600 mb-1">{language === 'ar' ? 'ADX المضافة' : 'ADX Added'}</div>
                  <div className="text-3xl font-bold text-orange-700">{currentHospital.adx_added}</div>
                </div>
              </div>

              {/* PDX Diagnoses Chart & Table */}
              {currentHospital.top_pdx_diagnoses && currentHospital.top_pdx_diagnoses.length > 0 && (
                <div className="grid md:grid-cols-2 gap-6">
                  {/* PDX Chart */}
                  <Card className="bg-blue-50">
                    <CardHeader>
                      <CardTitle className="text-lg text-gray-800">
                        {language === 'ar' ? '📊 رسم بياني - تشخيصات PDX/After CDI' : '📊 Chart - PDX/After CDI Diagnoses'}
                      </CardTitle>
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
                          <Bar dataKey="count" fill="#3b82f6" name={language === 'ar' ? 'التكرار' : 'Count'} />
                        </BarChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>

                  {/* PDX Table */}
                  <Card className="bg-blue-50">
                    <CardHeader>
                      <CardTitle className="text-lg text-gray-800">
                        {language === 'ar' ? '📋 جدول - تشخيصات PDX/After CDI' : '📋 Table - PDX/After CDI Diagnoses'}
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="max-h-80 overflow-y-auto">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead className="text-center">#</TableHead>
                              <TableHead>{language === 'ar' ? 'التشخيص' : 'Diagnosis'}</TableHead>
                              <TableHead className="text-center">{language === 'ar' ? 'التكرار' : 'Count'}</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {currentHospital.top_pdx_diagnoses.map((diag, index) => (
                              <TableRow key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-blue-100'}>
                                <TableCell className="text-center font-bold text-blue-600">{index + 1}</TableCell>
                                <TableCell className="text-sm">{diag.diagnosis}</TableCell>
                                <TableCell className="text-center">
                                  <span className="inline-block bg-blue-600 text-white px-3 py-1 rounded-full font-bold">
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

              {/* PDX due to CDI Diagnoses Chart & Table */}
              {currentHospital.top_pdx_due_to_cdi_diagnoses && currentHospital.top_pdx_due_to_cdi_diagnoses.length > 0 && (
                <div className="grid md:grid-cols-2 gap-6 mt-6">
                  {/* PDX due to CDI Chart */}
                  <Card className="bg-green-50">
                    <CardHeader>
                      <CardTitle className="text-lg text-gray-800">
                        {language === 'ar' ? '📊 رسم بياني - تشخيصات PDX due to CDI' : '📊 Chart - PDX due to CDI Diagnoses'}
                      </CardTitle>
                      <CardDescription className="text-xs">
                        {language === 'ar' ? '(التشخيصات الرئيسية المضافة فقط)' : '(Newly added primary only)'}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={currentHospital.top_pdx_due_to_cdi_diagnoses.slice(0, 10)}>
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
                          <Bar dataKey="count" fill="#22c55e" name={language === 'ar' ? 'التكرار' : 'Count'} />
                        </BarChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>

                  {/* PDX due to CDI Table */}
                  <Card className="bg-green-50">
                    <CardHeader>
                      <CardTitle className="text-lg text-gray-800">
                        {language === 'ar' ? '📋 جدول - تشخيصات PDX due to CDI' : '📋 Table - PDX due to CDI Diagnoses'}
                      </CardTitle>
                      <CardDescription className="text-xs">
                        {language === 'ar' ? '(التشخيصات الرئيسية المضافة فقط)' : '(Newly added primary only)'}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="max-h-80 overflow-y-auto">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead className="text-center">#</TableHead>
                              <TableHead>{language === 'ar' ? 'التشخيص' : 'Diagnosis'}</TableHead>
                              <TableHead className="text-center">{language === 'ar' ? 'التكرار' : 'Count'}</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {currentHospital.top_pdx_due_to_cdi_diagnoses.map((diag, index) => (
                              <TableRow key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-green-100'}>
                                <TableCell className="text-center font-bold text-green-600">{index + 1}</TableCell>
                                <TableCell className="text-sm">{diag.diagnosis}</TableCell>
                                <TableCell className="text-center">
                                  <span className="inline-block bg-green-600 text-white px-3 py-1 rounded-full font-bold">
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

              {/* ADX Diagnoses Chart & Table */}
              {currentHospital.top_adx_diagnoses && currentHospital.top_adx_diagnoses.length > 0 && (
                <div className="grid md:grid-cols-2 gap-6 mt-6">
                  {/* ADX Chart */}
                  <Card className="bg-orange-50">
                    <CardHeader>
                      <CardTitle className="text-lg text-gray-800">
                        {language === 'ar' ? '📊 رسم بياني - تشخيصات ADX due to CDI' : '📊 Chart - ADX due to CDI Diagnoses'}
                      </CardTitle>
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

                  {/* ADX Table */}
                  <Card className="bg-orange-50">
                    <CardHeader>
                      <CardTitle className="text-lg text-gray-800">
                        {language === 'ar' ? '📋 جدول - تشخيصات ADX due to CDI' : '📋 Table - ADX due to CDI Diagnoses'}
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="max-h-80 overflow-y-auto">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead className="text-center">#</TableHead>
                              <TableHead>{language === 'ar' ? 'التشخيص' : 'Diagnosis'}</TableHead>
                              <TableHead className="text-center">{language === 'ar' ? 'التكرار' : 'Count'}</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {currentHospital.top_adx_diagnoses.map((diag, index) => (
                              <TableRow key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-orange-100'}>
                                <TableCell className="text-center font-bold text-orange-600">{index + 1}</TableCell>
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
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
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
                          <span className="font-bold text-blue-600">{emp.notes_count || 0}</span>
                        </TableCell>
                        <TableCell className="text-center">
                          <span className="font-bold text-green-600">{emp.analyses_count || 0}</span>
                        </TableCell>
                        <TableCell className="text-center">
                          <Button
                            size="sm"
                            className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white shadow-md hover:shadow-lg transition-all duration-300"
                            onClick={() => handleImpersonateEmployee(emp.id, emp.full_name)}
                            title={language === 'ar' ? 'الدخول للحساب' : 'View Account'}
                          >
                            <Eye className="h-4 w-4 mr-1" />
                            {language === 'ar' ? 'عرض الحساب' : 'View'}
                          </Button>
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
                <div className="flex items-center gap-2 text-blue-600">
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
      <Footer />
    </div>
  );
};

export default SupervisorDashboard;
