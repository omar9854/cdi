import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { MessageCircle, X, Send, Minimize2, Users, User } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ChatWidget = ({ user }) => {
  const { language } = useLanguage();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [selectedUser, setSelectedUser] = useState('ALL');
  const [users, setUsers] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const messagesEndRef = useRef(null);

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

  // Auto-scroll to bottom
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchUsers = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/admin/users-statistics`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.statistics) {
        const userList = response.data.statistics
          .filter(u => u.id && u.id !== user.id)
          .map(u => ({
            id: u.id,
            name: u.full_name || u.email,
            email: u.email
          }));
        setUsers(userList);
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
        setMessages(response.data.messages);
        
        // Count unread messages
        const unread = response.data.messages.filter(m => !m.is_read).length;
        setUnreadCount(unread);
      }
    } catch (error) {
      console.error('Error fetching messages:', error);
    }
  };

  const sendMessage = async () => {
    if (!newMessage.trim()) return;

    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/messages/send`, {
        to_user_id: selectedUser,
        subject: language === 'ar' ? 'رسالة شات' : 'Chat Message',
        message: newMessage,
        is_draft: false
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setNewMessage('');
      fetchMessages(); // Refresh messages
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  const markAsRead = async (messageId) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/messages/${messageId}/read`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchMessages();
    } catch (error) {
      console.error('Error marking as read:', error);
    }
  };

  const formatTime = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString(language === 'ar' ? 'ar-SA' : 'en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (!user) return null;

  return (
    <>
      {/* Chat Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 bg-blue-600 hover:bg-blue-700 text-white rounded-full p-4 shadow-2xl transition-all duration-300 z-50 flex items-center justify-center"
        >
          <MessageCircle className="h-6 w-6" />
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-6 w-6 flex items-center justify-center font-bold animate-pulse">
              {unreadCount}
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
              <h3 className="font-bold">{language === 'ar' ? 'المحادثات' : 'Chat'}</h3>
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
          <div className="bg-gray-50 p-3 border-b">
            <select
              value={selectedUser}
              onChange={(e) => setSelectedUser(e.target_value)}
              className="w-full p-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="ALL">{language === 'ar' ? '📢 الكل' : '📢 All'}</option>
              {users.map(u => (
                <option key={u.id} value={u.id}>
                  👤 {u.name}
                </option>
              ))}
            </select>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50">
            {messages.length === 0 ? (
              <div className="text-center text-gray-400 mt-20">
                <MessageCircle className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>{language === 'ar' ? 'لا توجد رسائل' : 'No messages'}</p>
              </div>
            ) : (
              messages.map((msg) => {
                const isMyMessage = msg.from_user_id === user.id;
                return (
                  <div
                    key={msg.id}
                    className={`flex ${isMyMessage ? 'justify-end' : 'justify-start'}`}
                    onClick={() => !msg.is_read && markAsRead(msg.id)}
                  >
                    <div
                      className={`max-w-[75%] rounded-2xl p-3 ${
                        isMyMessage
                          ? 'bg-blue-600 text-white rounded-br-none'
                          : 'bg-white text-gray-800 rounded-bl-none shadow-md'
                      }`}
                    >
                      {!isMyMessage && (
                        <div className="text-xs font-semibold mb-1 opacity-75">
                          {msg.from_user_name || language === 'ar' ? 'مستخدم' : 'User'}
                        </div>
                      )}
                      <p className="text-sm break-words">{msg.message}</p>
                      <div className={`text-xs mt-1 ${isMyMessage ? 'text-blue-100' : 'text-gray-400'}`}>
                        {formatTime(msg.created_at)}
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
                placeholder={language === 'ar' ? 'اكتب رسالة...' : 'Type a message...'}
                className="flex-1 p-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              />
              <button
                onClick={sendMessage}
                disabled={!newMessage.trim()}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white p-3 rounded-xl transition-colors"
              >
                <Send className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default ChatWidget;
