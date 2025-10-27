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
  Users, Award, BarChart3, Stethoscope, Download, PieChart 
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
      setEmployees(response.data);
    } catch (error) {
      console.error('Failed to fetch employees:', error);
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

        <Card className="medical-card bg-gradient-to-br from-green-50 to-green-100">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              {language === 'ar' ? 'PDX/After CDI' : 'PDX/After CDI'}
            </CardTitle>
            <Stethoscope className="h-5 w-5 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-700">{analysis.pdx_metrics.total_after_cdi}</div>
            <p className="text-xs text-green-600 mt-1">
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
                    <div className="text-xs text-green-600 mb-1">{language === 'ar' ? 'PDX المضافة' : 'PDX Added'}</div>
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
      <div className="grid md:grid-cols-2 gap-6 mb-8">
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
                      <span className="font-bold text-green-600">{spec.impact_rate}%</span>
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

    return (
      <Card className="medical-card mb-8">
        <CardHeader>
          <CardTitle className="text-2xl text-gray-800">
            {language === 'ar' ? 'أداء CDS المتخصصين' : 'CDS Specialists Performance'}
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
                  <TableHead className="text-center">{language === 'ar' ? 'PDX' : 'PDX Queries'}</TableHead>
                  <TableHead className="text-center">{language === 'ar' ? 'ADX' : 'ADX Queries'}</TableHead>
                  <TableHead className="text-center">{language === 'ar' ? 'معدل النجاح' : 'Success Rate'}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {analysis.cds_performance.map((cds, index) => (
                  <TableRow key={index} className={index % 2 === 0 ? 'bg-gray-50' : ''}>
                    <TableCell className="text-center font-medium">{cds.cds_name}</TableCell>
                    <TableCell className="text-center">{cds.total_cases}</TableCell>
                    <TableCell className="text-center">
                      <span className="font-bold text-purple-600">{cds.drg_impact}</span>
                    </TableCell>
                    <TableCell className="text-center">
                      <span className="font-bold text-blue-600">{cds.pdx_queries}</span>
                    </TableCell>
                    <TableCell className="text-center">
                      <span className="font-bold text-orange-600">{cds.adx_queries}</span>
                    </TableCell>
                    <TableCell className="text-center">
                      <span className="font-bold text-green-600">{cds.success_rate}%</span>
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <Navbar user={user} onLogout={onLogout} />
      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            {language === 'ar' ? 'لوحة تحكم المشرف - أداة تحليل CDI الاحترافية' : 'Supervisor Dashboard - Professional CDI Analysis Tool'}
          </h1>
          <p className="text-gray-600">
            {language === 'ar' ? 'تحليل شامل لبيانات تحسين التوثيق السريري مع مؤشرات تفصيلية' : 'Comprehensive CDI Data Analysis with Detailed Indicators'}
          </p>
        </div>

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
            </div>
          </CardContent>
        </Card>

        {/* Analysis Results */}
        {analysis && (
          <>
            {renderSummaryCards()}
            {renderHospitalsAnalysis()}
            {renderTopDiagnoses()}
            {renderSpecialtyAnalysis()}
            {renderCDSPerformance()}
          </>
        )}

        {/* Employees Section */}
        {employees.length > 0 && (
          <Card className="medical-card mt-8">
            <CardHeader>
              <CardTitle className="text-2xl text-gray-800">
                {language === 'ar' ? 'الموظفون' : 'Employees'}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="text-center">{language === 'ar' ? 'الاسم' : 'Name'}</TableHead>
                      <TableHead className="text-center">{language === 'ar' ? 'البريد' : 'Email'}</TableHead>
                      <TableHead className="text-center">{language === 'ar' ? 'الجوال' : 'Phone'}</TableHead>
                      <TableHead className="text-center">{language === 'ar' ? 'الملاحظات' : 'Notes'}</TableHead>
                      <TableHead className="text-center">{language === 'ar' ? 'التحليلات' : 'Analyses'}</TableHead>
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
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        )}
      </main>
      <Footer />
    </div>
  );
};

export default SupervisorDashboard;
