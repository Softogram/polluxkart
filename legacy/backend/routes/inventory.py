from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List
from models.inventory import InventoryResponse, InventoryAdjustment
from services.inventory_service import InventoryService
from utils.auth import get_current_user

router = APIRouter(prefix="/inventory", tags=["Inventory"])
inventory_service = InventoryService()

@router.get("/{product_id}", response_model=InventoryResponse)
async def get_product_inventory(product_id: str):
    """Get inventory for a product"""
    inventory = await inventory_service.get_inventory(product_id)
    if not inventory:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory not found")
    return inventory

@router.get("/{product_id}/available")
async def get_available_stock(product_id: str):
    """Get available stock for a product"""
    stock = await inventory_service.get_available_stock(product_id)
    return {"product_id": product_id, "available": stock}

@router.post("/adjust", response_model=InventoryResponse)
async def adjust_inventory(
    adjustment: InventoryAdjustment,
    current_user: dict = Depends(get_current_user)
):
    """Adjust inventory quantity (admin only)"""
    try:
        return await inventory_service.adjust_inventory(
            product_id=adjustment.product_id,
            adjustment=adjustment.adjustment,
            reason=adjustment.reason,
            user_id=current_user["user_id"]
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/alerts/low-stock")
async def get_low_stock_alerts(current_user: dict = Depends(get_current_user)):
    """Get products with low stock (admin only)"""
    return await inventory_service.get_low_stock_products()
