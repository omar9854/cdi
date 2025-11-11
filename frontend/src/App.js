import React, { useState, useEffect } from 'react';
import '@/App.css';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { LanguageProvider, useLanguage } from '@/contexts/LanguageContext';
import { Toaster } from 'sonner';
import Login from '@/pages/Login';
import Register from '@/pages/Register';
import ForgotPassword from '@/pages/ForgotPassword';
import ResetPassword from '@/pages/ResetPassword';
import Dashboard from '@/pages/Dashboard';
import NewNote from '@/pages/NewNote';
import EditNote from '@/pages/EditNote';
import Analysis from '@/pages/Analysis';
import History from '@/pages/History';
import Chat from '@/pages/ChatEnhanced';
import AdminDashboard from '@/pages/AdminDashboard';
import SupervisorDashboard from '@/pages/SupervisorDashboard';
import Messages from '@/pages/Messages';
import MFAVerification from '@/pages/MFAVerification';
import SecurityDashboard from '@/pages/SecurityDashboard';
import CodingSupervisor from '@/pages/CodingSupervisorPro';
import CoderWorkspace from '@/pages/CoderWorkspacePro';
import AuditorWorkspace from '@/pages/AuditorWorkspace';
import ChatWidget from '@/components/ChatWidget';

function AppContent() {
  const { t } = useLanguage();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const userData = localStorage.getItem('user');
    
    if (token && userData) {
      setUser(JSON.parse(userData));
    }
    setLoading(false);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
        <div className="text-xl text-blue-600">{t('loading')}</div>
      </div>
    );
  }

  return (
    <div className="App">
      <Toaster position="top-center" richColors closeButton />
      <BrowserRouter>
        {user && <ChatWidget user={user} />}
        <Routes>
          <Route path="/login" element={!user ? <Login setUser={setUser} /> : <Navigate to="/dashboard" />} />
          <Route path="/register" element={!user ? <Register setUser={setUser} /> : <Navigate to="/dashboard" />} />
          <Route path="/forgot-password" element={!user ? <ForgotPassword /> : <Navigate to="/dashboard" />} />
          <Route path="/reset-password" element={!user ? <ResetPassword /> : <Navigate to="/dashboard" />} />
          <Route path="/dashboard" element={user ? <Dashboard user={user} onLogout={handleLogout} /> : <Navigate to="/login" />} />
          <Route path="/admin" element={user && user.role === 'admin' ? <AdminDashboard user={user} onLogout={handleLogout} /> : <Navigate to="/dashboard" />} />
          <Route path="/supervisor" element={user && (user.role === 'supervisor' || user.role === 'admin') ? <SupervisorDashboard user={user} onLogout={handleLogout} /> : <Navigate to="/dashboard" />} />
          <Route path="/security" element={user && user.role === 'admin' ? <SecurityDashboard user={user} onLogout={handleLogout} /> : <Navigate to="/dashboard" />} />
          <Route path="/coding-supervisor" element={user && user.department === 'coding' && (user.role === 'supervisor' || user.role === 'admin') ? <CodingSupervisor user={user} onLogout={handleLogout} /> : <Navigate to="/dashboard" />} />
          <Route path="/coder" element={user && user.department === 'coding' && user.coding_role === 'coder' ? <CoderWorkspace user={user} onLogout={handleLogout} /> : <Navigate to="/dashboard" />} />
          <Route path="/auditor" element={user && user.department === 'coding' && user.coding_role === 'auditor' ? <AuditorWorkspace user={user} onLogout={handleLogout} /> : <Navigate to="/dashboard" />} />
          <Route path="/mfa-verify" element={!user ? <MFAVerification setUser={setUser} /> : <Navigate to="/dashboard" />} />
          <Route path="/messages" element={user ? <Messages user={user} onLogout={handleLogout} /> : <Navigate to="/login" />} />
          <Route path="/new-note" element={user ? <NewNote user={user} onLogout={handleLogout} /> : <Navigate to="/login" />} />
          <Route path="/edit-note/:noteId" element={user ? <EditNote user={user} onLogout={handleLogout} /> : <Navigate to="/login" />} />
          <Route path="/analysis/:noteId" element={user ? <Analysis user={user} onLogout={handleLogout} /> : <Navigate to="/login" />} />
          <Route path="/chat/:analysisId" element={user ? <Chat user={user} onLogout={handleLogout} /> : <Navigate to="/login" />} />
          <Route path="/history" element={user ? <History user={user} onLogout={handleLogout} /> : <Navigate to="/login" />} />
          <Route path="/" element={<Navigate to={user ? "/dashboard" : "/login"} />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

function App() {
  return (
    <LanguageProvider>
      <AppContent />
    </LanguageProvider>
  );
}

export default App;
