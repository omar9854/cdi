import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { LogOut, FileText, History, Home, Languages } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';

const Navbar = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { language, toggleLanguage, t } = useLanguage();

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="medical-blue text-white shadow-lg" data-testid="navbar">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
                <FileText className="w-6 h-6" />
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
              <Button
                variant={isActive('/history') ? 'secondary' : 'ghost'}
                onClick={() => navigate('/history')}
                className={isActive('/history') ? '' : 'text-white hover:bg-white/10'}
                data-testid="nav-history"
              >
                {language === 'ar' ? <History className="ml-2 w-4 h-4" /> : <History className="mr-2 w-4 h-4" />}
                {t('history')}
              </Button>
            </div>
          </div>

          <div className="flex items-center gap-4">
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