import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import { FileText, AlertTriangle, DollarSign, CheckCircle } from 'lucide-react';
import Navbar from '@/components/Navbar';
import { useLanguage } from '@/contexts/LanguageContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AuditorWorkspace = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const { language } = useLanguage();
  const [cases, setCases] = useState([]);
  const [selectedCase, setSelectedCase] = useState(null);
  const [audit, setAudit] = useState({
    errors: [],
    corrected_principal: '',
    corrected_secondary: [],
    corrected_drg: '',
    corrected_value: 0,
    recommendations: '',
    risk_level: 'low'
  });
  const [newError, setNewError] = useState({
    error_type: 'undercoding',
    description: '',
    icd_code: '',
    financial_impact: 0,
    severity: 'low'
  });

  useEffect(() => {
    if (user?.department !== 'coding' || user?.coding_role !== 'auditor') {
      navigate('/dashboard');
      return;
    }
    fetchCasesForAudit();
  }, [user]);

  const fetchCasesForAudit = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await axios.get(`${API}/coding/cases/for-audit?sample_size=10`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCases(res.data.cases || []);
    } catch (error) {
      toast.error('Failed to load cases');
    }
  };

  const addError = () => {
    if (!newError.description) {
      toast.error(language === 'ar' ? 'أدخل وصف الخطأ' : 'Enter error description');
      return;
    }
    setAudit({...audit, errors: [...audit.errors, newError]});
    setNewError({ error_type: 'undercoding', description: '', icd_code: '', financial_impact: 0, severity: 'low' });
  };

  const submitAudit = async () => {
    if (audit.errors.length === 0) {
      toast.error(language === 'ar' ? 'أضف خطأ واحد على الأقل' : 'Add at least one error');
      return;
    }
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/coding/audit/submit?auditor_id=${user.id}`, {
        case_id: selectedCase.id,
        ...audit
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(language === 'ar' ? 'تم إرسال التدقيق بنجاح' : 'Audit submitted successfully');
      setSelectedCase(null);
      setAudit({ errors: [], corrected_principal: '', corrected_secondary: [], corrected_drg: '', corrected_value: 0, recommendations: '', risk_level: 'low' });
      fetchCasesForAudit();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar user={user} onLogout={onLogout} />
      <main className="max-w-7xl mx-auto p-6">
        <h1 className="text-3xl font-bold mb-6">
          {language === 'ar' ? 'منصة عمل المدقق الطبي' : 'Medical Auditor Workspace'}
        </h1>

        {!selectedCase ? (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                {language === 'ar' ? 'عينة الحالات للتدقيق (10%)' : 'Cases Sample for Audit (10%)'}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {cases.map(c => (
                  <div key={c.id} className="p-4 bg-white border rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-semibold">{c.case_number}</div>
                        <div className="text-sm text-gray-600">{c.patient_id} - {c.chief_complaint}</div>
                        <div className="text-xs text-gray-500 mt-1">
                          DRG: {c.drg_code} - {language === 'ar' ? 'قيمة:' : 'Value:'} {c.financial_value?.toLocaleString()} SAR
                        </div>
                      </div>
                      <Button onClick={() => setSelectedCase(c)}>
                        {language === 'ar' ? 'تدقيق' : 'Audit'}
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>{selectedCase.case_number} - {language === 'ar' ? 'الترميز الأصلي' : 'Original Coding'}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div>
                    <div className="text-sm font-semibold text-gray-600">{language === 'ar' ? 'التشخيص الرئيسي' : 'Principal Diagnosis'}</div>
                    <div className="p-2 bg-blue-50 rounded mt-1">
                      {selectedCase.principal_diagnosis?.code} - {selectedCase.principal_diagnosis?.description}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-gray-600">{language === 'ar' ? 'التشخيصات الثانوية' : 'Secondary Diagnoses'}</div>
                    {selectedCase.secondary_diagnoses?.map((d, i) => (
                      <div key={i} className="p-2 bg-gray-50 rounded mt-1 text-sm">{d.code} - {d.description}</div>
                    ))}
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <div className="text-sm font-semibold text-gray-600">DRG Code</div>
                      <div className="p-2 bg-gray-50 rounded mt-1">{selectedCase.drg_code}</div>
                    </div>
                    <div>
                      <div className="text-sm font-semibold text-gray-600">{language === 'ar' ? 'القيمة المالية' : 'Financial Value'}</div>
                      <div className="p-2 bg-green-50 rounded mt-1">{selectedCase.financial_value?.toLocaleString()} SAR</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <AlertTriangle className="h-5 w-5" />
                    {language === 'ar' ? 'الأخطاء المكتشفة' : 'Detected Errors'}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-3">
                      <Select value={newError.error_type} onValueChange={(v) => setNewError({...newError, error_type: v})}>
                        <SelectTrigger>
                          <SelectValue placeholder="Error Type" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="undercoding">{language === 'ar' ? 'نقص ترميز' : 'Undercoding'}</SelectItem>
                          <SelectItem value="overcoding">{language === 'ar' ? 'زيادة ترميز' : 'Overcoding'}</SelectItem>
                          <SelectItem value="poa_error">POA Error</SelectItem>
                          <SelectItem value="cc_mcc_error">CC/MCC Error</SelectItem>
                        </SelectContent>
                      </Select>

                      <Select value={newError.severity} onValueChange={(v) => setNewError({...newError, severity: v})}>
                        <SelectTrigger>
                          <SelectValue placeholder="Severity" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="low">{language === 'ar' ? 'منخفض' : 'Low'}</SelectItem>
                          <SelectItem value="medium">{language === 'ar' ? 'متوسط' : 'Medium'}</SelectItem>
                          <SelectItem value="high">{language === 'ar' ? 'عالي' : 'High'}</SelectItem>
                          <SelectItem value="critical">{language === 'ar' ? 'حرج' : 'Critical'}</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <Input
                      placeholder={language === 'ar' ? 'كود ICD (اختياري)' : 'ICD Code (optional)'}
                      value={newError.icd_code}
                      onChange={(e) => setNewError({...newError, icd_code: e.target.value})}
                    />

                    <Textarea
                      placeholder={language === 'ar' ? 'وصف الخطأ' : 'Error description'}
                      value={newError.description}
                      onChange={(e) => setNewError({...newError, description: e.target.value})}
                    />

                    <Input
                      type="number"
                      placeholder={language === 'ar' ? 'الأثر المالي (ريال)' : 'Financial Impact (SAR)'}
                      value={newError.financial_impact}
                      onChange={(e) => setNewError({...newError, financial_impact: parseFloat(e.target.value)})}
                    />

                    <Button onClick={addError} className="w-full">
                      {language === 'ar' ? 'إضافة خطأ' : 'Add Error'}
                    </Button>

                    <div className="space-y-2 mt-4">
                      {audit.errors.map((err, i) => (
                        <div key={i} className={`p-3 rounded border-l-4 ${{
                          low: 'border-blue-500 bg-blue-50',
                          medium: 'border-yellow-500 bg-yellow-50',
                          high: 'border-orange-500 bg-orange-50',
                          critical: 'border-red-500 bg-red-50'
                        }[err.severity]}`}>
                          <div className="font-semibold text-sm">{err.error_type.toUpperCase()}</div>
                          <div className="text-xs text-gray-700">{err.description}</div>
                          {err.financial_impact > 0 && (
                            <div className="text-xs text-red-600 mt-1">{language === 'ar' ? 'أثر مالي:' : 'Impact:'} {err.financial_impact} SAR</div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>{language === 'ar' ? 'الترميز المصحح' : 'Corrected Coding'}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <label className="text-sm font-semibold">{language === 'ar' ? 'التشخيص المصحح' : 'Corrected Principal'}</label>
                    <Input value={audit.corrected_principal} onChange={(e) => setAudit({...audit, corrected_principal: e.target.value})} />
                  </div>

                  <div>
                    <label className="text-sm font-semibold">{language === 'ar' ? 'DRG المصحح' : 'Corrected DRG'}</label>
                    <Input value={audit.corrected_drg} onChange={(e) => setAudit({...audit, corrected_drg: e.target.value})} />
                  </div>

                  <div>
                    <label className="text-sm font-semibold">{language === 'ar' ? 'القيمة المصححة' : 'Corrected Value'}</label>
                    <Input type="number" value={audit.corrected_value} onChange={(e) => setAudit({...audit, corrected_value: parseFloat(e.target.value)})} />
                  </div>

                  <div>
                    <label className="text-sm font-semibold">{language === 'ar' ? 'مستوى الخطورة' : 'Risk Level'}</label>
                    <Select value={audit.risk_level} onValueChange={(v) => setAudit({...audit, risk_level: v})}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="low">{language === 'ar' ? 'منخفض' : 'Low'}</SelectItem>
                        <SelectItem value="medium">{language === 'ar' ? 'متوسط' : 'Medium'}</SelectItem>
                        <SelectItem value="high">{language === 'ar' ? 'عالي' : 'High'}</SelectItem>
                        <SelectItem value="critical">{language === 'ar' ? 'حرج' : 'Critical'}</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <label className="text-sm font-semibold">{language === 'ar' ? 'التوصيات' : 'Recommendations'}</label>
                    <Textarea
                      value={audit.recommendations}
                      onChange={(e) => setAudit({...audit, recommendations: e.target.value})}
                      rows={4}
                    />
                  </div>

                  <Button onClick={submitAudit} className="w-full" disabled={audit.errors.length === 0}>
                    <CheckCircle className="h-4 w-4 mr-2" />
                    {language === 'ar' ? 'إرسال التدقيق' : 'Submit Audit'}
                  </Button>

                  <Button onClick={() => setSelectedCase(null)} variant="outline" className="w-full">
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

export default AuditorWorkspace;
