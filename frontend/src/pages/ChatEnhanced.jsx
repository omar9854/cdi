import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';
import { 
  ArrowRight, Send, Loader2, Bot, User, Sparkles, 
  FileText, AlertCircle, HelpCircle, TrendingUp, CheckCircle,
  BarChart3, ClipboardList, MessageCircle
} from 'lucide-react';
import Navbar from '@/components/Navbar';
import { useLanguage } from '@/contexts/LanguageContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ChatEnhanced = ({ user, onLogout }) => {
  const { analysisId } = useParams();
  const navigate = useNavigate();
  const { language } = useLanguage();
  
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [questions, setQuestions] = useState([]);
  const [loadingQuestions, setLoadingQuestions] = useState(true);
  const [activeTab, setActiveTab] = useState('quick');
  const [noteId, setNoteId] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    fetchAnalysisAndNoteId();
    fetchChatHistory();
    fetchQuestions();
  }, [analysisId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchAnalysisAndNoteId = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/analysis/${analysisId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.data && response.data.note_id) {
        setNoteId(response.data.note_id);
      }
    } catch (error) {
      console.error('Error fetching analysis:', error);
    }
  };

  const fetchChatHistory = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/chat/${analysisId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMessages(response.data);
    } catch (error) {
      // No chat history yet
    } finally {
      setLoading(false);
    }
  };

  const fetchQuestions = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/clinical-questions?language=${language}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setQuestions(response.data.questions || []);
    } catch (error) {
      console.error('Error fetching questions:', error);
    } finally {
      setLoadingQuestions(false);
    }
  };

  const handleAskPredefinedQuestion = async (question) => {
    setSending(true);
    try {
      const token = localStorage.getItem('token');
      
      // Add question to messages
      setMessages(prev => [...prev, {
        question: question.question,
        answer: '',
        isLoading: true
      }]);

      const response = await axios.post(
        `${API}/chat/ask-question/${question.id}?analysis_id=${analysisId}&language=${language}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );

      // Update with answer
      setMessages(prev => prev.map((msg, idx) => 
        idx === prev.length - 1 ? {
          question: response.data.question,
          answer: response.data.answer,
          category: response.data.category,
          isLoading: false
        } : msg
      ));

      // Switch to chat tab to see the answer
      setActiveTab('chat');
      
    } catch (error) {
      toast.error(language === 'ar' ? 'فشل إرسال السؤال' : 'Failed to send question');
      setMessages(prev => prev.filter((_, idx) => idx !== prev.length - 1));
    } finally {
      setSending(false);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || sending) return;

    const userMessage = inputMessage.trim();
    setInputMessage('');
    setSending(true);

    try {
      const token = localStorage.getItem('token');
      
      // Add user message
      setMessages(prev => [...prev, {
        question: userMessage,
        answer: '',
        isLoading: true
      }]);

      const response = await axios.post(
        `${API}/chat/${analysisId}`,
        { question: userMessage },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      // Update with AI response
      setMessages(prev => prev.map((msg, idx) => 
        idx === prev.length - 1 ? {
          question: response.data.question,
          answer: response.data.answer,
          isLoading: false
        } : msg
      ));

    } catch (error) {
      toast.error(language === 'ar' ? 'فشل إرسال الرسالة' : 'Failed to send message');
      setMessages(prev => prev.filter((_, idx) => idx !== prev.length - 1));
    } finally {
      setSending(false);
    }
  };

  const getCategoryIcon = (category) => {
    const icons = {
      'التشخيصات': FileText,
      'Diagnoses': FileText,
      'التوثيق الناقص': AlertCircle,
      'Missing Documentation': AlertCircle,
      'الاستفسارات': HelpCircle,
      'Queries': HelpCircle,
      'DRG': TrendingUp,
      'الجودة': CheckCircle,
      'Quality': CheckCircle,
      'الامتثال': ClipboardList,
      'Compliance': ClipboardList,
      'تحليل عام': BarChart3,
      'General Analysis': BarChart3
    };
    return icons[category] || MessageCircle;
  };

  const getCategoryColor = (category) => {
    const colors = {
      'التشخيصات': 'bg-blue-100 text-blue-700 border-blue-300',
      'Diagnoses': 'bg-blue-100 text-blue-700 border-blue-300',
      'التوثيق الناقص': 'bg-red-100 text-red-700 border-red-300',
      'Missing Documentation': 'bg-red-100 text-red-700 border-red-300',
      'الاستفسارات': 'bg-purple-100 text-purple-700 border-purple-300',
      'Queries': 'bg-purple-100 text-purple-700 border-purple-300',
      'DRG': 'bg-green-100 text-green-700 border-green-300',
      'الجودة': 'bg-emerald-100 text-emerald-700 border-emerald-300',
      'Quality': 'bg-emerald-100 text-emerald-700 border-emerald-300',
      'الامتثال': 'bg-amber-100 text-amber-700 border-amber-300',
      'Compliance': 'bg-amber-100 text-amber-700 border-amber-300',
      'تحليل عام': 'bg-indigo-100 text-indigo-700 border-indigo-300',
      'General Analysis': 'bg-indigo-100 text-indigo-700 border-indigo-300'
    };
    return colors[category] || 'bg-gray-100 text-gray-700 border-gray-300';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
        <Navbar user={user} onLogout={onLogout} />
        <div className="flex justify-center items-center py-20">
          <Loader2 className="w-12 h-12 text-blue-600 animate-spin" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <Navbar user={user} onLogout={onLogout} />
      
      <main className="container mx-auto px-4 py-8 max-w-7xl">
        <div className="mb-6">
          <Button 
            variant="ghost" 
            onClick={() => navigate(noteId ? `/analysis/${noteId}` : '/dashboard')} 
            className="mb-4"
          >
            {language === 'ar' ? <ArrowRight className="ml-2" /> : <ArrowRight className="mr-2" />}
            {language === 'ar' ? 'العودة للتحليل' : 'Back to Analysis'}
          </Button>
          
          <div className="flex items-center gap-3">
            <Sparkles className="h-10 w-10 text-purple-600" />
            <div>
              <h1 className="text-4xl font-bold text-gray-800">
                {language === 'ar' ? 'مناقشة التحليل مع الذكاء الاصطناعي' : 'AI-Powered Analysis Discussion'}
              </h1>
              <p className="text-gray-600 mt-1">
                {language === 'ar' 
                  ? 'اطرح أسئلة سريعة أو ابدأ دردشة مفتوحة'
                  : 'Ask quick questions or start an open chat'
                }
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Quick Questions Sidebar */}
          <div className="lg:col-span-1">
            <Card className="sticky top-4">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Sparkles className="h-5 w-5 text-purple-600" />
                  {language === 'ar' ? 'الأسئلة السريعة' : 'Quick Questions'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {loadingQuestions ? (
                  <div className="flex justify-center py-8">
                    <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
                  </div>
                ) : (
                  <div className="space-y-2 max-h-[600px] overflow-y-auto">
                    {questions.map((q) => {
                      const Icon = getCategoryIcon(q.category);
                      const colorClass = getCategoryColor(q.category);
                      
                      return (
                        <button
                          key={q.id}
                          onClick={() => handleAskPredefinedQuestion(q)}
                          disabled={sending}
                          className={`w-full text-right p-3 rounded-lg border-2 hover:shadow-md transition-all ${colorClass} ${
                            sending ? 'opacity-50 cursor-not-allowed' : 'hover:scale-105'
                          }`}
                        >
                          <div className="flex items-start gap-2">
                            <Icon className="h-4 w-4 mt-1 flex-shrink-0" />
                            <div className="flex-1">
                              <p className="font-medium text-sm">{q.question}</p>
                              <Badge variant="outline" className="mt-1 text-xs">
                                {q.category}
                              </Badge>
                            </div>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Chat Area */}
          <div className="lg:col-span-2">
            <Card className="h-[700px] flex flex-col">
              <CardHeader className="border-b">
                <Tabs value={activeTab} onValueChange={setActiveTab}>
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="quick">
                      {language === 'ar' ? '✨ الأسئلة' : '✨ Questions'}
                    </TabsTrigger>
                    <TabsTrigger value="chat">
                      {language === 'ar' ? '💬 الدردشة' : '💬 Chat'}
                    </TabsTrigger>
                  </TabsList>
                </Tabs>
              </CardHeader>

              <CardContent className="flex-1 overflow-y-auto p-6 space-y-4">
                {messages.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-full text-center">
                    <Bot className="h-16 w-16 text-gray-300 mb-4" />
                    <h3 className="text-xl font-semibold text-gray-700 mb-2">
                      {language === 'ar' 
                        ? 'ابدأ المحادثة مع الذكاء الاصطناعي'
                        : 'Start conversation with AI'
                      }
                    </h3>
                    <p className="text-gray-500">
                      {language === 'ar'
                        ? 'اختر سؤالاً سريعاً أو اكتب سؤالك الخاص'
                        : 'Choose a quick question or type your own'
                      }
                    </p>
                  </div>
                ) : (
                  <>
                    {messages.map((msg, idx) => (
                      <div key={idx} className="space-y-3">
                        {/* User Question */}
                        <div className="flex gap-3 justify-end">
                          <div className="bg-blue-600 text-white rounded-lg px-4 py-3 max-w-[80%]">
                            <div className="flex items-center gap-2 mb-1">
                              <User className="h-4 w-4" />
                              <span className="font-semibold text-sm">
                                {language === 'ar' ? 'أنت' : 'You'}
                              </span>
                            </div>
                            <p className="text-sm">{msg.question}</p>
                            {msg.category && (
                              <Badge variant="secondary" className="mt-2 text-xs">
                                {msg.category}
                              </Badge>
                            )}
                          </div>
                        </div>

                        {/* AI Answer */}
                        <div className="flex gap-3">
                          <div className="bg-gradient-to-r from-purple-100 to-indigo-100 rounded-lg px-4 py-3 max-w-[80%]">
                            <div className="flex items-center gap-2 mb-2">
                              <Bot className="h-4 w-4 text-purple-600" />
                              <span className="font-semibold text-sm text-purple-900">
                                {language === 'ar' ? 'الذكاء الاصطناعي' : 'AI Assistant'}
                              </span>
                            </div>
                            {msg.isLoading ? (
                              <div className="flex items-center gap-2 text-gray-600">
                                <Loader2 className="h-4 w-4 animate-spin" />
                                <span className="text-sm">
                                  {language === 'ar' ? 'جاري التحليل...' : 'Analyzing...'}
                                </span>
                              </div>
                            ) : (
                              <div className="prose prose-sm max-w-none">
                                <pre className="whitespace-pre-wrap text-sm text-gray-800 font-sans">
                                  {msg.answer}
                                </pre>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                    <div ref={messagesEndRef} />
                  </>
                )}
              </CardContent>

              {/* Input Area */}
              <div className="border-t p-4">
                <form onSubmit={handleSendMessage} className="flex gap-2">
                  <Input
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    placeholder={language === 'ar' 
                      ? 'اكتب سؤالك هنا...'
                      : 'Type your question here...'
                    }
                    disabled={sending}
                    className="flex-1"
                  />
                  <Button 
                    type="submit" 
                    disabled={sending || !inputMessage.trim()}
                    className="bg-purple-600 hover:bg-purple-700"
                  >
                    {sending ? (
                      <Loader2 className="h-5 w-5 animate-spin" />
                    ) : (
                      <Send className="h-5 w-5" />
                    )}
                  </Button>
                </form>
              </div>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
};

export default ChatEnhanced;
