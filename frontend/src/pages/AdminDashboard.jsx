import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { toast } from 'sonner';
import { Users, Download, Activity, Calendar, UserCheck, UserX, Trash2, Edit, ShieldCheck, Lock, Eye } from 'lucide-react';
import Navbar from '@/components/Navbar';
import { useLanguage } from '@/contexts/LanguageContext';
import Footer from '@/components/Footer';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AdminDashboard = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const { language, t } = useLanguage();
  const [statistics, setStatistics] = useState(null);
  const [allUsers, setAllUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [editFormData, setEditFormData] = useState({});
  const [changePasswordUser, setChangePasswordUser] = useState(null);
  const [newPassword, setNewPassword] = useState('');
  const [editDepartmentUser, setEditDepartmentUser] = useState(null);
  const [departmentForm, setDepartmentForm] = useState({
    department: 'cdi',
    coding_role: null,
    daily_case_target: 10
  });

  useEffect(() => {
    if (user.role !== 'admin') {
      navigate('/dashboard');
      return;
    }
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');
      
      // Fetch statistics
      const statsResponse = await axios.get(`${API}/admin/users-statistics`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStatistics(statsResponse.data);
      
      // Fetch all users
      const usersResponse = await axios.get(`${API}/admin/stats`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Get detailed user list
      const users = statsResponse.data.statistics.map(stat => ({
        ...stat,
        id: stat.user_id,
        is_active: true // Will be updated from backend
      }));
      setAllUsers(users);
    } catch (error) {
      toast.error(language === 'ar' ? 'فشل تحميل البيانات' : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateDepartment = async () => {
    if (!editDepartmentUser) return;
    
    try {
      const token = localStorage.getItem('token');
      await axios.put(
        `${API}/admin/users/${editDepartmentUser.id}/department?department=${departmentForm.department}&coding_role=${departmentForm.coding_role || ''}&daily_case_target=${departmentForm.daily_case_target || ''}`,
        {},
        { headers: { Authorization: `Bearer ${token}` }}
      );
      
      toast.success(language === 'ar' ? 'تم تحديث القسم بنجاح' : 'Department updated successfully');
      setEditDepartmentUser(null);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update');
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

  const handlePromoteToSupervisor = async (userId) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/admin/assign-supervisor/${userId}`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(language === 'ar' ? 'تم تعيين المشرف بنجاح' : 'Supervisor assigned successfully');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || (language === 'ar' ? 'فشل التعيين' : 'Failed to assign'));
    }
  };

  const handleRemoveSupervisor = async (userId) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/admin/remove-supervisor/${userId}`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(language === 'ar' ? 'تم إلغاء صلاحيات المشرف' : 'Supervisor removed successfully');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || (language === 'ar' ? 'فشل الإلغاء' : 'Failed to remove'));
    }
  };

  const handleSuspendUser = async (userId) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/admin/suspend-user/${userId}`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(language === 'ar' ? 'تم تعليق الحساب' : 'Account suspended');
      fetchData();
    } catch (error) {
      toast.error(language === 'ar' ? 'فشل التعليق' : 'Failed to suspend');
    }
  };

  const handleActivateUser = async (userId) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/admin/activate-user/${userId}`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(language === 'ar' ? 'تم تفعيل الحساب' : 'Account activated');
      fetchData();
    } catch (error) {
      toast.error(language === 'ar' ? 'فشل التفعيل' : 'Failed to activate');
    }
  };

  const handleDeleteUser = async (userId) => {
    if (!window.confirm(language === 'ar' ? 'هل أنت متأكد من حذف هذا المستخدم؟' : 'Are you sure you want to delete this user?')) {
      return;
    }
    
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API}/admin/users/${userId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(language === 'ar' ? 'تم حذف المستخدم' : 'User deleted');
      fetchData();
    } catch (error) {
      toast.error(language === 'ar' ? 'فشل الحذف' : 'Failed to delete');
    }
  };

  const handleEditUser = (userStat) => {
    setEditingUser(userStat);
    setEditFormData({
      full_name: userStat.full_name,
      email: userStat.email,
      phone_number: userStat.phone_number
    });
  };

  const handleSaveEdit = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.put(`${API}/admin/users/${editingUser.user_id}`, editFormData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(language === 'ar' ? 'تم تحديث البيانات' : 'Data updated');
      setEditingUser(null);
      fetchData();
    } catch (error) {
      toast.error(language === 'ar' ? 'فشل التحديث' : 'Failed to update');
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
        `${API}/admin/change-user-password/${changePasswordUser.user_id}`,
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

  const handleImpersonateUser = async (userId, userName) => {
    if (!window.confirm(language === 'ar' ? `هل تريد الدخول إلى حساب ${userName}؟` : `Do you want to access ${userName}'s account?`)) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API}/admin/impersonate/${userId}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );

      // Store original admin token
      localStorage.setItem('admin_token_backup', token);
      localStorage.setItem('is_impersonating', 'true');
      
      // Set the impersonated user's token
      localStorage.setItem('token', response.data.access_token);
      
      toast.success(language === 'ar' ? `تم الدخول إلى حساب ${userName}` : `Now viewing ${userName}'s account`);
      
      // Reload to dashboard
      window.location.href = '/dashboard';
    } catch (error) {
      toast.error(language === 'ar' ? 'فشل الدخول للحساب' : 'Failed to impersonate user');
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
            {language === 'ar' ? 'إدارة المستخدمين والإحصائيات' : 'User Management & Statistics'}
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

        {/* Users Management Table */}
        <Card className="medical-card">
          <CardHeader>
            <CardTitle className="text-2xl text-gray-800">
              {language === 'ar' ? 'إدارة المستخدمين' : 'User Management'}
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
                    <TableHead className="text-center">{language === 'ar' ? 'الدور' : 'Role'}</TableHead>
                    <TableHead className="text-center">{language === 'ar' ? 'النشاط اليوم' : 'Today'}</TableHead>
                    <TableHead className="text-center">{language === 'ar' ? 'الإجراءات' : 'Actions'}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {statistics?.statistics?.map((userStat) => (
                    <TableRow key={userStat.user_id}>
                      <TableCell className="text-center font-medium">{userStat.full_name}</TableCell>
                      <TableCell className="text-center text-sm">{userStat.email}</TableCell>
                      <TableCell className="text-center text-sm">{userStat.phone_number || '-'}</TableCell>
                      <TableCell className="text-center">
                        {userStat.role === 'supervisor' ? (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                            {language === 'ar' ? 'مشرف' : 'Supervisor'}
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                            {language === 'ar' ? 'موظف' : 'User'}
                          </span>
                        )}
                      </TableCell>
                      <TableCell className="text-center">
                        <span className="font-bold text-orange-600">{userStat.today_notes}</span>
                        {' / '}
                        <span className="font-bold text-purple-600">{userStat.today_analyses}</span>
                      </TableCell>
                      <TableCell className="text-center">
                        <div className="flex items-center justify-center gap-2 flex-wrap">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleEditUser(userStat)}
                            title={language === 'ar' ? 'تعديل' : 'Edit'}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          
                          <Button
                            size="sm"
                            variant="outline"
                            className="text-blue-600"
                            onClick={() => setChangePasswordUser(userStat)}
                            title={language === 'ar' ? 'تغيير كلمة المرور' : 'Change Password'}
                          >
                            <Lock className="h-4 w-4" />
                          </Button>
                          
                          <Button
                            size="sm"
                            variant="outline"
                            className="text-green-600"
                            onClick={() => handleImpersonateUser(userStat.user_id, userStat.full_name)}
                            title={language === 'ar' ? 'الدخول للحساب' : 'Impersonate User'}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                          
                          {userStat.role !== 'supervisor' ? (
                            <Button
                              size="sm"
                              variant="outline"
                              className="text-purple-600"
                              onClick={() => handlePromoteToSupervisor(userStat.user_id)}
                              title={language === 'ar' ? 'تعيين كمشرف' : 'Make Supervisor'}
                            >
                              <ShieldCheck className="h-4 w-4" />
                            </Button>
                          ) : (
                            <Button
                              size="sm"
                              variant="outline"
                              className="text-gray-600"
                              onClick={() => handleRemoveSupervisor(userStat.user_id)}
                              title={language === 'ar' ? 'إلغاء المشرف' : 'Remove Supervisor'}
                            >
                              <UserX className="h-4 w-4" />
                            </Button>
                          )}
                          
                          <Button
                            size="sm"
                            variant="outline"
                            className="text-red-600"
                            onClick={() => handleDeleteUser(userStat.user_id)}
                            title={language === 'ar' ? 'حذف' : 'Delete'}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>

        {/* Edit User Dialog */}
        {editingUser && (
          <Dialog open={!!editingUser} onOpenChange={() => setEditingUser(null)}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>{language === 'ar' ? 'تعديل بيانات المستخدم' : 'Edit User Data'}</DialogTitle>
                <DialogDescription>
                  {language === 'ar' ? 'قم بتعديل البيانات أدناه' : 'Modify the data below'}
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label>{language === 'ar' ? 'الاسم الكامل' : 'Full Name'}</Label>
                  <Input
                    value={editFormData.full_name}
                    onChange={(e) => setEditFormData({...editFormData, full_name: e.target.value})}
                  />
                </div>
                <div>
                  <Label>{language === 'ar' ? 'البريد الإلكتروني' : 'Email'}</Label>
                  <Input
                    type="email"
                    value={editFormData.email}
                    onChange={(e) => setEditFormData({...editFormData, email: e.target.value})}
                  />
                </div>
                <div>
                  <Label>{language === 'ar' ? 'رقم الجوال' : 'Phone Number'}</Label>
                  <Input
                    value={editFormData.phone_number}
                    onChange={(e) => setEditFormData({...editFormData, phone_number: e.target.value})}
                  />
                </div>
                <div className="flex gap-2 justify-end">
                  <Button variant="outline" onClick={() => setEditingUser(null)}>
                    {language === 'ar' ? 'إلغاء' : 'Cancel'}
                  </Button>
                  <Button onClick={handleSaveEdit} className="medical-blue">
                    {language === 'ar' ? 'حفظ' : 'Save'}
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        )}

        {/* Change Password Dialog */}
        {changePasswordUser && (
          <Dialog open={!!changePasswordUser} onOpenChange={() => {setChangePasswordUser(null); setNewPassword('');}}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>{language === 'ar' ? 'تغيير كلمة المرور' : 'Change Password'}</DialogTitle>
                <DialogDescription>
                  {language === 'ar' ? `تغيير كلمة المرور للمستخدم: ${changePasswordUser.full_name}` : `Change password for: ${changePasswordUser.full_name}`}
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label>{language === 'ar' ? 'كلمة المرور الجديدة' : 'New Password'}</Label>
                  <Input
                    type="password"
                    placeholder={language === 'ar' ? 'أدخل كلمة المرور الجديدة (6 أحرف على الأقل)' : 'Enter new password (min 6 characters)'}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                  />
                </div>
                <div className="flex gap-2 justify-end">
                  <Button variant="outline" onClick={() => {setChangePasswordUser(null); setNewPassword('');}}>
                    {language === 'ar' ? 'إلغاء' : 'Cancel'}
                  </Button>
                  <Button onClick={handleChangePassword} className="medical-blue">
                    {language === 'ar' ? 'تغيير كلمة المرور' : 'Change Password'}
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        )}
      </main>
      <Footer />
    </div>
  );
};

export default AdminDashboard;