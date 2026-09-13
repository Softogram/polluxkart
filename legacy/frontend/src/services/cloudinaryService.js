// Cloudinary Service - Cloud image upload integration
import { API_CONFIG, apiFetch } from './apiConfig';

/**
 * Check if Cloudinary is configured
 */
export const isCloudinaryConfigured = async () => {
  try {
    const response = await apiFetch('/cloudinary/config', {
      method: 'GET',
      includeAuth: false,
    });
    return response.configured;
  } catch (error) {
    console.error('Error checking Cloudinary config:', error);
    return false;
  }
};

/**
 * Get signed upload parameters from backend
 */
export const getUploadSignature = async (folder = 'products', resourceType = 'image') => {
  const response = await apiFetch(
    `/cloudinary/signature?folder=${folder}&resource_type=${resourceType}`,
    { method: 'GET' }
  );
  return response;
};

/**
 * Upload a single image to Cloudinary
 */
export const uploadImage = async (file, folder = 'products', onProgress = null) => {
  const sig = await getUploadSignature(folder, 'image');
  
  const formData = new FormData();
  formData.append('file', file);
  formData.append('api_key', sig.api_key);
  formData.append('timestamp', sig.timestamp);
  formData.append('signature', sig.signature);
  formData.append('folder', sig.folder);
  
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    
    xhr.open('POST', `https://api.cloudinary.com/v1_1/${sig.cloud_name}/image/upload`);
    
    if (onProgress) {
      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          const progress = Math.round((event.loaded / event.total) * 100);
          onProgress(progress);
        }
      };
    }
    
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        const response = JSON.parse(xhr.responseText);
        resolve({
          url: response.secure_url,
          publicId: response.public_id,
          width: response.width,
          height: response.height,
          format: response.format,
          size: response.bytes,
        });
      } else {
        reject(new Error('Upload failed'));
      }
    };
    
    xhr.onerror = () => reject(new Error('Upload failed'));
    xhr.send(formData);
  });
};

/**
 * Upload multiple images to Cloudinary
 */
export const uploadMultipleImages = async (files, folder = 'products', onProgress = null) => {
  const results = [];
  const totalFiles = files.length;
  
  for (let i = 0; i < totalFiles; i++) {
    const file = files[i];
    const result = await uploadImage(file, folder, (fileProgress) => {
      if (onProgress) {
        const overallProgress = Math.round(((i + fileProgress / 100) / totalFiles) * 100);
        onProgress(overallProgress);
      }
    });
    results.push(result);
  }
  
  return results;
};

/**
 * Get optimized image URL with transformations
 */
export const getOptimizedUrl = (url, options = {}) => {
  if (!url || !url.includes('cloudinary.com')) {
    return url;
  }
  
  const {
    width,
    height,
    crop = 'fill',
    quality = 'auto',
    format = 'auto',
  } = options;
  
  // Build transformation string
  const transforms = [];
  if (width) transforms.push(`w_${width}`);
  if (height) transforms.push(`h_${height}`);
  if (crop) transforms.push(`c_${crop}`);
  if (quality) transforms.push(`q_${quality}`);
  if (format) transforms.push(`f_${format}`);
  
  if (transforms.length === 0) {
    return url;
  }
  
  // Insert transformations into URL
  const transformString = transforms.join(',');
  return url.replace('/upload/', `/upload/${transformString}/`);
};

const CloudinaryService = {
  isCloudinaryConfigured,
  getUploadSignature,
  uploadImage,
  uploadMultipleImages,
  getOptimizedUrl,
};

export default CloudinaryService;
