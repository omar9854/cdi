import React from 'react';
import { MessageCircle } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';

const WhatsAppSupport = () => {
  const { language, t } = useLanguage();
  const supportNumber = '966502468148';
  const supportMessage = language === 'ar' 
    ? 'مرحباً، أحتاج إلى مساعدة في استخدام منصة مركز الترميز الطبي وتحسين التوثيق السريري'
    : 'Hello, I need help with the Medical Coding & CDI Center platform';
  
  const whatsappLink = `https://wa.me/${supportNumber}?text=${encodeURIComponent(supportMessage)}`;

  return (
    <a
      href={whatsappLink}
      target="_blank"
      rel="noopener noreferrer"
      className="fixed bottom-6 z-50 bg-green-500 hover:bg-green-600 text-white rounded-full p-4 shadow-lg transition-all hover:scale-110 flex items-center justify-center"
      style={{ [language === 'ar' ? 'left' : 'right']: '24px' }}
      title={t('contactSupport')}
    >
      <MessageCircle className="h-6 w-6" />
    </a>
  );
};

export default WhatsAppSupport;
