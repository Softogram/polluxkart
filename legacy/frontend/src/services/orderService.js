// Order Service - API integration for order operations
import { API_CONFIG, apiFetch } from './apiConfig';

/**
 * Create a new order
 * @param {Object} orderData - {shipping_address: Object, payment_method: string}
 * @returns {Promise<Object>}
 */
export const createOrder = async (orderData) => {
  try {
    return await apiFetch(API_CONFIG.endpoints.orders.create, {
      method: 'POST',
      body: JSON.stringify(orderData),
    });
  } catch (error) {
    console.error('Error creating order:', error);
    throw error;
  }
};

/**
 * Get user's orders
 * @param {Object} params - {page, pageSize, status}
 * @returns {Promise<{orders: Array, total: number, page: number, page_size: number, total_pages: number}>}
 */
export const getOrders = async ({ page = 1, pageSize = 10, status = null } = {}) => {
  const params = new URLSearchParams();
  params.append('page', page.toString());
  params.append('page_size', pageSize.toString());
  if (status) params.append('status', status);
  
  const endpoint = `${API_CONFIG.endpoints.orders.list}?${params.toString()}`;
  
  try {
    return await apiFetch(endpoint, {
      method: 'GET',
    });
  } catch (error) {
    console.error('Error fetching orders:', error);
    throw error;
  }
};

/**
 * Get single order by ID
 * @param {string} orderId - Order ID
 * @returns {Promise<Object>}
 */
export const getOrder = async (orderId) => {
  try {
    return await apiFetch(API_CONFIG.endpoints.orders.single(orderId), {
      method: 'GET',
    });
  } catch (error) {
    console.error('Error fetching order:', error);
    throw error;
  }
};

/**
 * Get order by order number
 * @param {string} orderNumber - Order number
 * @returns {Promise<Object>}
 */
export const getOrderByNumber = async (orderNumber) => {
  try {
    return await apiFetch(API_CONFIG.endpoints.orders.byNumber(orderNumber), {
      method: 'GET',
    });
  } catch (error) {
    console.error('Error fetching order:', error);
    throw error;
  }
};

/**
 * Cancel an order
 * @param {string} orderId - Order ID
 * @returns {Promise<Object>}
 */
export const cancelOrder = async (orderId) => {
  try {
    return await apiFetch(API_CONFIG.endpoints.orders.cancel(orderId), {
      method: 'POST',
    });
  } catch (error) {
    console.error('Error cancelling order:', error);
    throw error;
  }
};

const OrderService = {
  createOrder,
  getOrders,
  getOrder,
  getOrderByNumber,
  cancelOrder,
};

export default OrderService;
