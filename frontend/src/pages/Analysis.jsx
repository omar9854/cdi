import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { ArrowRight, Loader2, Sparkles, FileDown, FileSpreadsheet, MessageSquare, AlertTriangle, HelpCircle, CheckCircle, XCircle } from 'lucide-react';
import Navbar from '@/components/Navbar';
import { useLanguage } from '@/contexts/LanguageContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const Analysis = ({ user, onLogout }) => {
  const { noteId } = useParams();
  const navigate = useNavigate();
  const { language, t } = useLanguage();
  const [note, setNote] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [aiProviders, setAiProviders] = useState([]);
  const [selectedProvider, setSelectedProvider] = useState('phi3');

  useEffect(() => {
    fetchNote();
    fetchAnalysis();
    fetchAIProviders();
  }, [noteId]);
  
  const fetchAIProviders = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/ai-providers`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAiProviders(response.data.providers || []);
      if (response.data.providers && response.data.providers.length > 0) {
        const savedProvider = localStorage.getItem('preferred_ai_provider');
        if (savedProvider && response.data.providers.some(p => p.id === savedProvider)) {
          setSelectedProvider(savedProvider);
        } else {
          setSelectedProvider(response.data.providers[0].id);
        }
      }
    } catch (error) {
      console.error('Failed to fetch AI providers:', error);
    }
  };

  const fetchNote = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/notes/${noteId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setNote(response.data);
    } catch (error) {
      toast.error(t('error'));
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

  const handleAnalyze = async (providerId = null) => {
    const provider = providerId || selectedProvider;
    
    setAnalyzing(true);
    
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API}/analyze`,
        { 
          note_id: noteId,
          ai_provider: provider
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setAnalysis(response.data);
      
      localStorage.setItem('preferred_ai_provider', provider);
      
      toast.success(
        language === 'ar' ? 
        `تم التحليل بنجاح باستخدام ${aiProviders.find(p => p.id === provider)?.name_ar || provider}` :
        `Analysis completed using ${aiProviders.find(p => p.id === provider)?.name || provider}`
      );
    } catch (error) {
      toast.error(error.response?.data?.detail || t('error'));
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
      
      toast.success(t('exportSuccess'));
    } catch (error) {
      toast.error(t('error'));
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#f0f9ff] via-[#e0f2fe] to-[#f0fdfa] flex items-center justify-center">
        <Loader2 className="w-12 h-12 text-cyan-600 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#f0f9ff] via-[#e0f2fe] to-[#f0fdfa]">
      <Navbar user={user} onLogout={onLogout} />
      
      <main className="container mx-auto px-4 py-8 max-w-6xl" data-testid="analysis-page">
        <div className="mb-6 fade-in">
          <Button variant="ghost" onClick={() => navigate('/dashboard')} className="mb-4 text-gray-800 hover:bg-gray-100" data-testid="back-button">
            {language === 'ar' ? <ArrowRight className="ml-2" /> : <ArrowRight className="mr-2" />}
            {t('back')}
          </Button>
          <h1 className="text-4xl font-bold text-gray-800 mb-2">{note?.title}</h1>
          <p className="text-cyan-600">{t('analysisOf')} {t('clinicalNotes')}</p>
        </div>

        {/* Doctor Notes */}
        <Card className="mb-6 fade-in bg-white/80 backdrop-blur-xl border-gray-200">
          <CardHeader>
            <CardTitle className="text-2xl text-gray-800">{t('clinicalNotes')}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4" data-testid="doctor-notes">
              {note?.doctor_notes?.map((dn, idx) => (
                <div key={idx} className="bg-white/60 p-4 rounded-lg border-r-4 border-cyan-500">
                  <p className="font-semibold text-cyan-600 mb-2">
                    {note.doctor_notes[idx].specialty}
                  </p>
                  <pre className="whitespace-pre-wrap text-gray-700 font-sans">{dn.text}</pre>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Analyze Button */}
        {!analysis && (
          <Card className="mb-6 fade-in bg-white/80 backdrop-blur-xl border-gray-200">
            <CardContent className="text-center py-8">
              <Sparkles className="w-16 h-16 text-cyan-600 mx-auto mb-4" />
              <h3 className="text-2xl font-semibold text-gray-800 mb-2">{t('readyToAnalyze')}</h3>
              <p className="text-gray-800/70 mb-4">{t('aiAnalysisDescription')}</p>
              
              <div className="mb-6 inline-flex items-center gap-2 bg-gradient-to-r from-cyan-500/20 to-blue-500/20 px-4 py-2 rounded-full border border-cyan-500/30">
                <span className="text-2xl">🏥</span>
                <span className="font-semibold text-cyan-600">
                  {language === 'ar' ? 'Qwen2.5-32B الطبي المتخصص' : 'Qwen2.5-32B Medical AI'}
                </span>
                <span className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded-full border border-green-500/30">
                  {language === 'ar' ? 'محلي 100%' : '100% Local'}
                </span>
              </div>
              
              <Button
                onClick={() => handleAnalyze()}
                disabled={analyzing}
                className="bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-gray-800 text-lg py-6 px-8"
                data-testid="analyze-button"
              >
                {analyzing ? (
                  <>
                    {language === 'ar' ? <Loader2 className="ml-2 animate-spin" /> : <Loader2 className="mr-2 animate-spin" />}
                    {t('analyzing')}
                  </>
                ) : (
                  <>
                    {language === 'ar' ? <Sparkles className="ml-2" /> : <Sparkles className="mr-2" />}
                    {t('analyzeWithAI')}
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Analysis Results */}
        {analysis && (
          <div className="space-y-6 fade-in">
            {/* Action Buttons */}
            <div className="flex gap-4 justify-end flex-wrap">
              <Button 
                onClick={() => navigate(`/chat/${analysis.id}`)} 
                className="bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-gray-800"
                data-testid="chat-button"
              >
                {language === 'ar' ? <MessageSquare className="ml-2" /> : <MessageSquare className="mr-2" />}
                {t('discussWithAI')}
              </Button>
              <Button onClick={() => handleExport('pdf')} variant="outline" className="border-gray-300 text-gray-800 hover:bg-gray-100" data-testid="export-pdf-button">
                {language === 'ar' ? <FileDown className="ml-2" /> : <FileDown className="mr-2" />}
                {t('exportPDF')}
              </Button>
              <Button onClick={() => handleExport('excel')} variant="outline" className="border-gray-300 text-gray-800 hover:bg-gray-100" data-testid="export-excel-button">
                {language === 'ar' ? <FileSpreadsheet className="ml-2" /> : <FileSpreadsheet className="mr-2" />}
                {t('exportExcel')}
              </Button>
            </div>

            {/* Principal Diagnosis */}
            {analysis.principal_diagnosis && (
              <Card className="bg-gradient-to-r from-blue-600/20 to-cyan-600/20 backdrop-blur-xl border-blue-500/30">
                <CardHeader>
                  <CardTitle className="text-2xl text-blue-600 flex items-center gap-2">
                    <CheckCircle className="w-6 h-6" />
                    {language === 'ar' ? 'التشخيص الرئيسي' : 'Principal Diagnosis'}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="bg-white/60 p-4 rounded-lg">
                    <div className="flex justify-between items-start gap-4">
                      <div className="flex-1">
                        <p className="text-gray-800 font-medium text-lg mb-1">
                          {language === 'ar' ? analysis.principal_diagnosis.diagnosis_ar : analysis.principal_diagnosis.diagnosis_en}
                        </p>
                        <p className="text-gray-800/60 text-sm">
                          {language === 'ar' ? analysis.principal_diagnosis.diagnosis_en : analysis.principal_diagnosis.diagnosis_ar}
                        </p>
                      </div>
                      <span className="bg-blue-500 text-gray-800 px-3 py-1 rounded-full text-sm font-semibold">
                        {analysis.principal_diagnosis.icd_code}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Diagnoses to Document */}
            {analysis.diagnoses_to_document && analysis.diagnoses_to_document.length > 0 && (
              <Card className="bg-white/80 backdrop-blur-xl border-gray-200">
                <CardHeader>
                  <CardTitle className="text-2xl text-cyan-600 flex items-center gap-2">
                    <Sparkles className="w-6 h-6" />
                    {language === 'ar' ? 'التشخيصات المستنتجة للتوثيق' : 'Diagnoses to Document'}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3" data-testid="diagnoses-to-document">
                    {analysis.diagnoses_to_document.map((diag, idx) => (
                      <div key={idx} className="bg-white/60 p-4 rounded-lg border-r-4 border-cyan-500">
                        <div className="flex justify-between items-start gap-4">
                          <div className="flex-1">
                            <p className="text-gray-800 font-medium mb-1">
                              {language === 'ar' ? diag.diagnosis_ar : diag.diagnosis_en}
                            </p>
                            <p className="text-gray-800/60 text-sm">
                              {language === 'ar' ? diag.diagnosis_en : diag.diagnosis_ar}
                            </p>
                          </div>
                          <span className="bg-cyan-500 text-gray-800 px-3 py-1 rounded-full text-sm font-semibold whitespace-nowrap">
                            {diag.icd_code}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Secondary Diagnoses */}
            {analysis.secondary_diagnoses && analysis.secondary_diagnoses.length > 0 && (
              <Card className="bg-white/80 backdrop-blur-xl border-gray-200">
                <CardHeader>
                  <CardTitle className="text-2xl text-purple-300 flex items-center gap-2">
                    <CheckCircle className="w-6 h-6" />
                    {language === 'ar' ? 'التشخيصات الثانوية' : 'Secondary Diagnoses'}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {analysis.secondary_diagnoses.map((diag, idx) => (
                      <div key={idx} className="bg-white/60 p-4 rounded-lg border-r-4 border-purple-500">
                        <div className="flex justify-between items-start gap-4">
                          <div className="flex-1">
                            <p className="text-gray-800 font-medium mb-1">
                              {language === 'ar' ? diag.diagnosis_ar : diag.diagnosis_en}
                            </p>
                            <p className="text-gray-800/60 text-sm">
                              {language === 'ar' ? diag.diagnosis_en : diag.diagnosis_ar}
                            </p>
                          </div>
                          <span className="bg-purple-500 text-gray-800 px-3 py-1 rounded-full text-sm font-semibold whitespace-nowrap">
                            {diag.icd_code}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Missing Documentation */}
            {analysis.missing_documentation && analysis.missing_documentation.length > 0 && (
              <Card className="bg-gradient-to-r from-orange-600/20 to-amber-600/20 backdrop-blur-xl border-orange-500/30">
                <CardHeader>
                  <CardTitle className="text-2xl text-orange-600 flex items-center gap-2">
                    <XCircle className="w-6 h-6" />
                    {language === 'ar' ? 'النواقص في التوثيق' : 'Missing Documentation'}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3" data-testid="missing-documentation">
                    {analysis.missing_documentation.map((item, idx) => (
                      <div key={idx} className="bg-white/60 p-4 rounded-lg border-r-4 border-orange-500">
                        <p className="text-gray-800 font-medium">
                          {item.diagnosis}
                        </p>
                        <p className="text-orange-600 text-sm mt-1">
                          {language === 'ar' ? item.description_ar : item.description_en}
                        </p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Gaps */}
            {((language === 'ar' ? analysis.gaps_ar : analysis.gaps_en) || []).length > 0 && (
              <Card className="bg-gradient-to-r from-amber-600/20 to-yellow-600/20 backdrop-blur-xl border-amber-500/30">
                <CardHeader>
                  <CardTitle className="text-2xl text-amber-600 flex items-center gap-2">
                    <AlertTriangle className="w-6 h-6" />
                    {language === 'ar' ? 'الفجوات في التوثيق' : 'Documentation Gaps'}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3" data-testid="gaps">
                    {(language === 'ar' ? analysis.gaps_ar : analysis.gaps_en).map((gap, idx) => (
                      <div key={idx} className="bg-white/60 p-4 rounded-lg border-r-4 border-amber-500">
                        <p className="text-gray-800">{gap}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Queries for Doctor */}
            {((language === 'ar' ? analysis.queries_ar : analysis.queries_en) || []).length > 0 && (
              <Card className="bg-gradient-to-r from-green-600/20 to-emerald-600/20 backdrop-blur-xl border-green-500/30">
                <CardHeader>
                  <CardTitle className="text-2xl text-green-600 flex items-center gap-2">
                    <HelpCircle className="w-6 h-6" />
                    {language === 'ar' ? 'استفسارات للطبيب' : 'Queries for Doctor'}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3" data-testid="queries">
                    {(language === 'ar' ? analysis.queries_ar : analysis.queries_en).map((query, idx) => (
                      <div key={idx} className="bg-white/60 p-4 rounded-lg border-r-4 border-green-500">
                        <p className="text-gray-800">{query}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Recommendations */}
            {analysis.recommendations_ar && analysis.recommendations_ar.length > 0 && (
              <Card className="bg-white/80 backdrop-blur-xl border-gray-200">
                <CardHeader>
                  <CardTitle className="text-2xl text-purple-300">{t('recommendations')}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3" data-testid="recommendations">
                    {(language === 'ar' ? analysis.recommendations_ar : analysis.recommendations_en).map((rec, idx) => (
                      <div key={idx} className="bg-purple-500/10 p-4 rounded-lg border-r-4 border-purple-500">
                        <p className="text-gray-800">{rec}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Full Analysis Summary */}
            {(analysis.summary_ar || analysis.summary_en) && (
              <Card className="bg-white/80 backdrop-blur-xl border-gray-200">
                <CardHeader>
                  <CardTitle className="text-2xl text-gray-800">{t('comprehensiveSummary')}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="bg-white/60 p-6 rounded-lg" data-testid="full-analysis">
                    <p className="text-gray-700 whitespace-pre-wrap">
                      {language === 'ar' ? analysis.summary_ar : analysis.summary_en}
                    </p>
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
