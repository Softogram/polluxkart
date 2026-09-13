import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import AuthService from '../services/authService';
import { getAuthToken, removeAuthToken } from '../services/apiConfig';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem('polluxkart-user');
    return savedUser ? JSON.parse(savedUser) : null;
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (user) {
      localStorage.setItem('polluxkart-user', JSON.stringify(user));
    } else {
      localStorage.removeItem('polluxkart-user');
    }
  }, [user]);

  useEffect(() => {
    const checkAuth = async () => {
      const token = getAuthToken();
      if (token && !user) {
        const savedUser = localStorage.getItem('polluxkart-user');
        if (savedUser) {
          setUser(JSON.parse(savedUser));
        }
      }
      setIsLoading(false);
    };
    checkAuth();
  }, [user]);

  const login = useCallback(async (identifier, password) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await AuthService.login(identifier, password);
      const userData = {
        id: response.user.id,
        name: response.user.name,
        email: response.user.email,
        phone: response.user.phone,
        avatar: response.user.avatar || `https://api.dicebear.com/7.x/initials/svg?seed=${response.user.name}`,
        role: response.user.role || 'user',
      };
      setUser(userData);
      return userData;
    } catch (err) {
      const errorMessage = err.message || 'Login failed';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const signup = useCallback(async (name, email, phone, password) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await AuthService.register({
        name,
        email: email || undefined,
        phone,
        password,
      });
      const userData = {
        id: response.user.id,
        name: response.user.name,
        email: response.user.email,
        phone: response.user.phone,
        avatar: response.user.avatar || `https://api.dicebear.com/7.x/initials/svg?seed=${name}`,
        role: response.user.role || 'user',
      };
      setUser(userData);
      return userData;
    } catch (err) {
      const errorMessage = err.message || 'Registration failed';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    AuthService.logout();
    setUser(null);
    setError(null);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user && !!getAuthToken(),
        error,
        login,
        signup,
        logout,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
