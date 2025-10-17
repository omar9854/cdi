import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { ArrowRight, Loader2, Sparkles, FileDown, FileSpreadsheet } from 'lucide-react';
import Navbar from '@/components/Navbar';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Analysis = ({ user, onLogout }) => {
  const { noteId } = useParams();
  const navigate = useNavigate();
  const [note, setNote] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => {
    fetchNote();
    fetchAnalysis();
  }, [noteId]);

  const fetchNote = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/notes/${noteId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setNote(response.data);
    } catch (error) {
      toast.error('فشل تحميل الملاحظة');
    }
  };

  const fetchAnalysis = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/analyses/${noteId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.data.length > 0) {
        setAnalysis(response.data[0]);
      }
    } catch (error) {
      // No analysis yet
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async () => {
    setAnalyzing(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API}/analyze`,
        { note_id: noteId },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setAnalysis(response.data);
      toast.success('تم التحليل بنجاح!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'فشل التحليل');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleExport = async (format) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${API}/export/${format}/${analysis.id}`,
        {
          headers: { Authorization: `Bearer ${token}` },
          responseType: 'blob'
        }
      );
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `analysis_${analysis.id}.${format === 'pdf' ? 'pdf' : 'xlsx'}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      toast.success('تم تصدير التحليل بنجاح!');
    } catch (error) {
      toast.error('فشل تصدير التحليل');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center">
        <Loader2 className="w-12 h-12 text-blue-600 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <Navbar user={user} onLogout={onLogout} />
      
      <main className="container mx-auto px-4 py-8 max-w-6xl" data-testid="analysis-page">
        <div className="mb-6 fade-in">
          <Button variant="ghost" onClick={() => navigate('/dashboard')} className="mb-4" data-testid="back-button">
            <ArrowRight className="ml-2" /> العودة
          </Button>
          <h1 className="text-4xl font-bold text-gray-800 mb-2">{note?.title}</h1>
          <p className="text-gray-600">تحليل الملاحظات السريرية</p>
        </div>

        {/* Note Content */}
        <Card className="medical-card mb-6 fade-in">
          <CardHeader>
            <CardTitle className="text-2xl">الملاحظات السريرية</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="bg-gray-50 p-6 rounded-lg" data-testid="note-content">
              <pre className="whitespace-pre-wrap text-gray-700 font-sans">{note?.notes_text}</pre>
            </div>
          </CardContent>
        </Card>

        {/* Analyze Button */}
        {!analysis && (
          <Card className="medical-card mb-6 fade-in">
            <CardContent className="text-center py-8">
              <Sparkles className="w-16 h-16 text-blue-600 mx-auto mb-4" />
              <h3 className="text-2xl font-semibold text-gray-800 mb-2">جاهز للتحليل</h3>
              <p className="text-gray-600 mb-6">استخدم الذكاء الاصطناعي لتحليل الملاحظات واستخراج أكواد ICD-10-CM</p>
              <Button
                onClick={handleAnalyze}
                disabled={analyzing}
                className="medical-blue text-lg py-6 px-8"
                data-testid="analyze-button"
              >
                {analyzing ? (
                  <>
                    <Loader2 className="ml-2 animate-spin" /> جاري التحليل...
                  </>
                ) : (
                  <>
                    <Sparkles className="ml-2" /> تحليل بالذكاء الاصطناعي
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Analysis Results */}
        {analysis && (
          <div className="space-y-6 fade-in">
            {/* Export Buttons */}
            <div className="flex gap-4 justify-end">
              <Button onClick={() => handleExport('pdf')} variant="outline" data-testid="export-pdf-button">
                <FileDown className="ml-2" /> تصدير PDF
              </Button>
              <Button onClick={() => handleExport('excel')} variant="outline" data-testid="export-excel-button">
                <FileSpreadsheet className="ml-2" /> تصدير Excel
              </Button>
            </div>

            {/* Primary Diagnoses */}
            <Card className="medical-card">
              <CardHeader>
                <CardTitle className="text-2xl text-blue-700">التشخيصات الرئيسية</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3" data-testid="primary-diagnoses">
                  {analysis.primary_diagnoses.map((diag, idx) => (
                    <div key={idx} className="diagnosis-card p-4 rounded-lg">
                      <div className="flex justify-between items-start">
                        <p className="text-gray-800 font-medium">{diag.diagnosis}</p>
                        <span className="bg-blue-600 text-white px-3 py-1 rounded-full text-sm font-semibold">
                          {diag.icd_code}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Secondary Diagnoses */}
            <Card className="medical-card">
              <CardHeader>
                <CardTitle className="text-2xl text-indigo-700">التشخيصات الثانوية</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3" data-testid="secondary-diagnoses">
                  {analysis.secondary_diagnoses.map((diag, idx) => (
                    <div key={idx} className="diagnosis-card p-4 rounded-lg">
                      <div className="flex justify-between items-start">
                        <p className="text-gray-800 font-medium">{diag.diagnosis}</p>
                        <span className="bg-indigo-600 text-white px-3 py-1 rounded-full text-sm font-semibold">
                          {diag.icd_code}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Gaps */}
            <Card className="medical-card">
              <CardHeader>
                <CardTitle className="text-2xl text-amber-700">الثغرات في التوثيق</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3" data-testid="gaps">
                  {analysis.gaps.map((gap, idx) => (
                    <div key={idx} className="gap-card p-4 rounded-lg">
                      <p className="text-gray-800">{gap}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Queries for Doctor */}
            <Card className="medical-card">
              <CardHeader>
                <CardTitle className="text-2xl text-green-700">استفسارات للطبيب</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3" data-testid="queries">
                  {analysis.queries_for_doctor.map((query, idx) => (
                    <div key={idx} className="query-card p-4 rounded-lg">
                      <p className="text-gray-800">{query}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Full Analysis Summary */}
            {analysis.full_analysis && (
              <Card className="medical-card">
                <CardHeader>
                  <CardTitle className="text-2xl text-gray-800">الملخص الشامل</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="bg-gray-50 p-6 rounded-lg" data-testid="full-analysis">
                    <p className="text-gray-700 whitespace-pre-wrap">{analysis.full_analysis}</p>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </main>
    </div>
  );
};

export default Analysis;