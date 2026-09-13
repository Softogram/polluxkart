from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
import uuid

def generate_uuid():
    return str(uuid.uuid4())

def current_time():
    return datetime.now(timezone.utc)

# Cart Item
class CartItem(BaseModel):
    product_id: str
    quantity: int = Field(ge=1)
    price: float
    name: str
    image: Optional[str] = None

class CartItemAdd(BaseModel):
    product_id: str
    quantity: int = Field(ge=1, default=1)

class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=0)  # 0 means remove

# Cart
class CartResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=generate_uuid)
    user_id: str
    items: List[CartItem] = []
    subtotal: float = 0.0
    discount: float = 0.0
    tax: float = 0.0
    total: float = 0.0
    item_count: int = 0
    updated_at: datetime = Field(default_factory=current_time)

# Wishlist
class WishlistItem(BaseModel):
    product_id: str
    added_at: datetime = Field(default_factory=current_time)

class WishlistResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=generate_uuid)
    user_id: str
    items: List[WishlistItem] = []
    updated_at: datetime = Field(default_factory=current_time)

class WishlistItemAdd(BaseModel):
    product_id: str
