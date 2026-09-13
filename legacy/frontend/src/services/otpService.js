// OTP Service - MongoDB-based OTP verification
// Simple, reliable OTP system without Firebase dependencies

import { API_CONFIG, apiFetch } from './apiConfig';

/**
 * Check if OTP service is available (always true for MongoDB-based)
 */
export const isOTPServiceAvailable = () => {
  return true;
};

/**
 * Send OTP to phone number using our backend
 * @param {string} phoneNumber - Phone number with country code (e.g., +919876543210)
 * @returns {Promise<{success: boolean, message: string}>}
 */
export const sendOTP = async (phoneNumber) => {
  try {
    const response = await apiFetch('/otp/send', {
      method: 'POST',
      body: JSON.stringify({ phone: phoneNumber }),
      includeAuth: false,
    });
    
    return {
      success: response.success,
      message: response.message,
      isMock: false,
    };
  } catch (error) {
    console.error('Error sending OTP:', error);
    return {
      success: false,
      message: error.message || 'Failed to send OTP',
      isMock: false,
    };
  }
};

/**
 * Verify OTP code
 * @param {string} otpCode - 6-digit OTP code entered by user
 * @param {string} phoneNumber - Phone number the OTP was sent to
 * @returns {Promise<{success: boolean, message: string}>}
 */
export const verifyOTP = async (otpCode, phoneNumber) => {
  try {
    const response = await apiFetch('/otp/verify', {
      method: 'POST',
      body: JSON.stringify({ 
        phone: phoneNumber,
        code: otpCode 
      }),
      includeAuth: false,
    });
    
    return {
      success: response.success,
      message: response.message,
      isMock: false,
    };
  } catch (error) {
    console.error('Error verifying OTP:', error);
    return {
      success: false,
      message: error.message || 'Failed to verify OTP',
      isMock: false,
    };
  }
};

/**
 * Resend OTP (just calls sendOTP again)
 * @param {string} phoneNumber - Phone number with country code
 */
export const resendOTP = async (phoneNumber) => {
  return sendOTP(phoneNumber);
};

/**
 * Debug: Get current OTP for a phone (DEVELOPMENT ONLY)
 * @param {string} phoneNumber - Phone number to check
 */
export const debugGetOTP = async (phoneNumber) => {
  try {
    const response = await fetch(
      `${API_CONFIG.baseUrl}/otp/debug/${encodeURIComponent(phoneNumber)}`
    );
    return await response.json();
  } catch (error) {
    console.error('Debug OTP error:', error);
    return null;
  }
};

const OTPService = {
  isOTPServiceAvailable,
  sendOTP,
  verifyOTP,
  resendOTP,
  debugGetOTP,
};

export default OTPService;
