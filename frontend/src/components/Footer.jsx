import React from 'react';
import { useLanguage } from '@/contexts/LanguageContext';

const Footer = () => {
  const { language } = useLanguage();
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-gradient-to-r from-blue-900 to-indigo-900 text-white py-6 mt-auto">
      <div className="container mx-auto px-4">
        <div className="flex flex-col md:flex-row justify-between items-center gap-4">
          {/* Copyright */}
          <div className="text-center md:text-right">
            <p className="text-sm">
              {language === 'ar' ? (
                <>
                  © {currentYear} جميع الحقوق محفوظة
                  <span className="mx-2">|</span>
                  <span className="font-semibold">عمر المغذوي</span>
                </>
              ) : (
                <>
                  © {currentYear} All Rights Reserved
                  <span className="mx-2">|</span>
                  <span className="font-semibold">Omar Almaghthawi</span>
                </>
              )}
            </p>
          </div>

          {/* App Name */}
          <div className="text-center">
            <p className="text-sm font-medium">
              {language === 'ar' 
                ? 'إدارة تحسين التوثيق السريري - تجمع المدينة المنورة الصحي'
                : 'نـبـيـه | NABIH - إدارة تحسين التوثيق السريري'
              }
            </p>
          </div>

          {/* Version */}
          <div className="text-center md:text-left">
            <p className="text-xs text-blue-200">
              {language === 'ar' ? 'الإصدار' : 'Version'} 2.0
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
