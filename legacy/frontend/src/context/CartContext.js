import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import CartService from '../services/cartService';
import { useAuth } from './AuthContext';

const CartContext = createContext();

export const useCart = () => {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error('useCart must be used within a CartProvider');
  }
  return context;
};

export const CartProvider = ({ children }) => {
  const { isAuthenticated, user } = useAuth();
  const [cartItems, setCartItems] = useState(() => {
    const savedCart = localStorage.getItem('polluxkart-cart');
    return savedCart ? JSON.parse(savedCart) : [];
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);

  // Save to localStorage for offline/guest support
  useEffect(() => {
    localStorage.setItem('polluxkart-cart', JSON.stringify(cartItems));
  }, [cartItems]);

  // Sync with backend when user logs in
  useEffect(() => {
    const syncCart = async () => {
      if (isAuthenticated && CartService.canUseBackendCart()) {
        setIsSyncing(true);
        try {
          const backendCart = await CartService.getCart();
          if (backendCart && backendCart.items && backendCart.items.length > 0) {
            // Transform backend cart items to frontend format
            const items = backendCart.items.map(item => ({
              id: item.product_id,
              name: item.product_name,
              price: item.price,
              quantity: item.quantity,
              image: item.image,
            }));
            setCartItems(items);
          }
        } catch (err) {
          console.error('Failed to sync cart:', err);
        } finally {
          setIsSyncing(false);
        }
      }
    };

    syncCart();
  }, [isAuthenticated, user?.id]);

  const addToCart = useCallback(async (product, quantity = 1) => {
    // Optimistically update local state
    setCartItems(prev => {
      const existingItem = prev.find(item => item.id === product.id);
      if (existingItem) {
        return prev.map(item =>
          item.id === product.id
            ? { ...item, quantity: item.quantity + quantity }
            : item
        );
      }
      return [...prev, { ...product, quantity }];
    });

    // Sync with backend if authenticated
    if (isAuthenticated && CartService.canUseBackendCart()) {
      try {
        await CartService.addToCart(product.id, quantity);
      } catch (err) {
        console.error('Failed to sync add to cart:', err);
      }
    }
  }, [isAuthenticated]);

  const removeFromCart = useCallback(async (productId) => {
    setCartItems(prev => prev.filter(item => item.id !== productId));

    if (isAuthenticated && CartService.canUseBackendCart()) {
      try {
        await CartService.removeFromCart(productId);
      } catch (err) {
        console.error('Failed to sync remove from cart:', err);
      }
    }
  }, [isAuthenticated]);

  const updateQuantity = useCallback(async (productId, quantity) => {
    if (quantity < 1) {
      removeFromCart(productId);
      return;
    }

    setCartItems(prev =>
      prev.map(item =>
        item.id === productId ? { ...item, quantity } : item
      )
    );

    if (isAuthenticated && CartService.canUseBackendCart()) {
      try {
        await CartService.updateCartItem(productId, quantity);
      } catch (err) {
        console.error('Failed to sync quantity update:', err);
      }
    }
  }, [isAuthenticated, removeFromCart]);

  const clearCart = useCallback(async () => {
    setCartItems([]);

    if (isAuthenticated && CartService.canUseBackendCart()) {
      try {
        await CartService.clearCart();
      } catch (err) {
        console.error('Failed to sync clear cart:', err);
      }
    }
  }, [isAuthenticated]);

  const cartTotal = cartItems.reduce(
    (total, item) => total + item.price * item.quantity,
    0
  );

  const cartCount = cartItems.reduce(
    (count, item) => count + item.quantity,
    0
  );

  return (
    <CartContext.Provider
      value={{
        cartItems,
        addToCart,
        removeFromCart,
        updateQuantity,
        clearCart,
        cartTotal,
        cartCount,
        isLoading,
        isSyncing,
      }}
    >
      {children}
    </CartContext.Provider>
  );
};
