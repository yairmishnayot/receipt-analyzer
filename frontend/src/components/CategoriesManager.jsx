import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import ItemCategoryManager from './ItemCategoryManager';
import CategoryRenameView from './CategoryRenameView';
import '../styles/categories.css';

/**
 * Main categories management component with tab navigation.
 * Provides two views:
 * 1. Item management - Edit category for specific items
 * 2. Category management - Rename categories globally
 */
function CategoriesManager() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState('items');

  return (
    <div className="categories-manager">
      <div className="categories-header">
        <h2>ניהול קטגוריות</h2>
      </div>

      {/* Tab navigation */}
      <div className="tabs">
        <button
          className={`tab-button ${activeTab === 'items' ? 'active' : ''}`}
          onClick={() => setActiveTab('items')}
        >
          🏷️ ניהול פריטים
        </button>
        <button
          className={`tab-button ${activeTab === 'categories' ? 'active' : ''}`}
          onClick={() => setActiveTab('categories')}
        >
          📝 ניהול קטגוריות
        </button>
      </div>

      {/* Tab content */}
      <div className="tab-content">
        {activeTab === 'items' ? (
          <ItemCategoryManager />
        ) : (
          <CategoryRenameView />
        )}
      </div>
    </div>
  );
}

export default CategoriesManager;
