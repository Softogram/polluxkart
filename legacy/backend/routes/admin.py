# Admin Routes
from fastapi import APIRouter, HTTPException, status, Depends, Query, UploadFile, File
from typing import Optional, List
from pydantic import BaseModel, EmailStr
from models.admin import (
    DashboardStats, PromotionCreate, PromotionResponse, PromotionUpdate,
    ProductCreate, ProductUpdate, CategoryCreate, CategoryUpdate,
    BrandCreate, BrandUpdate,
    ImageUploadResponse, UserRole
)
from models.order import OrderStatus
from services.admin_service import AdminService
from utils.auth import get_current_user, hash_password
from config.database import get_db
import os
import uuid
import aiofiles
from datetime import datetime, timezone

router = APIRouter(prefix="/admin", tags=["Admin"])
admin_service = AdminService()

# Model for initial admin setup
class InitialAdminCreate(BaseModel):
    email: EmailStr
    phone: str
    name: str
    password: str
    setup_key: str  # Secret key for extra security

# Upload directory
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Secret key for initial admin setup (should match in production)
ADMIN_SETUP_KEY = os.environ.get("ADMIN_SETUP_KEY", "POLLUXKART_INITIAL_ADMIN_2025")

# ===============================================
# INITIAL ADMIN SETUP - ONE TIME USE ONLY
# ===============================================
@router.post("/setup/initial-admin", status_code=status.HTTP_201_CREATED)
async def create_initial_admin(admin_data: InitialAdminCreate):
    """
    Create the first admin user for a fresh production deployment.
    
    This endpoint ONLY works when:
    1. There are NO existing admin users in the database
    2. The correct setup_key is provided
    
    After the first admin is created, this endpoint becomes permanently disabled.
    """
    db = get_db()
    
    # Verify setup key
    if admin_data.setup_key != ADMIN_SETUP_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid setup key. This endpoint is protected."
        )
    
    # Check if any admin already exists
    existing_admin = await db.users.find_one({"role": {"$in": ["admin", "super_admin"]}})
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An admin user already exists. This endpoint can only be used once for initial setup."
        )
    
    # Check if email or phone already exists
    existing_user = await db.users.find_one({
        "$or": [
            {"email": admin_data.email},
            {"phone": admin_data.phone}
        ]
    })
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email or phone already exists."
        )
    
    # Create the admin user
    user_id = str(uuid.uuid4())
    admin_user = {
        "id": user_id,
        "email": admin_data.email,
        "phone": admin_data.phone,
        "name": admin_data.name,
        "password_hash": hash_password(admin_data.password),
        "avatar": f"https://api.dicebear.com/7.x/avataaars/svg?seed={user_id}",
        "is_active": True,
        "role": "admin",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    
    await db.users.insert_one(admin_user)
    
    return {
        "message": "Initial admin user created successfully",
        "user": {
            "id": user_id,
            "email": admin_data.email,
            "phone": admin_data.phone,
            "name": admin_data.name,
            "role": "admin"
        },
        "note": "This endpoint is now disabled. No more admins can be created through this endpoint."
    }

# ===============================================
# CHECK IF INITIAL SETUP IS NEEDED
# ===============================================
@router.get("/setup/status")
async def check_setup_status():
    """
    Check if the initial admin setup has been completed.
    Returns whether an admin exists and if setup is still possible.
    """
    db = get_db()
    
    # Check if any admin exists
    admin_count = await db.users.count_documents({"role": {"$in": ["admin", "super_admin"]}})
    
    return {
        "admin_exists": admin_count > 0,
        "setup_available": admin_count == 0,
        "message": "Initial admin setup is complete" if admin_count > 0 else "No admin exists. Initial setup endpoint is available."
    }

@router.get("/setup/admin-info")
async def get_admin_info():
    """
    Get basic info about existing admin users (for debugging).
    Only returns email/phone, not sensitive data.
    """
    db = get_db()
    
    admins = await db.users.find(
        {"role": {"$in": ["admin", "super_admin"]}},
        {"_id": 0, "email": 1, "phone": 1, "name": 1, "role": 1, "created_at": 1}
    ).to_list(length=10)
    
    return {
        "admin_count": len(admins),
        "admins": admins
    }

# Middleware to check admin role
async def require_admin(current_user: dict = Depends(get_current_user)):
    """Require admin role for access"""
    user_role = current_user.get("role", "user")
    if user_role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

# Dashboard
@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(current_user: dict = Depends(require_admin)):
    """Get dashboard statistics"""
    return await admin_service.get_dashboard_stats()

# Image Upload
@router.post("/upload", response_model=ImageUploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_admin)
):
    """Upload an image file"""
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed: {', '.join(allowed_types)}"
        )
    
    # Validate file size (max 5MB)
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 5MB limit"
        )
    
    # Generate unique filename
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    # Save file
    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)
    
    # Return URL (relative path that will be served)
    return ImageUploadResponse(
        url=f"/api/uploads/{filename}",
        filename=filename,
        size=len(content),
        content_type=file.content_type
    )

