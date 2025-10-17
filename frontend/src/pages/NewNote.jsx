import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { Save, ArrowRight } from 'lucide-react';
import Navbar from '@/components/Navbar';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const NewNote = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({ title: '', notes_text: '' });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API}/notes`,
        formData,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      toast.success('تم حفظ الملاحظة بنجاح!');
      navigate(`/analysis/${response.data.id}`);
    } catch (error) {
      toast.error('فشل حفظ الملاحظة');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <Navbar user={user} onLogout={onLogout} />
      
      <main className="container mx-auto px-4 py-8 max-w-4xl" data-testid="new-note-page">
        <div className="mb-6 fade-in">
          <Button variant="ghost" onClick={() => navigate('/dashboard')} className="mb-4" data-testid="back-button">
            <ArrowRight className="ml-2" /> العودة
          </Button>
          <h1 className="text-4xl font-bold text-gray-800">ملاحظة سريرية جديدة</h1>
        </div>

        <Card className="medical-card fade-in">
          <CardHeader>
            <CardTitle className="text-2xl">أدخل تفاصيل الملاحظة السريرية</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="title" className="text-lg">عنوان الملاحظة</Label>
                <Input
                  id="title"
                  type="text"
                  placeholder="مثال: ملاحظات المريض - أحمد محمد"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  required
                  className="text-lg py-6"
                  data-testid="note-title-input"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="notes_text" className="text-lg">الملاحظات السريرية</Label>
                <Textarea
                  id="notes_text"
                  placeholder="الصق هنا الملاحظات السريرية المرقمة والمرتبة...&#10;&#10;مثال:&#10;1. المريض يعاني من ارتفاع ضغط الدم&#10;2. تم إجراء فحص الدم الشامل&#10;3. النتائج أظهرت..."
                  value={formData.notes_text}
                  onChange={(e) => setFormData({ ...formData, notes_text: e.target.value })}
                  required
                  rows={15}
                  className="text-lg"
                  data-testid="note-text-input"
                />
                <p className="text-sm text-gray-500">يمكنك نسخ ولصق الملاحظات السريرية هنا. تأكد من إزالة أي معلومات شخصية للمرضى.</p>
              </div>

              <div className="flex gap-4">
                <Button
                  type="submit"
                  className="flex-1 medical-blue text-white py-6 text-lg font-semibold"
                  disabled={loading}
                  data-testid="save-note-button"
                >
                  {loading ? 'جاري الحفظ...' : (
                    <>
                      <Save className="ml-2" /> حفظ ومتابعة للتحليل
                    </>
                  )}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </main>
    </div>
  );
};

export default NewNote;