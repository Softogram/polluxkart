from typing import Optional
from datetime import datetime, timezone
import uuid
from config.database import get_db, COLLECTIONS
from models.user import UserCreate, UserResponse, UserInDB, UserUpdate
from utils.auth import hash_password, verify_password, create_access_token

class AuthService:
    def __init__(self):
        self.db = get_db()
        self.collection = self.db[COLLECTIONS['users']]
    
    async def register(self, user_data: UserCreate) -> UserResponse:
        """Register a new user"""
        # Check if user already exists
        existing = await self.collection.find_one({
            "$or": [
                {"phone": user_data.phone},
                {"email": user_data.email} if user_data.email else {"_id": None}
            ]
        })
        
        if existing:
            if existing.get('phone') == user_data.phone:
                raise ValueError("Phone number already registered")
            if user_data.email and existing.get('email') == user_data.email:
                raise ValueError("Email already registered")
        
        # Create user
        user_id = str(uuid.uuid4())
        user_dict = {
            "id": user_id,
            "email": user_data.email,
            "phone": user_data.phone,
            "name": user_data.name,
            "password_hash": hash_password(user_data.password),
            "avatar": f"https://api.dicebear.com/7.x/avataaars/svg?seed={user_id}",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        
        await self.collection.insert_one(user_dict)
        
        return UserResponse(
            id=user_id,
            email=user_data.email,
            phone=user_data.phone,
            name=user_data.name,
            avatar=user_dict["avatar"],
            is_active=True,
        )
    
    async def login(self, identifier: str, password: str) -> tuple[UserResponse, str]:
        """Login user and return user data with access token"""
        # Find user by email or phone
        user = await self.collection.find_one({
            "$or": [
                {"email": identifier},
                {"phone": identifier}
            ]
        }, {"_id": 0})
        
        if not user:
            raise ValueError("Invalid credentials")
        
        if not verify_password(password, user.get("password_hash", "")):
            raise ValueError("Invalid credentials")
        
        if not user.get("is_active", True):
            raise ValueError("Account is deactivated")
        
        # Create access token
        token = create_access_token({
            "sub": user["id"],
            "email": user.get("email"),
            "phone": user.get("phone"),
            "role": user.get("role", "user"),
        })
        
        user_response = UserResponse(
            id=user["id"],
            email=user.get("email"),
            phone=user["phone"],
            name=user["name"],
            avatar=user.get("avatar", ""),
            is_active=user.get("is_active", True),
            role=user.get("role", "user"),
        )
        
        return user_response, token
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserResponse]:
        """Get user by ID"""
        user = await self.collection.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
        if not user:
            return None
        
        return UserResponse(**user)
    
    async def update_user(self, user_id: str, update_data: UserUpdate) -> Optional[UserResponse]:
        """Update user profile"""
        update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
        
        if not update_dict:
            return await self.get_user_by_id(user_id)
        
        update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        result = await self.collection.update_one(
            {"id": user_id},
            {"$set": update_dict}
        )
        
        if result.modified_count == 0:
            return None
        
        return await self.get_user_by_id(user_id)

    async def reset_password(self, identifier: str, new_password: str) -> bool:
        """Reset user password by email or phone"""
        # Find user by email or phone
        user = await self.collection.find_one({
            "$or": [
                {"email": identifier},
                {"phone": identifier}
            ]
        })
        
        if not user:
            raise ValueError("No account found with this email or phone number")
        
        # Update password
        new_password_hash = hash_password(new_password)
        
        result = await self.collection.update_one(
            {"id": user["id"]},
            {
                "$set": {
                    "password_hash": new_password_hash,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        if result.modified_count == 0:
            raise ValueError("Failed to update password")
        
        return True
