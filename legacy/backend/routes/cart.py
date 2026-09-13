from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from models.cart import CartResponse, CartItemAdd, CartItemUpdate, WishlistResponse, WishlistItemAdd
from models.product import ProductResponse
from services.cart_service import CartService, WishlistService
from utils.auth import get_current_user

router = APIRouter(tags=["Cart & Wishlist"])
cart_service = CartService()
wishlist_service = WishlistService()

# ============ Cart ============

@router.get("/cart", response_model=CartResponse)
async def get_cart(current_user: dict = Depends(get_current_user)):
    """Get current user's cart"""
    return await cart_service.get_cart(current_user["user_id"])

@router.post("/cart/items", response_model=CartResponse)
async def add_to_cart(
    item: CartItemAdd,
    current_user: dict = Depends(get_current_user)
):
    """Add item to cart"""
    try:
        return await cart_service.add_to_cart(
            current_user["user_id"],
            item.product_id,
            item.quantity
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.put("/cart/items/{product_id}", response_model=CartResponse)
async def update_cart_item(
    product_id: str,
    item: CartItemUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update item quantity in cart"""
    return await cart_service.update_cart_item(
        current_user["user_id"],
        product_id,
        item.quantity
    )

@router.delete("/cart/items/{product_id}", response_model=CartResponse)
async def remove_from_cart(
    product_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Remove item from cart"""
    return await cart_service.remove_from_cart(current_user["user_id"], product_id)

@router.delete("/cart", response_model=CartResponse)
async def clear_cart(current_user: dict = Depends(get_current_user)):
    """Clear all items from cart"""
    return await cart_service.clear_cart(current_user["user_id"])

# ============ Wishlist ============

@router.get("/wishlist", response_model=WishlistResponse)
async def get_wishlist(current_user: dict = Depends(get_current_user)):
    """Get current user's wishlist"""
    return await wishlist_service.get_wishlist(current_user["user_id"])

@router.get("/wishlist/products", response_model=List[ProductResponse])
async def get_wishlist_products(current_user: dict = Depends(get_current_user)):
    """Get full product details for wishlist items"""
    return await wishlist_service.get_wishlist_products(current_user["user_id"])

@router.post("/wishlist/items", response_model=WishlistResponse)
async def add_to_wishlist(
    item: WishlistItemAdd,
    current_user: dict = Depends(get_current_user)
):
    """Add item to wishlist"""
    try:
        return await wishlist_service.add_to_wishlist(
            current_user["user_id"],
            item.product_id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/wishlist/items/{product_id}", response_model=WishlistResponse)
async def remove_from_wishlist(
    product_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Remove item from wishlist"""
    return await wishlist_service.remove_from_wishlist(current_user["user_id"], product_id)

@router.get("/wishlist/check/{product_id}")
async def check_in_wishlist(
    product_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Check if product is in wishlist"""
    is_in = await wishlist_service.is_in_wishlist(current_user["user_id"], product_id)
    return {"in_wishlist": is_in}
