// Payment Service - API integration for payments
import { API_CONFIG, apiFetch } from './apiConfig';

/**
 * Create a Razorpay order for an existing order
 * @param {string} orderId - Order ID
 * @returns {Promise<{razorpay_order_id: string, amount: number, currency: string}>}
 */
export const createRazorpayOrder = async (orderId) => {
  try {
    return await apiFetch(`/payments/razorpay/create/${orderId}`, {
      method: 'POST',
    });
  } catch (error) {
    console.error('Error creating Razorpay order:', error);
    throw error;
  }
};

/**
 * Verify Razorpay payment
 * @param {Object} paymentData - {razorpay_order_id, razorpay_payment_id, razorpay_signature, order_id}
 * @returns {Promise<Object>}
 */
export const verifyRazorpayPayment = async (paymentData) => {
  try {
    return await apiFetch('/payments/razorpay/verify', {
      method: 'POST',
      body: JSON.stringify(paymentData),
    });
  } catch (error) {
    console.error('Error verifying payment:', error);
    throw error;
  }
};

/**
 * Get payment details for an order
 * @param {string} orderId - Order ID
 * @returns {Promise<Object>}
 */
export const getPaymentForOrder = async (orderId) => {
  try {
    return await apiFetch(`/payments/order/${orderId}`, {
      method: 'GET',
    });
  } catch (error) {
    console.error('Error fetching payment:', error);
    throw error;
  }
};

/**
 * Load Razorpay script dynamically
 * @returns {Promise<boolean>}
 */
export const loadRazorpayScript = () => {
  return new Promise((resolve) => {
    if (window.Razorpay) {
      resolve(true);
      return;
    }

    const script = document.createElement('script');
    script.src = 'https://checkout.razorpay.com/v1/checkout.js';
    script.onload = () => resolve(true);
    script.onerror = () => resolve(false);
    document.body.appendChild(script);
  });
};

/**
 * Open Razorpay checkout
 * @param {Object} options - Razorpay options
 * @returns {Promise<Object>} - Payment response
 */
export const openRazorpayCheckout = (options) => {
  return new Promise((resolve, reject) => {
    const razorpay = new window.Razorpay({
      ...options,
      handler: (response) => {
        resolve(response);
      },
      modal: {
        ondismiss: () => {
          reject(new Error('Payment cancelled by user'));
        },
      },
    });
    razorpay.open();
  });
};

const PaymentService = {
  createRazorpayOrder,
  verifyRazorpayPayment,
  getPaymentForOrder,
  loadRazorpayScript,
  openRazorpayCheckout,
};

export default PaymentService;
