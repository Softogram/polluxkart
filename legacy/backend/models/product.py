from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
import uuid

def generate_uuid():
    return str(uuid.uuid4())

def current_time():
    return datetime.now(timezone.utc)

# Category Models
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    image: Optional[str] = None
    parent_id: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=generate_uuid)
    slug: str = ""
    product_count: int = 0
    created_at: datetime = Field(default_factory=current_time)

class SubCategory(BaseModel):
    id: str
    name: str

class CategoryWithSubs(CategoryResponse):
    subcategories: List[SubCategory] = []

# Product Models
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    original_price: Optional[float] = None
    category_id: str
    brand: Optional[str] = None
    sku: Optional[str] = None
    
class ProductCreate(ProductBase):
    images: List[str] = []
    features: List[str] = []
    stock: int = 0
    
class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    original_price: Optional[float] = None
    category_id: Optional[str] = None
    brand: Optional[str] = None
    images: Optional[List[str]] = None
    features: Optional[List[str]] = None
    stock: Optional[int] = None
    is_active: Optional[bool] = None

class ProductResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=generate_uuid)
    name: str
    description: Optional[str] = None
    price: float
    original_price: Optional[float] = None
    category_id: str
    category_name: Optional[str] = None
    brand: Optional[str] = None
    sku: Optional[str] = None
    images: List[str] = []
    image: Optional[str] = None  # Primary image
    features: List[str] = []
    stock: int = 0
    in_stock: bool = True
    rating: float = 0.0
    review_count: int = 0
    is_active: bool = True
    created_at: datetime = Field(default_factory=current_time)
    updated_at: datetime = Field(default_factory=current_time)

class ProductListResponse(BaseModel):
    products: List[ProductResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

# Review Models
class ReviewBase(BaseModel):
    rating: int = Field(ge=1, le=5)
    title: Optional[str] = None
    comment: Optional[str] = None

class ReviewCreate(ReviewBase):
    product_id: str

class ReviewResponse(ReviewBase):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=generate_uuid)
    product_id: str
    user_id: str
    user_name: str
    user_avatar: Optional[str] = None
    created_at: datetime = Field(default_factory=current_time)
    helpful_count: int = 0
    verified_purchase: bool = False

class ProductWithReviews(ProductResponse):
    reviews: List[ReviewResponse] = []
