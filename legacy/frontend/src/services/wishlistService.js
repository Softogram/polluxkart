// Wishlist Service - API integration for wishlist operations
import { API_CONFIG, apiFetch, getAuthToken } from './apiConfig';

/**
 * Get current user's wishlist
 * @returns {Promise<{product_ids: Array}>}
 */
export const getWishlist = async () => {
  try {
    return await apiFetch(API_CONFIG.endpoints.wishlist.get, {
      method: 'GET',
    });
  } catch (error) {
    console.error('Error fetching wishlist:', error);
    throw error;
  }
};

/**
 * Get full product details for wishlist items
 * @returns {Promise<Array>}
 */
export const getWishlistProducts = async () => {
  try {
    return await apiFetch(API_CONFIG.endpoints.wishlist.products, {
      method: 'GET',
    });
  } catch (error) {
    console.error('Error fetching wishlist products:', error);
    throw error;
  }
};

/**
 * Add item to wishlist
 * @param {string} productId - Product ID
 * @returns {Promise<Object>}
 */
export const addToWishlist = async (productId) => {
  try {
    return await apiFetch(API_CONFIG.endpoints.wishlist.addItem, {
      method: 'POST',
      body: JSON.stringify({ product_id: productId }),
    });
  } catch (error) {
    console.error('Error adding to wishlist:', error);
    throw error;
  }
};

/**
 * Remove item from wishlist
 * @param {string} productId - Product ID
 * @returns {Promise<Object>}
 */
export const removeFromWishlist = async (productId) => {
  try {
    return await apiFetch(API_CONFIG.endpoints.wishlist.removeItem(productId), {
      method: 'DELETE',
    });
  } catch (error) {
    console.error('Error removing from wishlist:', error);
    throw error;
  }
};

/**
 * Check if product is in wishlist
 * @param {string} productId - Product ID
 * @returns {Promise<boolean>}
 */
export const checkInWishlist = async (productId) => {
  try {
    const response = await apiFetch(API_CONFIG.endpoints.wishlist.check(productId), {
      method: 'GET',
    });
    return response.in_wishlist;
  } catch (error) {
    console.error('Error checking wishlist:', error);
    return false;
  }
};

/**
 * Check if user is authenticated for wishlist operations
 * @returns {boolean}
 */
export const canUseBackendWishlist = () => {
  return !!getAuthToken();
};

const WishlistService = {
  getWishlist,
  getWishlistProducts,
  addToWishlist,
  removeFromWishlist,
  checkInWishlist,
  canUseBackendWishlist,
};

export default WishlistService;
