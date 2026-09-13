"""
Script to clean up seed/development data from production database.
Run this ONLY ONCE after initial deployment to remove test data.

Usage:
    python scripts/cleanup_seed_data.py
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

# Collections to clean
COLLECTIONS_TO_CLEAN = [
    "products",
    "categories", 
    "inventory",
    "reviews",
    "carts",
    "wishlists",
    "orders",
    "payments",
    "stock_movements",
    "promotions",
]

# Collections to preserve (user data)
PRESERVE_COLLECTIONS = ["users"]

async def cleanup_seed_data():
    """Remove all seed/test data from the database"""
    
    mongo_url = os.getenv("MONGO_URL")
    db_name = os.getenv("DB_NAME", "polluxkart")
    
    if not mongo_url:
        print("ERROR: MONGO_URL not set in environment")
        return
    
    print(f"Connecting to database: {db_name}")
    print(f"MongoDB URL: {mongo_url[:50]}...")
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("\n" + "="*50)
    print("⚠️  WARNING: This will DELETE all data from:")
    print("="*50)
    for collection in COLLECTIONS_TO_CLEAN:
        count = await db[collection].count_documents({})
        print(f"  - {collection}: {count} documents")
    
    print("\n✅ These collections will be PRESERVED:")
    for collection in PRESERVE_COLLECTIONS:
        count = await db[collection].count_documents({})
        print(f"  - {collection}: {count} documents")
    
    print("\n" + "="*50)
    confirm = input("Type 'DELETE' to confirm cleanup: ")
    
    if confirm != "DELETE":
        print("Cleanup cancelled.")
        return
    
    print("\nCleaning up collections...")
    
    for collection in COLLECTIONS_TO_CLEAN:
        result = await db[collection].delete_many({})
        print(f"  ✓ {collection}: deleted {result.deleted_count} documents")
    
    print("\n✅ Cleanup complete!")
    print("Your production database is now clean and ready for real data.")
    print("\nNext steps:")
    print("1. Add real products via Admin Panel (/admin/products)")
    print("2. Add categories via Admin Panel (/admin/categories)")
    print("3. Configure promotions via Admin Panel (/admin/promotions)")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(cleanup_seed_data())
