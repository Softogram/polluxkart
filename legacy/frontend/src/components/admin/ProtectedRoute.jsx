import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Loader2 } from 'lucide-react';

/**
 * Protected Route component for admin pages.
 * Checks if user is authenticated and has admin role.
 * Redirects to /auth if conditions are not met.
 */
const ProtectedRoute = ({ children }) => {
  const { user, isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  // Show loading state while checking auth
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50" data-testid="admin-loading">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  // Check if user is authenticated
  if (!isAuthenticated || !user) {
    return <Navigate to="/auth" state={{ from: location, message: 'Please login to access admin panel' }} replace />;
  }

  // Check if user has admin role
  if (user.role !== 'admin') {
    return <Navigate to="/auth" state={{ from: location, message: 'Admin access required' }} replace />;
  }

  return children;
};

export default ProtectedRoute;
