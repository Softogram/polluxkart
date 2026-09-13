// Currency formatting utility for Indian Rupee

export const CURRENCY_SYMBOL = '₹';
export const CURRENCY_CODE = 'INR';

/**
 * Format price in Indian Rupee
 * @param {number} amount - The amount to format
 * @param {boolean} showSymbol - Whether to show currency symbol
 * @returns {string} Formatted price string
 */
export const formatPrice = (amount, showSymbol = true) => {
  if (amount === null || amount === undefined) return showSymbol ? '₹0' : '0';
  
  // Format with Indian numbering system (lakhs, crores)
  const formatted = amount.toLocaleString('en-IN', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  });
  
  return showSymbol ? `₹${formatted}` : formatted;
};

/**
 * Convert USD to INR (approximate conversion for display)
 * @param {number} usdAmount - Amount in USD
 * @param {number} exchangeRate - Exchange rate (default ~83)
 * @returns {number} Amount in INR
 */
export const convertToINR = (usdAmount, exchangeRate = 83) => {
  return Math.round(usdAmount * exchangeRate);
};

export default formatPrice;
