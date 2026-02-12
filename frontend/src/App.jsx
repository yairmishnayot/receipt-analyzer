import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import ReceiptForm from './components/ReceiptForm';
import CategoriesManager from './components/CategoriesManager';
import './styles/global.css';
import './styles/tabs.css';

function App() {
  const { i18n } = useTranslation();
  const [activeTab, setActiveTab] = useState('receipt');

  useEffect(() => {
    // Update HTML lang and dir attributes based on language
    const html = document.documentElement;
    html.setAttribute('lang', i18n.language);
    html.setAttribute('dir', i18n.language === 'he' ? 'rtl' : 'ltr');
  }, [i18n.language]);

  return (
    <div className="app">
      <div className="tabs">
        <button
          className={`tab ${activeTab === 'receipt' ? 'active' : ''}`}
          onClick={() => setActiveTab('receipt')}
        >
          📄 עיבוד קבלה
        </button>
        <button
          className={`tab ${activeTab === 'categories' ? 'active' : ''}`}
          onClick={() => setActiveTab('categories')}
        >
          🏷️ ניהול קטגוריות
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'receipt' && <ReceiptForm />}
        {activeTab === 'categories' && <CategoriesManager />}
      </div>
    </div>
  );
}

export default App;
