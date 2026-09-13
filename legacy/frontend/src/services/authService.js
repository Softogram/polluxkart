// Auth Service - API integration for authentication
import { API_CONFIG, apiFetch, setAuthToken, removeAuthToken, getAuthToken } from './apiConfig';

/**
 * Register a new user
 * @param {Object} userData - {name, phone, password, email?}
 * @returns {Promise<{access_token: string, user: Object}>}
 */
export const register = async (userData) => {
  const response = await apiFetch(API_CONFIG.endpoints.auth.register, {
    method: 'POST',
    body: JSON.stringify(userData),
    includeAuth: false,
  });
  
  // Store token
  if (response.access_token) {
    setAuthToken(response.access_token);
  }
  
  return response;
};

/**
 * Login user
 * @param {string} identifier - Email or phone number
 * @param {string} password - User password
 * @returns {Promise<{access_token: string, user: Object}>}
 */
export const login = async (identifier, password) => {
  const response = await apiFetch(API_CONFIG.endpoints.auth.login, {
    method: 'POST',
    body: JSON.stringify({ identifier, password }),
    includeAuth: false,
  });
  
  // Store token
  if (response.access_token) {
    setAuthToken(response.access_token);
  }
  
  return response;
};

/**
 * Logout user
 */
export const logout = () => {
  removeAuthToken();
};

/**
 * Get current user profile
 * @returns {Promise<Object>}
 */
export const getCurrentUser = async () => {
  const token = getAuthToken();
  if (!token) {
    return null;
  }
  
  try {
    return await apiFetch(API_CONFIG.endpoints.auth.me, {
      method: 'GET',
    });
  } catch (error) {
    if (error.status === 401) {
      removeAuthToken();
      return null;
    }
    throw error;
  }
};

/**
 * Check if user is authenticated (has valid token)
 * @returns {boolean}
 */
export const isAuthenticated = () => {
  return !!getAuthToken();
};

const AuthService = {
  register,
  login,
  logout,
  getCurrentUser,
  isAuthenticated,
};

export default AuthService;
