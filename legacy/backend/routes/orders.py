from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional
from models.order import (
    OrderCreate, OrderResponse, OrderListResponse, 
    OrderStatus, OrderStatusUpdate
)
from services.order_service import OrderService
from utils.auth import get_current_user

router = APIRouter(prefix="/orders", tags=["Orders"])
order_service = OrderService()

@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new order from cart"""
    try:
        return await order_service.create_order(current_user["user_id"], order_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("", response_model=OrderListResponse)
async def get_my_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    status: Optional[OrderStatus] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get current user's orders"""
    return await order_service.get_user_orders(
        current_user["user_id"],
        page=page,
        page_size=page_size,
        status=status
    )

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get order by ID"""
    order = await order_service.get_order(order_id, current_user["user_id"])
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order

@router.get("/number/{order_number}", response_model=OrderResponse)
async def get_order_by_number(
    order_number: str,
    current_user: dict = Depends(get_current_user)
):
    """Get order by order number"""
    order = await order_service.get_order_by_number(order_number, current_user["user_id"])
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order

@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Cancel an order"""
    try:
        order = await order_service.cancel_order(order_id, current_user["user_id"])
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        return order
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# Admin endpoints
@router.put("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: str,
    status_update: OrderStatusUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update order status (admin only)"""
    order = await order_service.update_order_status(order_id, status_update)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order
