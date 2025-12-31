import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { toast } from 'sonner';
import { ArrowRight, Loader2, FileText, Edit, Trash2 } from 'lucide-react';
import Navbar from '@/components/Navbar';
import { useLanguage } from '@/contexts/LanguageContext';
import Footer from '@/components/Footer';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const History = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const { language, t } = useLanguage();
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [noteToDelete, setNoteToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/history`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setHistory(response.data);
    } catch (error) {
      toast.error(t('error'));
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

  const handleEdit = (e, noteId) => {
    e.stopPropagation(); // Prevent card click
    navigate(`/edit-note/${noteId}`);
  };

  const handleDeleteClick = (e, item) => {
    e.stopPropagation(); // Prevent card click
    setNoteToDelete(item);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = async () => {
    if (!noteToDelete) return;
    
    setDeleting(true);
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API}/notes/${noteToDelete.note_id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success(language === 'ar' ? 'تم حذف الملاحظة بنجاح' : 'Note deleted successfully');
      setDeleteDialogOpen(false);
      setNoteToDelete(null);
      fetchHistory(); // Refresh list
    } catch (error) {
      toast.error(language === 'ar' ? 'فشل حذف الملاحظة' : 'Failed to delete note');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <Navbar user={user} onLogout={onLogout} />
      
      <main className="container mx-auto px-4 py-8 max-w-6xl" data-testid="history-page">
        <div className="mb-6 fade-in">
          <Button variant="ghost" onClick={() => navigate('/dashboard')} className="mb-4" data-testid="back-button">
            {language === 'ar' ? <ArrowRight className="ml-2" /> : <ArrowRight className="mr-2" />}
            {t('back')}
          </Button>
          <h1 className="text-4xl font-bold text-gray-800">{t('analysisHistory')}</h1>
          <p className="text-gray-600 mt-2">{t('allPreviousAnalyses')}</p>
        </div>

        {loading ? (
          <div className="flex justify-center items-center py-12">
            <Loader2 className="w-12 h-12 text-blue-600 animate-spin" />
          </div>
        ) : history.length === 0 ? (
          <Card className="medical-card fade-in">
            <CardContent className="text-center py-12">
              <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 text-lg">{t('noHistory')}</p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4 fade-in">
            {history.map((item) => (
              <Card
                key={item.id}
                className="medical-card card-hover cursor-pointer"
                onClick={() => navigate(`/analysis/${item.note_id}`)}
                data-testid={`history-item-${item.id}`}
              >
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <CardTitle className="text-xl text-gray-800">{item.note_title}</CardTitle>
                      <p className="text-sm text-gray-500">{formatDate(item.created_at)}</p>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={(e) => handleEdit(e, item.note_id)}
                        className="text-blue-600 hover:bg-blue-50 border-blue-300"
                        data-testid={`edit-note-${item.id}`}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={(e) => handleDeleteClick(e, item)}
                        className="text-red-600 hover:bg-red-50 border-red-300"
                        data-testid={`delete-note-${item.id}`}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm font-semibold text-blue-700 mb-1">
                        {language === 'ar' ? 'التشخيصات الموثقة' : 'Documented Diagnoses'}
                      </p>
                      <p className="text-gray-700">
                        {item.diagnoses_to_document?.length || 0} {t('diagnoses')}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-orange-700 mb-1">
                        {language === 'ar' ? 'التوثيق الناقص' : 'Missing Documentation'}
                      </p>
                      <p className="text-gray-700">
                        {item.missing_documentation?.length || 0} {language === 'ar' ? 'عنصر' : 'items'}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-amber-700 mb-1">
                        {language === 'ar' ? 'الثغرات' : 'Gaps'}
                      </p>
                      <p className="text-gray-700">
                        {(item.gaps_ar?.length || item.gaps_en?.length || 0)} {t('gaps')}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-green-700 mb-1">
                        {language === 'ar' ? 'الاستفسارات' : 'Queries'}
                      </p>
                      <p className="text-gray-700">
                        {(item.queries_ar?.length || item.queries_en?.length || 0)} {t('queries')}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
            
            {/* زر إضافة ملاحظة جديدة */}
            <div className="mt-8 flex justify-center">
              <Button
                onClick={() => navigate('/new-note')}
                className="medical-blue text-white px-8 py-6 text-lg font-semibold"
                data-testid="add-new-note-button"
              >
                <FileText className={language === 'ar' ? 'ml-2' : 'mr-2'} />
                {t('newNote')}
              </Button>
            </div>
          </div>
        )}
      </main>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="text-red-600 flex items-center gap-2">
              <Trash2 className="h-5 w-5" />
              {language === 'ar' ? 'تأكيد الحذف' : 'Confirm Delete'}
            </DialogTitle>
            <DialogDescription className="text-base pt-4">
              {language === 'ar' ? (
                <>
                  <p className="font-semibold mb-2">هل أنت متأكد من حذف هذه الملاحظة؟</p>
                  <p className="text-gray-600">
                    سيتم حذف الملاحظة "{noteToDelete?.note_title}" وجميع التحليلات المرتبطة بها بشكل نهائي.
                  </p>
                  <p className="text-red-600 mt-2">لا يمكن التراجع عن هذا الإجراء.</p>
                </>
              ) : (
                <>
                  <p className="font-semibold mb-2">Are you sure you want to delete this note?</p>
                  <p className="text-gray-600">
                    The note "{noteToDelete?.note_title}" and all its associated analyses will be permanently deleted.
                  </p>
                  <p className="text-red-600 mt-2">This action cannot be undone.</p>
                </>
              )}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="flex gap-2 sm:gap-2">
            <Button
              variant="outline"
              onClick={() => {
                setDeleteDialogOpen(false);
                setNoteToDelete(null);
              }}
              disabled={deleting}
              className="flex-1"
            >
              {language === 'ar' ? 'لا، إلغاء' : 'No, Cancel'}
            </Button>
            <Button
              onClick={confirmDelete}
              disabled={deleting}
              className="flex-1 bg-red-600 hover:bg-red-700"
            >
              {deleting ? (
                <>
                  <Loader2 className={`h-4 w-4 animate-spin ${language === 'ar' ? 'ml-2' : 'mr-2'}`} />
                  {language === 'ar' ? 'جاري الحذف...' : 'Deleting...'}
                </>
              ) : (
                <>
                  {language === 'ar' ? 'نعم، احذف' : 'Yes, Delete'}
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default History;