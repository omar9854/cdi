import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import { FileText, Search, Clock, CheckCircle } from 'lucide-react';
import Navbar from '@/components/Navbar';
import { useLanguage } from '@/contexts/LanguageContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CoderWorkspace = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const { language } = useLanguage();
  const [cases, setCases] = useState([]);
  const [selectedCase, setSelectedCase] = useState(null);
  const [icdCodes, setIcdCodes] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [coding, setCoding] = useState({
    principal_diagnosis: null,
    secondary_diagnoses: [],
    drg_code: '',
    drg_description: '',
    financial_value: 0
  });

  useEffect(() => {
    if (user?.department !== 'coding' || user?.coding_role !== 'coder') {
      navigate('/dashboard');
      return;
    }
    fetchMyCases();
  }, [user]);

  const fetchMyCases = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await axios.get(`${API}/coding/my-cases?user_id=${user.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCases(res.data.cases || []);
    } catch (error) {
      toast.error('Failed to load cases');
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

  const startCoding = async (caseId) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/coding/cases/${caseId}/start?user_id=${user.id}`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSelectedCase(cases.find(c => c.id === caseId));
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
      setCoding({ principal_diagnosis: null, secondary_diagnoses: [], drg_code: '', drg_description: '', financial_value: 0 });
      fetchMyCases();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar user={user} onLogout={onLogout} />
      <main className="max-w-7xl mx-auto p-6">
        <h1 className="text-3xl font-bold mb-6">
          {language === 'ar' ? 'منصة عمل المرمز الطبي' : 'Medical Coder Workspace'}
        </h1>

        {!selectedCase ? (
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  {language === 'ar' ? 'حالاتي' : 'My Cases'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {cases.filter(c => c.status !== 'completed').map(c => (
                    <div key={c.id} className="p-4 bg-white border rounded-lg">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-semibold">{c.case_number}</div>
                          <div className="text-sm text-gray-600">{c.patient_id} - {c.chief_complaint}</div>
                          <div className="text-xs text-gray-500 mt-1">{c.age} {language === 'ar' ? 'سنة' : 'years'} - {c.gender}</div>
                        </div>
                        <Button onClick={() => startCoding(c.id)}>
                          {language === 'ar' ? 'بدء الترميز' : 'Start Coding'}
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>{selectedCase.case_number}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <div className="font-semibold text-sm text-gray-600">{language === 'ar' ? 'الشكوى الرئيسية' : 'Chief Complaint'}</div>
                    <div>{selectedCase.chief_complaint}</div>
                  </div>
                  <div>
                    <div className="font-semibold text-sm text-gray-600">{language === 'ar' ? 'الملخص السريري' : 'Clinical Summary'}</div>
                    <div className="text-sm">{selectedCase.clinical_summary}</div>
                  </div>
                  <div>
                    <div className="font-semibold text-sm text-gray-600">{language === 'ar' ? 'الإجراءات' : 'Procedures'}</div>
                    <ul className="list-disc list-inside text-sm">
                      {selectedCase.procedures.map((p, i) => <li key={i}>{p}</li>)}
                    </ul>
                  </div>
                </CardContent>
              </Card>

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
                               setCoding({...coding, secondary_diagnoses: [...coding.secondary_diagnoses, { code: code.code, description: code.description_ar, is_principal: false }]});
                             }
                           }}
                           className="p-2 bg-gray-50 rounded hover:bg-blue-50 cursor-pointer">
                        <div className="font-semibold text-sm">{code.code}</div>
                        <div className="text-xs text-gray-600">{code.description_ar}</div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>

            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>{language === 'ar' ? 'الترميز' : 'Coding'}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <div className="text-sm font-semibold mb-2">{language === 'ar' ? 'التشخيص الرئيسي' : 'Principal Diagnosis'}</div>
                    {coding.principal_diagnosis ? (
                      <div className="p-2 bg-blue-50 rounded text-sm">
                        <div className="font-semibold">{coding.principal_diagnosis.code}</div>
                        <div className="text-xs">{coding.principal_diagnosis.description}</div>
                      </div>
                    ) : (
                      <div className="p-2 border-2 border-dashed rounded text-xs text-gray-500">
                        {language === 'ar' ? 'اختر من البحث' : 'Select from search'}
                      </div>
                    )}
                  </div>

                  <div>
                    <div className="text-sm font-semibold mb-2">{language === 'ar' ? 'تشخيصات ثانوية' : 'Secondary Diagnoses'}</div>
                    {coding.secondary_diagnoses.map((d, i) => (
                      <div key={i} className="p-2 bg-gray-50 rounded text-sm mb-1">
                        <div className="font-semibold">{d.code}</div>
                      </div>
                    ))}
                  </div>

                  <div>
                    <label className="text-sm font-semibold">DRG Code</label>
                    <Input value={coding.drg_code} onChange={(e) => setCoding({...coding, drg_code: e.target.value})} />
                  </div>

                  <div>
                    <label className="text-sm font-semibold">{language === 'ar' ? 'وصف DRG' : 'DRG Description'}</label>
                    <Input value={coding.drg_description} onChange={(e) => setCoding({...coding, drg_description: e.target.value})} />
                  </div>

                  <div>
                    <label className="text-sm font-semibold">{language === 'ar' ? 'القيمة المالية (ريال)' : 'Financial Value (SAR)'}</label>
                    <Input type="number" value={coding.financial_value} onChange={(e) => setCoding({...coding, financial_value: parseFloat(e.target.value)})} />
                  </div>

                  <Button onClick={submitCoding} className="w-full" disabled={!coding.principal_diagnosis}>
                    <CheckCircle className="h-4 w-4 mr-2" />
                    {language === 'ar' ? 'إرسال الترميز' : 'Submit Coding'}
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

export default CoderWorkspace;
