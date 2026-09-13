from fastapi import APIRouter, HTTPException, status, Depends, Request, Header
from typing import Optional
from models.order import RazorpayOrderResponse, PaymentVerify, PaymentResponse
from services.payment_service import PaymentService
from services.order_service import OrderService
from utils.auth import get_current_user

router = APIRouter(prefix="/payments", tags=["Payments"])
payment_service = PaymentService()
order_service = OrderService()

@router.post("/razorpay/create/{order_id}", response_model=RazorpayOrderResponse)
async def create_razorpay_order(
    order_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Create a Razorpay order for payment"""
    try:
        return await payment_service.create_razorpay_order(order_id, current_user["user_id"])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/razorpay/verify", response_model=PaymentResponse)
async def verify_razorpay_payment(
    payment_data: PaymentVerify,
    current_user: dict = Depends(get_current_user)
):
    """Verify Razorpay payment and complete the order"""
    try:
        # Verify payment
        payment = await payment_service.verify_payment(payment_data, current_user["user_id"])
        
        # Confirm order
        order = await order_service.confirm_order(payment.order_id)
        
        return payment
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/order/{order_id}", response_model=PaymentResponse)
async def get_payment_for_order(
    order_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get payment details for an order"""
    payment = await payment_service.get_payment_by_order(order_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return payment

@router.post("/razorpay/webhook")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None)
):
    """Handle Razorpay webhook events"""
    try:
        payload = await request.json()
        await payment_service.handle_webhook(payload, x_razorpay_signature or "")
        return {"status": "ok"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
