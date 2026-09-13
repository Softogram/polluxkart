# PolluxKart - E-Commerce Platform PRD

## Original Problem Statement
Build a complete e-commerce platform named "PolluxKart" with:
- Frontend: React with tech-savvy, organic, fresh design
- Backend: Microservice architecture with MongoDB
- Features: Products, Cart, Checkout, Orders, Payments, Reviews, Wishlist, Inventory
- Admin Panel: CRUD for Products, Categories, Promotions, Orders, Users

## Technical Architecture

### Frontend (React)
- **Stack**: React 19, Tailwind CSS, shadcn/ui
- **State Management**: React Context API
- **Routing**: React Router DOM v7
- **Testing**: Jest, React Testing Library (28 tests)
- **CI/CD**: GitHub Actions
- **API Integration**: Fully connected to FastAPI backend

### Backend (FastAPI)
- **Stack**: FastAPI, Python 3.11, MongoDB (Motor async driver)
- **Authentication**: JWT (python-jose) with role-based access (user/admin)
- **Payment**: Razorpay integration with Cash on Delivery option
- **Testing**: Pytest (62 tests)
- **File Uploads**: Cloudinary cloud storage (with local fallback via aiofiles)
- **Image CDN**: Cloudinary for optimized image delivery

### Database (MongoDB)
Collections:
- `users` - User accounts with role field (user/admin)
- `products` - Product catalog with multiple images
- `categories` - Product categories
- `carts` - Shopping carts
- `wishlists` - User wishlists
- `orders` - Order records with shipping address
- `payments` - Payment transactions
- `inventory` - Stock management
- `reviews` - Product reviews
- `stock_movements` - Inventory audit trail
- `promotions` - Discount codes and promotions
- `brands` - Product brands

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login (email/phone) - returns user with role

### Products
- `GET /api/products` - List products (pagination, filter, sort, search)
- `GET /api/products/{id}` - Get product
- `GET /api/products/categories` - Get categories
- `GET /api/products/brands` - Get brands
- `GET /api/products/{id}/reviews` - Get reviews
- `POST /api/products/{id}/reviews` - Add review (auth)

### Cart
- `GET /api/cart` - Get cart (auth)
- `POST /api/cart/items` - Add to cart (auth)
- `PUT /api/cart/items/{product_id}` - Update quantity (auth)
- `DELETE /api/cart/items/{product_id}` - Remove item (auth)

### Wishlist
- `GET /api/wishlist` - Get wishlist (auth)
- `GET /api/wishlist/products` - Get full product details (auth)
- `POST /api/wishlist/items` - Add item (auth)
- `DELETE /api/wishlist/items/{product_id}` - Remove item (auth)

### Orders
- `GET /api/orders` - Get orders (auth)
- `POST /api/orders` - Create order (auth)
- `GET /api/orders/{id}` - Get order (auth)
- `POST /api/orders/{id}/cancel` - Cancel order (auth)

### Payments
- `POST /api/payments/razorpay/create/{order_id}` - Create Razorpay order
- `POST /api/payments/razorpay/verify` - Verify payment
- `POST /api/payments/razorpay/webhook` - Webhook handler

### Inventory
- `GET /api/inventory/{product_id}` - Get inventory
- `GET /api/inventory/{product_id}/available` - Get available stock
- `POST /api/inventory/adjust` - Adjust stock (admin)
- `GET /api/inventory/alerts/low-stock` - Low stock alerts (admin)

### Admin (require admin role)
- `GET /api/admin/dashboard` - Dashboard stats
- `POST /api/admin/upload` - Upload image (local fallback)
- `POST /api/admin/upload/multiple` - Upload multiple images (local fallback)
- `POST /api/admin/products` - Create product
- `PUT /api/admin/products/{id}` - Update product
- `DELETE /api/admin/products/{id}` - Delete product
- `GET /api/admin/categories` - Get all categories
- `POST /api/admin/categories` - Create category
- `PUT /api/admin/categories/{id}` - Update category
- `DELETE /api/admin/categories/{id}` - Delete category
- `GET /api/admin/brands` - Get all brands
- `POST /api/admin/brands` - Create brand
- `PUT /api/admin/brands/{id}` - Update brand
- `DELETE /api/admin/brands/{id}` - Delete brand
- `POST /api/admin/brands/migrate` - Migrate brands from products
- `GET /api/admin/promotions` - Get all promotions
- `POST /api/admin/promotions` - Create promotion
- `PUT /api/admin/promotions/{id}` - Update promotion
- `DELETE /api/admin/promotions/{id}` - Delete promotion
- `GET /api/admin/orders` - Get all orders
- `DELETE /api/admin/cleanup/seed-data` - Remove all seed/test data (preserves users)

### Admin Setup (no auth required - one-time use)
- `GET /api/admin/setup/status` - Check if admin exists
- `POST /api/admin/setup/initial-admin` - Create first admin user (only works once)
- `PUT /api/admin/orders/{id}/status` - Update order status
- `GET /api/admin/users` - Get all users
- `PUT /api/admin/users/{id}/role` - Update user role

