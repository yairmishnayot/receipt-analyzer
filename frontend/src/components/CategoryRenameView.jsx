import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { getAllCategories, renameCategory } from '../services/categoriesApi';
import '../styles/categories.css';

/**
 * Component for renaming category names globally.
 * Shows unique categories with item counts and allows inline editing.
 */
function CategoryRenameView() {
  const { t } = useTranslation();
  const [uniqueCategories, setUniqueCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editingCategory, setEditingCategory] = useState(null);
  const [newName, setNewName] = useState('');
  const [saving, setSaving] = useState(false);
  const [successMessage, setSuccessMessage] = useState(null);

  // Load categories on mount
  useEffect(() => {
    loadCategories();
  }, []);

  // Auto-dismiss success message after 5 seconds
  useEffect(() => {
    if (successMessage) {
      const timer = setTimeout(() => {
        setSuccessMessage(null);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [successMessage]);

  /**
   * Load all categories and extract unique category names with counts
   */
  const loadCategories = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getAllCategories();

      // Group items by category and count
      const categoryMap = new Map();
      data.items.forEach(item => {
        const category = item.category;
        if (!categoryMap.has(category)) {
          categoryMap.set(category, { name: category, count: 0, items: [] });
        }
        const catData = categoryMap.get(category);
        catData.count += 1;
        catData.items.push(item.item_name);
      });

      // Convert to array and sort by name
      const categories = Array.from(categoryMap.values()).sort((a, b) =>
        a.name.localeCompare(b.name, 'he')
      );

      setUniqueCategories(categories);
    } catch (err) {
      console.error('Failed to load categories:', err);
      setError(err.response?.data?.detail || 'שגיאה בטעינת הקטגוריות');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Enter edit mode for a category
   */
  const handleEdit = (category) => {
    setEditingCategory(category.name);
    setNewName(category.name);
    setError(null);
    setSuccessMessage(null);
  };

  /**
   * Cancel editing
   */
  const handleCancel = () => {
    setEditingCategory(null);
    setNewName('');
    setError(null);
  };

  /**
   * Save renamed category
   */
  const handleSave = async (oldName) => {
    // Validation
    if (!newName.trim()) {
      setError('שם הקטגוריה לא יכול להיות ריק');
      return;
    }

    if (newName === oldName) {
      setError('הקטגוריה החדשה זהה לקיימת');
      return;
    }

    try {
      setSaving(true);
      setError(null);

      const result = await renameCategory(oldName, newName);

      // Update local state optimistically
      setUniqueCategories(prevCategories =>
        prevCategories.map(cat =>
          cat.name === oldName ? { ...cat, name: newName } : cat
        ).sort((a, b) => a.name.localeCompare(b.name, 'he'))
      );

      // Show success message
      setSuccessMessage(
        `הקטגוריה '${oldName}' שונתה ל-'${newName}' - ${result.cache_items_updated} פריטים במטמון, ${result.sheets_rows_updated} שורות בגיליון`
      );

      // Exit edit mode
      setEditingCategory(null);
      setNewName('');

    } catch (err) {
      console.error('Failed to rename category:', err);
      setError(err.response?.data?.detail || 'שגיאה בשינוי שם הקטגוריה');
    } finally {
      setSaving(false);
    }
  };

  /**
   * Handle Enter key in input
   */
  const handleKeyPress = (e, oldName) => {
    if (e.key === 'Enter') {
      handleSave(oldName);
    } else if (e.key === 'Escape') {
      handleCancel();
    }
  };

  if (loading) {
    return (
      <div className="categories-loading">
        <div className="spinner"></div>
        <p>טוען קטגוריות...</p>
      </div>
    );
  }

  return (
    <div className="category-rename-view">
      <div className="category-rename-header">
        <h2>ניהול שמות קטגוריות</h2>
        <p className="category-count">סה״כ {uniqueCategories.length} קטגוריות</p>
      </div>

      {/* Success message */}
      {successMessage && (
        <div className="success-toast">
          <span className="success-icon">✓</span>
          {successMessage}
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="error-message">
          <span className="error-icon">⚠</span>
          {error}
          <button onClick={() => setError(null)} className="dismiss-btn">×</button>
        </div>
      )}

      {/* Categories table */}
      <div className="categories-table-container">
        <table className="categories-table">
          <thead>
            <tr>
              <th>קטגוריה</th>
              <th>פריטים</th>
              <th>פעולות</th>
            </tr>
          </thead>
          <tbody>
            {uniqueCategories.length === 0 ? (
              <tr>
                <td colSpan="3" className="no-categories">
                  אין קטגוריות זמינות
                </td>
              </tr>
            ) : (
              uniqueCategories.map((category) => (
                <tr key={category.name}>
                  <td className="category-name-cell">
                    {editingCategory === category.name ? (
                      <input
                        type="text"
                        value={newName}
                        onChange={(e) => setNewName(e.target.value)}
                        onKeyDown={(e) => handleKeyPress(e, category.name)}
                        className="category-name-input"
                        autoFocus
                        disabled={saving}
                      />
                    ) : (
                      <span className="category-name">{category.name}</span>
                    )}
                  </td>
                  <td className="category-count-cell">
                    <span className="item-count">{category.count}</span>
                  </td>
                  <td className="category-actions-cell">
                    {editingCategory === category.name ? (
                      <div className="edit-actions">
                        <button
                          onClick={() => handleSave(category.name)}
                          className="save-btn"
                          disabled={saving}
                          title="שמור"
                        >
                          {saving ? '...' : '✓'}
                        </button>
                        <button
                          onClick={handleCancel}
                          className="cancel-btn"
                          disabled={saving}
                          title="בטל"
                        >
                          ✗
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => handleEdit(category)}
                        className="edit-btn"
                        title="ערוך"
                      >
                        ✏️ ערוך
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Retry button for errors */}
      {error && !loading && (
        <div className="retry-container">
          <button onClick={loadCategories} className="retry-btn">
            נסה שוב
          </button>
        </div>
      )}
    </div>
  );
}

export default CategoryRenameView;
