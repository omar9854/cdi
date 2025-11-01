import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { LogOut, FileText, History, Home, Languages, Mail } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';

const Navbar = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { language, toggleLanguage, t } = useLanguage();
  const isImpersonating = localStorage.getItem('is_impersonating') === 'true';

  const handleExitImpersonation = () => {
    // Check if it was admin or supervisor who impersonated
    const adminToken = localStorage.getItem('admin_token_backup');
    const supervisorToken = localStorage.getItem('supervisor_token_backup');
    
    if (adminToken) {
      localStorage.setItem('token', adminToken);
      localStorage.removeItem('admin_token_backup');
      localStorage.removeItem('is_impersonating');
      window.location.href = '/admin';
    } else if (supervisorToken) {
      localStorage.setItem('token', supervisorToken);
      localStorage.removeItem('supervisor_token_backup');
      localStorage.removeItem('is_impersonating');
      window.location.href = '/supervisor';
    }
  };

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="medical-blue text-white shadow-lg" data-testid="navbar">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 flex items-center justify-center">
                <img src="/logo.jpeg" alt="Logo" className="w-full h-full object-contain rounded-lg" />
              </div>
              <div>
                <h1 className="text-xl font-bold">{t('appName')}</h1>
                <p className="text-sm text-blue-100">{t('appSubtitle')}</p>
              </div>
            </div>

            <div className="hidden md:flex gap-2">
              <Button
                variant={isActive('/dashboard') ? 'secondary' : 'ghost'}
                onClick={() => navigate('/dashboard')}
                className={isActive('/dashboard') ? '' : 'text-white hover:bg-white/10'}
                data-testid="nav-dashboard"
              >
                {language === 'ar' ? <Home className="ml-2 w-4 h-4" /> : <Home className="mr-2 w-4 h-4" />}
                {t('home')}
              </Button>
              {user.role === 'admin' && (
                <Button
                  variant={isActive('/admin') ? 'secondary' : 'ghost'}
                  onClick={() => navigate('/admin')}
                  className={isActive('/admin') ? '' : 'text-white hover:bg-white/10'}
                  data-testid="nav-admin"
                >
                  {language === 'ar' ? <History className="ml-2 w-4 h-4" /> : <History className="mr-2 w-4 h-4" />}
                  {language === 'ar' ? 'الأدمن' : 'Admin'}
                </Button>
              )}
              {(user.role === 'supervisor' || user.role === 'admin') && (
                <Button
                  variant={isActive('/supervisor') ? 'secondary' : 'ghost'}
                  onClick={() => navigate('/supervisor')}
                  className={isActive('/supervisor') ? '' : 'text-white hover:bg-white/10'}
                  data-testid="nav-supervisor"
                >
                  {language === 'ar' ? <FileText className="ml-2 w-4 h-4" /> : <FileText className="mr-2 w-4 h-4" />}
                  {language === 'ar' ? 'المشرف' : 'Supervisor'}
                </Button>
              )}
              <Button
                variant={isActive('/history') ? 'secondary' : 'ghost'}
                onClick={() => navigate('/history')}
                className={isActive('/history') ? '' : 'text-white hover:bg-white/10'}
                data-testid="nav-history"
              >
                {language === 'ar' ? <History className="ml-2 w-4 h-4" /> : <History className="mr-2 w-4 h-4" />}
                {t('history')}
              </Button>
              {!isImpersonating && (
                <Button
                  variant={isActive('/messages') ? 'secondary' : 'ghost'}
                  onClick={() => navigate('/messages')}
                  className={isActive('/messages') ? '' : 'text-white hover:bg-white/10'}
                  data-testid="nav-messages"
                >
                  {language === 'ar' ? <Mail className="ml-2 w-4 h-4" /> : <Mail className="mr-2 w-4 h-4" />}
                  {language === 'ar' ? 'البريد' : 'Messages'}
                </Button>
              )}
            </div>
          </div>

          <div className="flex items-center gap-4">
            {isImpersonating && (
              <Button
                variant="destructive"
                onClick={handleExitImpersonation}
                className="bg-red-600 hover:bg-red-700"
                title={language === 'ar' ? 'الخروج من الحساب' : 'Exit Impersonation'}
              >
                {language === 'ar' ? '← الخروج من الحساب' : 'Exit Impersonation →'}
              </Button>
            )}
            <Button
              variant="ghost"
              onClick={toggleLanguage}
              className="text-white hover:bg-white/10"
              data-testid="language-toggle"
              title={language === 'ar' ? 'Switch to English' : 'التبديل إلى العربية'}
            >
              {language === 'ar' ? <Languages className="ml-2 w-4 h-4" /> : <Languages className="mr-2 w-4 h-4" />}
              {language === 'ar' ? 'EN' : 'ع'}
            </Button>
            <span className="text-white">{user.full_name}</span>
            <Button
              variant="ghost"
              onClick={onLogout}
              className="text-white hover:bg-white/10"
              data-testid="logout-button"
            >
              {language === 'ar' ? <LogOut className="ml-2 w-4 h-4" /> : <LogOut className="mr-2 w-4 h-4" />}
              {t('logout')}
            </Button>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;