import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { ArrowRight, Loader2, Sparkles, FileDown, FileSpreadsheet, MessageSquare, AlertTriangle, HelpCircle, CheckCircle, XCircle, Stethoscope, ClipboardList, TestTube, Pill, FileText, Info } from 'lucide-react';
import Navbar from '@/components/Navbar';
import { useLanguage } from '@/contexts/LanguageContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
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
      toast.error(language === 'ar' ? 'فشل في تحميل الملاحظة' : 'Failed to load note');
    }
  };

  const fetchAnalysis = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/analysis/${noteId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAnalysis(response.data);
    } catch (error) {
      console.log('No existing analysis');
    } finally {
      setLoading(false);
    }
  };

  const runAnalysis = async (providerId = null) => {
    setAnalyzing(true);
    try {
      const token = localStorage.getItem('token');
      const provider = providerId || selectedProvider;
      const response = await axios.post(
        `${API}/analyze`,
        { note_id: noteId, provider: provider },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setAnalysis(response.data);
      toast.success(language === 'ar' ? 'تم التحليل بنجاح' : 'Analysis completed');
    } catch (error) {
      toast.error(language === 'ar' ? 'فشل في التحليل' : 'Analysis failed');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleExport = async (format) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${API}/export/${noteId}/${format}`,
        {
          headers: { Authorization: `Bearer ${token}` },
          responseType: 'blob'
        }
      );
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `analysis_${noteId}.${format === 'pdf' ? 'pdf' : 'xlsx'}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      toast.error(language === 'ar' ? 'فشل التصدير' : 'Export failed');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#f0f9ff] via-[#e0f2fe] to-[#f0fdfa] flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-[#0066a1]" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#f0f9ff] via-[#e0f2fe] to-[#f0fdfa]">
      <Navbar user={user} onLogout={onLogout} />
      
      <main className="container mx-auto px-4 py-8" dir={language === 'ar' ? 'rtl' : 'ltr'}>
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <Button 
            variant="ghost" 
            onClick={() => navigate('/dashboard')} 
            className="text-[#0066a1] hover:bg-[#0066a1]/10"
            data-testid="back-to-dashboard"
          >
            {language === 'ar' ? <ArrowRight className="ml-2" /> : <ArrowRight className="mr-2 rotate-180" />}
            {language === 'ar' ? 'العودة للوحة التحكم' : 'Back to Dashboard'}
          </Button>
          
          <Button
            onClick={() => navigate(`/chat/${noteId}`)}
            className="bg-[#00a99d] hover:bg-[#008577] text-white"
            data-testid="discuss-case-button"
          >
            <MessageSquare className={language === 'ar' ? 'ml-2' : 'mr-2'} />
            {language === 'ar' ? 'مناقشة الحالة' : 'Discuss Case'}
          </Button>
        </div>

        {/* Note Title */}
        {note && (
          <Card className="mb-6 bg-white/80 backdrop-blur-xl border-[#0066a1]/20">
            <CardHeader>
              <CardTitle className="text-2xl text-[#0066a1]" data-testid="note-title">
                {note.title}
              </CardTitle>
            </CardHeader>
          </Card>
        )}

        {/* Run Analysis Button */}
        {!analysis && (
          <Card className="mb-6 bg-white/80 backdrop-blur-xl border-[#00a99d]/20">
            <CardContent className="p-6">
              <div className="text-center">
                <p className="text-gray-600 mb-4">
                  {language === 'ar' ? 'لم يتم تحليل هذه الملاحظة بعد' : 'This note has not been analyzed yet'}
                </p>
                <Button
                  onClick={() => runAnalysis()}
                  disabled={analyzing}
                  className="bg-[#0066a1] hover:bg-[#005080] text-white"
                  data-testid="run-analysis-button"
                >
                  {analyzing ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin ml-2" />
                      {language === 'ar' ? 'جاري التحليل...' : 'Analyzing...'}
                    </>
                  ) : (
                    <>
                      <Sparkles className={language === 'ar' ? 'ml-2' : 'mr-2'} />
                      {language === 'ar' ? 'بدء التحليل' : 'Run Analysis'}
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Analysis Results */}
        {analysis && (
          <div className="space-y-6">
            {/* Export Buttons */}
            <div className="flex gap-4 justify-end">
              <Button onClick={() => runAnalysis()} disabled={analyzing} variant="outline" className="border-[#0066a1] text-[#0066a1] hover:bg-[#0066a1]/10">
                {analyzing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className={language === 'ar' ? 'ml-2' : 'mr-2'} />}
                {language === 'ar' ? 'إعادة التحليل' : 'Re-analyze'}
              </Button>
              <Button onClick={() => handleExport('pdf')} variant="outline" className="border-gray-300 text-gray-700 hover:bg-gray-100" data-testid="export-pdf-button">
                <FileDown className={language === 'ar' ? 'ml-2' : 'mr-2'} />
                {t('exportPDF')}
              </Button>
              <Button onClick={() => handleExport('excel')} variant="outline" className="border-gray-300 text-gray-700 hover:bg-gray-100" data-testid="export-excel-button">
                <FileSpreadsheet className={language === 'ar' ? 'ml-2' : 'mr-2'} />
                {t('exportExcel')}
              </Button>
            </div>

            {/* ============ 1. التشخيص الرئيسي ============ */}
            {analysis.principal_diagnosis && analysis.principal_diagnosis.diagnosis_ar && (
              <Card className="bg-gradient-to-r from-blue-50 to-cyan-50 border-2 border-blue-400 shadow-lg">
                <CardHeader className="bg-blue-500/10 border-b border-blue-200">
                  <CardTitle className="text-2xl text-blue-700 flex items-center gap-3">
                    <div className="bg-blue-500 p-2 rounded-full">
                      <Stethoscope className="w-6 h-6 text-white" />
                    </div>
                    {language === 'ar' ? 'التشخيص الرئيسي (Principal Diagnosis)' : 'Principal Diagnosis'}
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="flex justify-between items-start gap-4 mb-4">
                    <div className="flex-1">
                      <h3 className="text-xl font-bold text-gray-800 mb-1">
                        {analysis.principal_diagnosis.diagnosis_ar}
                      </h3>
                      <p className="text-gray-600 text-lg">
                        {analysis.principal_diagnosis.diagnosis_en}
                      </p>
                    </div>
                    <div className="text-right">
                      <span className="bg-blue-600 text-white px-4 py-2 rounded-lg text-lg font-bold inline-block">
                        {analysis.principal_diagnosis.icd_code}
                      </span>
                      {analysis.principal_diagnosis.drg_code && (
                        <p className="text-sm text-gray-500 mt-1">DRG: {analysis.principal_diagnosis.drg_code}</p>
                      )}
                    </div>
                  </div>
                  
                  {analysis.principal_diagnosis.evidence && (
                    <div className="bg-white/70 p-3 rounded-lg mb-3">
                      <p className="text-sm text-gray-500 mb-1">{language === 'ar' ? 'الدليل من النص:' : 'Evidence:'}</p>
                      <p className="text-gray-700 italic">"{analysis.principal_diagnosis.evidence}"</p>
                    </div>
                  )}
                  
                  {analysis.principal_diagnosis.missing_details && analysis.principal_diagnosis.missing_details.length > 0 && (
                    <div className="bg-amber-50 border border-amber-200 p-3 rounded-lg">
                      <p className="text-amber-700 font-medium mb-2 flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4" />
                        {language === 'ar' ? 'ما ينقص في التوثيق:' : 'Missing Documentation:'}
                      </p>
                      <ul className="list-disc list-inside text-amber-600 text-sm">
                        {analysis.principal_diagnosis.missing_details.map((detail, idx) => (
                          <li key={idx}>{detail}</li>
                        ))}
                      </ul>
                      {analysis.principal_diagnosis.missing_explanation && (
                        <p className="text-amber-600 text-sm mt-2 italic">{analysis.principal_diagnosis.missing_explanation}</p>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* ============ 2. التشخيصات الثانوية الموثقة ============ */}
            {analysis.secondary_diagnoses && analysis.secondary_diagnoses.length > 0 && (
              <Card className="bg-gradient-to-r from-purple-50 to-indigo-50 border-2 border-purple-400 shadow-lg">
                <CardHeader className="bg-purple-500/10 border-b border-purple-200">
                  <CardTitle className="text-2xl text-purple-700 flex items-center gap-3">
                    <div className="bg-purple-500 p-2 rounded-full">
                      <ClipboardList className="w-6 h-6 text-white" />
                    </div>
                    {language === 'ar' ? `التشخيصات الثانوية الموثقة (${analysis.secondary_diagnoses.length})` : `Secondary Diagnoses (${analysis.secondary_diagnoses.length})`}
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-4">
                    {analysis.secondary_diagnoses.map((diag, idx) => (
                      <div key={idx} className="bg-white/70 p-4 rounded-lg border-r-4 border-purple-500 shadow-sm hover:shadow-md transition-shadow">
                        <div className="flex justify-between items-start gap-4">
                          <div className="flex-1">
                            <h4 className="font-bold text-gray-800">{diag.diagnosis_ar}</h4>
                            <p className="text-gray-600 text-sm">{diag.diagnosis_en}</p>
                            {diag.evidence && (
                              <p className="text-gray-500 text-sm mt-1 italic">"{diag.evidence}"</p>
                            )}
                            {diag.category && (
                              <span className="inline-block bg-purple-100 text-purple-700 text-xs px-2 py-1 rounded mt-2">
                                {diag.category}
                              </span>
                            )}
                          </div>
                          <span className="bg-purple-600 text-white px-3 py-1 rounded-lg font-bold whitespace-nowrap">
                            {diag.icd_code}
                          </span>
                        </div>
                        {diag.missing_details && diag.missing_details.length > 0 && (
                          <div className="mt-3 bg-amber-50 p-2 rounded text-sm">
                            <span className="text-amber-600 font-medium">{language === 'ar' ? 'ينقص: ' : 'Missing: '}</span>
                            <span className="text-amber-600">{diag.missing_details.join('، ')}</span>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* ============ 3. التشخيصات المستنتجة ============ */}
            {analysis.inferred_diagnoses && analysis.inferred_diagnoses.length > 0 && (
              <Card className="bg-gradient-to-r from-cyan-50 to-teal-50 border-2 border-cyan-400 shadow-lg">
                <CardHeader className="bg-cyan-500/10 border-b border-cyan-200">
                  <CardTitle className="text-2xl text-cyan-700 flex items-center gap-3">
                    <div className="bg-cyan-500 p-2 rounded-full">
                      <Sparkles className="w-6 h-6 text-white" />
                    </div>
                    {language === 'ar' ? `التشخيصات المستنتجة - تحتاج توثيق (${analysis.inferred_diagnoses.length})` : `Inferred Diagnoses - Need Documentation (${analysis.inferred_diagnoses.length})`}
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-4">
                    {analysis.inferred_diagnoses.map((diag, idx) => (
                      <div key={idx} className="bg-white/70 p-4 rounded-lg border-r-4 border-cyan-500 shadow-sm">
                        <div className="flex justify-between items-start gap-4 mb-3">
                          <div className="flex-1">
                            <h4 className="font-bold text-gray-800">{diag.diagnosis_ar}</h4>
                            <p className="text-gray-600 text-sm">{diag.diagnosis_en}</p>
                          </div>
                          <span className="bg-cyan-600 text-white px-3 py-1 rounded-lg font-bold whitespace-nowrap">
                            {diag.icd_code}
                          </span>
                        </div>
                        
                        {/* سبب الاستنتاج */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
                          {diag.lab_result && (
                            <div className="bg-blue-50 p-3 rounded-lg">
                              <p className="text-blue-600 text-sm font-medium flex items-center gap-1">
                                <TestTube className="w-4 h-4" />
                                {language === 'ar' ? 'نتيجة التحليل:' : 'Lab Result:'}
                              </p>
                              <p className="text-blue-700">{diag.lab_result}</p>
                            </div>
                          )}
                          {diag.treatment_given && (
                            <div className="bg-green-50 p-3 rounded-lg">
                              <p className="text-green-600 text-sm font-medium flex items-center gap-1">
                                <Pill className="w-4 h-4" />
                                {language === 'ar' ? 'العلاج المقدم:' : 'Treatment Given:'}
                              </p>
                              <p className="text-green-700">{diag.treatment_given}</p>
                            </div>
                          )}
                        </div>
                        
                        {diag.reasoning && (
                          <div className="bg-gray-50 p-3 rounded-lg mb-3">
                            <p className="text-gray-600 text-sm font-medium">{language === 'ar' ? 'سبب الاستنتاج:' : 'Reasoning:'}</p>
                            <p className="text-gray-700">{diag.reasoning}</p>
                          </div>
                        )}
                        
                        {diag.clinical_significance && (
                          <div className="bg-amber-50 p-3 rounded-lg">
                            <p className="text-amber-600 text-sm font-medium flex items-center gap-1">
                              <Info className="w-4 h-4" />
                              {language === 'ar' ? 'الأهمية السريرية:' : 'Clinical Significance:'}
                            </p>
                            <p className="text-amber-700">{diag.clinical_significance}</p>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* ============ 4. الفجوات والنواقص ============ */}
            {analysis.documentation_gaps && analysis.documentation_gaps.length > 0 && (
              <Card className="bg-gradient-to-r from-orange-50 to-amber-50 border-2 border-orange-400 shadow-lg">
                <CardHeader className="bg-orange-500/10 border-b border-orange-200">
                  <CardTitle className="text-2xl text-orange-700 flex items-center gap-3">
                    <div className="bg-orange-500 p-2 rounded-full">
                      <AlertTriangle className="w-6 h-6 text-white" />
                    </div>
                    {language === 'ar' ? `الفجوات والنواقص في التوثيق (${analysis.documentation_gaps.length})` : `Documentation Gaps (${analysis.documentation_gaps.length})`}
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-4">
                    {analysis.documentation_gaps.map((gap, idx) => (
                      <div key={idx} className="bg-white/70 p-4 rounded-lg border-r-4 border-orange-500 shadow-sm">
                        <h4 className="font-bold text-gray-800 mb-2">{gap.diagnosis}</h4>
                        {gap.gap_type && (
                          <span className="inline-block bg-orange-100 text-orange-700 text-xs px-2 py-1 rounded mb-2">
                            {gap.gap_type}
                          </span>
                        )}
                        <p className="text-orange-700 mb-2">{gap.what_is_missing}</p>
                        {gap.why_important && (
                          <p className="text-gray-600 text-sm italic">{gap.why_important}</p>
                        )}
                        {gap.acs_reference && (
                          <p className="text-gray-500 text-sm mt-2">📋 {gap.acs_reference}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* ============ 5. الاستفسارات للطبيب ============ */}
            {((analysis.queries_ar && analysis.queries_ar.length > 0) || (analysis.physician_queries && analysis.physician_queries.length > 0)) && (
              <Card className="bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-400 shadow-lg">
                <CardHeader className="bg-green-500/10 border-b border-green-200">
                  <CardTitle className="text-2xl text-green-700 flex items-center gap-3">
                    <div className="bg-green-500 p-2 rounded-full">
                      <HelpCircle className="w-6 h-6 text-white" />
                    </div>
                    {language === 'ar' ? 'استفسارات للطبيب (Non-Leading Queries)' : 'Physician Queries'}
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-4">
                    {(analysis.physician_queries || []).map((query, idx) => (
                      <div key={idx} className="bg-white/70 p-4 rounded-lg border-r-4 border-green-500 shadow-sm">
                        {query.related_diagnosis && (
                          <span className="inline-block bg-green-100 text-green-700 text-xs px-2 py-1 rounded mb-2">
                            {query.related_diagnosis}
                          </span>
                        )}
                        <p className="text-gray-800">{language === 'ar' ? query.query_ar : query.query_en}</p>
                        {query.clinical_indicators && (
                          <p className="text-gray-500 text-sm mt-2 italic">{query.clinical_indicators}</p>
                        )}
                      </div>
                    ))}
                    {(analysis.queries_ar || []).filter(q => !analysis.physician_queries?.some(pq => pq.query_ar === q)).map((query, idx) => (
                      <div key={`q-${idx}`} className="bg-white/70 p-4 rounded-lg border-r-4 border-green-500 shadow-sm">
                        <p className="text-gray-800">{query}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* ============ 6. نبذة عن الحالة ============ */}
            {analysis.case_summary && (analysis.case_summary.summary_ar || analysis.summary_ar) && (
              <Card className="bg-gradient-to-r from-gray-50 to-slate-50 border-2 border-gray-400 shadow-lg">
                <CardHeader className="bg-gray-500/10 border-b border-gray-200">
                  <CardTitle className="text-2xl text-gray-700 flex items-center gap-3">
                    <div className="bg-gray-500 p-2 rounded-full">
                      <FileText className="w-6 h-6 text-white" />
                    </div>
                    {language === 'ar' ? 'نبذة عن الحالة (Case Summary)' : 'Case Summary'}
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  {analysis.case_summary.admission_reason && (
                    <div className="mb-4">
                      <h4 className="font-bold text-gray-700 mb-1">{language === 'ar' ? 'سبب الدخول:' : 'Admission Reason:'}</h4>
                      <p className="text-gray-600">{analysis.case_summary.admission_reason}</p>
                    </div>
                  )}
                  
                  {analysis.case_summary.patient_profile && (
                    <div className="mb-4">
                      <h4 className="font-bold text-gray-700 mb-1">{language === 'ar' ? 'وصف المريض:' : 'Patient Profile:'}</h4>
                      <p className="text-gray-600">{analysis.case_summary.patient_profile}</p>
                    </div>
                  )}
                  
                  {analysis.case_summary.current_problems && analysis.case_summary.current_problems.length > 0 && (
                    <div className="mb-4">
                      <h4 className="font-bold text-gray-700 mb-1">{language === 'ar' ? 'المشاكل الحالية:' : 'Current Problems:'}</h4>
                      <ul className="list-disc list-inside text-gray-600">
                        {analysis.case_summary.current_problems.map((prob, idx) => (
                          <li key={idx}>{prob}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  {analysis.case_summary.key_findings && analysis.case_summary.key_findings.length > 0 && (
                    <div className="mb-4">
                      <h4 className="font-bold text-gray-700 mb-1">{language === 'ar' ? 'النتائج الرئيسية:' : 'Key Findings:'}</h4>
                      <ul className="list-disc list-inside text-gray-600">
                        {analysis.case_summary.key_findings.map((finding, idx) => (
                          <li key={idx}>{finding}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  <div className="bg-white/70 p-4 rounded-lg mt-4">
                    <h4 className="font-bold text-gray-700 mb-2">{language === 'ar' ? 'الملخص:' : 'Summary:'}</h4>
                    <p className="text-gray-700 whitespace-pre-wrap">
                      {language === 'ar' ? (analysis.case_summary.summary_ar || analysis.summary_ar) : (analysis.case_summary.summary_en || analysis.summary_en)}
                    </p>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* ============ المعلومات الإضافية ============ */}
            {(analysis.clinical_indicators?.length > 0 || analysis.treatments_found?.length > 0) && (
              <Card className="bg-white/80 backdrop-blur-xl border-gray-200">
                <CardHeader>
                  <CardTitle className="text-xl text-gray-700">{language === 'ar' ? 'المعطيات السريرية المستخرجة' : 'Extracted Clinical Data'}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {analysis.clinical_indicators?.length > 0 && (
                      <div className="bg-blue-50 p-4 rounded-lg">
                        <h4 className="font-medium text-blue-700 mb-2 flex items-center gap-2">
                          <TestTube className="w-4 h-4" />
                          {language === 'ar' ? 'نتائج التحاليل:' : 'Lab Results:'}
                        </h4>
                        <div className="flex flex-wrap gap-2">
                          {analysis.clinical_indicators.map((indicator, idx) => (
                            <span key={idx} className="bg-blue-100 text-blue-700 px-2 py-1 rounded text-sm">{indicator}</span>
                          ))}
                        </div>
                      </div>
                    )}
                    {analysis.treatments_found?.length > 0 && (
                      <div className="bg-green-50 p-4 rounded-lg">
                        <h4 className="font-medium text-green-700 mb-2 flex items-center gap-2">
                          <Pill className="w-4 h-4" />
                          {language === 'ar' ? 'العلاجات:' : 'Treatments:'}
                        </h4>
                        <div className="flex flex-wrap gap-2">
                          {analysis.treatments_found.map((treatment, idx) => (
                            <span key={idx} className="bg-green-100 text-green-700 px-2 py-1 rounded text-sm">{treatment}</span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* ============ جودة التحليل ============ */}
            {analysis.analysis_quality && (
              <Card className="bg-white/80 backdrop-blur-xl border-gray-200">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between text-sm text-gray-600">
                    <span>{language === 'ar' ? 'التشخيصات الموثقة:' : 'Documented:'} <strong>{analysis.analysis_quality.documented_count || (1 + (analysis.secondary_diagnoses?.length || 0))}</strong></span>
                    <span>{language === 'ar' ? 'المستنتجة:' : 'Inferred:'} <strong>{analysis.analysis_quality.inferred_count || analysis.inferred_diagnoses?.length || 0}</strong></span>
                    <span>{language === 'ar' ? 'الفجوات:' : 'Gaps:'} <strong>{analysis.analysis_quality.gaps_count || analysis.documentation_gaps?.length || 0}</strong></span>
                    <span>{language === 'ar' ? 'الاستفسارات:' : 'Queries:'} <strong>{analysis.analysis_quality.queries_count || analysis.queries_ar?.length || 0}</strong></span>
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
