import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import { Upload, FileSpreadsheet, TrendingUp, AlertTriangle, Activity, Hospital } from 'lucide-react';
import Navbar from '@/components/Navbar';
import { useLanguage } from '@/contexts/LanguageContext';
import Footer from '@/components/Footer';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

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
      toast.success(language === 'ar' ? 'تم تحليل البيانات بنجاح' : 'Data analyzed successfully');
    } catch (error) {
      toast.error(
        error.response?.data?.detail || 
        (language === 'ar' ? 'فشل تحليل البيانات' : 'Failed to analyze data')
      );
    } finally {
      setUploading(false);
    }
  };

  const renderAnalysis = () => {
    if (!analysis) return null;

    return (
      <div className="space-y-6">
        {/* Summary Cards */}
        <div className="grid md:grid-cols-4 gap-6">
          <Card className="medical-card">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {language === 'ar' ? 'إجمالي السجلات' : 'Total Records'}
              </CardTitle>
              <FileSpreadsheet className="h-4 w-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-blue-700">{analysis.total_records}</div>
            </CardContent>
          </Card>

          <Card className="medical-card">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {language === 'ar' ? 'المستشفيات' : 'Hospitals'}
              </CardTitle>
              <Hospital className="h-4 w-4 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-green-700">{analysis.total_hospitals}</div>
            </CardContent>
          </Card>

          <Card className="medical-card">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {language === 'ar' ? 'تأثير DRG' : 'DRG Impact'}
              </CardTitle>
              <TrendingUp className="h-4 w-4 text-purple-600" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-purple-700">{analysis.drg_changes}</div>
            </CardContent>
          </Card>

          <Card className="medical-card">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {language === 'ar' ? 'تشخيصات غير موثقة' : 'Undocumented'}
              </CardTitle>
              <AlertTriangle className="h-4 w-4 text-red-600" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-red-700">{analysis.undocumented_total}</div>
            </CardContent>
          </Card>
        </div>

        {/* Hospital Analysis */}
        <Card className="medical-card">
          <CardHeader>
            <CardTitle className="text-2xl text-gray-800">
              {language === 'ar' ? 'تحليل التشخيصات حسب المستشفى' : 'Diagnosis Analysis by Hospital'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-center">{language === 'ar' ? 'المستشفى' : 'Hospital'}</TableHead>
                    <TableHead className="text-center">{language === 'ar' ? 'السجلات' : 'Records'}</TableHead>
                    <TableHead className="text-center">{language === 'ar' ? 'غير موثق رئيسي' : 'Primary Undoc.'}</TableHead>
                    <TableHead className="text-center">{language === 'ar' ? 'غير موثق ثانوي' : 'Secondary Undoc.'}</TableHead>
                    <TableHead className="text-center">{language === 'ar' ? 'تغير DRG' : 'DRG Changes'}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {analysis.hospitals_data?.map((hospital, index) => (
                    <TableRow key={index} className={index % 2 === 0 ? 'bg-gray-50' : ''}>
                      <TableCell className="text-center font-medium">{hospital.hospital_name}</TableCell>
                      <TableCell className="text-center">{hospital.total_records}</TableCell>
                      <TableCell className="text-center">
                        <span className="font-bold text-red-600">{hospital.primary_undocumented}</span>
                      </TableCell>
                      <TableCell className="text-center">
                        <span className="font-bold text-orange-600">{hospital.secondary_undocumented}</span>
                      </TableCell>
                      <TableCell className="text-center">
                        <span className="font-bold text-purple-600">{hospital.drg_changes}</span>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <Navbar user={user} onLogout={onLogout} />
      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            {language === 'ar' ? 'لوحة تحكم المشرف' : 'Supervisor Dashboard'}
          </h1>
          <p className="text-gray-600">
            {language === 'ar' ? 'تحليل بيانات تحسين التوثيق السريري' : 'CDI Data Analysis Tool'}
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
                    ? 'قم برفع ملف Excel يحتوي على البيانات التالية: CDS Name, Hospital Name, Admission Date, DRG Change' 
                    : 'Upload Excel file containing: CDS Name, Hospital Name, Admission Date, DRG Change'}
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
              <p className="text-sm text-gray-500">
                {language === 'ar' 
                  ? '* الملف يجب أن يحتوي على الأعمدة التالية: CDS Name, Hospital Name, Admission Date, Primary Diagnosis, Secondary Diagnosis, DRG Before, DRG After, DRG Change' 
                  : '* File should contain columns: CDS Name, Hospital Name, Admission Date, Primary Diagnosis, Secondary Diagnosis, DRG Before, DRG After, DRG Change'}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Analysis Results */}
        {renderAnalysis()}

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
