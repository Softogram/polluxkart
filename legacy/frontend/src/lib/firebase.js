// Firebase Configuration
import { initializeApp, getApps } from 'firebase/app';
import { getAuth, RecaptchaVerifier } from 'firebase/auth';

const firebaseConfig = {
  apiKey: process.env.REACT_APP_FIREBASE_API_KEY,
  authDomain: process.env.REACT_APP_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.REACT_APP_FIREBASE_PROJECT_ID,
  storageBucket: process.env.REACT_APP_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.REACT_APP_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.REACT_APP_FIREBASE_APP_ID,
};

// Initialize Firebase only once
let firebaseApp;
export const getFirebaseApp = () => {
  if (!firebaseApp && getApps().length === 0) {
    // Check if Firebase is configured
    if (!firebaseConfig.apiKey || firebaseConfig.apiKey === 'undefined') {
      console.warn('Firebase is not configured. OTP will use mock mode.');
      return null;
    }
    firebaseApp = initializeApp(firebaseConfig);
  }
  return firebaseApp || getApps()[0];
};

// Get Firebase Auth instance
export const getFirebaseAuth = () => {
  const app = getFirebaseApp();
  if (!app) return null;
  return getAuth(app);
};

// Check if Firebase is configured
export const isFirebaseConfigured = () => {
  return !!(
    process.env.REACT_APP_FIREBASE_API_KEY &&
    process.env.REACT_APP_FIREBASE_API_KEY !== 'undefined' &&
    process.env.REACT_APP_FIREBASE_PROJECT_ID &&
    process.env.REACT_APP_FIREBASE_PROJECT_ID !== 'undefined'
  );
};

// Setup invisible reCAPTCHA for phone auth
export const setupRecaptcha = (containerId) => {
  const auth = getFirebaseAuth();
  if (!auth) return null;
  
  // Clear any existing recaptcha
  if (window.recaptchaVerifier) {
    window.recaptchaVerifier.clear();
  }
  
  window.recaptchaVerifier = new RecaptchaVerifier(auth, containerId, {
    size: 'invisible',
    callback: () => {
      // reCAPTCHA solved, allow signInWithPhoneNumber
      console.log('reCAPTCHA verified');
    },
    'expired-callback': () => {
      console.log('reCAPTCHA expired');
    },
  });
  
  return window.recaptchaVerifier;
};

export default {
  getFirebaseApp,
  getFirebaseAuth,
  isFirebaseConfigured,
  setupRecaptcha,
};