### Cloudinary (cloud image storage)
- `GET /api/cloudinary/config` - Check if Cloudinary is configured
- `GET /api/cloudinary/signature` - Get signed upload params (auth required)

## Features Implemented

### Frontend (December 2025 - February 2026)
- [x] All pages: Home, Store, Product, Cart, Checkout, Orders, Wishlist, Auth
- [x] INR currency formatting (₹)
- [x] Country code selector for phone auth
- [x] OTP verification flow (MOCKED)
- [x] Categories dropdown in navbar
- [x] **Debounced search (500ms) - FIXED**
- [x] Out-of-stock handling
- [x] Toast notifications with close button
- [x] Unit tests (28 passing)
- [x] GitHub Actions CI/CD
- [x] **Frontend-Backend Integration - COMPLETED**
- [x] **Admin Panel UI - COMPLETED** (Dashboard, Products, Orders, Users, Categories, Promotions)
- [x] **Admin Route Protection - COMPLETED** (ProtectedRoute component)
- [x] **Product Reviews UI - COMPLETED** (ReviewForm component with star ratings)
- [x] **Cloudinary Integration - COMPLETED** (with local upload fallback)
- [x] **Clean Database Button - COMPLETED** (Admin Dashboard with confirmation dialog)

### Backend (December 2025 - February 2026)
- [x] JWT Authentication with role-based access (user/admin)
- [x] Product CRUD with filtering, sorting, search
- [x] Shopping cart management
- [x] Wishlist sync
- [x] Order management with shipping address
- [x] Razorpay payment integration + Cash on Delivery
- [x] Inventory management with stock movements
- [x] Product reviews & ratings
- [x] Email notifications (templates ready)
- [x] Pytest tests (62 passing)
- [x] **Admin APIs - COMPLETED** (Dashboard, Products, Categories, Promotions, Orders, Users)
- [x] **Image Upload API - COMPLETED** (Cloudinary + local fallback)
- [x] **Cloudinary Integration - COMPLETED** (signed upload flow)
- [x] **Initial Admin Setup Endpoint - COMPLETED** (One-time use for production)
- [x] **Database Cleanup API - COMPLETED** (Remove seed data while preserving users)
- [x] **MongoDB-based OTP System - COMPLETED** (Replaces Firebase, simple and reliable)

## Frontend-Backend Integration (December 2025)

### Services Created/Updated
- `apiConfig.js` - Base API configuration with auth token management
- `authService.js` - Login, register, logout with JWT
- `productService.js` - Products, categories, brands, reviews
- `cartService.js` - Cart operations (syncs with backend when authenticated)
- `wishlistService.js` - Wishlist operations (syncs with backend when authenticated)
- `orderService.js` - Order management
- `adminService.js` - Admin CRUD operations with Cloudinary support
- `cloudinaryService.js` - Cloud image upload with signed uploads

### Context Updates
- `AuthContext.js` - Real API login/signup, JWT token storage
- `CartContext.js` - Hybrid approach: localStorage fallback + backend sync
- `WishlistContext.js` - Hybrid approach: localStorage fallback + backend sync

### Key Features
- Products load from MongoDB via backend API
- Search with 500ms debounce (fixed recurring bug)
- Categories and brands dynamically loaded
- Cart syncs to backend when user is authenticated
- Wishlist syncs to backend when user is authenticated
- Guest users can still use cart/wishlist via localStorage

## Test Credentials
- **Email**: test@polluxkart.com
- **Phone**: +919876543210
- **Password**: Test@123

## Seed Data
- 6 Categories
- 21 Products (2 out of stock)
- 20 Brands
- 1 Test user

## Known Mocked Elements
- **OTP Verification**: Uses simple MongoDB-based OTP with TTL (5 minutes). OTP codes are stored in database and auto-expire. For development, use `/api/otp/debug/{phone}` to see the generated code.
- **Razorpay**: Mock order IDs generated when API keys not configured
- **Email Notifications**: SMTP not configured - logs to console

## Environment Variables Required

### Backend (.env)
```
MONGO_URL=mongodb://localhost:27017
DB_NAME=polluxkart
JWT_SECRET=your-secret-key
RAZORPAY_KEY_ID=rzp_test_xxx  # Optional
RAZORPAY_KEY_SECRET=xxx  # Optional
SMTP_HOST=smtp.gmail.com  # Optional
SMTP_USER=xxx  # Optional
SMTP_PASSWORD=xxx  # Optional
CLOUDINARY_CLOUD_NAME=your_cloud_name  # Optional - for cloud image storage
CLOUDINARY_API_KEY=your_api_key  # Optional
CLOUDINARY_API_SECRET=your_api_secret  # Optional
```

### Frontend (.env)
```
REACT_APP_BACKEND_URL=https://your-domain.com
# Firebase Configuration (for Phone OTP - 10K free verifications/month)
REACT_APP_FIREBASE_API_KEY=your-api-key
REACT_APP_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
REACT_APP_FIREBASE_PROJECT_ID=your-project-id
REACT_APP_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
REACT_APP_FIREBASE_MESSAGING_SENDER_ID=your-sender-id
REACT_APP_FIREBASE_APP_ID=your-app-id
```

