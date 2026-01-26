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
  Users, Award, BarChart3, Stethoscope, Download, FileText, PieChart 
} from 'lucide-react';
import {
  BarChart, Bar, PieChart as RePieChart, Pie, Cell, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import Navbar from '@/components/Navbar';
import { useLanguage } from '@/contexts/LanguageContext';
import Footer from '@/components/Footer';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82ca9d', '#ffc658'];

const SupervisorDashboardPro = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const { language, t } = useLanguage();
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [employees, setEmployees] = useState([]);
  const [activeTab, setActiveTab] = useState('overview');

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
      
      toast.success(language === 'ar' ? 'تم تحميل التقرير بنجاح' : 'Report downloaded successfully');
    } catch (error) {
      toast.error(language === 'ar' ? 'فشل تحميل التقرير' : 'Failed to download report');
    }
  };

  const renderSummaryCards = () => {
    if (!analysis) return null;

    return (
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card className="medical-card bg-gradient-to-br from-blue-50 to-blue-100 hover:shadow-lg transition">
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

        <Card className="medical-card bg-gradient-to-br from-purple-50 to-purple-100 hover:shadow-lg transition">
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

        <Card className="medical-card bg-gradient-to-br from-green-50 to-green-100 hover:shadow-lg transition">
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

        <Card className="medical-card bg-gradient-to-br from-orange-50 to-orange-100 hover:shadow-lg transition">
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

  const renderCharts = () => {
    if (!analysis || !analysis.hospitals_analysis) return null;

    // Prepare data for charts
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
              {language === 'ar' ? 'مقارنة المستشفيات' : 'Hospitals Comparison'}
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
                <Bar dataKey="DRG" fill="#8b5cf6" name="DRG" />
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

    const recommendations = generateRecommendations(analysis);

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
              <div key={index} className="bg-white p-4 rounded-lg border-l-4 border-orange-500 shadow-sm">
                <h3 className="font-bold text-gray-800 mb-2">{rec.category}</h3>
                <p className="text-gray-700 text-sm leading-relaxed">{rec.recommendation}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  };

  const generateRecommendations = (data) => {
    const recommendations = [];
    
    const drgRate = data.drg_metrics?.change_rate || 0;
    const pdxRate = data.pdx_metrics?.change_rate || 0;
    const hospitals = data.hospitals_analysis || [];
    
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

    const topPdx = data.top_diagnoses?.pdx_after_cdi || [];
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

    return recommendations;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <Navbar user={user} onLogout={onLogout} />
      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            {language === 'ar' ? '🎯 أداة تحليل CDI الاحترافية' : '🎯 Professional CDI Analysis Tool'}
          </h1>
          <p className="text-gray-600">
            {language === 'ar' ? 'تحليل شامل مع رسوم بيانية وتوصيات ذكية' : 'Comprehensive Analysis with Charts & Smart Recommendations'}
          </p>
        </div>

        {/* Upload Section */}
        <Card className="medical-card mb-8 bg-gradient-to-r from-blue-50 to-indigo-50">
          <CardHeader>
            <CardTitle className="text-2xl text-gray-800 flex items-center gap-2">
              <Upload className="h-6 w-6 text-blue-600" />
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
                    {language === 'ar' ? 'تحميل تقرير Excel' : 'Download Excel Report'}
                  </Button>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Analysis Results */}
        {analysis && (
          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="overview">{language === 'ar' ? 'نظرة عامة' : 'Overview'}</TabsTrigger>
              <TabsTrigger value="charts">{language === 'ar' ? 'الرسوم البيانية' : 'Charts'}</TabsTrigger>
              <TabsTrigger value="recommendations">{language === 'ar' ? 'التوصيات' : 'Recommendations'}</TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-6">
              {renderSummaryCards()}
              {/* Keep existing hospital detailed analysis from SupervisorDashboard */}
            </TabsContent>

            <TabsContent value="charts">
              {renderCharts()}
            </TabsContent>

            <TabsContent value="recommendations">
              {renderRecommendations()}
            </TabsContent>
          </Tabs>
        )}
      </main>
      <Footer />
    </div>
  );
};

export default SupervisorDashboardPro;