@router.post("/upload/multiple", response_model=List[ImageUploadResponse])
async def upload_multiple_images(
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(require_admin)
):
    """Upload multiple image files"""
    if len(files) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 files allowed per upload"
        )
    
    results = []
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    
    for file in files:
        if file.content_type not in allowed_types:
            continue
        
        content = await file.read()
        if len(content) > 5 * 1024 * 1024:
            continue
        
        ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        
        async with aiofiles.open(filepath, "wb") as f:
            await f.write(content)
        
        results.append(ImageUploadResponse(
            url=f"/api/uploads/{filename}",
            filename=filename,
            size=len(content),
            content_type=file.content_type
        ))
    
    return results

# Products
@router.post("/products", status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    current_user: dict = Depends(require_admin)
):
    """Create a new product"""
    return await admin_service.create_product(product_data)

@router.put("/products/{product_id}")
async def update_product(
    product_id: str,
    update_data: ProductUpdate,
    current_user: dict = Depends(require_admin)
):
    """Update a product"""
    product = await admin_service.update_product(product_id, update_data)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product

@router.delete("/products/{product_id}")
async def delete_product(
    product_id: str,
    current_user: dict = Depends(require_admin)
):
    """Delete a product"""
    success = await admin_service.delete_product(product_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return {"message": "Product deleted successfully"}

# Categories
@router.get("/categories")
async def get_all_categories(current_user: dict = Depends(require_admin)):
    """Get all categories with product counts"""
    return await admin_service.get_all_categories()

@router.post("/categories", status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    current_user: dict = Depends(require_admin)
):
    """Create a new category"""
    return await admin_service.create_category(category_data)

@router.put("/categories/{category_id}")
async def update_category(
    category_id: str,
    update_data: CategoryUpdate,
    current_user: dict = Depends(require_admin)
):
    """Update a category"""
    category = await admin_service.update_category(category_id, update_data)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category

@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: str,
    current_user: dict = Depends(require_admin)
):
    """Delete a category"""
    try:
        success = await admin_service.delete_category(category_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        return {"message": "Category deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# Brands
@router.get("/brands")
async def get_all_brands(
    include_inactive: bool = Query(False),
    current_user: dict = Depends(require_admin)
):
    """Get all brands with product counts"""
    return await admin_service.get_all_brands(include_inactive)

@router.post("/brands", status_code=status.HTTP_201_CREATED)
async def create_brand(
    brand_data: BrandCreate,
    current_user: dict = Depends(require_admin)
):
    """Create a new brand"""
    try:
        return await admin_service.create_brand(brand_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.put("/brands/{brand_id}")
async def update_brand(
    brand_id: str,
    update_data: BrandUpdate,
    current_user: dict = Depends(require_admin)
):
    """Update a brand"""
    try:
        brand = await admin_service.update_brand(brand_id, update_data)
        if not brand:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")
        return brand
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/brands/{brand_id}")
async def delete_brand(
    brand_id: str,
    current_user: dict = Depends(require_admin)
):
    """Delete a brand"""
    try:
        success = await admin_service.delete_brand(brand_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")
        return {"message": "Brand deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/brands/migrate")
async def migrate_brands(current_user: dict = Depends(require_admin)):
    """Migrate existing brands from products to brands collection (one-time use)"""
    result = await admin_service.migrate_existing_brands()
    return {
        "message": "Brand migration completed",
        "details": result
    }

# Promotions
@router.get("/promotions")
async def get_all_promotions(
    status: Optional[str] = None,
    current_user: dict = Depends(require_admin)
):
    """Get all promotions"""
    return await admin_service.get_all_promotions(status)

@router.post("/promotions", status_code=status.HTTP_201_CREATED)
async def create_promotion(
    promo_data: PromotionCreate,
    current_user: dict = Depends(require_admin)
):
    """Create a new promotion"""
    try:
        return await admin_service.create_promotion(promo_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.put("/promotions/{promo_id}")
async def update_promotion(
    promo_id: str,
    update_data: PromotionUpdate,
    current_user: dict = Depends(require_admin)
):
    """Update a promotion"""
    promotion = await admin_service.update_promotion(promo_id, update_data)
    if not promotion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Promotion not found")
    return promotion

@router.delete("/promotions/{promo_id}")
async def delete_promotion(
    promo_id: str,
    current_user: dict = Depends(require_admin)
):
    """Delete a promotion"""
    success = await admin_service.delete_promotion(promo_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Promotion not found")
    return {"message": "Promotion deleted successfully"}

@router.post("/promotions/validate")
async def validate_promotion(
    code: str,
    order_total: float,
    current_user: dict = Depends(get_current_user)
):
    """Validate a promotion code"""
    try:
        return await admin_service.validate_promotion(code, order_total, current_user["user_id"])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# Orders (Admin)
@router.get("/orders")
async def get_all_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(require_admin)
):
    """Get all orders with pagination"""
    return await admin_service.get_all_orders(page, page_size, status, search)

@router.put("/orders/{order_id}/status")
async def update_order_status(
    order_id: str,
    status: str,
    tracking_number: Optional[str] = None,
    current_user: dict = Depends(require_admin)
):
    """Update order status"""
    # Validate status
    valid_statuses = [s.value for s in OrderStatus]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Valid: {', '.join(valid_statuses)}"
        )
    
    order = await admin_service.update_order_status(order_id, status, tracking_number)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order

# Users (Admin)
@router.get("/users")
async def get_all_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    current_user: dict = Depends(require_admin)
):
    """Get all users with pagination"""
    return await admin_service.get_all_users(page, page_size, search)

@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    role: str,
    current_user: dict = Depends(require_admin)
):
    """Update user role"""
    valid_roles = [r.value for r in UserRole]
    if role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Valid: {', '.join(valid_roles)}"
        )
    
    user = await admin_service.update_user_role(user_id, role)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

# Database Cleanup (for removing seed data)
@router.delete("/cleanup/seed-data")
async def cleanup_seed_data(
    confirm: str = Query(..., description="Must be 'CONFIRM' to proceed"),
    current_user: dict = Depends(require_admin)
):
    """
    Delete all seed/test data from the database.
    This removes products, categories, orders, etc. but preserves users.
    Use this ONLY ONCE after deployment to clean up development data.
    """
    if confirm != "CONFIRM":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must pass confirm=CONFIRM to proceed with cleanup"
        )
    
    db = admin_service.db
    
    collections_to_clean = [
        "products", "categories", "inventory", "reviews",
        "carts", "wishlists", "orders", "payments", 
        "stock_movements", "promotions"
    ]
    
    results = {}
    for collection in collections_to_clean:
        result = await db[collection].delete_many({})
        results[collection] = result.deleted_count
    
    return {
        "message": "Seed data cleanup complete",
        "deleted": results,
        "preserved": ["users"]
    }

