import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import WishlistService from '../services/wishlistService';
import { useAuth } from './AuthContext';

const WishlistContext = createContext();

export const useWishlist = () => {
  const context = useContext(WishlistContext);
  if (!context) {
    throw new Error('useWishlist must be used within a WishlistProvider');
  }
  return context;
};

export const WishlistProvider = ({ children }) => {
  const { isAuthenticated, user } = useAuth();
  const [wishlistItems, setWishlistItems] = useState(() => {
    const savedWishlist = localStorage.getItem('polluxkart-wishlist');
    return savedWishlist ? JSON.parse(savedWishlist) : [];
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);

  // Save to localStorage for offline/guest support
  useEffect(() => {
    localStorage.setItem('polluxkart-wishlist', JSON.stringify(wishlistItems));
  }, [wishlistItems]);

  // Sync with backend when user logs in
  useEffect(() => {
    const syncWishlist = async () => {
      if (isAuthenticated && WishlistService.canUseBackendWishlist()) {
        setIsSyncing(true);
        try {
          const products = await WishlistService.getWishlistProducts();
          if (products && products.length > 0) {
            // Transform backend products to frontend format
            const items = products.map(product => ({
              id: product.id,
              name: product.name,
              price: product.price,
              originalPrice: product.original_price,
              image: product.image || (product.images && product.images[0]),
              category: product.category_name,
              rating: product.rating,
              inStock: product.in_stock,
            }));
            setWishlistItems(items);
          }
        } catch (err) {
          console.error('Failed to sync wishlist:', err);
        } finally {
          setIsSyncing(false);
        }
      }
    };

    syncWishlist();
  }, [isAuthenticated, user?.id]);

  const addToWishlist = useCallback(async (product) => {
    // Check if already exists
    const exists = wishlistItems.find(item => item.id === product.id);
    if (exists) return;

    // Optimistically update local state
    setWishlistItems(prev => [...prev, product]);

    // Sync with backend if authenticated
    if (isAuthenticated && WishlistService.canUseBackendWishlist()) {
      try {
        await WishlistService.addToWishlist(product.id);
      } catch (err) {
        console.error('Failed to sync add to wishlist:', err);
      }
    }
  }, [isAuthenticated, wishlistItems]);

  const removeFromWishlist = useCallback(async (productId) => {
    setWishlistItems(prev => prev.filter(item => item.id !== productId));

    if (isAuthenticated && WishlistService.canUseBackendWishlist()) {
      try {
        await WishlistService.removeFromWishlist(productId);
      } catch (err) {
        console.error('Failed to sync remove from wishlist:', err);
      }
    }
  }, [isAuthenticated]);

  const isInWishlist = useCallback((productId) => {
    return wishlistItems.some(item => item.id === productId);
  }, [wishlistItems]);

  const toggleWishlist = useCallback(async (product) => {
    if (isInWishlist(product.id)) {
      await removeFromWishlist(product.id);
      return false;
    } else {
      await addToWishlist(product);
      return true;
    }
  }, [isInWishlist, removeFromWishlist, addToWishlist]);

  const clearWishlist = useCallback(() => {
    setWishlistItems([]);
  }, []);

  const wishlistCount = wishlistItems.length;

  return (
    <WishlistContext.Provider
      value={{
        wishlistItems,
        addToWishlist,
        removeFromWishlist,
        isInWishlist,
        toggleWishlist,
        clearWishlist,
        wishlistCount,
        isLoading,
        isSyncing,
      }}
    >
      {children}
    </WishlistContext.Provider>
  );
};
