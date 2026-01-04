import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { LogOut, FileText, History, Home, Languages, Mail, Shield, Brain } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

const Navbar = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { language, toggleLanguage, t } = useLanguage();
  const isImpersonating = localStorage.getItem('is_impersonating') === 'true';

  const handleExitImpersonation = async () => {
    const adminToken = localStorage.getItem('admin_token_backup');
    const supervisorToken = localStorage.getItem('supervisor_token_backup');
    
    if (adminToken) {
      localStorage.setItem('token', adminToken);
      localStorage.removeItem('admin_token_backup');
      localStorage.removeItem('is_impersonating');
      
      try {
        const response = await axios.get(`${API}/api/auth/me`, {
          headers: { Authorization: `Bearer ${adminToken}` }
        });
        localStorage.setItem('user', JSON.stringify(response.data));
      } catch (error) {
        console.error('Failed to fetch admin data:', error);
      }
      
      window.location.href = '/admin';
    } else if (supervisorToken) {
      localStorage.setItem('token', supervisorToken);
      localStorage.removeItem('supervisor_token_backup');
      localStorage.removeItem('is_impersonating');
      
      try {
        const response = await axios.get(`${API}/api/auth/me`, {
          headers: { Authorization: `Bearer ${supervisorToken}` }
        });
        localStorage.setItem('user', JSON.stringify(response.data));
      } catch (error) {
        console.error('Failed to fetch supervisor data:', error);
      }
      
      window.location.href = '/supervisor';
    }
  };

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="bg-gradient-to-r from-[#0066a1] to-[#00a99d] text-white shadow-2xl" data-testid="navbar">
      <div className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            {/* Logo and Brand */}
            <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate('/dashboard')}>
              <div className="w-12 h-12 flex items-center justify-center bg-white rounded-xl p-1">
                <img src="/nabeeh-logo.png" alt="نبيه Logo" className="w-full h-full object-contain" />
              </div>
              <div>
                <h1 className="text-xl font-bold">نـبـيـه | NABEEH</h1>
                <p className="text-xs text-white/80">
                  {language === 'ar' ? 'تحسين التوثيق السريري' : 'Clinical Documentation'}
                </p>
              </div>
            </div>

            {/* Navigation Links */}
            <div className="hidden md:flex gap-1">
              <Button
                variant={isActive('/dashboard') ? 'secondary' : 'ghost'}
                onClick={() => navigate('/dashboard')}
                className={isActive('/dashboard') ? 'bg-white/20' : 'text-white hover:bg-white/10'}
                data-testid="nav-dashboard"
              >
                {language === 'ar' ? <Home className="ml-2 w-4 h-4" /> : <Home className="mr-2 w-4 h-4" />}
                {t('home')}
              </Button>
              {user.role === 'admin' && (
                <>
                  <Button
                    variant={isActive('/admin') ? 'secondary' : 'ghost'}
                    onClick={() => navigate('/admin')}
                    className={isActive('/admin') ? 'bg-white/20' : 'text-white hover:bg-white/10'}
                    data-testid="nav-admin"
                  >
                    {language === 'ar' ? <History className="ml-2 w-4 h-4" /> : <History className="mr-2 w-4 h-4" />}
                    {language === 'ar' ? 'الإدارة' : 'Admin'}
                  </Button>
                  <Button
                    variant={isActive('/security') ? 'secondary' : 'ghost'}
                    onClick={() => navigate('/security')}
                    className={isActive('/security') ? 'bg-white/20' : 'text-white hover:bg-white/10'}
                    data-testid="nav-security"
                  >
                    {language === 'ar' ? <Shield className="ml-2 w-4 h-4" /> : <Shield className="mr-2 w-4 h-4" />}
                    {language === 'ar' ? 'الأمان' : 'Security'}
                  </Button>
                  <Button
                    variant={isActive('/ai-settings') ? 'secondary' : 'ghost'}
                    onClick={() => navigate('/ai-settings')}
                    className={isActive('/ai-settings') ? 'bg-white/20' : 'text-white hover:bg-white/10'}
                    data-testid="nav-ai-settings"
                  >
                    {language === 'ar' ? <Brain className="ml-2 w-4 h-4" /> : <Brain className="mr-2 w-4 h-4" />}
                    {language === 'ar' ? 'الذكاء الاصطناعي' : 'AI Settings'}
                  </Button>
                </>
              )}
              {(user.role === 'supervisor' || user.role === 'admin') && (
                <Button
                  variant={isActive('/supervisor') ? 'secondary' : 'ghost'}
                  onClick={() => navigate('/supervisor')}
                  className={isActive('/supervisor') ? 'bg-white/20' : 'text-white hover:bg-white/10'}
                  data-testid="nav-supervisor"
                >
                  {language === 'ar' ? <FileText className="ml-2 w-4 h-4" /> : <FileText className="mr-2 w-4 h-4" />}
                  {language === 'ar' ? 'المشرف' : 'Supervisor'}
                </Button>
              )}
              <Button
                variant={isActive('/history') ? 'secondary' : 'ghost'}
                onClick={() => navigate('/history')}
                className={isActive('/history') ? 'bg-white/20' : 'text-white hover:bg-white/10'}
                data-testid="nav-history"
              >
                {language === 'ar' ? <History className="ml-2 w-4 h-4" /> : <History className="mr-2 w-4 h-4" />}
                {t('history')}
              </Button>
              {!isImpersonating && (
                <Button
                  variant={isActive('/messages') ? 'secondary' : 'ghost'}
                  onClick={() => navigate('/messages')}
                  className={isActive('/messages') ? 'bg-white/20' : 'text-white hover:bg-white/10'}
                  data-testid="nav-messages"
                >
                  {language === 'ar' ? <Mail className="ml-2 w-4 h-4" /> : <Mail className="mr-2 w-4 h-4" />}
                  {language === 'ar' ? 'البريد' : 'Messages'}
                </Button>
              )}

              {/* Coding Department Links */}
              {user.department === 'coding' && (user.role === 'supervisor' || user.role === 'admin') && (
                <Button
                  variant={isActive('/coding-supervisor') ? 'secondary' : 'ghost'}
                  onClick={() => navigate('/coding-supervisor')}
                  className={isActive('/coding-supervisor') ? 'bg-white/20' : 'text-white hover:bg-white/10'}
                >
                  {language === 'ar' ? 'الترميز الطبي' : 'Medical Coding'}
                </Button>
              )}
              {user.department === 'coding' && user.coding_role === 'coder' && (
                <Button
                  variant={isActive('/coder') ? 'secondary' : 'ghost'}
                  onClick={() => navigate('/coder')}
                  className={isActive('/coder') ? 'bg-white/20' : 'text-white hover:bg-white/10'}
                >
                  {language === 'ar' ? 'منصة المرمز' : 'Coder Workspace'}
                </Button>
              )}
              {user.department === 'coding' && user.coding_role === 'auditor' && (
                <Button
                  variant={isActive('/auditor') ? 'secondary' : 'ghost'}
                  onClick={() => navigate('/auditor')}
                  className={isActive('/auditor') ? 'bg-white/20' : 'text-white hover:bg-white/10'}
                >
                  {language === 'ar' ? 'منصة المدقق' : 'Auditor Workspace'}
                </Button>
              )}
            </div>
          </div>

          <div className="flex items-center gap-3">
            {isImpersonating && (
              <Button
                variant="destructive"
                onClick={handleExitImpersonation}
                className="bg-red-600 hover:bg-red-700"
                title={language === 'ar' ? 'الخروج من الحساب' : 'Exit Impersonation'}
              >
                {language === 'ar' ? '← الخروج' : 'Exit →'}
              </Button>
            )}
            <Button
              variant="ghost"
              onClick={toggleLanguage}
              className="text-white hover:bg-white/10"
              data-testid="language-toggle"
              title={language === 'ar' ? 'Switch to English' : 'التبديل إلى العربية'}
            >
              {language === 'ar' ? <Languages className="ml-1 w-4 h-4" /> : <Languages className="mr-1 w-4 h-4" />}
              {language === 'ar' ? 'EN' : 'ع'}
            </Button>
            <span className="text-white/90 text-sm hidden sm:block">{user.full_name}</span>
            <Button
              variant="ghost"
              onClick={onLogout}
              className="text-white hover:bg-white/10"
              data-testid="logout-button"
            >
              {language === 'ar' ? <LogOut className="ml-1 w-4 h-4" /> : <LogOut className="mr-1 w-4 h-4" />}
              {t('logout')}
            </Button>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
