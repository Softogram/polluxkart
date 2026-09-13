from typing import Optional
from datetime import datetime, timezone
import uuid
from config.database import get_db, COLLECTIONS
from models.inventory import InventoryResponse, InventoryAdjustment, StockMovement

class InventoryService:
    def __init__(self):
        self.db = get_db()
        self.inventory = self.db[COLLECTIONS['inventory']]
        self.products = self.db[COLLECTIONS['products']]
        self.movements = self.db['stock_movements']
    
    async def get_inventory(self, product_id: str) -> Optional[InventoryResponse]:
        """Get inventory for a product"""
        inv = await self.inventory.find_one({"product_id": product_id}, {"_id": 0})
        if not inv:
            return None
        
        # Get product name
        product = await self.products.find_one({"id": product_id}, {"_id": 0, "name": 1})
        
        available = inv["quantity"] - inv.get("reserved", 0)
        
        return InventoryResponse(
            id=inv["id"],
            product_id=product_id,
            product_name=product["name"] if product else None,
            quantity=inv["quantity"],
            reserved=inv.get("reserved", 0),
            available=available,
            low_stock_threshold=inv.get("low_stock_threshold", 10),
            is_low_stock=available <= inv.get("low_stock_threshold", 10),
            is_out_of_stock=available <= 0,
        )
    
    async def get_available_stock(self, product_id: str) -> int:
        """Get available stock (total - reserved)"""
        inv = await self.inventory.find_one({"product_id": product_id}, {"_id": 0})
        if not inv:
            return 0
        return inv["quantity"] - inv.get("reserved", 0)
    
    async def adjust_inventory(
        self, 
        product_id: str, 
        adjustment: int, 
        reason: str,
        user_id: Optional[str] = None
    ) -> InventoryResponse:
        """Adjust inventory quantity"""
        inv = await self.inventory.find_one({"product_id": product_id}, {"_id": 0})
        
        if not inv:
            raise ValueError("Inventory record not found")
        
        previous_qty = inv["quantity"]
        new_qty = previous_qty + adjustment
        
        if new_qty < 0:
            raise ValueError("Insufficient stock")
        
        # Update inventory
        await self.inventory.update_one(
            {"product_id": product_id},
            {"$set": {
                "quantity": new_qty,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Update product stock
        await self.products.update_one(
            {"id": product_id},
            {"$set": {
                "stock": new_qty,
                "in_stock": new_qty > 0,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Record movement
        await self._record_movement(
            product_id=product_id,
            quantity_change=adjustment,
            previous_quantity=previous_qty,
            new_quantity=new_qty,
            reason=reason,
            created_by=user_id
        )
        
        return await self.get_inventory(product_id)
    
    async def reserve_stock(self, product_id: str, quantity: int, order_id: str) -> bool:
        """Reserve stock for an order"""
        inv = await self.inventory.find_one({"product_id": product_id}, {"_id": 0})
        
        if not inv:
            raise ValueError("Inventory record not found")
        
        available = inv["quantity"] - inv.get("reserved", 0)
        if available < quantity:
            raise ValueError("Insufficient stock")
        
        await self.inventory.update_one(
            {"product_id": product_id},
            {
                "$inc": {"reserved": quantity},
                "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
            }
        )
        
        # Record movement
        await self._record_movement(
            product_id=product_id,
            quantity_change=0,
            previous_quantity=inv["quantity"],
            new_quantity=inv["quantity"],
            reason=f"Reserved for order",
            reference_id=order_id
        )
        
        return True
    
    async def confirm_reservation(self, product_id: str, quantity: int, order_id: str) -> bool:
        """Confirm reservation - deduct from actual stock"""
        inv = await self.inventory.find_one({"product_id": product_id}, {"_id": 0})
        
        if not inv:
            raise ValueError("Inventory record not found")
        
        previous_qty = inv["quantity"]
        new_qty = previous_qty - quantity
        new_reserved = max(0, inv.get("reserved", 0) - quantity)
        
        await self.inventory.update_one(
            {"product_id": product_id},
            {"$set": {
                "quantity": new_qty,
                "reserved": new_reserved,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Update product stock
        await self.products.update_one(
            {"id": product_id},
            {"$set": {
                "stock": new_qty,
                "in_stock": new_qty > 0,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Record movement
        await self._record_movement(
            product_id=product_id,
            quantity_change=-quantity,
            previous_quantity=previous_qty,
            new_quantity=new_qty,
            reason="Order confirmed - stock deducted",
            reference_id=order_id
        )
        
        return True
    
    async def release_reservation(self, product_id: str, quantity: int, order_id: str) -> bool:
        """Release reserved stock (e.g., order cancelled)"""
        await self.inventory.update_one(
            {"product_id": product_id},
            {
                "$inc": {"reserved": -quantity},
                "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
            }
        )
        
        # Make sure reserved doesn't go negative
        await self.inventory.update_one(
            {"product_id": product_id, "reserved": {"$lt": 0}},
            {"$set": {"reserved": 0}}
        )
        
        # Record movement
        inv = await self.inventory.find_one({"product_id": product_id}, {"_id": 0})
        await self._record_movement(
            product_id=product_id,
            quantity_change=0,
            previous_quantity=inv["quantity"] if inv else 0,
            new_quantity=inv["quantity"] if inv else 0,
            reason="Reservation released - order cancelled",
            reference_id=order_id
        )
        
        return True
    
    async def get_low_stock_products(self) -> list:
        """Get all products with low stock"""
        pipeline = [
            {
                "$lookup": {
                    "from": "products",
                    "localField": "product_id",
                    "foreignField": "id",
                    "as": "product"
                }
            },
            {"$unwind": "$product"},
            {
                "$project": {
                    "_id": 0,
                    "product_id": 1,
                    "product_name": "$product.name",
                    "quantity": 1,
                    "reserved": 1,
                    "available": {"$subtract": ["$quantity", {"$ifNull": ["$reserved", 0]}]},
                    "low_stock_threshold": 1,
                }
            },
            {
                "$match": {
                    "$expr": {"$lte": ["$available", "$low_stock_threshold"]}
                }
            }
        ]
        
        results = await self.inventory.aggregate(pipeline).to_list(100)
        return results
    
    async def _record_movement(
        self,
        product_id: str,
        quantity_change: int,
        previous_quantity: int,
        new_quantity: int,
        reason: str,
        reference_id: Optional[str] = None,
        created_by: Optional[str] = None
    ):
        """Record a stock movement"""
        movement = {
            "id": str(uuid.uuid4()),
            "product_id": product_id,
            "quantity_change": quantity_change,
            "previous_quantity": previous_quantity,
            "new_quantity": new_quantity,
            "reason": reason,
            "reference_id": reference_id,
            "created_by": created_by,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await self.movements.insert_one(movement)
