// Admin Service - API integration for admin operations
import { API_CONFIG, apiFetch } from './apiConfig';

const ADMIN_BASE = '/admin';
const UPLOAD_BASE = '/upload';

// Dashboard
export const getDashboardStats = async () => {
  return await apiFetch(`${ADMIN_BASE}/dashboard`, { method: 'GET' });
};

// Check if S3 is configured
export const getUploadConfig = async () => {
  try {
    const response = await fetch(`${API_CONFIG.baseUrl}${UPLOAD_BASE}/config`);
    return await response.json();
  } catch (error) {
    console.error('Failed to get upload config:', error);
    return { s3_configured: false };
  }
};

// Image Upload - Uses S3 if configured, falls back to local
export const uploadImage = async (file, entityType = 'temp', entityId = null, onProgress = null) => {
  const formData = new FormData();
  formData.append('file', file);
  
  // Determine the upload endpoint based on entity type
  let uploadUrl;
  if (entityType === 'product' && entityId) {
    uploadUrl = `${UPLOAD_BASE}/product/${entityId}`;
  } else if (entityType === 'category' && entityId) {
    uploadUrl = `${UPLOAD_BASE}/category/${entityId}`;
  } else {
    uploadUrl = `${UPLOAD_BASE}/temp`;
  }
  
  const response = await fetch(`${API_CONFIG.baseUrl}${uploadUrl}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('polluxkart-token')}`,
    },
    body: formData,
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Upload failed');
  }
  
  const result = await response.json();
  return { 
    url: result.url, 
    key: result.key,
    filename: file.name 
  };
};

export const uploadMultipleImages = async (files, entityType = 'temp', entityId = null, onProgress = null) => {
  // For multiple files, upload one by one
  const results = [];
  
  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    try {
      const result = await uploadImage(file, entityType, entityId);
      results.push(result);
      
      if (onProgress) {
        onProgress((i + 1) / files.length * 100);
      }
    } catch (error) {
      console.error(`Failed to upload ${file.name}:`, error);
    }
  }
  
  return results;
};

// Legacy upload functions for backward compatibility
export const uploadProductImage = async (file, productId, onProgress = null) => {
  return uploadImage(file, 'product', productId, onProgress);
};

export const uploadCategoryImage = async (file, categoryId, onProgress = null) => {
  return uploadImage(file, 'category', categoryId, onProgress);
};

// Products
export const createProduct = async (productData) => {
  return await apiFetch(`${ADMIN_BASE}/products`, {
    method: 'POST',
    body: JSON.stringify(productData),
  });
};

export const updateProduct = async (productId, updateData) => {
  return await apiFetch(`${ADMIN_BASE}/products/${productId}`, {
    method: 'PUT',
    body: JSON.stringify(updateData),
  });
};

export const deleteProduct = async (productId) => {
  return await apiFetch(`${ADMIN_BASE}/products/${productId}`, {
    method: 'DELETE',
  });
};

// Categories
export const getAdminCategories = async () => {
  return await apiFetch(`${ADMIN_BASE}/categories`, { method: 'GET' });
};

export const createCategory = async (categoryData) => {
  return await apiFetch(`${ADMIN_BASE}/categories`, {
    method: 'POST',
    body: JSON.stringify(categoryData),
  });
};

export const updateCategory = async (categoryId, updateData) => {
  return await apiFetch(`${ADMIN_BASE}/categories/${categoryId}`, {
    method: 'PUT',
    body: JSON.stringify(updateData),
  });
};

export const deleteCategory = async (categoryId) => {
  return await apiFetch(`${ADMIN_BASE}/categories/${categoryId}`, {
    method: 'DELETE',
  });
};

// Promotions
export const getPromotions = async (status = null) => {
  const params = status ? `?status=${status}` : '';
  return await apiFetch(`${ADMIN_BASE}/promotions${params}`, { method: 'GET' });
};

