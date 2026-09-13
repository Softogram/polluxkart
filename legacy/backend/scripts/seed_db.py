"""
Database seeder script for PolluxKart
Run this to populate the database with sample data
"""
import asyncio
import sys
sys.path.insert(0, '/app/backend')

from config.database import get_db, COLLECTIONS
from services.product_service import ProductService
from services.auth_service import AuthService
from models.product import CategoryCreate, ProductCreate
from models.user import UserCreate
import uuid

# Sample categories
CATEGORIES = [
    {"name": "Electronics", "description": "Gadgets, devices, and tech accessories", "image": "https://images.unsplash.com/photo-1498049794561-7780e7231661?w=500"},
    {"name": "Fashion", "description": "Clothing, shoes, and accessories", "image": "https://images.unsplash.com/photo-1445205170230-053b83016050?w=500"},
    {"name": "Home & Living", "description": "Furniture, decor, and home essentials", "image": "https://images.unsplash.com/photo-1484101403633-562f891dc89a?w=500"},
    {"name": "Grocery", "description": "Fresh produce and daily essentials", "image": "https://images.unsplash.com/photo-1542838132-92c53300491e?w=500"},
    {"name": "Beauty", "description": "Skincare, makeup, and personal care", "image": "https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=500"},
    {"name": "Sports", "description": "Sports equipment and fitness gear", "image": "https://images.unsplash.com/photo-1461896836934- voices-6a36f7c7dc3c?w=500"},
]

