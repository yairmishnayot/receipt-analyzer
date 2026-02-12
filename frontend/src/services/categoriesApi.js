import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Get all cached categories
 */
export const getAllCategories = async () => {
  const response = await axios.get(`${API_BASE_URL}/api/categories/`);
  return response.data;
};

/**
 * Update category for a specific item
 * Also updates all occurrences in Google Sheets
 */
export const updateCategory = async (itemName, newCategory) => {
  const response = await axios.put(`${API_BASE_URL}/api/categories/`, {
    item_name: itemName,
    new_category: newCategory
  });
  return response.data;
};

/**
 * Rename a category globally
 * Updates all items in cache and all rows in Google Sheets
 */
export const renameCategory = async (oldName, newName) => {
  const response = await axios.put(`${API_BASE_URL}/api/categories/rename`, {
    old_name: oldName,
    new_name: newName
  });
  return response.data;
};
