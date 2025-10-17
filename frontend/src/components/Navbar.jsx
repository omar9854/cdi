import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { LogOut, FileText, History, Home } from 'lucide-react';

const Navbar = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const location = useLocation();

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
                <h1 className="text-xl font-bold">مركز الترميز الطبي</h1>
                <p className="text-sm text-blue-100">تحسين التوثيق السريري</p>
              </div>
            </div>

            <div className="hidden md:flex gap-2">
              <Button
                variant={isActive('/dashboard') ? 'secondary' : 'ghost'}
                onClick={() => navigate('/dashboard')}
                className={isActive('/dashboard') ? '' : 'text-white hover:bg-white/10'}
                data-testid="nav-dashboard"
              >
                <Home className="ml-2 w-4 h-4" /> الرئيسية
              </Button>
              <Button
                variant={isActive('/history') ? 'secondary' : 'ghost'}
                onClick={() => navigate('/history')}
                className={isActive('/history') ? '' : 'text-white hover:bg-white/10'}
                data-testid="nav-history"
              >
                <History className="ml-2 w-4 h-4" /> السجل
              </Button>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <span className="text-white">{user.full_name}</span>
            <Button
              variant="ghost"
              onClick={onLogout}
              className="text-white hover:bg-white/10"
              data-testid="logout-button"
            >
              <LogOut className="ml-2 w-4 h-4" /> تسجيل الخروج
            </Button>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;