# Sample products
PRODUCTS = [
    # Electronics
    {"name": "Wireless Noise Cancelling Headphones", "description": "Premium over-ear headphones with active noise cancellation and 30-hour battery life.", "price": 299.99, "original_price": 399.99, "category": "Electronics", "brand": "SoundMax", "images": ["https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800"], "features": ["Active Noise Cancellation", "30-hour Battery", "Bluetooth 5.0", "Built-in Mic"], "stock": 50},
    {"name": "Smart Watch Pro Series", "description": "Advanced smartwatch with health monitoring, GPS, and 7-day battery.", "price": 449.00, "original_price": 549.00, "category": "Electronics", "brand": "TechFit", "images": ["https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800"], "features": ["Heart Rate Monitor", "GPS Tracking", "Water Resistant", "7-day Battery"], "stock": 30},
    {"name": "Ultra Slim Laptop 15\"", "description": "Powerful laptop with M2 chip, 16GB RAM, and stunning Retina display.", "price": 1299.00, "original_price": 1499.00, "category": "Electronics", "brand": "ProBook", "images": ["https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=800"], "features": ["M2 Chip", "16GB RAM", "512GB SSD", "15\" Retina Display"], "stock": 20},
    {"name": "Wireless Earbuds Pro", "description": "True wireless earbuds with spatial audio and transparency mode.", "price": 199.00, "original_price": 249.00, "category": "Electronics", "brand": "SoundMax", "images": ["https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=800"], "features": ["Spatial Audio", "Transparency Mode", "24-hour Battery", "Wireless Charging"], "stock": 100},
    {"name": "4K Smart TV 55\"", "description": "Crystal clear 4K resolution with smart features and voice control.", "price": 799.00, "original_price": 999.00, "category": "Electronics", "brand": "VisionPlus", "images": ["https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?w=800"], "features": ["4K UHD", "Smart TV", "Voice Control", "HDR10+"], "stock": 15},
    
    # Fashion
    {"name": "Premium Cotton T-Shirt", "description": "Soft, breathable cotton t-shirt perfect for everyday wear.", "price": 29.99, "original_price": 39.99, "category": "Fashion", "brand": "UrbanStyle", "images": ["https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=800"], "features": ["100% Cotton", "Breathable", "Machine Washable", "Multiple Colors"], "stock": 200},
    {"name": "Classic Denim Jeans", "description": "Timeless slim-fit jeans crafted from premium denim.", "price": 79.99, "original_price": 99.99, "category": "Fashion", "brand": "DenimCo", "images": ["https://images.unsplash.com/photo-1542272454315-4c01d7abdf4a?w=800"], "features": ["Premium Denim", "Slim Fit", "Stretch Comfort", "Classic Blue"], "stock": 150},
    {"name": "Running Sneakers", "description": "Lightweight running shoes with responsive cushioning.", "price": 129.00, "original_price": 159.00, "category": "Fashion", "brand": "SpeedRun", "images": ["https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=800"], "features": ["Lightweight", "Responsive Cushioning", "Breathable Mesh", "Non-slip Sole"], "stock": 80},
    {"name": "Leather Crossbody Bag", "description": "Elegant genuine leather bag perfect for any occasion.", "price": 149.00, "original_price": 199.00, "category": "Fashion", "brand": "LuxeLeather", "images": ["https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=800"], "features": ["Genuine Leather", "Adjustable Strap", "Multiple Pockets", "Gold Hardware"], "stock": 40},
    
    # Home & Living
    {"name": "Ergonomic Office Chair", "description": "Premium ergonomic chair with lumbar support and adjustable armrests.", "price": 399.00, "original_price": 499.00, "category": "Home & Living", "brand": "ComfortPro", "images": ["https://images.unsplash.com/photo-1580480055273-228ff5388ef8?w=800"], "features": ["Lumbar Support", "Adjustable Height", "Mesh Back", "360° Swivel"], "stock": 25},
    {"name": "Smart LED Desk Lamp", "description": "Touch-controlled desk lamp with multiple brightness levels and USB charging.", "price": 49.99, "original_price": 69.99, "category": "Home & Living", "brand": "BrightLife", "images": ["https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=800"], "features": ["Touch Control", "USB Charging Port", "5 Brightness Levels", "Eye Care Technology"], "stock": 75},
    {"name": "Luxury Bedding Set", "description": "Premium Egyptian cotton bedding set for ultimate comfort.", "price": 199.00, "original_price": 279.00, "category": "Home & Living", "brand": "DreamSleep", "images": ["https://images.unsplash.com/photo-1522771739844-6a9f6d5f14af?w=800"], "features": ["Egyptian Cotton", "Thread Count 400", "Hypoallergenic", "Machine Washable"], "stock": 35},
    
    # Beauty
    {"name": "Vitamin C Serum", "description": "Brightening serum with 20% Vitamin C for radiant skin.", "price": 45.00, "original_price": 59.00, "category": "Beauty", "brand": "GlowSkin", "images": ["https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=800"], "features": ["20% Vitamin C", "Hyaluronic Acid", "Brightening", "Anti-aging"], "stock": 100},
    {"name": "Premium Perfume", "description": "Luxurious fragrance with notes of jasmine, sandalwood, and vanilla.", "price": 125.00, "original_price": 150.00, "category": "Beauty", "brand": "ScentLux", "images": ["https://images.unsplash.com/photo-1541643600914-78b084683601?w=800"], "features": ["Eau de Parfum", "Long Lasting", "100ml", "Unisex"], "stock": 0},  # Out of stock
    {"name": "Hair Care Gift Set", "description": "Complete hair care set with shampoo, conditioner, and serum.", "price": 89.00, "original_price": 119.00, "category": "Beauty", "brand": "HairGlow", "images": ["https://images.unsplash.com/photo-1526947425960-945c6e72858f?w=800"], "features": ["Sulfate-free", "Natural Ingredients", "All Hair Types", "3-piece Set"], "stock": 60},
    
    # Sports
    {"name": "Yoga Mat Premium", "description": "Extra thick yoga mat with non-slip surface and carrying strap.", "price": 49.99, "original_price": 69.99, "category": "Sports", "brand": "ZenFit", "images": ["https://images.unsplash.com/photo-1601925260368-ae2f83cf8b7f?w=800"], "features": ["6mm Thick", "Non-slip Surface", "Eco-friendly", "Carrying Strap"], "stock": 120},
    {"name": "Adjustable Dumbbell Set", "description": "Space-saving adjustable dumbbells from 5-50 lbs.", "price": 299.00, "original_price": 399.00, "category": "Sports", "brand": "PowerLift", "images": ["https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=800"], "features": ["5-50 lbs Range", "Quick Adjust", "Space Saving", "Ergonomic Grip"], "stock": 20},
    {"name": "Smart Fitness Tracker", "description": "Advanced fitness tracker with heart rate monitoring and GPS.", "price": 149.00, "original_price": 179.00, "category": "Sports", "brand": "FitTrack", "images": ["https://images.unsplash.com/photo-1575311373937-040b8e1fd5b6?w=800"], "features": ["Heart Rate Monitor", "GPS", "Sleep Tracking", "Water Resistant"], "stock": 0},  # Out of stock
    {"name": "Resistance Bands Set", "description": "Complete set of 5 resistance bands for full-body workouts.", "price": 29.99, "original_price": 39.99, "category": "Sports", "brand": "FlexBand", "images": ["https://images.unsplash.com/photo-1598289431512-b97b0917affc?w=800"], "features": ["5 Resistance Levels", "Latex-free", "Portable", "Door Anchor Included"], "stock": 200},
    
    # Grocery
    {"name": "Organic Honey", "description": "Pure organic honey from local beekeepers.", "price": 15.99, "original_price": 19.99, "category": "Grocery", "brand": "NatureBee", "images": ["https://images.unsplash.com/photo-1587049352846-4a222e784d38?w=800"], "features": ["100% Organic", "Raw Unfiltered", "500g Jar", "Local Sourced"], "stock": 150},
    {"name": "Premium Green Tea", "description": "Japanese matcha green tea for a healthy lifestyle.", "price": 24.99, "original_price": 34.99, "category": "Grocery", "brand": "TeaZen", "images": ["https://images.unsplash.com/photo-1556881286-fc6915169721?w=800"], "features": ["Japanese Matcha", "50 Tea Bags", "Antioxidant Rich", "Caffeine Boost"], "stock": 80},
]

