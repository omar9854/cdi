import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { toast } from 'sonner';
import { Users, FileText, BarChart3, Download, Activity, Calendar } from 'lucide-react';
import Navbar from '@/components/Navbar';
import { useLanguage } from '@/contexts/LanguageContext';
import Footer from '@/components/Footer';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AdminDashboard = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const { language, t } = useLanguage();
  const [statistics, setStatistics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    if (user.role !== 'admin') {
      navigate('/dashboard');
      return;
    }
    fetchStatistics();
  }, []);

  const fetchStatistics = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/admin/users-statistics`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStatistics(response.data);
    } catch (error) {
      toast.error(language === 'ar' ? 'فشل تحميل الإحصائيات' : 'Failed to load statistics');
    } finally {
      setLoading(false);
    }
  };

  const handleExportExcel = async () => {
    setExporting(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/admin/export-statistics`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      });
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `user_statistics_${new Date().toISOString().split('T')[0]}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      toast.success(language === 'ar' ? 'تم تصدير البيانات بنجاح' : 'Data exported successfully');
    } catch (error) {
      toast.error(language === 'ar' ? 'فشل التصدير' : 'Export failed');
    } finally {
      setExporting(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('ar-SA', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateStr;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl text-blue-600">{t('loading')}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <Navbar user={user} onLogout={onLogout} />
      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            {language === 'ar' ? 'لوحة تحكم الأدمن' : 'Admin Dashboard'}
          </h1>
          <p className="text-gray-600">
            {language === 'ar' ? 'إحصائيات المستخدمين اليومية' : 'Daily User Statistics'}
          </p>
        </div>

        {/* Summary Cards */}
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <Card className="medical-card">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {language === 'ar' ? 'إجمالي المستخدمين' : 'Total Users'}
              </CardTitle>
              <Users className="h-4 w-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-blue-700">{statistics?.total_users || 0}</div>
            </CardContent>
          </Card>

          <Card className="medical-card">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {language === 'ar' ? 'نشط اليوم' : 'Active Today'}
              </CardTitle>
              <Activity className="h-4 w-4 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-green-700">{statistics?.active_today || 0}</div>
            </CardContent>
          </Card>

          <Card className="medical-card">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {language === 'ar' ? 'التاريخ' : 'Date'}
              </CardTitle>
              <Calendar className="h-4 w-4 text-purple-600" />
            </CardHeader>
            <CardContent>
              <div className="text-xl font-bold text-purple-700">{statistics?.date}</div>
            </CardContent>
          </Card>
        </div>

        {/* Export Button */}
        <div className="mb-6 flex justify-end">
          <Button
            onClick={handleExportExcel}
            disabled={exporting}
            className="medical-blue text-white px-6 py-3"
          >
            <Download className={language === 'ar' ? 'ml-2' : 'mr-2'} />
            {exporting 
              ? (language === 'ar' ? 'جاري التصدير...' : 'Exporting...') 
              : (language === 'ar' ? 'تصدير إلى Excel' : 'Export to Excel')
            }
          </Button>
        </div>

        {/* Statistics Table */}
        <Card className="medical-card">
          <CardHeader>
            <CardTitle className="text-2xl text-gray-800">
              {language === 'ar' ? 'إحصائيات المستخدمين التفصيلية' : 'Detailed User Statistics'}
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
                    <TableHead className="text-center">{language === 'ar' ? 'آخر نشاط' : 'Last Activity'}</TableHead>
                    <TableHead className="text-center">{language === 'ar' ? 'الملاحظات' : 'Notes'}</TableHead>
                    <TableHead className="text-center">{language === 'ar' ? 'التحليلات' : 'Analyses'}</TableHead>
                    <TableHead className="text-center">{language === 'ar' ? 'اليوم' : 'Today'}</TableHead>
                    <TableHead className="text-center">{language === 'ar' ? 'الحالة' : 'Status'}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {statistics?.statistics?.map((userStat, index) => (
                    <TableRow key={userStat.user_id} className={index % 2 === 0 ? 'bg-gray-50' : ''}>
                      <TableCell className="text-center font-medium">{userStat.full_name}</TableCell>
                      <TableCell className="text-center text-sm">{userStat.email}</TableCell>
                      <TableCell className="text-center text-sm">{userStat.phone_number || '-'}</TableCell>
                      <TableCell className="text-center text-sm">{formatDate(userStat.last_activity)}</TableCell>
                      <TableCell className="text-center">
                        <span className="font-semibold text-blue-600">{userStat.total_notes}</span>
                      </TableCell>
                      <TableCell className="text-center">
                        <span className="font-semibold text-green-600">{userStat.total_analyses}</span>
                      </TableCell>
                      <TableCell className="text-center">
                        <div className="flex flex-col items-center gap-1">
                          <span className="text-sm">
                            {language === 'ar' ? 'ملاحظات:' : 'Notes:'} 
                            <span className="font-bold text-orange-600 ml-1">{userStat.today_notes}</span>
                          </span>
                          <span className="text-sm">
                            {language === 'ar' ? 'تحليلات:' : 'Analyses:'} 
                            <span className="font-bold text-purple-600 ml-1">{userStat.today_analyses}</span>
                          </span>
                        </div>
                      </TableCell>
                      <TableCell className="text-center">
                        {userStat.is_active_today ? (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            {language === 'ar' ? 'نشط' : 'Active'}
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                            {language === 'ar' ? 'غير نشط' : 'Inactive'}
                          </span>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </main>
      <Footer />
    </div>
  );
};

export default AdminDashboard;
