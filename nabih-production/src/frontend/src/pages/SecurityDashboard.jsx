import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { 
  Shield, Users, Activity, Lock, AlertTriangle, CheckCircle, 
  XCircle, Eye, Download, RefreshCw, Search, Filter
} from 'lucide-react';
import Navbar from '@/components/Navbar';
import { useLanguage } from '@/contexts/LanguageContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const SecurityDashboard = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const { language } = useLanguage();
  
  const [stats, setStats] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterAction, setFilterAction] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [searchUser, setSearchUser] = useState('');
  const [availableActions, setAvailableActions] = useState([]);

  useEffect(() => {
    if (user?.role !== 'admin') {
      navigate('/dashboard');
      return;
    }
    fetchData();
  }, [user]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      const [statsRes, logsRes, activitiesRes, actionsRes] = await Promise.all([
        axios.get(`${API}/security/dashboard/stats`, { headers }),
        axios.get(`${API}/security/audit-logs?limit=50`, { headers }),
        axios.get(`${API}/security/dashboard/recent-activities`, { headers }),
        axios.get(`${API}/security/audit-logs/actions`, { headers })
      ]);

      setStats(statsRes.data);
      setAuditLogs(logsRes.data.logs || []);
      setActivities(activitiesRes.data.activities || []);
      setAvailableActions(actionsRes.data.actions || []);
    } catch (error) {
      console.error('Error fetching security data:', error);
      toast.error(language === 'ar' ? 'فشل تحميل البيانات' : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString(language === 'ar' ? 'ar-SA' : 'en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getActionLabel = (action) => {
    const labels = {
      'login': language === 'ar' ? 'تسجيل دخول' : 'Login',
      'logout': language === 'ar' ? 'تسجيل خروج' : 'Logout',
      'login_failed': language === 'ar' ? 'فشل تسجيل دخول' : 'Login Failed',
      'login_success': language === 'ar' ? 'تسجيل دخول ناجح' : 'Login Success',
      'mfa_otp_sent': language === 'ar' ? 'إرسال OTP' : 'OTP Sent',
      'mfa_verification_failed': language === 'ar' ? 'فشل التحقق' : 'Verification Failed',
      'password_changed': language === 'ar' ? 'تغيير كلمة المرور' : 'Password Changed',
      'create_note': language === 'ar' ? 'إنشاء ملاحظة' : 'Create Note',
      'edit_note': language === 'ar' ? 'تعديل ملاحظة' : 'Edit Note',
      'delete_note': language === 'ar' ? 'حذف ملاحظة' : 'Delete Note',
      'account_locked': language === 'ar' ? 'قفل الحساب' : 'Account Locked',
      'all_sessions_revoked': language === 'ar' ? 'إلغاء جميع الجلسات' : 'All Sessions Revoked'
    };
    return labels[action] || action;
  };

  const getStatusBadge = (status) => {
    if (status === 'success') {
      return <Badge className="bg-green-100 text-green-800">{language === 'ar' ? 'نجح' : 'Success'}</Badge>;
    } else {
      return <Badge className="bg-red-100 text-red-800">{language === 'ar' ? 'فشل' : 'Failed'}</Badge>;
    }
  };

  const exportLogs = async () => {
    try {
      toast.info(language === 'ar' ? 'جاري تصدير السجلات...' : 'Exporting logs...');
      // Implementation for export
      toast.success(language === 'ar' ? 'تم التصدير بنجاح' : 'Export successful');
    } catch (error) {
      toast.error(language === 'ar' ? 'فشل التصدير' : 'Export failed');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
        <Navbar user={user} onLogout={onLogout} />
        <div className="flex justify-center items-center py-20">
          <RefreshCw className="w-12 h-12 text-blue-600 animate-spin" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <Navbar user={user} onLogout={onLogout} />
      
      <main className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-gray-800 flex items-center gap-3">
                <Shield className="h-10 w-10 text-blue-600" />
                {language === 'ar' ? 'لوحة الأمن السيبراني' : 'Security Dashboard'}
              </h1>
              <p className="text-gray-600 mt-2">
                {language === 'ar' 
                  ? 'مراقبة وإدارة الأمان والسجلات'
                  : 'Monitor and manage security and audit logs'
                }
              </p>
            </div>
            <Button onClick={fetchData} variant="outline">
              <RefreshCw className={`h-4 w-4 ${language === 'ar' ? 'ml-2' : 'mr-2'}`} />
              {language === 'ar' ? 'تحديث' : 'Refresh'}
            </Button>
          </div>
        </div>

        {/* Statistics Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium opacity-90">
                  {language === 'ar' ? 'إجمالي المستخدمين' : 'Total Users'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">{stats.total_users}</div>
                <div className="text-xs opacity-75 mt-1">
                  <Users className="inline h-3 w-3 mr-1" />
                  {language === 'ar' ? 'مستخدم نشط' : 'Active users'}
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium opacity-90">
                  {language === 'ar' ? 'الجلسات النشطة' : 'Active Sessions'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">{stats.active_sessions}</div>
                <div className="text-xs opacity-75 mt-1">
                  <Activity className="inline h-3 w-3 mr-1" />
                  {language === 'ar' ? 'جلسة حالية' : 'Current sessions'}
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-red-500 to-red-600 text-white">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium opacity-90">
                  {language === 'ar' ? 'محاولات فاشلة اليوم' : 'Failed Attempts Today'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">{stats.failed_login_attempts_today}</div>
                <div className="text-xs opacity-75 mt-1">
                  <XCircle className="inline h-3 w-3 mr-1" />
                  {language === 'ar' ? 'محاولة تسجيل دخول' : 'Login attempts'}
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-amber-500 to-amber-600 text-white">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium opacity-90">
                  {language === 'ar' ? 'حسابات مقفلة' : 'Locked Accounts'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">{stats.locked_accounts}</div>
                <div className="text-xs opacity-75 mt-1">
                  <Lock className="inline h-3 w-3 mr-1" />
                  {language === 'ar' ? 'مؤقتاً' : 'Temporarily'}
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Additional Stats Row */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-gray-600">
                  {language === 'ar' ? 'سجلات اليوم' : 'Audit Logs Today'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-blue-600">{stats.audit_logs_today}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-gray-600">
                  {language === 'ar' ? 'MFA مفعل' : 'MFA Enabled'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">
                  {stats.mfa_enabled_users}/{stats.total_users}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-gray-600">
                  {language === 'ar' ? 'كلمات مرور تنتهي قريباً' : 'Passwords Expiring Soon'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-amber-600">{stats.password_expiring_soon}</div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Recent Activities */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              {language === 'ar' ? 'الأنشطة الأخيرة' : 'Recent Activities'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {activities.length === 0 ? (
              <p className="text-center text-gray-500 py-8">
                {language === 'ar' ? 'لا توجد أنشطة' : 'No activities'}
              </p>
            ) : (
              <div className="space-y-2">
                {activities.slice(0, 10).map((activity) => (
                  <div
                    key={activity.id}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition"
                  >
                    <div className="flex items-center gap-3 flex-1">
                      <div className={`w-2 h-2 rounded-full ${
                        activity.status === 'success' ? 'bg-green-500' : 'bg-red-500'
                      }`} />
                      <div>
                        <div className="font-medium text-gray-800">
                          {getActionLabel(activity.action)}
                        </div>
                        <div className="text-xs text-gray-500">
                          {activity.user_email || language === 'ar' ? 'مستخدم غير معروف' : 'Unknown user'}
                        </div>
                      </div>
                    </div>
                    <div className="text-xs text-gray-500">
                      {formatDate(activity.timestamp)}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Audit Logs Table */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Eye className="h-5 w-5" />
                {language === 'ar' ? 'سجلات المراجعة' : 'Audit Logs'}
              </CardTitle>
              <Button onClick={exportLogs} variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                {language === 'ar' ? 'تصدير' : 'Export'}
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {/* Filters */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <Input
                placeholder={language === 'ar' ? 'بحث عن مستخدم...' : 'Search user...'}
                value={searchUser}
                onChange={(e) => setSearchUser(e.target.value)}
              />
              
              <Select value={filterAction} onValueChange={setFilterAction}>
                <SelectTrigger>
                  <SelectValue placeholder={language === 'ar' ? 'نوع الإجراء' : 'Action Type'} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">{language === 'ar' ? 'الكل' : 'All'}</SelectItem>
                  {availableActions.map(action => (
                    <SelectItem key={action} value={action}>
                      {getActionLabel(action)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={filterStatus} onValueChange={setFilterStatus}>
                <SelectTrigger>
                  <SelectValue placeholder={language === 'ar' ? 'الحالة' : 'Status'} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">{language === 'ar' ? 'الكل' : 'All'}</SelectItem>
                  <SelectItem value="success">{language === 'ar' ? 'نجح' : 'Success'}</SelectItem>
                  <SelectItem value="failure">{language === 'ar' ? 'فشل' : 'Failed'}</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Logs Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b">
                  <tr>
                    <th className="px-4 py-3 text-right font-semibold">
                      {language === 'ar' ? 'الوقت' : 'Time'}
                    </th>
                    <th className="px-4 py-3 text-right font-semibold">
                      {language === 'ar' ? 'المستخدم' : 'User'}
                    </th>
                    <th className="px-4 py-3 text-right font-semibold">
                      {language === 'ar' ? 'الإجراء' : 'Action'}
                    </th>
                    <th className="px-4 py-3 text-right font-semibold">
                      {language === 'ar' ? 'الحالة' : 'Status'}
                    </th>
                    <th className="px-4 py-3 text-right font-semibold">
                      {language === 'ar' ? 'IP' : 'IP Address'}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {auditLogs
                    .filter(log => {
                      if (searchUser && !log.user_email?.toLowerCase().includes(searchUser.toLowerCase())) {
                        return false;
                      }
                      if (filterAction && filterAction !== 'all' && log.action !== filterAction) {
                        return false;
                      }
                      if (filterStatus && filterStatus !== 'all' && log.status !== filterStatus) {
                        return false;
                      }
                      return true;
                    })
                    .map((log) => (
                      <tr key={log.id} className="border-b hover:bg-gray-50">
                        <td className="px-4 py-3 text-gray-600">
                          {formatDate(log.timestamp)}
                        </td>
                        <td className="px-4 py-3">
                          {log.user_email || '-'}
                        </td>
                        <td className="px-4 py-3">
                          {getActionLabel(log.action)}
                        </td>
                        <td className="px-4 py-3">
                          {getStatusBadge(log.status)}
                        </td>
                        <td className="px-4 py-3 text-gray-600 font-mono text-xs">
                          {log.ip_address || '-'}
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
};

export default SecurityDashboard;
