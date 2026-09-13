import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from './components/ui/sonner';
import { CartProvider } from './context/CartContext';
import { AuthProvider } from './context/AuthContext';
import { WishlistProvider } from './context/WishlistContext';
import Header from './components/layout/Header';
import Footer from './components/layout/Footer';
import HomePage from './pages/HomePage';
import StorePage from './pages/StorePage';
import ProductPage from './pages/ProductPage';
import CartPage from './pages/CartPage';
import CheckoutPage from './pages/CheckoutPage';
import OrdersPage from './pages/OrdersPage';
import WishlistPage from './pages/WishlistPage';
import AuthPage from './pages/AuthPage';
import ProtectedRoute from './components/admin/ProtectedRoute';

// Admin Pages
import {
  AdminLayout,
  AdminDashboard,
  AdminProducts,
  AdminOrders,
  AdminCategories,
  AdminBrands,
  AdminPromotions,
  AdminUsers,
} from './pages/admin';

import './App.css';

function App() {
  return (
    <Router>
      <AuthProvider>
        <CartProvider>
          <WishlistProvider>
            <Routes>
              {/* Admin Routes - Protected, No Header/Footer */}
              <Route
                path="/admin"
                element={
                  <ProtectedRoute>
                    <AdminLayout />
                  </ProtectedRoute>
                }
              >
                <Route index element={<AdminDashboard />} />
                <Route path="products" element={<AdminProducts />} />
                <Route path="orders" element={<AdminOrders />} />
                <Route path="categories" element={<AdminCategories />} />
                <Route path="brands" element={<AdminBrands />} />
                <Route path="promotions" element={<AdminPromotions />} />
                <Route path="users" element={<AdminUsers />} />
              </Route>

              {/* Main Store Routes */}
              <Route
                path="*"
                element={
                  <div className="min-h-screen flex flex-col bg-background">
                    <Header />
                    <main className="flex-1">
                      <Routes>
                        <Route path="/" element={<HomePage />} />
                        <Route path="/store" element={<StorePage />} />
                        <Route path="/product/:id" element={<ProductPage />} />
                        <Route path="/cart" element={<CartPage />} />
                        <Route path="/checkout" element={<CheckoutPage />} />
                        <Route path="/orders" element={<OrdersPage />} />
                        <Route path="/wishlist" element={<WishlistPage />} />
                        <Route path="/auth" element={<AuthPage />} />
                      </Routes>
                    </main>
                    <Footer />
                  </div>
                }
              />
            </Routes>
            <Toaster 
              position="top-right" 
              richColors 
              closeButton
              toastOptions={{
                duration: 3000,
              }}
            />
          </WishlistProvider>
        </CartProvider>
      </AuthProvider>
    </Router>
  );
}

export default App;
