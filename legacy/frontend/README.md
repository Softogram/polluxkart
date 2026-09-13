# PolluxKart E-Commerce Store

> Your one-stop destination for electronics, fashion, home essentials, and more. Quality products at unbeatable prices.

![PolluxKart](https://img.shields.io/badge/PolluxKart-E--Commerce-20B2AA?style=for-the-badge)
![React](https://img.shields.io/badge/React-19.0.0-61DAFB?style=flat-square&logo=react)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4-38B2AC?style=flat-square&logo=tailwind-css)
![Shadcn/UI](https://img.shields.io/badge/Shadcn/UI-Components-000000?style=flat-square)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Design System](#design-system)
- [Pages](#pages)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Mock Data](#mock-data)
- [Customization](#customization)

---

## 🎯 Overview

PolluxKart is a modern, responsive e-commerce frontend prototype built with React and Tailwind CSS. It features a fresh, tech-savvy design with organic teal/cyan colors and lime accents, providing a delightful shopping experience across all devices.

### Key Highlights

- **Modern UI/UX**: Clean, minimalist design with attention to micro-interactions
- **Responsive**: Mobile-first design that works seamlessly on all screen sizes
- **Performance**: Optimized components with lazy loading and efficient state management
- **Accessibility**: WCAG compliant color contrasts and keyboard navigation support

---

## ✨ Features

### 🏠 Home Page
- Hero section with animated floating cards
- Promotional offers carousel with discount codes
- Category grid with product counts
- Featured products section
- New arrivals showcase
- Best sellers section
- Trust badges (Free Shipping, Secure Payment, Easy Returns, 24/7 Support)
- Newsletter subscription

### 🛒 Store Page
- **Sidebar Filters**:
  - Search functionality
  - Category checkboxes with product counts
  - Price range slider ($0 - $1500)
- **Product Grid**:
  - Grid/List view toggle
  - Sort options (Featured, Newest, Price, Rating)
  - Product cards with hover effects
  - Quick add to cart
  - Wishlist functionality
- **Pagination**: Navigate through product pages

### 📦 Product Details Page
- **Image Gallery**:
  - Main product image
  - Thumbnail navigation
  - Multiple image support
- **Product Information**:
  - Name, category, price
  - Discount percentage
  - Star rating with review count
  - Description
  - Key features list
- **Actions**:
  - Quantity selector
  - Add to Cart / Buy Now buttons
  - Wishlist and Share options
- **Tabs**:
  - Description tab
  - Specifications tab
  - Reviews tab with rating breakdown
- **Related Products**: Similar items from the same category

### 🛍️ Cart Page
- Product list with images
- Quantity controls (+/-)
- Remove item functionality
- Clear cart option
- **Promo Codes**:
  - `SUMMER50` - 50% off
  - `NEW15` - 15% off
  - `FREESHIP` - Free shipping
- Order summary with tax calculation
- Free shipping on orders over $100

### 💳 Checkout Page
- **Delivery Address**:
  - Saved addresses selection
  - Default address indicator
  - Add new address dialog
- **Payment Methods**:
  - Razorpay (default)
  - Credit/Debit Card
  - UPI (Google Pay, PhonePe, Paytm)
  - Cash on Delivery
- Order summary with item preview
- Secure checkout badges

### 📋 Orders Page
- Order history with status badges
- Order items preview
- **Order Tracking Timeline**:
  - Confirmed
  - Processing
  - Shipped
  - Delivered
- Filter tabs (All, Processing, Delivered)
- Delivery address and payment method info

### 🔐 Authentication Page
- **Login Tab**:
  - Email/Password fields
  - Show/Hide password toggle
  - Forgot password link
  - Google OAuth option
- **Sign Up Tab**:
  - Full name, Email, Password fields
  - Password confirmation
  - Terms & Conditions checkbox
- Brand information sidebar

---

## 🛠️ Tech Stack

| Technology | Purpose |
|------------|---------|
| **React 19** | Frontend framework |
| **React Router 7** | Client-side routing |
| **Tailwind CSS 3.4** | Utility-first styling |
| **Shadcn/UI** | Component library |
| **Lucide React** | Icon library |
| **Sonner** | Toast notifications |
| **Class Variance Authority** | Component variants |

---

## 🎨 Design System

### Color Palette

```css
/* Primary - Vibrant Teal/Cyan */
--primary: 174 72% 45%;           /* Main brand color */
--primary-glow: 174 72% 55%;      /* Lighter variant */
--primary-dark: 174 72% 35%;      /* Darker variant */

/* Accent - Fresh Lime Green */
--accent: 90 60% 50%;             /* Secondary accent */
--accent-glow: 90 65% 60%;        /* Lighter accent */

/* Neutral Colors */
--background: 0 0% 100%;          /* White background */
--foreground: 200 20% 15%;        /* Dark text */
--muted: 150 15% 96%;             /* Muted backgrounds */
--muted-foreground: 200 10% 45%;  /* Muted text */

/* State Colors */
--success: 142 72% 42%;           /* Success green */
--warning: 38 92% 50%;            /* Warning orange */
--destructive: 0 72% 51%;         /* Error red */
```

### Typography

| Element | Font | Weight | Size |
|---------|------|--------|------|
| Headings | Space Grotesk | 600-700 | text-2xl to text-6xl |
| Body | Inter | 400-500 | text-sm to text-base |
| Labels | Inter | 500 | text-xs to text-sm |

### Shadows & Effects

```css
--shadow-sm: 0 1px 2px 0 hsl(174 30% 20% / 0.05);
--shadow-md: 0 4px 6px -1px hsl(174 30% 20% / 0.08);
--shadow-lg: 0 10px 15px -3px hsl(174 30% 20% / 0.1);
--shadow-glow: 0 0 20px hsl(174 72% 45% / 0.3);
```

---

## 📁 Project Structure

```
/app/frontend/
├── public/
├── src/
│   ├── components/
│   │   ├── home/
│   │   │   ├── CategoryGrid.jsx      # Category cards
│   │   │   ├── FeaturedProducts.jsx  # Featured section
│   │   │   └── PromotionBanner.jsx   # Offers carousel
│   │   ├── layout/
│   │   │   ├── Header.jsx            # Navigation header
│   │   │   └── Footer.jsx            # Site footer
│   │   ├── products/
│   │   │   └── ProductCard.jsx       # Product card component
│   │   └── ui/                       # Shadcn components
│   │       ├── button.jsx
│   │       ├── card.jsx
│   │       ├── dialog.jsx
│   │       └── ... (40+ components)
│   ├── context/
│   │   ├── AuthContext.js            # Authentication state
│   │   └── CartContext.js            # Shopping cart state
│   ├── data/
│   │   └── products.js               # Mock product data
│   ├── hooks/
│   │   └── use-toast.js              # Toast hook
│   ├── lib/
│   │   └── utils.js                  # Utility functions
│   ├── pages/
│   │   ├── HomePage.jsx              # Landing page
│   │   ├── StorePage.jsx             # Product listing
│   │   ├── ProductPage.jsx           # Product details
│   │   ├── CartPage.jsx              # Shopping cart
│   │   ├── CheckoutPage.jsx          # Checkout flow
│   │   ├── OrdersPage.jsx            # Order history
│   │   └── AuthPage.jsx              # Login/Signup
│   ├── App.js                        # Main app component
│   ├── App.css                       # Global styles
│   ├── index.js                      # Entry point
│   └── index.css                     # Design tokens
├── tailwind.config.js                # Tailwind configuration
├── package.json
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- Node.js 18+
- Yarn package manager

### Installation

```bash
# Navigate to frontend directory
cd /app/frontend

# Install dependencies
yarn install

# Start development server
yarn start
```

### Build for Production

```bash
yarn build
```

The app will be available at `http://localhost:3000`

---

## 📊 Mock Data

The application uses mock data stored in `src/data/products.js`:

### Products (20 items)
- **Electronics**: Headphones, Smartwatch, Laptop, Speaker
- **Fashion**: Leather Jacket, Sneakers, Sunglasses, Shirt
- **Home & Lifestyle**: Desk Lamp, Plant Pots, Candles, Office Chair
- **Food & Grocery**: Coffee, Honey, Olive Oil, Tea Collection
- **Beauty & Care**: Skincare Set, Perfume
- **Sports & Fitness**: Yoga Mat, Fitness Tracker

### Categories (6 total)
| Category | Products |
|----------|----------|
| Electronics | 24 |
| Fashion | 56 |
| Home & Lifestyle | 38 |
| Food & Grocery | 42 |
| Beauty & Care | 28 |
| Sports & Fitness | 19 |

### Promotions
| Code | Discount | Description |
|------|----------|-------------|
| SUMMER50 | 50% | Summer sale |
| NEW15 | 15% | New arrivals |
| FREESHIP | Free | Free shipping |

---

## 🎛️ Customization

### Changing Colors

Edit the CSS variables in `src/index.css`:

```css
:root {
  /* Change primary color */
  --primary: 174 72% 45%;  /* Current: Teal */
  
  /* Change accent color */
  --accent: 90 60% 50%;    /* Current: Lime */
}
```

### Adding Products

Add new products to `src/data/products.js`:

```javascript
{
  id: 21,
  name: 'New Product Name',
  category: 'electronics',
  price: 99.99,
  originalPrice: 129.99,
  rating: 4.5,
  reviews: 100,
  image: 'https://example.com/image.jpg',
  images: ['url1', 'url2'],
  description: 'Product description...',
  features: ['Feature 1', 'Feature 2'],
  inStock: true,
  badge: 'New',
}
```

### Adding Payment Methods

Edit `src/pages/CheckoutPage.jsx` to add new payment options:

```javascript
const paymentMethods = [
  {
    id: 'new-method',
    name: 'New Payment Method',
    description: 'Description here',
    icon: IconComponent,
  },
  // ... existing methods
];
```

---

## 📝 Notes

### Mock Implementation
- **Authentication**: Uses localStorage for session persistence (mock)
- **Cart**: Persisted in localStorage
- **Orders**: Stored in localStorage after checkout
- **Payment**: Simulated payment processing (no real transactions)

### Future Enhancements
- Backend API integration
- Real payment gateway (Razorpay) integration
- User profile management
- Order notifications
- Product search with Algolia/Elasticsearch
- Wishlist persistence
- Product reviews submission

---

## 📄 License

This project is built for demonstration purposes.

---

<div align="center">
  <p>Built with ❤️ for <strong>PolluxKart</strong></p>
  <p>
    <a href="http://localhost:3000">View Demo</a>
  </p>
</div>
