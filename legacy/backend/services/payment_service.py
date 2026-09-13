from typing import Optional
from datetime import datetime, timezone
import uuid
import hmac
import hashlib
from config.database import get_db, COLLECTIONS
from config.settings import settings
from models.order import (
    PaymentCreate, RazorpayOrderResponse, PaymentVerify, 
    PaymentResponse, PaymentStatus
)

# Import razorpay if available
try:
    import razorpay
    RAZORPAY_AVAILABLE = True
except ImportError:
    RAZORPAY_AVAILABLE = False
    razorpay = None

class PaymentService:
    def __init__(self):
        self.db = get_db()
        self.payments = self.db[COLLECTIONS['payments']]
        self.orders = self.db[COLLECTIONS['orders']]
        
        # Initialize Razorpay client if credentials available
        self.razorpay_client = None
        if RAZORPAY_AVAILABLE and settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET:
            self.razorpay_client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )
    
    async def create_razorpay_order(
        self, 
        order_id: str, 
        user_id: str
    ) -> RazorpayOrderResponse:
        """Create a Razorpay order for payment"""
        # Get order
        order = await self.orders.find_one({"id": order_id, "user_id": user_id}, {"_id": 0})
        if not order:
            raise ValueError("Order not found")
        
        if order["payment_status"] == PaymentStatus.COMPLETED.value:
            raise ValueError("Order already paid")
        
        amount_paise = int(order["total"] * 100)  # Convert to paise
        
        if self.razorpay_client:
            # Create actual Razorpay order
            razorpay_order = self.razorpay_client.order.create({
                "amount": amount_paise,
                "currency": "INR",
                "receipt": order_id,
                "payment_capture": 1  # Auto capture
            })
            razorpay_order_id = razorpay_order["id"]
        else:
            # Mock for development
            razorpay_order_id = f"order_mock_{uuid.uuid4().hex[:16]}"
        
        # Save payment record
        payment_id = str(uuid.uuid4())
        payment_dict = {
            "id": payment_id,
            "order_id": order_id,
            "user_id": user_id,
            "amount": order["total"],
            "currency": "INR",
            "status": PaymentStatus.PENDING.value,
            "payment_method": "razorpay",
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": None,
            "razorpay_signature": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
        }
        
        await self.payments.insert_one(payment_dict)
        
        # Update order with Razorpay order ID
        await self.orders.update_one(
            {"id": order_id},
            {"$set": {
                "razorpay_order_id": razorpay_order_id,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        return RazorpayOrderResponse(
            razorpay_order_id=razorpay_order_id,
            amount=amount_paise,
            currency="INR",
            key_id=settings.RAZORPAY_KEY_ID or "rzp_test_mock"
        )
    
    async def verify_payment(
        self, 
        payment_data: PaymentVerify,
        user_id: str
    ) -> PaymentResponse:
        """Verify Razorpay payment signature and complete payment"""
        # Find payment record
        payment = await self.payments.find_one({
            "razorpay_order_id": payment_data.razorpay_order_id,
            "user_id": user_id
        }, {"_id": 0})
        
        if not payment:
            raise ValueError("Payment not found")
        
        if payment["status"] == PaymentStatus.COMPLETED.value:
            raise ValueError("Payment already completed")
        
        # Verify signature
        if self.razorpay_client and settings.RAZORPAY_KEY_SECRET:
            try:
                self.razorpay_client.utility.verify_payment_signature({
                    "razorpay_order_id": payment_data.razorpay_order_id,
                    "razorpay_payment_id": payment_data.razorpay_payment_id,
                    "razorpay_signature": payment_data.razorpay_signature
                })
            except Exception as e:
                # Update payment status to failed
                await self.payments.update_one(
                    {"id": payment["id"]},
                    {"$set": {"status": PaymentStatus.FAILED.value}}
                )
                raise ValueError(f"Payment verification failed: {str(e)}")
        else:
            # Mock verification for development
            # In real scenario, verify the signature
            pass
        
        # Update payment record
        await self.payments.update_one(
            {"id": payment["id"]},
            {"$set": {
                "status": PaymentStatus.COMPLETED.value,
                "razorpay_payment_id": payment_data.razorpay_payment_id,
                "razorpay_signature": payment_data.razorpay_signature,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }}
        )
        
        # Update order payment status
        await self.orders.update_one(
            {"id": payment["order_id"]},
            {"$set": {
                "payment_status": PaymentStatus.COMPLETED.value,
                "payment_id": payment_data.razorpay_payment_id,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        updated_payment = await self.payments.find_one({"id": payment["id"]}, {"_id": 0})
        return PaymentResponse(**updated_payment)
    
    async def get_payment_by_order(self, order_id: str) -> Optional[PaymentResponse]:
        """Get payment record for an order"""
        payment = await self.payments.find_one({"order_id": order_id}, {"_id": 0})
        if not payment:
            return None
        return PaymentResponse(**payment)
    
    async def handle_webhook(self, payload: dict, signature: str) -> bool:
        """Handle Razorpay webhook events"""
        # Verify webhook signature
        if settings.RAZORPAY_WEBHOOK_SECRET:
            expected_signature = hmac.new(
                settings.RAZORPAY_WEBHOOK_SECRET.encode(),
                str(payload).encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                raise ValueError("Invalid webhook signature")
        
        event = payload.get("event")
        payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
        
        if event == "payment.captured":
            # Payment successful
            razorpay_order_id = payment_entity.get("order_id")
            razorpay_payment_id = payment_entity.get("id")
            
            await self.payments.update_one(
                {"razorpay_order_id": razorpay_order_id},
                {"$set": {
                    "status": PaymentStatus.COMPLETED.value,
                    "razorpay_payment_id": razorpay_payment_id,
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                }}
            )
            
            # Update order
            payment = await self.payments.find_one({"razorpay_order_id": razorpay_order_id}, {"_id": 0})
            if payment:
                await self.orders.update_one(
                    {"id": payment["order_id"]},
                    {"$set": {
                        "payment_status": PaymentStatus.COMPLETED.value,
                        "payment_id": razorpay_payment_id,
                    }}
                )
        
        elif event == "payment.failed":
            razorpay_order_id = payment_entity.get("order_id")
            
            await self.payments.update_one(
                {"razorpay_order_id": razorpay_order_id},
                {"$set": {"status": PaymentStatus.FAILED.value}}
            )
        
        return True
