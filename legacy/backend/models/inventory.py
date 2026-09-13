from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, timezone
import uuid

def generate_uuid():
    return str(uuid.uuid4())

def current_time():
    return datetime.now(timezone.utc)

# Inventory Models
class InventoryBase(BaseModel):
    product_id: str
    quantity: int = 0
    reserved: int = 0  # Reserved for pending orders
    low_stock_threshold: int = 10

class InventoryCreate(InventoryBase):
    pass

class InventoryUpdate(BaseModel):
    quantity: Optional[int] = None
    reserved: Optional[int] = None
    low_stock_threshold: Optional[int] = None

class InventoryResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=generate_uuid)
    product_id: str
    product_name: Optional[str] = None
    quantity: int = 0
    reserved: int = 0
    available: int = 0  # quantity - reserved
    low_stock_threshold: int = 10
    is_low_stock: bool = False
    is_out_of_stock: bool = False
    updated_at: datetime = Field(default_factory=current_time)

class InventoryAdjustment(BaseModel):
    product_id: str
    adjustment: int  # Positive to add, negative to subtract
    reason: str = "Manual adjustment"

class StockMovement(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=generate_uuid)
    product_id: str
    quantity_change: int
    previous_quantity: int
    new_quantity: int
    reason: str
    reference_id: Optional[str] = None  # Order ID, etc.
    created_at: datetime = Field(default_factory=current_time)
    created_by: Optional[str] = None
