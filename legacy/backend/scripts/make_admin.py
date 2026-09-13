"""
Script to make a user an admin
Usage: python scripts/make_admin.py <email>
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import Database
from datetime import datetime, timezone

async def make_admin(email: str):
    """Make a user an admin by email"""
    db = Database.get_db()
    
    # Find user
    user = await db.users.find_one({"email": email})
    if not user:
        print(f"User with email '{email}' not found")
        return False
    
    # Update role
    result = await db.users.update_one(
        {"email": email},
        {"$set": {"role": "admin", "updated_at": datetime.now(timezone.utc)}}
    )
    
    if result.modified_count > 0:
        print(f"Successfully made '{email}' an admin!")
        return True
    else:
        print(f"User '{email}' is already an admin or update failed")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/make_admin.py <email>")
        print("Example: python scripts/make_admin.py test@polluxkart.com")
        sys.exit(1)
    
    email = sys.argv[1]
    asyncio.run(make_admin(email))
