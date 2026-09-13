from typing import Optional, List
from datetime import datetime, timezone
import uuid
import random
import string
from config.database import get_db, COLLECTIONS
from config.settings import settings
from models.order import (
    OrderCreate, OrderResponse, OrderListResponse, OrderStatus, 
    PaymentStatus, OrderItem, OrderStatusUpdate
)
from services.cart_service import CartService
from services.inventory_service import InventoryService
from utils.email import EmailService

class OrderService:
    def __init__(self):
        self.db = get_db()
        self.orders = self.db[COLLECTIONS['orders']]
        self.users = self.db[COLLECTIONS['users']]
        self.cart_service = CartService()
        self.inventory_service = InventoryService()
    
    def _generate_order_number(self) -> str:
        """Generate unique order number"""
        timestamp = datetime.now().strftime("%Y%m%d")
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"PK-{timestamp}-{random_str}"
    
    async def create_order(self, user_id: str, order_data: OrderCreate) -> OrderResponse:
        """Create a new order from cart"""
        # Get cart
        cart = await self.cart_service.get_cart(user_id)
        
        if not cart.items:
            raise ValueError("Cart is empty")
        
        # Batch check inventory for all items (avoid N+1)
        product_ids = [item.product_id for item in cart.items]
        inventory_cursor = self.db[COLLECTIONS['inventory']].find(
            {"product_id": {"$in": product_ids}},
            {"_id": 0}
        )
        inventory_list = await inventory_cursor.to_list(length=len(product_ids))
        inventory_map = {inv["product_id"]: inv for inv in inventory_list}
        
        # Validate stock for all items
        for item in cart.items:
            inv = inventory_map.get(item.product_id)
            available = (inv.get("quantity", 0) - inv.get("reserved", 0)) if inv else 0
            if available < item.quantity:
                raise ValueError(f"Insufficient stock for {item.name}. Available: {available}")
        
        # Create order items
        order_items = [
            OrderItem(
                product_id=item.product_id,
                name=item.name,
                image=item.image,
                price=item.price,
                quantity=item.quantity,
                total=round(item.price * item.quantity, 2)
            )
            for item in cart.items
        ]
        
        # Calculate totals
        subtotal = cart.subtotal
        tax = cart.tax
        shipping_fee = 0.0 if subtotal >= 500 else 50.0  # Free shipping over ₹500
        total = round(subtotal + tax + shipping_fee - cart.discount, 2)
        
        # Create order
        order_id = str(uuid.uuid4())
        order_number = self._generate_order_number()
        
        order_dict = {
            "id": order_id,
            "order_number": order_number,
            "user_id": user_id,
            "items": [item.model_dump() for item in order_items],
            "shipping_address": order_data.shipping_address.model_dump(),
            "billing_address": order_data.billing_address.model_dump() if order_data.billing_address else None,
            "subtotal": subtotal,
            "discount": cart.discount,
            "shipping_fee": shipping_fee,
            "tax": tax,
            "total": total,
            "status": OrderStatus.PENDING.value,
            "payment_status": PaymentStatus.PENDING.value,
            "payment_method": order_data.payment_method.value,
            "payment_id": None,
            "razorpay_order_id": None,
            "notes": order_data.notes,
            "tracking_number": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "delivered_at": None,
        }
        
        await self.orders.insert_one(order_dict)
        
        # Reserve inventory for each item
        for item in cart.items:
            await self.db[COLLECTIONS['inventory']].update_one(
                {"product_id": item.product_id},
                {"$inc": {"reserved": item.quantity}}
            )
            
            # Record stock movement
            await self.db[COLLECTIONS['stock_movements']].insert_one({
                "id": str(uuid.uuid4()),
                "product_id": item.product_id,
                "type": "reserve",
                "quantity": item.quantity,
                "reference_id": order_id,
                "reference_type": "order",
                "notes": f"Reserved for order {order_number}",
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
        
        return OrderResponse(**order_dict)
    
    async def get_order(self, order_id: str, user_id: Optional[str] = None) -> Optional[OrderResponse]:
        """Get order by ID"""
        query = {"id": order_id}
        if user_id:
            query["user_id"] = user_id
        
        order = await self.orders.find_one(query, {"_id": 0})
        if not order:
            return None
        
        return OrderResponse(**order)
    
    async def get_order_by_number(self, order_number: str, user_id: Optional[str] = None) -> Optional[OrderResponse]:
        """Get order by order number"""
        query = {"order_number": order_number}
        if user_id:
            query["user_id"] = user_id
        
        order = await self.orders.find_one(query, {"_id": 0})
        if not order:
            return None
        
        return OrderResponse(**order)
    
    async def get_user_orders(
        self, 
        user_id: str, 
        page: int = 1, 
        page_size: int = 10,
        status: Optional[OrderStatus] = None
    ) -> OrderListResponse:
        """Get all orders for a user"""
        query = {"user_id": user_id}
        if status:
            query["status"] = status.value
        
        total = await self.orders.count_documents(query)
        skip = (page - 1) * page_size
        
        orders = await self.orders.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(page_size).to_list(page_size)
        
        return OrderListResponse(
            orders=[OrderResponse(**o) for o in orders],
            total=total,
            page=page,
            page_size=page_size
        )
    
    async def update_order_status(
        self, 
        order_id: str, 
        status_update: OrderStatusUpdate
    ) -> Optional[OrderResponse]:
        """Update order status"""
        update_dict = {
            "status": status_update.status.value,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        
        if status_update.tracking_number:
            update_dict["tracking_number"] = status_update.tracking_number
        
        if status_update.notes:
            update_dict["notes"] = status_update.notes
        
        if status_update.status == OrderStatus.DELIVERED:
            update_dict["delivered_at"] = datetime.now(timezone.utc).isoformat()
        
        result = await self.orders.update_one(
            {"id": order_id},
            {"$set": update_dict}
        )
        
        if result.matched_count == 0:
            return None
        
        order = await self.get_order(order_id)
        
        # Send email notifications based on status
        if order and status_update.status == OrderStatus.SHIPPED:
            user = await self.users.find_one({"id": order.user_id}, {"_id": 0})
            if user and user.get("email"):
                await EmailService.send_order_shipped(
                    to_email=user["email"],
                    order_number=order.order_number,
                    customer_name=user["name"],
                    tracking_number=order.tracking_number
                )
        
        return order
    
    async def confirm_order(self, order_id: str) -> Optional[OrderResponse]:
        """Confirm order after payment"""
        order = await self.get_order(order_id)
        if not order:
            return None
        
        # Update order status
        update_dict = {
            "status": OrderStatus.CONFIRMED.value,
            "payment_status": PaymentStatus.COMPLETED.value,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        
        await self.orders.update_one(
            {"id": order_id},
            {"$set": update_dict}
        )
        
        # Confirm inventory reservation (deduct from actual stock)
        for item in order.items:
            await self.inventory_service.confirm_reservation(
                item.product_id,
                item.quantity,
                order_id
            )
        
        # Clear user's cart
        await self.cart_service.clear_cart(order.user_id)
        
        # Send confirmation email
        user = await self.users.find_one({"id": order.user_id}, {"_id": 0})
        if user and user.get("email"):
            await EmailService.send_order_confirmation(
                to_email=user["email"],
                order_number=order.order_number,
                customer_name=user["name"],
                items=[item.model_dump() for item in order.items],
                total=order.total,
                shipping_address=order.shipping_address.model_dump()
            )
        
        return await self.get_order(order_id)
    
    async def cancel_order(self, order_id: str, user_id: str) -> Optional[OrderResponse]:
        """Cancel an order"""
        order = await self.get_order(order_id, user_id)
        if not order:
            return None
        
        # Can only cancel pending or confirmed orders
        if order.status not in [OrderStatus.PENDING, OrderStatus.CONFIRMED]:
            raise ValueError(f"Cannot cancel order with status: {order.status}")
        
        # Release reserved inventory
        for item in order.items:
            await self.inventory_service.release_reservation(
                item.product_id,
                item.quantity,
                order_id
            )
        
        # Update order status
        update_dict = {
            "status": OrderStatus.CANCELLED.value,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        
        await self.orders.update_one(
            {"id": order_id},
            {"$set": update_dict}
        )
        
        return await self.get_order(order_id)
