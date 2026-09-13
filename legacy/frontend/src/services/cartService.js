// Cart Service - API integration for cart operations
import { API_CONFIG, apiFetch, getAuthToken } from './apiConfig';

/**
 * Get current user's cart
 * @returns {Promise<{items: Array, total: number}>}
 */
export const getCart = async () => {
  try {
    return await apiFetch(API_CONFIG.endpoints.cart.get, {
      method: 'GET',
    });
  } catch (error) {
    console.error('Error fetching cart:', error);
    throw error;
  }
};

/**
 * Add item to cart
 * @param {string} productId - Product ID
 * @param {number} quantity - Quantity to add
 * @returns {Promise<Object>}
 */
export const addToCart = async (productId, quantity = 1) => {
  try {
    return await apiFetch(API_CONFIG.endpoints.cart.addItem, {
      method: 'POST',
      body: JSON.stringify({ product_id: productId, quantity }),
    });
  } catch (error) {
    console.error('Error adding to cart:', error);
    throw error;
  }
};

/**
 * Update item quantity in cart
 * @param {string} productId - Product ID
 * @param {number} quantity - New quantity
 * @returns {Promise<Object>}
 */
export const updateCartItem = async (productId, quantity) => {
  try {
    return await apiFetch(API_CONFIG.endpoints.cart.updateItem(productId), {
      method: 'PUT',
      body: JSON.stringify({ quantity }),
    });
  } catch (error) {
    console.error('Error updating cart item:', error);
    throw error;
  }
};

/**
 * Remove item from cart
 * @param {string} productId - Product ID
 * @returns {Promise<Object>}
 */
export const removeFromCart = async (productId) => {
  try {
    return await apiFetch(API_CONFIG.endpoints.cart.removeItem(productId), {
      method: 'DELETE',
    });
  } catch (error) {
    console.error('Error removing from cart:', error);
    throw error;
  }
};

/**
 * Clear all items from cart
 * @returns {Promise<Object>}
 */
export const clearCart = async () => {
  try {
    return await apiFetch(API_CONFIG.endpoints.cart.clear, {
      method: 'DELETE',
    });
  } catch (error) {
    console.error('Error clearing cart:', error);
    throw error;
  }
};

/**
 * Check if user is authenticated for cart operations
 * @returns {boolean}
 */
export const canUseBackendCart = () => {
  return !!getAuthToken();
};

const CartService = {
  getCart,
  addToCart,
  updateCartItem,
  removeFromCart,
  clearCart,
  canUseBackendCart,
};

export default CartService;