async def seed_database():
    """Seed the database with sample data"""
    print("🌱 Starting database seeding...")
    
    db = get_db()
    product_service = ProductService()
    auth_service = AuthService()
    
    # Clear existing data
    print("🗑️ Clearing existing data...")
    for collection_name in COLLECTIONS.values():
        await db[collection_name].delete_many({})
    
    # Create categories
    print("📁 Creating categories...")
    category_map = {}
    for cat_data in CATEGORIES:
        category = await product_service.create_category(CategoryCreate(**cat_data))
        category_map[cat_data["name"]] = category.id
        print(f"  ✅ Created category: {cat_data['name']}")
    
    # Create products
    print("📦 Creating products...")
    for prod_data in PRODUCTS:
        category_name = prod_data.pop("category")
        category_id = category_map.get(category_name)
        
        if not category_id:
            print(f"  ⚠️ Category not found for {prod_data['name']}, skipping...")
            continue
        
        product = await product_service.create_product(ProductCreate(
            name=prod_data["name"],
            description=prod_data["description"],
            price=prod_data["price"],
            original_price=prod_data.get("original_price"),
            category_id=category_id,
            brand=prod_data.get("brand"),
            images=prod_data.get("images", []),
            features=prod_data.get("features", []),
            stock=prod_data.get("stock", 0),
        ))
        print(f"  ✅ Created product: {prod_data['name']} (Stock: {prod_data.get('stock', 0)})")
    
    # Create test user
    print("👤 Creating test user...")
    try:
        test_user = await auth_service.register(UserCreate(
            name="Test User",
            email="test@polluxkart.com",
            phone="+919876543210",
            password="Test@123"
        ))
        print(f"  ✅ Created test user: {test_user.email}")
    except ValueError as e:
        print(f"  ⚠️ Test user may already exist: {e}")
    
    print("\n✨ Database seeding completed!")
    print("\n📊 Summary:")
    print(f"  - Categories: {len(CATEGORIES)}")
    print(f"  - Products: {len(PRODUCTS)}")
    print(f"  - Test User: test@polluxkart.com / Test@123")

if __name__ == "__main__":
    asyncio.run(seed_database())