export const createPromotion = async (promoData) => {
  return await apiFetch(`${ADMIN_BASE}/promotions`, {
    method: 'POST',
    body: JSON.stringify(promoData),
  });
};

export const updatePromotion = async (promoId, updateData) => {
  return await apiFetch(`${ADMIN_BASE}/promotions/${promoId}`, {
    method: 'PUT',
    body: JSON.stringify(updateData),
  });
};

export const deletePromotion = async (promoId) => {
  return await apiFetch(`${ADMIN_BASE}/promotions/${promoId}`, {
    method: 'DELETE',
  });
};

export const validatePromotion = async (code, orderTotal) => {
  return await apiFetch(`${ADMIN_BASE}/promotions/validate?code=${code}&order_total=${orderTotal}`, {
    method: 'POST',
  });
};

// Orders (Admin)
export const getAdminOrders = async (page = 1, pageSize = 20, status = null, search = null) => {
  const params = new URLSearchParams();
  params.append('page', page.toString());
  params.append('page_size', pageSize.toString());
  if (status) params.append('status', status);
  if (search) params.append('search', search);
  
  return await apiFetch(`${ADMIN_BASE}/orders?${params.toString()}`, { method: 'GET' });
};

export const updateOrderStatus = async (orderId, status, trackingNumber = null) => {
  const params = new URLSearchParams();
  params.append('status', status);
  if (trackingNumber) params.append('tracking_number', trackingNumber);
  
  return await apiFetch(`${ADMIN_BASE}/orders/${orderId}/status?${params.toString()}`, {
    method: 'PUT',
  });
};

// Users (Admin)
export const getAdminUsers = async (page = 1, pageSize = 20, search = null) => {
  const params = new URLSearchParams();
  params.append('page', page.toString());
  params.append('page_size', pageSize.toString());
  if (search) params.append('search', search);
  
  return await apiFetch(`${ADMIN_BASE}/users?${params.toString()}`, { method: 'GET' });
};

export const updateUserRole = async (userId, role) => {
  return await apiFetch(`${ADMIN_BASE}/users/${userId}/role?role=${role}`, {
    method: 'PUT',
  });
};

// Database Cleanup
export const cleanSeedData = async () => {
  return await apiFetch(`${ADMIN_BASE}/cleanup/seed-data?confirm=CONFIRM`, {
    method: 'DELETE',
  });
};

// Brands
export const getAdminBrands = async (includeInactive = false) => {
  const params = includeInactive ? '?include_inactive=true' : '';
  return await apiFetch(`${ADMIN_BASE}/brands${params}`, { method: 'GET' });
};

export const createBrand = async (brandData) => {
  return await apiFetch(`${ADMIN_BASE}/brands`, {
    method: 'POST',
    body: JSON.stringify(brandData),
  });
};

export const updateBrand = async (brandId, updateData) => {
  return await apiFetch(`${ADMIN_BASE}/brands/${brandId}`, {
    method: 'PUT',
    body: JSON.stringify(updateData),
  });
};

export const deleteBrand = async (brandId) => {
  return await apiFetch(`${ADMIN_BASE}/brands/${brandId}`, {
    method: 'DELETE',
  });
};

export const migrateBrands = async () => {
  return await apiFetch(`${ADMIN_BASE}/brands/migrate`, {
    method: 'POST',
  });
};

const AdminService = {
  getDashboardStats,
  getUploadConfig,
  uploadImage,
  uploadMultipleImages,
  uploadProductImage,
  uploadCategoryImage,
  createProduct,
  updateProduct,
  deleteProduct,
  getAdminCategories,
  createCategory,
  updateCategory,
  deleteCategory,
  getAdminBrands,
  createBrand,
  updateBrand,
  deleteBrand,
  migrateBrands,
  getPromotions,
  createPromotion,
  updatePromotion,
  deletePromotion,
  validatePromotion,
  getAdminOrders,
  updateOrderStatus,
  getAdminUsers,
  updateUserRole,
  cleanSeedData,
};

export default AdminService;
