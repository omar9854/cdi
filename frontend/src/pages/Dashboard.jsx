import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { FileText, Plus, History, LogOut, Loader2 } from 'lucide-react';
import Navbar from '@/components/Navbar';
import { useLanguage } from '@/contexts/LanguageContext';
import Footer from '@/components/Footer';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Dashboard = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const { language, t } = useLanguage();
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchNotes();
  }, []);

  const fetchNotes = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/notes`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setNotes(response.data);
    } catch (error) {
      toast.error('فشل تحميل الملاحظات');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ar-SA', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <Navbar user={user} onLogout={onLogout} />
      
      <main className="container mx-auto px-4 py-8 max-w-7xl" data-testid="dashboard-main">
        {/* Header */}
        <div className="mb-8 fade-in">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">لوحة التحكم</h1>
          <p className="text-gray-600 text-lg">مرحباً بك، {user.full_name}</p>
        </div>

        {/* Action Cards */}
        <div className="grid md:grid-cols-2 gap-6 mb-8 fade-in">
          <Card className="medical-card card-hover cursor-pointer" onClick={() => navigate('/new-note')} data-testid="new-note-card">
            <CardContent className="flex items-center gap-4 p-6">
              <div className="w-14 h-14 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center">
                <Plus className="w-7 h-7 text-white" />
              </div>
              <div>
                <h3 className="text-xl font-semibold text-gray-800">ملاحظة جديدة</h3>
                <p className="text-gray-600">أضف ملاحظات سريرية جديدة للتحليل</p>
              </div>
            </CardContent>
          </Card>

          <Card className="medical-card card-hover cursor-pointer" onClick={() => navigate('/history')} data-testid="history-card">
            <CardContent className="flex items-center gap-4 p-6">
              <div className="w-14 h-14 bg-gradient-to-br from-green-600 to-emerald-600 rounded-xl flex items-center justify-center">
                <History className="w-7 h-7 text-white" />
              </div>
              <div>
                <h3 className="text-xl font-semibold text-gray-800">السجل</h3>
                <p className="text-gray-600">عرض جميع التحليلات السابقة</p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Recent Notes */}
        <div className="fade-in">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">الملاحظات الأخيرة</h2>
          
          {loading ? (
            <div className="flex justify-center items-center py-12">
              <Loader2 className="w-10 h-10 text-blue-600 animate-spin" />
            </div>
          ) : notes.length === 0 ? (
            <Card className="medical-card">
              <CardContent className="text-center py-12">
                <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 text-lg mb-4">لا توجد ملاحظات حتى الآن</p>
                <Button onClick={() => navigate('/new-note')} className="medical-blue" data-testid="create-first-note-button">
                  <Plus className="ml-2" /> إنشاء أول ملاحظة
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {notes.map((note) => (
                <Card
                  key={note.id}
                  className="medical-card card-hover cursor-pointer"
                  onClick={() => navigate(`/analysis/${note.id}`)}
                  data-testid={`note-card-${note.id}`}
                >
                  <CardHeader>
                    <CardTitle className="text-xl text-gray-800">{note.title}</CardTitle>
                    <p className="text-sm text-gray-500">{formatDate(note.created_at)}</p>
                  </CardHeader>
                  <CardContent>
                    <p className="text-gray-700 line-clamp-2">{note.notes_text}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default Dashboard;