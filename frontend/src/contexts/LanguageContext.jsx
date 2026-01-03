import React, { createContext, useState, useContext, useEffect } from 'react';

const LanguageContext = createContext();

export const translations = {
  ar: {
    // Auth
    login: 'تسجيل الدخول',
    register: 'إنشاء حساب جديد',
    email: 'البريد الإلكتروني',
    password: 'كلمة المرور',
    fullName: 'الاسم الكامل',
    phoneNumber: 'رقم الجوال',
    alreadyHaveAccount: 'لديك حساب بالفعل؟',
    dontHaveAccount: 'ليس لديك حساب؟',
    signupNow: 'سجل الآن',
    loginNow: 'سجل الدخول',
    forgotPassword: 'نسيت كلمة المرور؟',
    resetPassword: 'إعادة تعيين كلمة المرور',
    sendResetLink: 'إرسال رابط إعادة التعيين',
    backToLogin: 'العودة لتسجيل الدخول',
    resetLinkSent: 'تم إرسال رابط إعادة التعيين إلى بريدك الإلكتروني',
    newPassword: 'كلمة المرور الجديدة',
    confirmPassword: 'تأكيد كلمة المرور',
    resetPasswordTitle: 'إعادة تعيين كلمة المرور',
    support: 'الدعم الفني',
    contactSupport: 'تواصل مع الدعم',
    
    // App name
    appName: 'إدارة تحسين التوثيق السريري',
    appSubtitle: 'تجمع المدينة المنورة الصحي',
    
    // Dashboard
    dashboard: 'لوحة التحكم',
    welcome: 'مرحباً بك',
    newNote: 'ملاحظة جديدة',
    addNewNote: 'أضف ملاحظات سريرية جديدة للتحليل',
    history: 'السجل',
    viewAllAnalyses: 'عرض جميع التحليلات السابقة',
    recentNotes: 'الملاحظات الأخيرة',
    noNotes: 'لا توجد ملاحظات حتى الآن',
    createFirstNote: 'إنشاء أول ملاحظة',
    
    // New Note
    newClinicalNote: 'ملاحظة سريرية جديدة',
    noteTitle: 'رمز المريض',
    noteTitlePlaceholder: 'مثال: رمز المريض - P12345',
    doctorNotes: 'ملاحظات الأطباء',
    specialty: 'التخصص',
    selectSpecialty: 'اختر التخصص',
    noteText: 'نص الملاحظة',
    notePlaceholder: 'أدخل ملاحظات الطبيب هنا...',
    addAnotherNote: 'إضافة ملاحظة أخرى',
    removeNote: 'إزالة الملاحظة',
    saveAndAnalyze: 'حفظ ومتابعة للتحليل',
    saving: 'جاري الحفظ...',
    back: 'العودة',
    enterNoteDetails: 'أدخل تفاصيل الملاحظة السريرية',
    
    // Analysis
    analysisOf: 'مراجعة تحسين التوثيق لـ',
    clinicalNotes: 'الملاحظات السريرية',
    readyToAnalyze: 'جاهز للمراجعة',
    aiAnalysisDescription: 'استخدم الذكاء الاصطناعي لمراجعة التوثيق وتحديد الفجوات',
    analyzeWithAI: 'مراجعة بالذكاء الاصطناعي',
    analyzing: 'جاري المراجعة...',
    diagnosesToDocument: 'التشخيصات التي يجب توثيقها',
    missingDocumentation: 'التوثيق الناقص',
    documentationGaps: 'الثغرات في التوثيق',
    queriesForDoctor: 'استفسارات للطبيب',
    recommendations: 'توصيات لتحسين التوثيق',
    comprehensiveSummary: 'ملخص مراجعة التوثيق',
    exportPDF: 'تصدير PDF',
    exportExcel: 'تصدير Excel',
    discussWithAI: 'مناقشة مع الذكاء الاصطناعي',
    
    // Chat
    chatWithAI: 'محادثة مع الذكاء الاصطناعي',
    askQuestion: 'اسأل سؤالاً حول التحليل...',
    send: 'إرسال',
    sending: 'جاري الإرسال...',
    
    // History
    analysisHistory: 'سجل التحليلات',
    allPreviousAnalyses: 'جميع التحليلات السابقة',
    noHistory: 'لا يوجد سجل تحليلات حتى الآن',
    diagnoses: 'تشخيص',
    gaps: 'ثغرة',
    queries: 'استفسار',
    
    // Navbar
    home: 'الرئيسية',
    logout: 'تسجيل الخروج',
    
    // Messages
    loading: 'جاري التحميل...',
    loginSuccess: 'تم تسجيل الدخول بنجاح!',
    registerSuccess: 'تم التسجيل بنجاح!',
    noteSaved: 'تم حفظ الملاحظة بنجاح!',
    analysisComplete: 'تم التحليل بنجاح!',
    exportSuccess: 'تم تصدير التحليل بنجاح!',
    error: 'حدث خطأ',
  },
  en: {
    // Auth
    login: 'Login',
    register: 'Create New Account',
    email: 'Email',
    password: 'Password',
    fullName: 'Full Name',
    phoneNumber: 'Phone Number',
    alreadyHaveAccount: 'Already have an account?',
    dontHaveAccount: "Don't have an account?",
    signupNow: 'Sign Up Now',
    loginNow: 'Login',
    forgotPassword: 'Forgot Password?',
    resetPassword: 'Reset Password',
    sendResetLink: 'Send Reset Link',
    backToLogin: 'Back to Login',
    resetLinkSent: 'Password reset link has been sent to your email',
    newPassword: 'New Password',
    confirmPassword: 'Confirm Password',
    resetPasswordTitle: 'Reset Your Password',
    support: 'Technical Support',
    contactSupport: 'Contact Support',
    
    // App name
    appName: 'Nabeeh Platform',
    appSubtitle: 'Madinah Health Cluster',
    
    // Dashboard
    dashboard: 'Dashboard',
    welcome: 'Welcome',
    newNote: 'New Note',
    addNewNote: 'Add new clinical notes for analysis',
    history: 'History',
    viewAllAnalyses: 'View all previous analyses',
    recentNotes: 'Recent Notes',
    noNotes: 'No notes yet',
    createFirstNote: 'Create First Note',
    
    // New Note
    newClinicalNote: 'New Clinical Note',
    noteTitle: 'Patient ID',
    noteTitlePlaceholder: 'Example: Patient ID - P12345',
    doctorNotes: "Doctor's Notes",
    specialty: 'Specialty',
    selectSpecialty: 'Select Specialty',
    noteText: 'Note Text',
    notePlaceholder: "Enter doctor's note here...",
    addAnotherNote: 'Add Another Note',
    removeNote: 'Remove Note',
    saveAndAnalyze: 'Save and Continue to Analysis',
    saving: 'Saving...',
    back: 'Back',
    enterNoteDetails: 'Enter Clinical Note Details',
    
    // Analysis
    analysisOf: 'CDI Review of',
    clinicalNotes: 'Clinical Notes',
    readyToAnalyze: 'Ready for CDI Review',
    aiAnalysisDescription: 'Use AI to review documentation and identify gaps',
    analyzeWithAI: 'Review with AI',
    analyzing: 'Reviewing...',
    diagnosesToDocument: 'Diagnoses to Document',
    missingDocumentation: 'Missing Documentation',
    documentationGaps: 'Documentation Gaps',
    queriesForDoctor: 'Physician Queries',
    recommendations: 'Documentation Improvement Recommendations',
    comprehensiveSummary: 'CDI Review Summary',
    exportPDF: 'Export PDF',
    exportExcel: 'Export Excel',
    discussWithAI: 'Discuss with AI',
    
    // Chat
    chatWithAI: 'Chat with AI',
    askQuestion: 'Ask a question about the analysis...',
    send: 'Send',
    sending: 'Sending...',
    
    // History
    analysisHistory: 'Analysis History',
    allPreviousAnalyses: 'All Previous Analyses',
    noHistory: 'No analysis history yet',
    diagnoses: 'diagnosis',
    gaps: 'gap',
    queries: 'query',
    
    // Navbar
    home: 'Home',
    logout: 'Logout',
    
    // Messages
    loading: 'Loading...',
    loginSuccess: 'Login successful!',
    registerSuccess: 'Registration successful!',
    noteSaved: 'Note saved successfully!',
    analysisComplete: 'Analysis complete!',
    exportSuccess: 'Analysis exported successfully!',
    error: 'An error occurred',
  }
};

export const LanguageProvider = ({ children }) => {
  const [language, setLanguage] = useState('ar');
  
  useEffect(() => {
    const savedLang = localStorage.getItem('language') || 'ar';
    setLanguage(savedLang);
    document.dir = savedLang === 'ar' ? 'rtl' : 'ltr';
  }, []);
  
  const toggleLanguage = () => {
    const newLang = language === 'ar' ? 'en' : 'ar';
    setLanguage(newLang);
    localStorage.setItem('language', newLang);
    document.dir = newLang === 'ar' ? 'rtl' : 'ltr';
  };
  
  const t = (key) => translations[language][key] || key;
  
  return (
    <LanguageContext.Provider value={{ language, toggleLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within LanguageProvider');
  }
  return context;
};