import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { Inbox, Send, FileText, Mail, Trash2, Eye, Plus, Users } from 'lucide-react';
import Navbar from '@/components/Navbar';
import { useLanguage } from '@/contexts/LanguageContext';
import Footer from '@/components/Footer';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Messages = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const { language } = useLanguage();
  const [activeTab, setActiveTab] = useState('inbox');
  const [inboxMessages, setInboxMessages] = useState([]);
  const [sentMessages, setSentMessages] = useState([]);
  const [draftMessages, setDraftMessages] = useState([]);
  const [allUsers, setAllUsers] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [selectedMessage, setSelectedMessage] = useState(null);
  const [showCompose, setShowCompose] = useState(false);
  const [composeData, setComposeData] = useState({
    to_user_id: '',
    subject: '',
    body: '',
    is_draft: false
  });

  useEffect(() => {
    fetchMessages();
    fetchUnreadCount();
    if (user.role === 'supervisor' || user.role === 'admin') {
      fetchAllUsers();
    }
  }, []);

  const fetchMessages = async () => {
    try {
      const token = localStorage.getItem('token');
      const [inbox, sent, drafts] = await Promise.all([
        axios.get(`${API}/messages/inbox`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/messages/sent`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/messages/drafts`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      setInboxMessages(inbox.data);
      setSentMessages(sent.data);
      setDraftMessages(drafts.data);
    } catch (error) {
      console.error('Failed to fetch messages:', error);
    }
  };

  const fetchUnreadCount = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/messages/unread-count`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUnreadCount(response.data.count);
    } catch (error) {
      console.error('Failed to fetch unread count:', error);
    }
  };

  const fetchAllUsers = async () => {
    try {
      const token = localStorage.getItem('token');
      // Try to get all users from supervisor/employees endpoint (works for both admin and supervisor)
      const response = await axios.get(`${API}/supervisor/employees`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      console.log('Users for messages:', response.data);
      // These users already have id, full_name, email
      setAllUsers(response.data || []);
    } catch (error) {
      console.error('Failed to fetch users:', error);
      // Fallback to admin/users-statistics if supervisor endpoint fails
      try {
        const response = await axios.get(`${API}/admin/users-statistics`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        const users = (response.data.statistics || []).filter(u => u.user_id && u.user_id.trim() !== '');
        console.log('Users from statistics:', users);
        setAllUsers(users);
      } catch (err) {
        console.error('Failed to fetch users from statistics:', err);
        toast.error(language === 'ar' ? 'فشل تحميل قائمة المستخدمين' : 'Failed to load users');
      }
    }
  };

  const handleSendMessage = async (isDraft = false) => {
    if (!composeData.subject || !composeData.body) {
      toast.error(language === 'ar' ? 'الموضوع والمحتوى مطلوبان' : 'Subject and body are required');
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/messages/send`,
        { ...composeData, is_draft: isDraft },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success(language === 'ar' ? (isDraft ? 'تم الحفظ كمسودة' : 'تم إرسال الرسالة') : (isDraft ? 'Saved as draft' : 'Message sent'));
      setShowCompose(false);
      setComposeData({ to_user_id: '', subject: '', body: '', is_draft: false });
      fetchMessages();
      fetchUnreadCount();
    } catch (error) {
      toast.error(language === 'ar' ? 'فشل الإرسال' : 'Failed to send');
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAsRead = async (messageId) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/messages/${messageId}/read`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchMessages();
      fetchUnreadCount();
    } catch (error) {
      console.error('Failed to mark as read:', error);
    }
  };

  const handleDeleteMessage = async (messageId) => {
    if (!confirm(language === 'ar' ? 'هل أنت متأكد من حذف هذه الرسالة؟' : 'Are you sure you want to delete this message?')) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API}/messages/${messageId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(language === 'ar' ? 'تم الحذف' : 'Deleted');
      fetchMessages();
      setSelectedMessage(null);
    } catch (error) {
      toast.error(language === 'ar' ? 'فشل الحذف' : 'Failed to delete');
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleString(language === 'ar' ? 'ar-SA' : 'en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const renderMessagesList = (messages, type) => {
    if (messages.length === 0) {
      return (
        <div className="text-center py-12 text-gray-500">
          <Mail className="h-16 w-16 mx-auto mb-4 text-gray-300" />
          <p>{language === 'ar' ? 'لا توجد رسائل' : 'No messages'}</p>
        </div>
      );
    }

    return (
      <div className="space-y-2">
        {messages.map((msg) => (
          <div
            key={msg.id}
            onClick={() => {
              setSelectedMessage(msg);
              if (type === 'inbox' && !msg.is_read) {
                handleMarkAsRead(msg.id);
              }
            }}
            className={`p-4 border rounded-lg cursor-pointer hover:bg-blue-50 transition ${
              !msg.is_read && type === 'inbox' ? 'bg-blue-50 border-blue-300' : 'bg-white'
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  {!msg.is_read && type === 'inbox' && (
                    <Badge className="bg-blue-600">{language === 'ar' ? 'جديد' : 'New'}</Badge>
                  )}
                  <h3 className="font-semibold text-gray-800">{msg.subject}</h3>
                </div>
                <p className="text-sm text-gray-600 mb-2">
                  {type === 'inbox' ? (
                    <>
                      {language === 'ar' ? 'من:' : 'From:'} {msg.from_user_name}
                    </>
                  ) : (
                    <>
                      {language === 'ar' ? 'إلى:' : 'To:'} {msg.to_user_name || (language === 'ar' ? 'الكل' : 'All')}
                    </>
                  )}
                </p>
                <p className="text-xs text-gray-500">{formatDate(msg.created_at)}</p>
              </div>
              <Button
                size="sm"
                variant="ghost"
                onClick={(e) => {
                  e.stopPropagation();
                  handleDeleteMessage(msg.id);
                }}
              >
                <Trash2 className="h-4 w-4 text-red-500" />
              </Button>
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <Navbar user={user} onLogout={onLogout} />
      <main className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Header */}
        <div className="mb-8 animate-fade-in">
          <h1 className="text-4xl font-bold gradient-text mb-2">البريد الداخلي</h1>
          <p className="text-gray-600 text-lg">إدارة الرسائل والتواصل مع الفريق</p>
        </div>

        {/* New Message Button */}
        <div className="mb-6 animate-slide-in">
          <Button
            onClick={() => {
              setShowCompose(true);
              fetchAllUsers();
            }}
            className="medical-blue px-6 py-3 rounded-xl shadow-lg hover:shadow-xl"
          >
            <Plus className="mr-2 h-5 w-5" />
            {language === 'ar' ? 'رسالة جديدة' : 'New Message'}
          </Button>
        </div>

        {/* Tabs */}
        <Card className="professional-card animate-fade-in">
          <CardContent className="p-6">
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="inbox" className="flex items-center gap-2">
                  <Inbox className="h-4 w-4" />
                  {language === 'ar' ? 'الوارد' : 'Inbox'}
                  {unreadCount > 0 && (
                    <Badge className="bg-red-600 text-white">{unreadCount}</Badge>
                  )}
                </TabsTrigger>
                <TabsTrigger value="sent" className="flex items-center gap-2">
                  <Send className="h-4 w-4" />
                  {language === 'ar' ? 'المرسلة' : 'Sent'}
                </TabsTrigger>
                <TabsTrigger value="drafts" className="flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  {language === 'ar' ? 'المسودات' : 'Drafts'}
                </TabsTrigger>
              </TabsList>

              <TabsContent value="inbox" className="mt-6">
                {renderMessagesList(inboxMessages, 'inbox')}
              </TabsContent>

              <TabsContent value="sent" className="mt-6">
                {renderMessagesList(sentMessages, 'sent')}
              </TabsContent>

              <TabsContent value="drafts" className="mt-6">
                {renderMessagesList(draftMessages, 'drafts')}
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        {/* Compose Dialog */}
        {showCompose && (
          <Dialog open={showCompose} onOpenChange={setShowCompose}>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>{language === 'ar' ? 'رسالة جديدة' : 'New Message'}</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label>{language === 'ar' ? 'إلى' : 'To'}</Label>
                  <Select value={composeData.to_user_id} onValueChange={(val) => setComposeData({ ...composeData, to_user_id: val })}>
                    <SelectTrigger>
                      <SelectValue placeholder={language === 'ar' ? 'اختر المستلم' : 'Select recipient'} />
                    </SelectTrigger>
                    <SelectContent className="max-h-[300px] overflow-y-auto">
                      <SelectItem value="ALL">{language === 'ar' ? 'الكل' : 'All Users'}</SelectItem>
                      {allUsers && allUsers.length > 0 ? (
                        allUsers.map((u) => (
                          <SelectItem key={u.user_id || u.id} value={u.user_id || u.id}>
                            {u.full_name} ({u.email})
                          </SelectItem>
                        ))
                      ) : (
                        <SelectItem value="loading" disabled>
                          {language === 'ar' ? 'جاري التحميل...' : 'Loading...'}
                        </SelectItem>
                      )}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>{language === 'ar' ? 'الموضوع' : 'Subject'}</Label>
                  <Input
                    value={composeData.subject}
                    onChange={(e) => setComposeData({ ...composeData, subject: e.target.value })}
                    placeholder={language === 'ar' ? 'أدخل موضوع الرسالة' : 'Enter message subject'}
                  />
                </div>
                <div>
                  <Label>{language === 'ar' ? 'المحتوى' : 'Message'}</Label>
                  <Textarea
                    value={composeData.body}
                    onChange={(e) => setComposeData({ ...composeData, body: e.target.value })}
                    placeholder={language === 'ar' ? 'اكتب رسالتك هنا...' : 'Write your message here...'}
                    rows={8}
                  />
                </div>
                <div className="flex gap-2 justify-end">
                  <Button variant="outline" onClick={() => handleSendMessage(true)} disabled={loading}>
                    {language === 'ar' ? 'حفظ كمسودة' : 'Save as Draft'}
                  </Button>
                  <Button onClick={() => handleSendMessage(false)} disabled={loading} className="medical-blue">
                    <Send className="h-4 w-4 mr-2" />
                    {language === 'ar' ? 'إرسال' : 'Send'}
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        )}

        {/* View Message Dialog */}
        {selectedMessage && (
          <Dialog open={!!selectedMessage} onOpenChange={() => setSelectedMessage(null)}>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>{selectedMessage.subject}</DialogTitle>
                <DialogDescription>
                  {language === 'ar' ? 'من:' : 'From:'} {selectedMessage.from_user_name} | {formatDate(selectedMessage.created_at)}
                </DialogDescription>
              </DialogHeader>
              <div className="mt-4">
                <div className="bg-gray-50 p-4 rounded-lg whitespace-pre-wrap">
                  {selectedMessage.body}
                </div>
              </div>
            </DialogContent>
          </Dialog>
        )}
      </main>
      <Footer />
    </div>
  );
};

export default Messages;
