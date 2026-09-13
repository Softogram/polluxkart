from typing import Optional
from datetime import datetime, timezone
import uuid
from config.database import get_db, COLLECTIONS
from models.cart import CartResponse, CartItem, WishlistResponse, WishlistItem
from services.product_service import ProductService

class CartService:
    def __init__(self):
        self.db = get_db()
        self.carts = self.db[COLLECTIONS['carts']]
        self.product_service = ProductService()
    
    async def get_cart(self, user_id: str) -> CartResponse:
        """Get user's cart or create empty one"""
        cart = await self.carts.find_one({"user_id": user_id}, {"_id": 0})
        
        if not cart:
            cart = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "items": [],
                "subtotal": 0.0,
                "discount": 0.0,
                "tax": 0.0,
                "total": 0.0,
                "item_count": 0,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            await self.carts.insert_one(cart)
        
        return CartResponse(**cart)
    
    async def add_to_cart(self, user_id: str, product_id: str, quantity: int = 1) -> CartResponse:
        """Add item to cart"""
        # Get product details
        product = await self.product_service.get_product_by_id(product_id)
        if not product:
            raise ValueError("Product not found")
        
        if not product.in_stock:
            raise ValueError("Product is out of stock")
        
        cart = await self.get_cart(user_id)
        items = cart.items
        
        # Check if item already in cart
        existing_idx = None
        for idx, item in enumerate(items):
            if item.product_id == product_id:
                existing_idx = idx
                break
        
        if existing_idx is not None:
            # Update quantity
            items[existing_idx].quantity += quantity
        else:
            # Add new item
            items.append(CartItem(
                product_id=product_id,
                quantity=quantity,
                price=product.price,
                name=product.name,
                image=product.image
            ))
        
        # Recalculate totals
        return await self._update_cart(user_id, items)
    
    async def update_cart_item(self, user_id: str, product_id: str, quantity: int) -> CartResponse:
        """Update item quantity in cart"""
        cart = await self.get_cart(user_id)
        items = cart.items
        
        if quantity <= 0:
            # Remove item
            items = [item for item in items if item.product_id != product_id]
        else:
            # Update quantity
            for item in items:
                if item.product_id == product_id:
                    item.quantity = quantity
                    break
        
        return await self._update_cart(user_id, items)
    
    async def remove_from_cart(self, user_id: str, product_id: str) -> CartResponse:
        """Remove item from cart"""
        return await self.update_cart_item(user_id, product_id, 0)
    
    async def clear_cart(self, user_id: str) -> CartResponse:
        """Clear all items from cart"""
        return await self._update_cart(user_id, [])
    
    async def _update_cart(self, user_id: str, items: list) -> CartResponse:
        """Update cart with new items and recalculate totals"""
        # Calculate totals
        subtotal = sum(item.price * item.quantity for item in items)
        tax = round(subtotal * 0.18, 2)  # 18% GST
        total = round(subtotal + tax, 2)
        item_count = sum(item.quantity for item in items)
        
        cart_dict = {
            "items": [item.model_dump() for item in items],
            "subtotal": round(subtotal, 2),
            "discount": 0.0,
            "tax": tax,
            "total": total,
            "item_count": item_count,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        
        await self.carts.update_one(
            {"user_id": user_id},
            {"$set": cart_dict},
            upsert=True
        )
        
        return await self.get_cart(user_id)


class WishlistService:
    def __init__(self):
        self.db = get_db()
        self.wishlists = self.db[COLLECTIONS['wishlists']]
        self.product_service = ProductService()
    
    async def get_wishlist(self, user_id: str) -> WishlistResponse:
        """Get user's wishlist"""
        wishlist = await self.wishlists.find_one({"user_id": user_id}, {"_id": 0})
        
        if not wishlist:
            wishlist = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "items": [],
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            await self.wishlists.insert_one(wishlist)
        
        return WishlistResponse(**wishlist)
    
    async def add_to_wishlist(self, user_id: str, product_id: str) -> WishlistResponse:
        """Add item to wishlist"""
        # Verify product exists
        product = await self.product_service.get_product_by_id(product_id)
        if not product:
            raise ValueError("Product not found")
        
        wishlist = await self.get_wishlist(user_id)
        
        # Check if already in wishlist
        if any(item.product_id == product_id for item in wishlist.items):
            return wishlist
        
        # Add item
        await self.wishlists.update_one(
            {"user_id": user_id},
            {
                "$push": {
                    "items": {
                        "product_id": product_id,
                        "added_at": datetime.now(timezone.utc).isoformat()
                    }
                },
                "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
            }
        )
        
        return await self.get_wishlist(user_id)
    
    async def remove_from_wishlist(self, user_id: str, product_id: str) -> WishlistResponse:
        """Remove item from wishlist"""
        await self.wishlists.update_one(
            {"user_id": user_id},
            {
                "$pull": {"items": {"product_id": product_id}},
                "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
            }
        )
        
        return await self.get_wishlist(user_id)
    
    async def is_in_wishlist(self, user_id: str, product_id: str) -> bool:
        """Check if product is in wishlist"""
        wishlist = await self.get_wishlist(user_id)
        return any(item.product_id == product_id for item in wishlist.items)
    
    async def get_wishlist_products(self, user_id: str):
        """Get full product details for wishlist items - optimized batch query"""
        wishlist = await self.get_wishlist(user_id)
        
        if not wishlist.items:
            return []
        
        # Batch fetch all products in a single query (avoid N+1)
        product_ids = [item.product_id for item in wishlist.items]
        products_cursor = self.db[COLLECTIONS['products']].find(
            {"id": {"$in": product_ids}, "is_active": True},
            {"_id": 0}
        )
        products_list = await products_cursor.to_list(length=len(product_ids))
        
        # Convert to ProductResponse objects
        from models.product import ProductResponse
        return [ProductResponse(**p) for p in products_list]

