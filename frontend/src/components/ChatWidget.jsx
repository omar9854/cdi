import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { MessageCircle, X, Send, Minimize2, Users, User, Check, CheckCheck } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ChatWidget = ({ user }) => {
  const { language } = useLanguage();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [filteredMessages, setFilteredMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [selectedUser, setSelectedUser] = useState('ALL');
  const [users, setUsers] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const messagesEndRef = useRef(null);
  const markedAsReadRef = useRef(new Set()); // Track which messages have been marked as read

  // Fetch users list
  useEffect(() => {
    if (user && isOpen) {
      fetchUsers();
    }
  }, [user, isOpen]);

  // Fetch messages periodically (real-time simulation)
  useEffect(() => {
    if (user) {
      fetchMessages();
      const interval = setInterval(fetchMessages, 5000); // Poll every 5 seconds
      return () => clearInterval(interval);
    }
  }, [user]);

  // Filter messages based on selected user
  useEffect(() => {
    if (selectedUser === 'ALL') {
      setFilteredMessages(messages);
    } else {
      // Show messages between current user and selected user
      const filtered = messages.filter(msg => 
        (msg.from_user_id === user.id && msg.to_user_id === selectedUser) ||
        (msg.from_user_id === selectedUser && msg.to_user_id === user.id) ||
        msg.to_user_id === 'ALL'
      );
      setFilteredMessages(filtered);
    }
  }, [messages, selectedUser, user]);

  // Auto-scroll to bottom
  useEffect(() => {
    scrollToBottom();
  }, [filteredMessages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchUsers = async () => {
    try {
      const token = localStorage.getItem('token');
      
      // Try supervisor/employees endpoint first (works for admin and supervisor)
      try {
        const response = await axios.get(`${API}/supervisor/employees`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        if (response.data && Array.isArray(response.data)) {
          const userList = response.data
            .filter(u => u.id && u.id !== user.id)
            .map(u => ({
              id: u.id,
              name: u.full_name || u.email,
              email: u.email,
              role: u.role || 'user'
            }));
          setUsers(userList);
          console.log('Users loaded from /supervisor/employees:', userList.length);
          return;
        }
      } catch (error) {
        console.log('Could not fetch from /supervisor/employees, trying /admin/users-statistics');
      }
      
      // Fallback to admin endpoint
      try {
        const response = await axios.get(`${API}/admin/users-statistics`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        if (response.data.statistics) {
          const userList = response.data.statistics
            .filter(u => u.id && u.id !== user.id)
            .map(u => ({
              id: u.id,
              name: u.full_name || u.email,
              email: u.email,
              role: u.role || 'user'
            }));
          setUsers(userList);
          console.log('Users loaded from /admin/users-statistics:', userList.length);
        }
      } catch (error) {
        console.error('Could not fetch users from any endpoint:', error);
        // Load at least the current user's info
        setUsers([]);
      }
    } catch (error) {
      console.error('Error fetching users:', error);
    }
  };

  const fetchMessages = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/messages/inbox`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.messages) {
        console.log('Messages fetched:', response.data.messages.length);
        console.log('Sample message:', response.data.messages[0]);
        setMessages(response.data.messages);
        
        // Count unread messages that are NOT from current user (only received messages)
        const unread = response.data.messages.filter(m => 
          !m.is_read && m.from_user_id !== user.id
        ).length;
        setUnreadCount(unread);
        console.log('Unread count:', unread);
      }
    } catch (error) {
      console.error('Error fetching messages:', error);
    }
  };

  const sendMessage = async () => {
    if (!newMessage.trim()) return;

    try {
      const token = localStorage.getItem('token');
      console.log('Sending message to:', selectedUser);
      console.log('Message:', newMessage);
      
      const response = await axios.post(`${API}/messages/send`, {
        to_user_id: selectedUser,
        subject: language === 'ar' ? 'رسالة شات' : 'Chat Message',
        body: newMessage,  // Changed from 'message' to 'body'
        is_draft: false
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      console.log('Message sent successfully:', response.data);
      setNewMessage('');
      
      // Immediate refresh
      setTimeout(() => {
        fetchMessages();
      }, 500);
    } catch (error) {
      console.error('Error sending message:', error);
      console.error('Error details:', error.response?.data);
      alert(language === 'ar' ? 'فشل إرسال الرسالة. يرجى المحاولة مرة أخرى.' : 'Failed to send message. Please try again.');
    }
  };

  const markAsRead = async (messageId) => {
    try {
      const token = localStorage.getItem('token');
      console.log('Marking message as read:', messageId);
      await axios.post(`${API}/messages/${messageId}/read`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Update messages state immediately without full refresh
      setMessages(prevMessages => 
        prevMessages.map(msg => 
          msg.id === messageId ? { ...msg, is_read: true } : msg
        )
      );
      
      // Update unread count
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      console.error('Error marking as read:', error);
    }
  };

  // Mark all visible unread messages as read when chat opens
  useEffect(() => {
    if (isOpen && filteredMessages.length > 0 && users.length > 0) {
      const unreadMessages = filteredMessages.filter(msg => 
        !msg.is_read && msg.from_user_id !== user.id
      );
      
      // Mark each unread message as read
      unreadMessages.forEach(msg => {
        markAsRead(msg.id);
      });
    }
  }, [isOpen, selectedUser, filteredMessages.length]); // Trigger when opening chat or changing user

  const formatTime = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString(language === 'ar' ? 'ar-SA' : 'en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getUserName = (userId) => {
    if (userId === 'ALL') return language === 'ar' ? 'الكل' : 'All';
    if (userId === user.id) return language === 'ar' ? 'أنت' : 'You';
    
    const foundUser = users.find(u => u.id === userId);
    if (foundUser) return foundUser.name;
    
    // Fallback: try to get from messages
    const msg = messages.find(m => m.from_user_id === userId);
    if (msg && msg.from_user_name) return msg.from_user_name;
    
    return language === 'ar' ? 'مستخدم' : 'User';
  };

  const getUserRole = (userId) => {
    const foundUser = users.find(u => u.id === userId);
    return foundUser?.role || 'user';
  };

  const getRoleIcon = (role) => {
    if (role === 'admin') return '👑';
    if (role === 'supervisor') return '👨‍💼';
    return '👤';
  };

  if (!user) return null;

  return (
    <>
      {/* Chat Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 bg-blue-600 hover:bg-blue-700 text-white rounded-full p-4 shadow-2xl transition-all duration-300 z-50 flex items-center justify-center hover:scale-110"
        >
          <MessageCircle className="h-6 w-6" />
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-6 w-6 flex items-center justify-center font-bold animate-pulse">
              {unreadCount > 99 ? '99+' : unreadCount}
            </span>
          )}
        </button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 w-96 h-[600px] bg-white rounded-2xl shadow-2xl flex flex-col z-50 border border-gray-200">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-4 rounded-t-2xl flex items-center justify-between">
            <div className="flex items-center gap-2">
              <MessageCircle className="h-5 w-5" />
              <div>
                <h3 className="font-bold">{language === 'ar' ? 'المحادثات' : 'Chat'}</h3>
                <p className="text-xs text-blue-100">
                  {selectedUser === 'ALL' 
                    ? (language === 'ar' ? 'محادثة جماعية' : 'Group chat')
                    : (language === 'ar' ? 'محادثة خاصة' : 'Private chat')
                  }
                </p>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setIsOpen(false)}
                className="hover:bg-blue-800 p-1 rounded transition-colors"
              >
                <Minimize2 className="h-5 w-5" />
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="hover:bg-blue-800 p-1 rounded transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          </div>

          {/* User Selector */}
          <div className="bg-gradient-to-r from-gray-50 to-gray-100 p-3 border-b">
            <label className="text-xs text-gray-600 mb-1 block font-medium">
              {language === 'ar' ? 'إرسال إلى:' : 'Send to:'}
            </label>
            <select
              value={selectedUser}
              onChange={(e) => setSelectedUser(e.target.value)}
              className="w-full p-2.5 border-2 border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
            >
              <option value="ALL">
                📢 {language === 'ar' ? 'الجميع (محادثة عامة)' : 'Everyone (Public chat)'}
              </option>
              <optgroup label={language === 'ar' ? 'المستخدمون' : 'Users'}>
                {users.map(u => (
                  <option key={u.id} value={u.id}>
                    {getRoleIcon(u.role)} {u.name}
                  </option>
                ))}
              </optgroup>
            </select>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50">
            {filteredMessages.length === 0 ? (
              <div className="text-center text-gray-400 mt-20">
                <MessageCircle className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p className="text-sm">
                  {selectedUser === 'ALL' 
                    ? (language === 'ar' ? 'لا توجد رسائل عامة' : 'No public messages')
                    : (language === 'ar' ? 'ابدأ محادثة جديدة' : 'Start a new conversation')
                  }
                </p>
              </div>
            ) : (
              filteredMessages.map((msg) => {
                const isMyMessage = msg.from_user_id === user.id;
                const isToAll = msg.to_user_id === 'ALL';
                
                return (
                  <div
                    key={msg.id}
                    className={`flex ${isMyMessage ? 'justify-end' : 'justify-start'}`}
                    onClick={() => !msg.is_read && !isMyMessage && markAsRead(msg.id)}
                  >
                    <div
                      className={`max-w-[75%] rounded-2xl p-3 ${
                        isMyMessage
                          ? 'bg-blue-600 text-white rounded-br-none'
                          : 'bg-white text-gray-800 rounded-bl-none shadow-md'
                      }`}
                    >
                      {!isMyMessage && (
                        <div className="text-xs font-semibold mb-1 opacity-75 flex items-center gap-1">
                          {getRoleIcon(getUserRole(msg.from_user_id))}
                          {getUserName(msg.from_user_id)}
                        </div>
                      )}
                      {isToAll && (
                        <div className={`text-[10px] mb-1 ${isMyMessage ? 'text-blue-200' : 'text-gray-500'}`}>
                          📢 {language === 'ar' ? 'رسالة عامة' : 'Public message'}
                        </div>
                      )}
                      <p className="text-sm break-words">{msg.message}</p>
                      <div className={`text-xs mt-1 flex items-center gap-1 ${isMyMessage ? 'text-blue-100 justify-end' : 'text-gray-400'}`}>
                        {formatTime(msg.created_at)}
                        {isMyMessage && (
                          <span>
                            {msg.is_read ? <CheckCheck className="h-3 w-3" /> : <Check className="h-3 w-3" />}
                          </span>
                        )}
                        {!msg.is_read && !isMyMessage && (
                          <span className="ml-2 bg-red-500 text-white px-2 py-0.5 rounded-full text-[10px]">
                            {language === 'ar' ? 'جديد' : 'New'}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="p-4 bg-white border-t rounded-b-2xl">
            <div className="flex gap-2">
              <input
                type="text"
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                placeholder={
                  selectedUser === 'ALL'
                    ? (language === 'ar' ? 'رسالة للجميع...' : 'Message to everyone...')
                    : (language === 'ar' ? `رسالة إلى ${getUserName(selectedUser)}...` : `Message to ${getUserName(selectedUser)}...`)
                }
                className="flex-1 p-3 border-2 border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              />
              <button
                onClick={sendMessage}
                disabled={!newMessage.trim()}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white p-3 rounded-xl transition-all hover:scale-105"
              >
                <Send className="h-5 w-5" />
              </button>
            </div>
            <div className="text-xs text-gray-500 mt-2 text-center">
              {language === 'ar' 
                ? 'اضغط Enter للإرسال' 
                : 'Press Enter to send'
              }
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default ChatWidget;