## Test Results
- **Backend Tests**: 62/62 passing (100%)
- **Frontend Integration**: All features tested and working
- **Search Debounce**: Verified working with 500ms delay
- **Admin Auth Flow**: Verified - non-admin users redirected to /auth
- **Admin Products**: Verified - loads without 422 error (pageSize=50)
- **Product Reviews UI**: Verified - form displays for logged-in users
- **Cloudinary Integration**: Verified - graceful fallback to local uploads
- **Firebase OTP**: Ready - graceful fallback to mock mode when not configured
- **Image Uploads (Admin)**: Fixed - URLs now correctly include base URL
- **Checkout Flow**: Fixed - cart syncs to backend before order creation
- **Orders Page**: Fixed - loads orders from API instead of localStorage

## Next Steps (Backlog)

### P0 - Critical
- [x] ~~Connect frontend to backend APIs~~ ✅ COMPLETED
- [x] ~~Add admin panel for product management~~ ✅ COMPLETED
- [x] ~~Admin route protection~~ ✅ COMPLETED
- [x] ~~Product Reviews UI~~ ✅ COMPLETED
- [x] ~~Cloud image storage (Cloudinary)~~ ✅ COMPLETED
- [x] ~~Fix image upload URL issues~~ ✅ COMPLETED
- [x] ~~Fix checkout 400 error (cart sync)~~ ✅ COMPLETED
- [x] ~~Fix Orders page (API integration)~~ ✅ COMPLETED
- [x] ~~Categories sync (navbar, homepage, modal)~~ ✅ COMPLETED
- [ ] Configure Razorpay live keys

### P1 - Important
- [x] ~~Wire up admin panel forms~~ ✅ COMPLETED (Categories, Promotions already working)
- [x] ~~Add real OTP service~~ ✅ COMPLETED (Firebase Phone Auth integrated)
- [x] ~~Category image upload~~ ✅ COMPLETED (replaced URL input with upload)
- [ ] Configure Cloudinary API keys for production
- [ ] Configure Firebase API keys for production OTP
- [ ] Configure SMTP for email notifications
- [ ] Add order tracking with status updates
- [ ] Add user profile/settings page

### P2 - Nice to Have
- [ ] Add coupon/discount codes UI on checkout
- [ ] Add order invoice PDF generation
- [ ] Add social login (Google/Facebook)
- [ ] "Remember this device" for OTP

## Cloudinary Setup Instructions
To enable cloud image storage, add the following to your backend `.env`:

1. Create a free Cloudinary account at https://cloudinary.com
2. Go to Dashboard and copy your credentials
3. Add to `/app/backend/.env`:
```
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```
4. Restart the backend service

Without these keys, image uploads will fall back to local storage.

## Firebase Phone Auth Setup Instructions
To enable real SMS OTP verification (10,000 free verifications/month):

1. Create a Firebase project at https://console.firebase.google.com
2. Go to Authentication > Sign-in method > Enable Phone
3. Go to Project Settings > General > Add a web app
4. Copy the configuration values and add to `/app/frontend/.env`:
```
REACT_APP_FIREBASE_API_KEY=AIzaSy...
REACT_APP_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
REACT_APP_FIREBASE_PROJECT_ID=your-project-id
REACT_APP_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
REACT_APP_FIREBASE_MESSAGING_SENDER_ID=123456789
REACT_APP_FIREBASE_APP_ID=1:123456789:web:abc123
```
5. Add your domain to Firebase Console > Authentication > Settings > Authorized domains
6. Restart the frontend service

Without these keys, OTP will use mock mode (any 6-digit code works, use 123456).


## Production Admin Setup Instructions
For fresh production deployments, you need to create the first admin user:

### Step 1: Check if Setup is Needed
```bash
curl https://your-domain.com/api/admin/setup/status
```
Response will show `"setup_available": true` if no admin exists.

### Step 2: Create Initial Admin (ONE-TIME ONLY)
```bash
curl -X POST https://your-domain.com/api/admin/setup/initial-admin \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@yourdomain.com",
    "phone": "+919876543210",
    "name": "Admin User",
    "password": "YourSecurePassword123",
    "setup_key": "POLLUXKART_INITIAL_ADMIN_2025"
  }'
```

**Important Security Notes:**
- This endpoint only works ONCE when no admin exists
- After the first admin is created, this endpoint is permanently disabled
- The `setup_key` is set to `POLLUXKART_INITIAL_ADMIN_2025` by default
- For extra security, set `ADMIN_SETUP_KEY` environment variable in production
- After creating the admin, login via the web UI at /login

### Troubleshooting Firebase OTP `auth/network-request-failed`
This error typically occurs when:
1. **Domain not authorized**: Add your domain to Firebase Console → Authentication → Settings → Authorized domains
2. **Network issues**: Check your internet connection
3. **Firebase configuration**: Verify all Firebase env variables are set correctly
