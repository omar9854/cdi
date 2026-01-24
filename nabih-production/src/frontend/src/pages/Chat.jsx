import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { ArrowRight, Send, Loader2, Bot, User } from 'lucide-react';
import Navbar from '@/components/Navbar';
import { useLanguage } from '@/contexts/LanguageContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Chat = ({ user, onLogout }) => {
  const { analysisId } = useParams();
  const navigate = useNavigate();
  const { language, t } = useLanguage();
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    fetchChatHistory();
  }, [analysisId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
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

  const handleSend = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim()) return;

    const userMessage = inputMessage;
    setInputMessage('');
    setSending(true);

    // Add user message optimistically
    const tempUserMsg = {
      role: 'user',
      message: userMessage,
      created_at: new Date().toISOString()
    };
    setMessages(prev => [...prev, tempUserMsg]);

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API}/chat`,
        {
          analysis_id: analysisId,
          message: userMessage
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      // Add assistant response
      const assistantMsg = {
        role: 'assistant',
        message: response.data.message,
        created_at: new Date().toISOString()
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (error) {
      toast.error(t('error'));
      // Remove optimistic message on error
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setSending(false);
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
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex flex-col">
      <Navbar user={user} onLogout={onLogout} />
      
      <main className="flex-1 container mx-auto px-4 py-8 max-w-5xl flex flex-col" data-testid="chat-page">
        <div className="mb-6 fade-in">
          <Button variant="ghost" onClick={() => navigate(-1)} className="mb-4" data-testid="back-button">
            {language === 'ar' ? <ArrowRight className="ml-2" /> : <ArrowRight className="mr-2" />}
            {t('back')}
          </Button>
          <h1 className="text-4xl font-bold text-gray-800">{t('chatWithAI')}</h1>
        </div>

        <Card className="medical-card flex-1 flex flex-col fade-in" style={{ minHeight: '500px' }}>
          <CardContent className="flex-1 flex flex-col p-6">
            {/* Messages Container */}
            <div className="flex-1 overflow-y-auto space-y-4 mb-4" style={{ maxHeight: '60vh' }}>
              {messages.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <Bot className="w-16 h-16 mx-auto mb-4 text-blue-400" />
                  <p>{language === 'ar' ? 'ابدأ المحادثة حول التحليل' : 'Start the conversation about the analysis'}</p>
                </div>
              ) : (
                messages.map((msg, index) => (
                  <div
                    key={index}
                    className={`flex gap-3 ${msg.role === 'user' ? (language === 'ar' ? 'justify-start' : 'justify-end') : (language === 'ar' ? 'justify-end' : 'justify-start')}`}
                    data-testid={`message-${index}`}
                  >
                    {msg.role === 'assistant' && (
                      <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-full flex items-center justify-center flex-shrink-0">
                        <Bot className="w-5 h-5 text-white" />
                      </div>
                    )}
                    <div
                      className={`max-w-[70%] rounded-2xl px-4 py-3 ${
                        msg.role === 'user'
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      <p className="whitespace-pre-wrap">{msg.message}</p>
                    </div>
                    {msg.role === 'user' && (
                      <div className="w-8 h-8 bg-gradient-to-br from-green-600 to-emerald-600 rounded-full flex items-center justify-center flex-shrink-0">
                        <User className="w-5 h-5 text-white" />
                      </div>
                    )}
                  </div>
                ))
              )}
              {sending && (
                <div className={`flex gap-3 ${language === 'ar' ? 'justify-end' : 'justify-start'}`}>
                  <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-full flex items-center justify-center">
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                  <div className="bg-gray-100 rounded-2xl px-4 py-3">
                    <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Form */}
            <form onSubmit={handleSend} className="flex gap-2">
              <Input
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder={t('askQuestion')}
                disabled={sending}
                className="flex-1"
                data-testid="chat-input"
              />
              <Button
                type="submit"
                disabled={sending || !inputMessage.trim()}
                className="medical-blue"
                data-testid="send-button"
              >
                {sending ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <>
                    {language === 'ar' ? <Send className="ml-2" /> : <Send className="mr-2" />}
                    {t('send')}
                  </>
                )}
              </Button>
            </form>
          </CardContent>
        </Card>
      </main>
    </div>
  );
};

export default Chat;
