import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import { FileText, Search, Clock, CheckCircle, Sparkles, Calculator, Brain, TrendingUp, Award } from 'lucide-react';
import Navbar from '@/components/Navbar';
import { useLanguage } from '@/contexts/LanguageContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CoderWorkspacePro = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const { language } = useLanguage();
  const [cases, setCases] = useState([]);
  const [selectedCase, setSelectedCase] = useState(null);
  const [icdCodes, setIcdCodes] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [aiAnalysis, setAiAnalysis] = useState(null);
  const [loadingAI, setLoadingAI] = useState(false);
  const [coding, setCoding] = useState({
    principal_diagnosis: null,
    secondary_diagnoses: [],
    drg_code: '',
    drg_description: '',
    financial_value: 0
  });
  const [myStats, setMyStats] = useState(null);
  const [completedCases, setCompletedCases] = useState([]);

  useEffect(() => {
    if (user?.department !== 'coding' || user?.coding_role !== 'coder') {
      navigate('/dashboard');
      return;
    }
    fetchMyCases();
    fetchMyStats();
  }, [user]);

  const fetchMyCases = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await axios.get(`${API}/coding/my-cases?user_id=${user.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const allCases = res.data.cases || [];
      setCases(allCases.filter(c => c.status !== 'completed'));
      setCompletedCases(allCases.filter(c => c.status === 'completed'));
    } catch (error) {
      toast.error('Failed to load cases');
    }
  };

  const fetchMyStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await axios.get(`${API}/coding/stats/coders`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const allStats = res.data.coders || [];
      const myStat = allStats.find(s => s.user_id === user.id);
      setMyStats(myStat);
    } catch (error) {
      console.error(error);
    }
  };

  const searchICDCodes = async (term) => {
    if (!term || term.length < 2) return;
    try {
      const token = localStorage.getItem('token');
      const res = await axios.get(`${API}/coding/icd-codes?search=${term}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setIcdCodes(res.data.codes || []);
    } catch (error) {
      console.error(error);
    }
  };

  const analyzeWithAI = async () => {
    if (!selectedCase) return;
    setLoadingAI(true);
    try {
      const token = localStorage.getItem('token');
      const res = await axios.post(
        `${API}/coding/ai/analyze-case?case_id=${selectedCase.id}`,
        {},
        { headers: { Authorization: `Bearer ${token}` }}
      );
      
      if (res.data.success) {
        setAiAnalysis(res.data.analysis);
        toast.success(language === 'ar' ? 'تم التحليل بنجاح' : 'Analysis complete');
      } else {
        toast.error(res.data.error || 'Analysis failed');
      }
    } catch (error) {
      toast.error('AI analysis failed');
    } finally {
      setLoadingAI(false);
    }
  };

  const calculateDRG = async () => {
    if (!coding.principal_diagnosis) return;
    try {
      const token = localStorage.getItem('token');
      const secondary = coding.secondary_diagnoses.map(d => d.code);
      const res = await axios.post(
        `${API}/coding/ai/calculate-drg?principal_code=${coding.principal_diagnosis.code}&secondary_codes=${secondary.join(',')}`,
        {},
        { headers: { Authorization: `Bearer ${token}` }}
      );
      
      if (!res.data.error) {
        setCoding({
          ...coding,
          drg_code: res.data.drg_code,
          drg_description: res.data.description,
          financial_value: res.data.estimated_value
        });
        toast.success(language === 'ar' ? 'تم حساب DRG' : 'DRG calculated');
      }
    } catch (error) {
      console.error(error);
    }
  };

  const useAISuggestion = (suggestion) => {
    if (suggestion.principal_diagnosis) {
      setCoding({
        ...coding,
        principal_diagnosis: {
          code: suggestion.principal_diagnosis.code,
          description: suggestion.principal_diagnosis.description,
          is_principal: true
        }
      });
    }
    
    if (suggestion.secondary_diagnoses) {
      const secondary = suggestion.secondary_diagnoses.map(d => ({
        code: d.code,
        description: d.description,
        is_principal: false,
        is_complication: d.is_complication
      }));
      setCoding({...coding, secondary_diagnoses: secondary});
    }
    
    if (suggestion.suggested_drg) {
      setCoding({...coding, drg_code: suggestion.suggested_drg});
    }
    
    toast.success(language === 'ar' ? 'تم تطبيق الاقتراحات' : 'Suggestions applied');
  };

  const startCoding = async (caseId) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/coding/cases/${caseId}/start?user_id=${user.id}`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const caseData = cases.find(c => c.id === caseId);
      setSelectedCase(caseData);
      setAiAnalysis(null);
      toast.success(language === 'ar' ? 'تم بدء الترميز' : 'Coding started');
    } catch (error) {
      toast.error('Failed to start');
    }
  };

  const submitCoding = async () => {
    if (!coding.principal_diagnosis) {
      toast.error(language === 'ar' ? 'اختر التشخيص الرئيسي' : 'Select principal diagnosis');
      return;
    }
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/coding/cases/${selectedCase.id}/submit?user_id=${user.id}`, {
        case_id: selectedCase.id,
        ...coding
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(language === 'ar' ? 'تم إرسال الترميز بنجاح' : 'Coding submitted successfully');
      setSelectedCase(null);
      setAiAnalysis(null);
      setCoding({ principal_diagnosis: null, secondary_diagnoses: [], drg_code: '', drg_description: '', financial_value: 0 });
      fetchMyCases();
      fetchMyStats();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar user={user} onLogout={onLogout} />
      <main className="max-w-7xl mx-auto p-6">
        <h1 className="text-3xl font-bold mb-6">
          {language === 'ar' ? 'منصة المرمز الطبي - مدعومة بالذكاء الاصطناعي' : 'Medical Coder Workspace - AI Powered'}
        </h1>

        {/* My Stats */}
        {myStats && !selectedCase && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <Card className="bg-blue-50">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm text-gray-600">{language === 'ar' ? 'اليوم' : 'Today'}</div>
                    <div className="text-2xl font-bold">{myStats.completed_today}/{myStats.daily_target}</div>
                  </div>
                  <Award className="h-8 w-8 text-blue-600" />
                </div>
              </CardContent>
            </Card>
            <Card className="bg-green-50">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm text-gray-600">{language === 'ar' ? 'معدل الإنجاز' : 'Completion Rate'}</div>
                    <div className="text-2xl font-bold">{myStats.completion_rate.toFixed(1)}%</div>
                  </div>
                  <TrendingUp className="h-8 w-8 text-green-600" />
                </div>
              </CardContent>
            </Card>
            <Card className="bg-purple-50">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm text-gray-600">{language === 'ar' ? 'متوسط الوقت' : 'Avg Time'}</div>
                    <div className="text-2xl font-bold">{myStats.avg_coding_time} {language === 'ar' ? 'د' : 'min'}</div>
                  </div>
                  <Clock className="h-8 w-8 text-purple-600" />
                </div>
              </CardContent>
            </Card>
            <Card className="bg-amber-50">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm text-gray-600">{language === 'ar' ? 'إجمالي الحالات' : 'Total Cases'}</div>
                    <div className="text-2xl font-bold">{myStats.total_cases}</div>
                  </div>
                  <FileText className="h-8 w-8 text-amber-600" />
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {!selectedCase ? (
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  {language === 'ar' ? 'حالاتي المعلقة' : 'My Pending Cases'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {cases.map(c => (
                    <div key={c.id} className="p-4 bg-white border rounded-lg hover:shadow-md transition">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="font-semibold text-lg">{c.case_number}</div>
                          <div className="text-sm text-gray-600 mt-1">{c.patient_id} - {c.chief_complaint}</div>
                          <div className="text-xs text-gray-500 mt-1">
                            {c.age} {language === 'ar' ? 'سنة' : 'years'} - {c.gender} | 
                            {language === 'ar' ? ' مدة التنويم: ' : ' LOS: '}
                            {Math.ceil((new Date(c.discharge_date) - new Date(c.admission_date)) / (1000 * 60 * 60 * 24))} {language === 'ar' ? 'أيام' : 'days'}
                          </div>
                        </div>
                        <Button onClick={() => startCoding(c.id)} className="bg-blue-600">
                          <Brain className="h-4 w-4 mr-2" />
                          {language === 'ar' ? 'بدء الترميز بمساعدة AI' : 'Start Coding with AI'}
                        </Button>
                      </div>
                    </div>
                  ))}
                  {cases.length === 0 && (
                    <div className="text-center py-8 text-gray-500">
                      {language === 'ar' ? 'لا توجد حالات معلقة' : 'No pending cases'}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Completed Cases */}
            {completedCases.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <CheckCircle className="h-5 w-5 text-green-600" />
                    {language === 'ar' ? 'الحالات المكتملة' : 'Completed Cases'}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {completedCases.slice(0, 5).map(c => (
                      <div key={c.id} className="p-3 bg-green-50 border border-green-200 rounded-lg">
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="font-semibold">{c.case_number}</div>
                            <div className="text-xs text-gray-600">DRG: {c.drg_code} - {c.financial_value?.toLocaleString()} SAR</div>
                          </div>
                          <div className="text-xs text-gray-500">
                            {c.coding_duration_minutes} {language === 'ar' ? 'دقيقة' : 'min'}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Case Details & AI Analysis */}
            <div className="lg:col-span-2 space-y-4">
              {/* Case Info */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>{selectedCase.case_number}</span>
                    <Button onClick={analyzeWithAI} disabled={loadingAI} size="sm" className="bg-purple-600">
                      <Sparkles className="h-4 w-4 mr-2" />
                      {loadingAI ? (language === 'ar' ? 'جاري التحليل...' : 'Analyzing...') : (language === 'ar' ? 'تحليل بالذكاء الاصطناعي' : 'AI Analysis')}
                    </Button>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">{language === 'ar' ? 'رقم المريض:' : 'Patient ID:'}</span>
                      <span className="font-semibold ml-2">{selectedCase.patient_id}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">{language === 'ar' ? 'العمر:' : 'Age:'}</span>
                      <span className="font-semibold ml-2">{selectedCase.age} {language === 'ar' ? 'سنة' : 'years'}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">{language === 'ar' ? 'الجنس:' : 'Gender:'}</span>
                      <span className="font-semibold ml-2">{selectedCase.gender}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">{language === 'ar' ? 'مدة التنويم:' : 'LOS:'}</span>
                      <span className="font-semibold ml-2">
                        {Math.ceil((new Date(selectedCase.discharge_date) - new Date(selectedCase.admission_date)) / (1000 * 60 * 60 * 24))} {language === 'ar' ? 'أيام' : 'days'}
                      </span>
                    </div>
                  </div>
                  <div>
                    <div className="font-semibold text-sm text-gray-600 mb-1">{language === 'ar' ? 'الشكوى الرئيسية' : 'Chief Complaint'}</div>
                    <div className="p-3 bg-blue-50 rounded">{selectedCase.chief_complaint}</div>
                  </div>
                  <div>
                    <div className="font-semibold text-sm text-gray-600 mb-1">{language === 'ar' ? 'الملخص السريري' : 'Clinical Summary'}</div>
                    <div className="p-3 bg-gray-50 rounded text-sm">{selectedCase.clinical_summary}</div>
                  </div>
                  {selectedCase.procedures?.length > 0 && (
                    <div>
                      <div className="font-semibold text-sm text-gray-600 mb-1">{language === 'ar' ? 'الإجراءات' : 'Procedures'}</div>
                      <ul className="list-disc list-inside text-sm space-y-1">
                        {selectedCase.procedures.map((p, i) => <li key={i}>{p}</li>)}
                      </ul>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* AI Analysis Results */}
              {aiAnalysis && (
                <Card className="border-2 border-purple-300 bg-purple-50">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-purple-800">
                      <Brain className="h-5 w-5" />
                      {language === 'ar' ? 'تحليل الذكاء الاصطناعي' : 'AI Analysis'}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {aiAnalysis.principal_diagnosis && (
                      <div className="bg-white p-3 rounded">
                        <div className="font-semibold text-sm mb-1">{language === 'ar' ? 'التشخيص الرئيسي المقترح' : 'Suggested Principal Diagnosis'}</div>
                        <div className="text-sm">
                          <span className="font-bold text-blue-600">{aiAnalysis.principal_diagnosis.code}</span>
                          <span className="ml-2">{aiAnalysis.principal_diagnosis.description}</span>
                          <div className="text-xs text-gray-600 mt-1">
                            {language === 'ar' ? 'الثقة:' : 'Confidence:'} {aiAnalysis.principal_diagnosis.confidence}
                          </div>
                          <div className="text-xs text-gray-500 mt-1">{aiAnalysis.principal_diagnosis.reasoning}</div>
                        </div>
                      </div>
                    )}
                    {aiAnalysis.secondary_diagnoses?.length > 0 && (
                      <div className="bg-white p-3 rounded">
                        <div className="font-semibold text-sm mb-2">{language === 'ar' ? 'التشخيصات الثانوية المقترحة' : 'Suggested Secondary Diagnoses'}</div>
                        {aiAnalysis.secondary_diagnoses.map((d, i) => (
                          <div key={i} className="text-sm mb-2">
                            <span className="font-bold text-green-600">{d.code}</span>
                            <span className="ml-2">{d.description}</span>
                            {d.is_complication && <span className="ml-2 text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded">CC/MCC</span>}
                            <div className="text-xs text-gray-500 mt-0.5">{d.reasoning}</div>
                          </div>
                        ))}
                      </div>
                    )}
                    {aiAnalysis.coding_notes && (
                      <div className="bg-amber-50 p-3 rounded border border-amber-200">
                        <div className="font-semibold text-sm mb-1">{language === 'ar' ? 'ملاحظات الترميز' : 'Coding Notes'}</div>
                        <div className="text-xs">{aiAnalysis.coding_notes}</div>
                      </div>
                    )}
                    <Button onClick={() => useAISuggestion(aiAnalysis)} className="w-full bg-purple-600">
                      <Sparkles className="h-4 w-4 mr-2" />
                      {language === 'ar' ? 'تطبيق اقتراحات AI' : 'Apply AI Suggestions'}
                    </Button>
                  </CardContent>
                </Card>
              )}

              {/* ICD Search */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Search className="h-5 w-5" />
                    {language === 'ar' ? 'بحث أكواد ICD-10-AM' : 'Search ICD-10-AM Codes'}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <Input
                    placeholder={language === 'ar' ? 'ابحث عن كود أو وصف...' : 'Search code or description...'}
                    value={searchTerm}
                    onChange={(e) => {
                      setSearchTerm(e.target.value);
                      searchICDCodes(e.target.value);
                    }}
                  />
                  <div className="mt-3 space-y-2 max-h-64 overflow-y-auto">
                    {icdCodes.map(code => (
                      <div key={code.id} 
                           onClick={() => {
                             if (!coding.principal_diagnosis) {
                               setCoding({...coding, principal_diagnosis: { code: code.code, description: code.description_ar, is_principal: true }});
                             } else {
                               const newSecondary = [...coding.secondary_diagnoses, { code: code.code, description: code.description_ar, is_principal: false }];
                               setCoding({...coding, secondary_diagnoses: newSecondary});
                             }
                             toast.success(language === 'ar' ? 'تم إضافة الكود' : 'Code added');
                           }}
                           className="p-2 bg-gray-50 rounded hover:bg-blue-50 cursor-pointer transition">
                        <div className="font-semibold text-sm">{code.code}</div>
                        <div className="text-xs text-gray-600">{code.description_ar}</div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Coding Panel */}
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>{language === 'ar' ? 'الترميز' : 'Coding'}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <div className="text-sm font-semibold mb-2">{language === 'ar' ? 'التشخيص الرئيسي' : 'Principal Diagnosis'}</div>
                    {coding.principal_diagnosis ? (
                      <div className="p-3 bg-blue-50 rounded text-sm">
                        <div className="font-semibold">{coding.principal_diagnosis.code}</div>
                        <div className="text-xs mt-1">{coding.principal_diagnosis.description}</div>
                        <Button size="sm" variant="destructive" className="mt-2" onClick={() => setCoding({...coding, principal_diagnosis: null})}>
                          {language === 'ar' ? 'حذف' : 'Remove'}
                        </Button>
                      </div>
                    ) : (
                      <div className="p-3 border-2 border-dashed rounded text-xs text-gray-500">
                        {language === 'ar' ? 'اختر من البحث أو استخدم اقتراحات AI' : 'Select from search or use AI suggestions'}
                      </div>
                    )}
                  </div>

                  <div>
                    <div className="text-sm font-semibold mb-2">{language === 'ar' ? 'تشخيصات ثانوية' : 'Secondary Diagnoses'}</div>
                    {coding.secondary_diagnoses.map((d, i) => (
                      <div key={i} className="p-2 bg-gray-50 rounded text-sm mb-2 flex justify-between items-start">
                        <div>
                          <div className="font-semibold">{d.code}</div>
                          <div className="text-xs">{d.description}</div>
                        </div>
                        <Button size="sm" variant="ghost" onClick={() => {
                          const newSecondary = coding.secondary_diagnoses.filter((_, idx) => idx !== i);
                          setCoding({...coding, secondary_diagnoses: newSecondary});
                        }}>
                          ×
                        </Button>
                      </div>
                    ))}
                  </div>

                  {coding.principal_diagnosis && (
                    <Button onClick={calculateDRG} className="w-full" variant="outline">
                      <Calculator className="h-4 w-4 mr-2" />
                      {language === 'ar' ? 'حساب DRG تلقائياً' : 'Calculate DRG'}
                    </Button>
                  )}

                  <div>
                    <label className="text-sm font-semibold">DRG Code</label>
                    <Input value={coding.drg_code} onChange={(e) => setCoding({...coding, drg_code: e.target.value})} />
                  </div>

                  <div>
                    <label className="text-sm font-semibold">{language === 'ar' ? 'وصف DRG' : 'DRG Description'}</label>
                    <Textarea value={coding.drg_description} onChange={(e) => setCoding({...coding, drg_description: e.target.value})} rows={2} />
                  </div>

                  <div>
                    <label className="text-sm font-semibold">{language === 'ar' ? 'القيمة المالية (ريال)' : 'Financial Value (SAR)'}</label>
                    <Input type="number" value={coding.financial_value} onChange={(e) => setCoding({...coding, financial_value: parseFloat(e.target.value)})} />
                  </div>

                  <Button onClick={submitCoding} className="w-full bg-green-600" disabled={!coding.principal_diagnosis}>
                    <CheckCircle className="h-4 w-4 mr-2" />
                    {language === 'ar' ? 'إرسال الترميز' : 'Submit Coding'}
                  </Button>

                  <Button onClick={() => { setSelectedCase(null); setAiAnalysis(null); }} variant="outline" className="w-full">
                    {language === 'ar' ? 'إلغاء' : 'Cancel'}
                  </Button>
                </CardContent>
              </Card>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default CoderWorkspacePro;