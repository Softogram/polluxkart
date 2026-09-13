from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
from enum import Enum
import uuid

def generate_uuid():
    return str(uuid.uuid4())

def current_time():
    return datetime.now(timezone.utc)

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class PaymentMethod(str, Enum):
    RAZORPAY = "razorpay"
    COD = "cod"
    WALLET = "wallet"

# Address
class Address(BaseModel):
    full_name: str
    phone: str
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    pincode: str
    country: str = "India"
    is_default: bool = False

class AddressCreate(Address):
    pass

# Order Item
class OrderItem(BaseModel):
    product_id: str
    name: str
    image: Optional[str] = None
    price: float
    quantity: int
    total: float

# Order
class OrderCreate(BaseModel):
    shipping_address: Address
    billing_address: Optional[Address] = None
    payment_method: PaymentMethod = PaymentMethod.RAZORPAY
    notes: Optional[str] = None

class OrderResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=generate_uuid)
    order_number: str = ""
    user_id: str
    items: List[OrderItem] = []
    shipping_address: Address
    billing_address: Optional[Address] = None
    
    subtotal: float = 0.0
    discount: float = 0.0
    shipping_fee: float = 0.0
    tax: float = 0.0
    total: float = 0.0
    
    status: OrderStatus = OrderStatus.PENDING
    payment_status: PaymentStatus = PaymentStatus.PENDING
    payment_method: PaymentMethod = PaymentMethod.RAZORPAY
    payment_id: Optional[str] = None
    razorpay_order_id: Optional[str] = None
    
    notes: Optional[str] = None
    tracking_number: Optional[str] = None
    
    created_at: datetime = Field(default_factory=current_time)
    updated_at: datetime = Field(default_factory=current_time)
    delivered_at: Optional[datetime] = None

class OrderListResponse(BaseModel):
    orders: List[OrderResponse]
    total: int
    page: int
    page_size: int

class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    tracking_number: Optional[str] = None
    notes: Optional[str] = None

# Payment
class PaymentCreate(BaseModel):
    order_id: str
    amount: float

class RazorpayOrderResponse(BaseModel):
    razorpay_order_id: str
    amount: int  # In paise
    currency: str = "INR"
    key_id: str

class PaymentVerify(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str

class PaymentResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=generate_uuid)
    order_id: str
    user_id: str
    amount: float
    currency: str = "INR"
    status: PaymentStatus = PaymentStatus.PENDING
    payment_method: PaymentMethod = PaymentMethod.RAZORPAY
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    razorpay_signature: Optional[str] = None
    created_at: datetime = Field(default_factory=current_time)
    completed_at: Optional[datetime] = None
