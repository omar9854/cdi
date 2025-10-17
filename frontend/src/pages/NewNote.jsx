import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { Save, ArrowRight, Plus, X } from 'lucide-react';
import Navbar from '@/components/Navbar';
import { useLanguage } from '@/contexts/LanguageContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const NewNote = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const { language, t } = useLanguage();
  const [title, setTitle] = useState('');
  const [doctorNotes, setDoctorNotes] = useState([{ text: '', specialty: '' }]);
  const [specialties, setSpecialties] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchSpecialties();
  }, []);

  const fetchSpecialties = async () => {
    try {
      const response = await axios.get(`${API}/specialties`);
      setSpecialties(response.data);
    } catch (error) {
      toast.error(t('error'));
    }
  };

  const addNote = () => {
    setDoctorNotes([...doctorNotes, { text: '', specialty: '' }]);
  };

  const removeNote = (index) => {
    if (doctorNotes.length > 1) {
      const newNotes = doctorNotes.filter((_, i) => i !== index);
      setDoctorNotes(newNotes);
    }
  };

  const updateNote = (index, field, value) => {
    const newNotes = [...doctorNotes];
    newNotes[index][field] = value;
    setDoctorNotes(newNotes);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate
    if (!title.trim()) {
      toast.error(language === 'ar' ? 'يرجى إدخال عنوان الملاحظة' : 'Please enter note title');
      return;
    }
    
    const validNotes = doctorNotes.filter(n => n.text.trim() && n.specialty);
    if (validNotes.length === 0) {
      toast.error(language === 'ar' ? 'يرجى إضافة ملاحظة واحدة على الأقل' : 'Please add at least one note');
      return;
    }
    
    setLoading(true);

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API}/notes`,
        {
          title,
          doctor_notes: validNotes
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      toast.success(t('noteSaved'));
      navigate(`/analysis/${response.data.id}`);
    } catch (error) {
      toast.error(t('error'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <Navbar user={user} onLogout={onLogout} />
      
      <main className="container mx-auto px-4 py-8 max-w-6xl" data-testid="new-note-page">
        <div className="mb-6 fade-in">
          <Button variant="ghost" onClick={() => navigate('/dashboard')} className="mb-4" data-testid="back-button">
            {language === 'ar' ? <ArrowRight className="ml-2" /> : <ArrowRight className="mr-2" />}
            {t('back')}
          </Button>
          <h1 className="text-4xl font-bold text-gray-800">{t('newClinicalNote')}</h1>
        </div>

        <Card className="medical-card fade-in">
          <CardHeader>
            <CardTitle className="text-2xl">{t('enterNoteDetails')}</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="title" className="text-lg">{t('noteTitle')}</Label>
                <Input
                  id="title"
                  type="text"
                  placeholder={t('noteTitlePlaceholder')}
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  required
                  className="text-lg py-6"
                  data-testid="note-title-input"
                />
              </div>

              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <Label className="text-lg">{t('doctorNotes')}</Label>
                  <Button
                    type="button"
                    onClick={addNote}
                    variant="outline"
                    className="text-blue-600"
                    data-testid="add-note-button"
                  >
                    {language === 'ar' ? <Plus className="ml-2" /> : <Plus className="mr-2" />}
                    {t('addAnotherNote')}
                  </Button>
                </div>

                {doctorNotes.map((note, index) => (
                  <Card key={index} className="border-2 border-blue-100">
                    <CardContent className="pt-6 space-y-4">
                      <div className="flex justify-between items-center mb-2">
                        <Label className="font-semibold">
                          {language === 'ar' ? `ملاحظة ${index + 1}` : `Note ${index + 1}`}
                        </Label>
                        {doctorNotes.length > 1 && (
                          <Button
                            type="button"
                            onClick={() => removeNote(index)}
                            variant="ghost"
                            size="sm"
                            className="text-red-600 hover:bg-red-50"
                            data-testid={`remove-note-${index}`}
                          >
                            {language === 'ar' ? <X className="ml-1" /> : <X className="mr-1" />}
                            {t('removeNote')}
                          </Button>
                        )}
                      </div>

                      <div>
                        <Label>{t('specialty')}</Label>
                        <Select
                          value={note.specialty}
                          onValueChange={(value) => updateNote(index, 'specialty', value)}
                        >
                          <SelectTrigger data-testid={`specialty-select-${index}`}>
                            <SelectValue placeholder={t('selectSpecialty')} />
                          </SelectTrigger>
                          <SelectContent>
                            {specialties.map((spec) => (
                              <SelectItem key={spec.value} value={spec.value}>
                                {language === 'ar' ? spec.label_ar : spec.label_en}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <div>
                        <Label>{t('noteText')}</Label>
                        <Textarea
                          value={note.text}
                          onChange={(e) => updateNote(index, 'text', e.target.value)}
                          placeholder={t('notePlaceholder')}
                          rows={8}
                          className="text-base"
                          data-testid={`note-text-${index}`}
                        />
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              <div className="flex gap-4 pt-4">
                <Button
                  type="submit"
                  className="flex-1 medical-blue text-white py-6 text-lg font-semibold"
                  disabled={loading}
                  data-testid="save-note-button"
                >
                  {loading ? t('saving') : (
                    <>
                      {language === 'ar' ? <Save className="ml-2" /> : <Save className="mr-2" />}
                      {t('saveAndAnalyze')}
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