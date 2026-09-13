# Admin Models
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
from enum import Enum
import uuid

def generate_uuid():
    return str(uuid.uuid4())

def current_time():
    return datetime.now(timezone.utc)

# User Role
class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

# Dashboard Stats
class DashboardStats(BaseModel):
    total_orders: int = 0
    total_revenue: float = 0.0
    total_products: int = 0
    total_users: int = 0
    pending_orders: int = 0
    low_stock_products: int = 0
    orders_today: int = 0
    revenue_today: float = 0.0

# Promotion/Coupon
class DiscountType(str, Enum):
    PERCENTAGE = "percentage"
    FIXED = "fixed"

class PromotionStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"

class PromotionCreate(BaseModel):
    code: str
    description: Optional[str] = None
    discount_type: DiscountType = DiscountType.PERCENTAGE
    discount_value: float
    min_order_amount: Optional[float] = None
    max_discount: Optional[float] = None
    usage_limit: Optional[int] = None
    per_user_limit: int = 1
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    applicable_categories: List[str] = []
    applicable_products: List[str] = []

class PromotionResponse(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    code: str
    description: Optional[str] = None
    discount_type: DiscountType
    discount_value: float
    min_order_amount: Optional[float] = None
    max_discount: Optional[float] = None
    usage_limit: Optional[int] = None
    per_user_limit: int = 1
    times_used: int = 0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    applicable_categories: List[str] = []
    applicable_products: List[str] = []
    status: PromotionStatus = PromotionStatus.ACTIVE
    created_at: datetime = Field(default_factory=current_time)
    updated_at: datetime = Field(default_factory=current_time)

class PromotionUpdate(BaseModel):
    description: Optional[str] = None
    discount_type: Optional[DiscountType] = None
    discount_value: Optional[float] = None
    min_order_amount: Optional[float] = None
    max_discount: Optional[float] = None
    usage_limit: Optional[int] = None
    per_user_limit: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    applicable_categories: Optional[List[str]] = None
    applicable_products: Optional[List[str]] = None
    status: Optional[PromotionStatus] = None

# Product Admin
class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    original_price: Optional[float] = None
    category_id: str
    brand: Optional[str] = None
    sku: Optional[str] = None
    stock: int = 0
    images: List[str] = []
    features: List[str] = []
    is_active: bool = True

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    original_price: Optional[float] = None
    category_id: Optional[str] = None
    brand: Optional[str] = None
    sku: Optional[str] = None
    stock: Optional[int] = None
    images: Optional[List[str]] = None
    features: Optional[List[str]] = None
    is_active: Optional[bool] = None

# Category Admin
class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    image: Optional[str] = None
    parent_id: Optional[str] = None
    is_active: bool = True

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None
    parent_id: Optional[str] = None
    is_active: Optional[bool] = None

# Brand Admin
class BrandCreate(BaseModel):
    name: str
    description: Optional[str] = None
    logo: Optional[str] = None
    website: Optional[str] = None
    is_active: bool = True

class BrandUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    logo: Optional[str] = None
    website: Optional[str] = None
    is_active: Optional[bool] = None

class BrandResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    logo: Optional[str] = None
    website: Optional[str] = None
    is_active: bool = True
    product_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# Image Upload
class ImageUploadResponse(BaseModel):
    url: str
    filename: str
    size: int
    content_type: str
