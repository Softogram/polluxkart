from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional, List
from models.product import (
    ProductCreate, ProductUpdate, ProductResponse, ProductListResponse,
    CategoryCreate, CategoryResponse, CategoryWithSubs,
    ReviewCreate, ReviewResponse
)
from services.product_service import ProductService
from utils.auth import get_current_user, get_optional_user

router = APIRouter(prefix="/products", tags=["Products"])
product_service = ProductService()

# ============ Categories ============

@router.get("/categories", response_model=List[CategoryWithSubs])
async def get_categories(include_subcategories: bool = True):
    """Get all product categories"""
    return await product_service.get_categories(include_subcategories)

@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new category (admin only)"""
    return await product_service.create_category(category_data)

@router.get("/categories/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: str):
    """Get category by ID"""
    category = await product_service.get_category_by_id(category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category

# ============ Products ============

@router.get("", response_model=ProductListResponse)
async def get_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    category_id: Optional[str] = None,
    brand: Optional[str] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    sort_by: str = Query("default", regex="^(default|price_asc|price_desc|rating|newest|name_asc|name_desc)$"),
    in_stock_only: bool = False
):
    """Get products with filtering, sorting, and pagination"""
    return await product_service.get_products(
        page=page,
        page_size=page_size,
        category_id=category_id,
        brand=brand,
        search=search,
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by,
        in_stock_only=in_stock_only
    )

@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new product (admin only)"""
    return await product_service.create_product(product_data)

@router.get("/brands", response_model=List[str])
async def get_brands():
    """Get all unique product brands"""
    return await product_service.get_brands()

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str):
    """Get product by ID"""
    product = await product_service.get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product

@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    update_data: ProductUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a product (admin only)"""
    product = await product_service.update_product(product_id, update_data)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a product (admin only)"""
    success = await product_service.delete_product(product_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

# ============ Reviews ============

@router.get("/{product_id}/reviews", response_model=List[ReviewResponse])
async def get_product_reviews(
    product_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50)
):
    """Get reviews for a product"""
    return await product_service.get_product_reviews(product_id, page, page_size)

@router.post("/{product_id}/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def add_product_review(
    product_id: str,
    review_data: ReviewCreate,
    current_user: dict = Depends(get_current_user)
):
    """Add a review to a product"""
    # Get user details
    from services.auth_service import AuthService
    auth_service = AuthService()
    user = await auth_service.get_user_by_id(current_user["user_id"])
    
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    
    review_data.product_id = product_id
    
    try:
        return await product_service.add_review(
            user_id=current_user["user_id"],
            user_name=user.name,
            review_data=review_data,
            user_avatar=user.avatar
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
