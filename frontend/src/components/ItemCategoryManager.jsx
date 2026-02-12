import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { getAllCategories, updateCategory } from '../services/categoriesApi';
import '../styles/categories.css';

/**
 * Component for managing individual item-to-category mappings.
 * Allows editing the category for specific items.
 */
function ItemCategoryManager() {
  const { t } = useTranslation();
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editingItem, setEditingItem] = useState(null);
  const [editValue, setEditValue] = useState('');
  const [filter, setFilter] = useState('');
  const [filterCategory, setFilterCategory] = useState('all');
  const [savingItem, setSavingItem] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getAllCategories();
      setCategories(data.items || []);
    } catch (err) {
      console.error('Failed to load categories:', err);
      setError('שגיאה בטעינת הקטגוריות');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (item) => {
    setEditingItem(item.item_name);
    setEditValue(item.category);
  };

  const handleCancel = () => {
    setEditingItem(null);
    setEditValue('');
  };

  const handleSave = async (itemName) => {
    try {
      setSavingItem(itemName);
      const result = await updateCategory(itemName, editValue);

      // Update local state
      setCategories(categories.map(item =>
        item.item_name === itemName
          ? { ...item, category: editValue }
          : item
      ));

      setEditingItem(null);
      setEditValue('');
      setSavingItem(null);

      // Show success message
      setSuccessMessage({
        itemName,
        category: editValue,
        sheetsUpdated: result.sheets_updated || 0
      });

      // Auto-dismiss after 5 seconds
      setTimeout(() => setSuccessMessage(null), 5000);
    } catch (err) {
      console.error('Failed to update category:', err);
      setSavingItem(null);
      setError('שגיאה בעדכון הקטגוריה');
      setTimeout(() => setError(null), 3000);
    }
  };

  // Get unique categories for filter dropdown
  const uniqueCategories = [...new Set(categories.map(item => item.category))].sort();

  // Filter items
  const filteredItems = categories.filter(item => {
    const matchesText = item.item_name.toLowerCase().includes(filter.toLowerCase()) ||
                       item.category.toLowerCase().includes(filter.toLowerCase());
    const matchesCategory = filterCategory === 'all' || item.category === filterCategory;
    return matchesText && matchesCategory;
  });

  // Group by category
  const groupedByCategory = filteredItems.reduce((acc, item) => {
    if (!acc[item.category]) {
      acc[item.category] = [];
    }
    acc[item.category].push(item);
    return acc;
  }, {});

  if (loading) {
    return <div className="categories-loading">טוען קטגוריות...</div>;
  }

  if (error) {
    return (
      <div className="categories-error">
        <p>{error}</p>
        <button onClick={loadCategories}>נסה שוב</button>
      </div>
    );
  }

  return (
    <div className="item-category-manager">
      {successMessage && (
        <div className="success-toast">
          <div className="toast-content">
            <span className="toast-icon">✓</span>
            <div className="toast-text">
              <strong>הקטגוריה עודכנה בהצלחה!</strong>
              <p>"{successMessage.itemName}" → {successMessage.category}</p>
              {successMessage.sheetsUpdated > 0 && (
                <p className="sheets-info">
                  📊 {successMessage.sheetsUpdated} שורות עודכנו בגיליון
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="categories-header">
        <p className="categories-count">
          סה"כ {categories.length} פריטים במטמון
        </p>
      </div>

      <div className="categories-filters">
        <input
          type="text"
          placeholder="חיפוש לפי שם פריט או קטגוריה..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="filter-input"
        />
        <select
          value={filterCategory}
          onChange={(e) => setFilterCategory(e.target.value)}
          className="filter-select"
        >
          <option value="all">כל הקטגוריות</option>
          {uniqueCategories.map(cat => (
            <option key={cat} value={cat}>{cat}</option>
          ))}
        </select>
        <button onClick={loadCategories} className="refresh-button">
          🔄 רענן
        </button>
      </div>

      <div className="categories-list">
        {Object.entries(groupedByCategory).map(([category, items]) => (
          <div key={category} className="category-group">
            <h3 className="category-title">
              {category} ({items.length})
            </h3>
            <table className="categories-table">
              <thead>
                <tr>
                  <th>שם הפריט</th>
                  <th>קטגוריה</th>
                  <th>פעולות</th>
                </tr>
              </thead>
              <tbody>
                {items.map(item => (
                  <tr key={item.item_name}>
                    <td className="item-name">{item.item_name}</td>
                    <td className="item-category">
                      {editingItem === item.item_name ? (
                        <input
                          type="text"
                          value={editValue}
                          onChange={(e) => setEditValue(e.target.value)}
                          className="edit-input"
                          autoFocus
                        />
                      ) : (
                        <span className="category-badge">{item.category}</span>
                      )}
                    </td>
                    <td className="item-actions">
                      {editingItem === item.item_name ? (
                        <>
                          <button
                            onClick={() => handleSave(item.item_name)}
                            className="save-button"
                            disabled={savingItem === item.item_name}
                          >
                            {savingItem === item.item_name ? (
                              <>
                                <span className="spinner"></span>
                                שומר...
                              </>
                            ) : (
                              <>✓ שמור</>
                            )}
                          </button>
                          <button
                            onClick={handleCancel}
                            className="cancel-button"
                            disabled={savingItem === item.item_name}
                          >
                            ✗ בטל
                          </button>
                        </>
                      ) : (
                        <button
                          onClick={() => handleEdit(item)}
                          className="edit-button"
                          disabled={savingItem !== null}
                        >
                          ✏️ ערוך
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}
      </div>

      {filteredItems.length === 0 && (
        <div className="no-results">
          אין תוצאות מתאימות לחיפוש
        </div>
      )}
    </div>
  );
}

export default ItemCategoryManager;
