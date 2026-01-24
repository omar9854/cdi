import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { Users, FileText, BarChart3, Shield, Trash2, CheckCircle, XCircle } from 'lucide-react';
import Navbar from '@/components/Navbar';
import { useLanguage } from '@/contexts/LanguageContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AdminDashboard = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const { language, t } = useLanguage();
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user.role !== 'admin') {
      navigate('/dashboard');
      return;
    }
    fetchStats();
    fetchUsers();
  }, []);

  const fetchStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/admin/stats`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStats(response.data);
    } catch (error) {
      toast.error(language === 'ar' ? 'فشل تحميل الإحصائيات' : 'Failed to load stats');
    }
  };

  const fetchUsers = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/admin/users`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUsers(response.data);
    } catch (error) {
      toast.error(language === 'ar' ? 'فشل تحميل المستخدمين' : 'Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleActive = async (userId) => {
    try {
      const token = localStorage.getItem('token');
      await axios.put(`${API}/admin/users/${userId}/toggle-active`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(language === 'ar' ? 'تم تحديث حالة المستخدم' : 'User status updated');
      fetchUsers();
    } catch (error) {
      toast.error(language === 'ar' ? 'فشل التحديث' : 'Update failed');
    }
  };

  const handleDeleteUser = async (userId) => {
    if (!window.confirm(language === 'ar' ? 'هل أنت متأكد من حذف المستخدم؟' : 'Are you sure you want to delete this user?')) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API}/admin/users/${userId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(language === 'ar' ? 'تم حذف المستخدم' : 'User deleted');
      fetchUsers();
      fetchStats();
    } catch (error) {
      toast.error(error.response?.data?.detail || (language === 'ar' ? 'فشل الحذف' : 'Delete failed'));
    }
  };

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">{t('loading')}</div>;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <Navbar user={user} onLogout={onLogout} />
      
      <main className="container mx-auto px-4 py-8 max-w-7xl" data-testid="admin-dashboard">
        <div className="mb-8 fade-in">
          <div className="flex items-center gap-3 mb-2">
            <Shield className="w-8 h-8 text-blue-600" />
            <h1 className="text-4xl font-bold text-gray-800">
              {language === 'ar' ? 'لوحة تحكم الأدمن' : 'Admin Dashboard'}
            </h1>
          </div>
          <p className="text-gray-600">
            {language === 'ar' ? 'إدارة المستخدمين والنظام' : 'Manage users and system'}
          </p>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid md:grid-cols-4 gap-6 mb-8 fade-in">
            <Card className="medical-card">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">{language === 'ar' ? 'إجمالي المستخدمين' : 'Total Users'}</p>
                    <p className="text-3xl font-bold text-blue-600">{stats.total_users}</p>
                  </div>
                  <Users className="w-12 h-12 text-blue-600 opacity-20" />
                </div>
              </CardContent>
            </Card>

            <Card className="medical-card">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">{language === 'ar' ? 'المستخدمين العاديين' : 'Regular Users'}</p>
                    <p className="text-3xl font-bold text-green-600">{stats.regular_users}</p>
                  </div>
                  <Users className="w-12 h-12 text-green-600 opacity-20" />
                </div>
              </CardContent>
            </Card>

            <Card className="medical-card">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">{language === 'ar' ? 'الملاحظات' : 'Notes'}</p>
                    <p className="text-3xl font-bold text-purple-600">{stats.total_notes}</p>
                  </div>
                  <FileText className="w-12 h-12 text-purple-600 opacity-20" />
                </div>
              </CardContent>
            </Card>

            <Card className="medical-card">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">{language === 'ar' ? 'التحليلات' : 'Analyses'}</p>
                    <p className="text-3xl font-bold text-orange-600">{stats.total_analyses}</p>
                  </div>
                  <BarChart3 className="w-12 h-12 text-orange-600 opacity-20" />
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Users Table */}
        <Card className="medical-card fade-in">
          <CardHeader>
            <CardTitle className="text-2xl">
              {language === 'ar' ? 'إدارة المستخدمين' : 'User Management'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b-2 border-gray-200">
                    <th className="text-right p-3 font-semibold">{language === 'ar' ? 'الاسم' : 'Name'}</th>
                    <th className="text-right p-3 font-semibold">{language === 'ar' ? 'البريد' : 'Email'}</th>
                    <th className="text-right p-3 font-semibold">{language === 'ar' ? 'الصلاحية' : 'Role'}</th>
                    <th className="text-right p-3 font-semibold">{language === 'ar' ? 'الحالة' : 'Status'}</th>
                    <th className="text-right p-3 font-semibold">{language === 'ar' ? 'الإجراءات' : 'Actions'}</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="p-3">{u.full_name}</td>
                      <td className="p-3">{u.email}</td>
                      <td className="p-3">
                        <span className={`px-2 py-1 rounded text-sm ${u.role === 'admin' ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-700'}`}>
                          {u.role === 'admin' ? (language === 'ar' ? 'أدمن' : 'Admin') : (language === 'ar' ? 'مستخدم' : 'User')}
                        </span>
                      </td>
                      <td className="p-3">
                        {u.is_active !== false ? (
                          <CheckCircle className="w-5 h-5 text-green-600" />
                        ) : (
                          <XCircle className="w-5 h-5 text-red-600" />
                        )}
                      </td>
                      <td className="p-3">
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleToggleActive(u.id)}
                            disabled={u.id === user.id}
                          >
                            {u.is_active !== false ? 
                              (language === 'ar' ? 'تعطيل' : 'Disable') : 
                              (language === 'ar' ? 'تفعيل' : 'Enable')
                            }
                          </Button>
                          {u.id !== user.id && (
                            <Button
                              size="sm"
                              variant="destructive"
                              onClick={() => handleDeleteUser(u.id)}
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          )}
                        </div>
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

export default AdminDashboard;
