import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { ArrowRight, Loader2, FileText } from 'lucide-react';
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';
import { useLanguage } from '@/contexts/LanguageContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const History = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const { language, t } = useLanguage();
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

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
                  <CardTitle className="text-xl text-gray-800">{item.note_title}</CardTitle>
                  <p className="text-sm text-gray-500">{formatDate(item.created_at)}</p>
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
          </div>
        )}
      </main>
    </div>
  );
};

export default History;