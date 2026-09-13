# Admin Service - Business logic for admin operations
from config.database import Database
from models.admin import (
    DashboardStats, PromotionCreate, PromotionResponse, PromotionUpdate,
    ProductCreate, ProductUpdate, CategoryCreate, CategoryUpdate,
    BrandCreate, BrandUpdate, BrandResponse,
    PromotionStatus, UserRole
)
from models.order import OrderStatus
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import uuid

class AdminService:
    def __init__(self):
        self.db = Database.get_db()

    # Dashboard
    async def get_dashboard_stats(self) -> DashboardStats:
        """Get dashboard statistics"""
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Get counts
        total_orders = await self.db.orders.count_documents({})
        total_products = await self.db.products.count_documents({})
        total_users = await self.db.users.count_documents({})
        pending_orders = await self.db.orders.count_documents({"status": OrderStatus.PENDING.value})
        low_stock = await self.db.inventory.count_documents({"quantity": {"$lte": 10}})
        
        # Today's stats
        orders_today = await self.db.orders.count_documents({
            "created_at": {"$gte": today_start}
        })
        
        # Revenue calculations
        pipeline = [{"$group": {"_id": None, "total": {"$sum": "$total"}}}]
        total_revenue_result = await self.db.orders.aggregate(pipeline).to_list(1)
        total_revenue = total_revenue_result[0]["total"] if total_revenue_result else 0
        
        today_pipeline = [
            {"$match": {"created_at": {"$gte": today_start}}},
            {"$group": {"_id": None, "total": {"$sum": "$total"}}}
        ]
        today_revenue_result = await self.db.orders.aggregate(today_pipeline).to_list(1)
        revenue_today = today_revenue_result[0]["total"] if today_revenue_result else 0
        
        return DashboardStats(
            total_orders=total_orders,
            total_revenue=total_revenue,
            total_products=total_products,
            total_users=total_users,
            pending_orders=pending_orders,
            low_stock_products=low_stock,
            orders_today=orders_today,
            revenue_today=revenue_today
        )

    # Products
    async def create_product(self, product_data: ProductCreate) -> dict:
        """Create a new product"""
        product = {
            "id": str(uuid.uuid4()),
            "name": product_data.name,
            "description": product_data.description,
            "price": product_data.price,
            "original_price": product_data.original_price,
            "category_id": product_data.category_id,
            "brand": product_data.brand,
            "sku": product_data.sku or f"SKU-{uuid.uuid4().hex[:8].upper()}",
            "stock": product_data.stock,
            "images": product_data.images,
            "features": product_data.features,
            "rating": 0,
            "review_count": 0,
            "is_active": product_data.is_active,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        await self.db.products.insert_one(product)
        
        # Create inventory record
        await self.db.inventory.insert_one({
            "id": str(uuid.uuid4()),
            "product_id": product["id"],
            "quantity": product_data.stock,
            "reserved": 0,
            "last_updated": datetime.now(timezone.utc)
        })
        
        return await self._get_product_with_category(product["id"])

    async def update_product(self, product_id: str, update_data: ProductUpdate) -> Optional[dict]:
        """Update a product"""
        update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
        if not update_dict:
            return await self._get_product_with_category(product_id)
        
        update_dict["updated_at"] = datetime.now(timezone.utc)
        
        result = await self.db.products.update_one(
            {"id": product_id},
            {"$set": update_dict}
        )
        
        if result.modified_count == 0:
            return None
        
        # Update inventory if stock changed
        if "stock" in update_dict:
            await self.db.inventory.update_one(
                {"product_id": product_id},
                {"$set": {"quantity": update_dict["stock"], "last_updated": datetime.now(timezone.utc)}}
            )
        
        return await self._get_product_with_category(product_id)

    async def delete_product(self, product_id: str) -> bool:
        """Delete a product"""
        result = await self.db.products.delete_one({"id": product_id})
        if result.deleted_count > 0:
            await self.db.inventory.delete_one({"product_id": product_id})
            return True
        return False

    async def _get_product_with_category(self, product_id: str) -> Optional[dict]:
        """Get product with category info"""
        product = await self.db.products.find_one({"id": product_id}, {"_id": 0})
        if product and product.get("category_id"):
            category = await self.db.categories.find_one({"id": product["category_id"]}, {"_id": 0})
            if category:
                product["category_name"] = category.get("name")
        return product

    # Categories
    async def create_category(self, category_data: CategoryCreate) -> dict:
        """Create a new category"""
        category = {
            "id": str(uuid.uuid4()),
            "name": category_data.name,
            "description": category_data.description,
            "image": category_data.image,
            "parent_id": category_data.parent_id,
            "is_active": category_data.is_active,
            "product_count": 0,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        await self.db.categories.insert_one(category)
        category.pop("_id", None)
        return category

    async def update_category(self, category_id: str, update_data: CategoryUpdate) -> Optional[dict]:
        """Update a category"""
        update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
        if not update_dict:
            return await self.db.categories.find_one({"id": category_id}, {"_id": 0})
        
        update_dict["updated_at"] = datetime.now(timezone.utc)
        
        result = await self.db.categories.update_one(
            {"id": category_id},
            {"$set": update_dict}
        )
        
        if result.modified_count == 0:
            return None
        
        return await self.db.categories.find_one({"id": category_id}, {"_id": 0})

    async def delete_category(self, category_id: str) -> bool:
        """Delete a category"""
        # Check if category has products
        product_count = await self.db.products.count_documents({"category_id": category_id})
        if product_count > 0:
            raise ValueError(f"Cannot delete category with {product_count} products")
        
        result = await self.db.categories.delete_one({"id": category_id})
        return result.deleted_count > 0

    async def get_all_categories(self) -> List[dict]:
        """Get all categories with product counts"""
        categories = await self.db.categories.find({}, {"_id": 0}).to_list(100)
        
        for category in categories:
            count = await self.db.products.count_documents({"category_id": category["id"]})
            category["product_count"] = count
        
        return categories

    # Promotions
    async def create_promotion(self, promo_data: PromotionCreate) -> dict:
        """Create a new promotion"""
        # Check if code already exists
        existing = await self.db.promotions.find_one({"code": promo_data.code.upper()})
        if existing:
            raise ValueError("Promotion code already exists")
        
        promotion = {
            "id": str(uuid.uuid4()),
            "code": promo_data.code.upper(),
            "description": promo_data.description,
            "discount_type": promo_data.discount_type.value,
            "discount_value": promo_data.discount_value,
            "min_order_amount": promo_data.min_order_amount,
            "max_discount": promo_data.max_discount,
            "usage_limit": promo_data.usage_limit,
            "per_user_limit": promo_data.per_user_limit,
            "times_used": 0,
            "start_date": promo_data.start_date,
            "end_date": promo_data.end_date,
            "applicable_categories": promo_data.applicable_categories,
            "applicable_products": promo_data.applicable_products,
            "status": PromotionStatus.ACTIVE.value,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        await self.db.promotions.insert_one(promotion)
        promotion.pop("_id", None)
        return promotion

    async def update_promotion(self, promo_id: str, update_data: PromotionUpdate) -> Optional[dict]:
        """Update a promotion"""
        update_dict = {}
        for k, v in update_data.model_dump().items():
            if v is not None:
                if k in ['discount_type', 'status']:
                    update_dict[k] = v.value if hasattr(v, 'value') else v
                else:
                    update_dict[k] = v
        
        if not update_dict:
            return await self.db.promotions.find_one({"id": promo_id}, {"_id": 0})
        
        update_dict["updated_at"] = datetime.now(timezone.utc)
        
        result = await self.db.promotions.update_one(
            {"id": promo_id},
            {"$set": update_dict}
        )
        
        if result.modified_count == 0:
            return None
        
        return await self.db.promotions.find_one({"id": promo_id}, {"_id": 0})

    async def delete_promotion(self, promo_id: str) -> bool:
        """Delete a promotion"""
        result = await self.db.promotions.delete_one({"id": promo_id})
        return result.deleted_count > 0

    async def get_all_promotions(self, status: Optional[str] = None) -> List[dict]:
        """Get all promotions"""
        query = {}
        if status:
            query["status"] = status
        
        promotions = await self.db.promotions.find(query, {"_id": 0}).to_list(100)
        return promotions

    async def validate_promotion(self, code: str, order_total: float, user_id: str) -> dict:
        """Validate and calculate promotion discount"""
        promotion = await self.db.promotions.find_one({"code": code.upper()}, {"_id": 0})
        
        if not promotion:
            raise ValueError("Invalid promotion code")
        
        if promotion["status"] != PromotionStatus.ACTIVE.value:
            raise ValueError("Promotion is not active")
        
        now = datetime.now(timezone.utc)
        if promotion.get("start_date") and now < promotion["start_date"]:
            raise ValueError("Promotion has not started yet")
        
        if promotion.get("end_date") and now > promotion["end_date"]:
            raise ValueError("Promotion has expired")
        
        if promotion.get("usage_limit") and promotion["times_used"] >= promotion["usage_limit"]:
            raise ValueError("Promotion usage limit reached")
        
        if promotion.get("min_order_amount") and order_total < promotion["min_order_amount"]:
            raise ValueError(f"Minimum order amount is ₹{promotion['min_order_amount']}")
        
        # Calculate discount
        if promotion["discount_type"] == "percentage":
            discount = order_total * (promotion["discount_value"] / 100)
            if promotion.get("max_discount"):
                discount = min(discount, promotion["max_discount"])
        else:
            discount = promotion["discount_value"]
        
        return {
            "promotion_id": promotion["id"],
            "code": promotion["code"],
            "discount": round(discount, 2),
            "discount_type": promotion["discount_type"],
            "discount_value": promotion["discount_value"]
        }

    # Orders (Admin)
    async def get_all_orders(
        self, 
        page: int = 1, 
        page_size: int = 20,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> dict:
        """Get all orders with pagination"""
        query = {}
        if status:
            query["status"] = status
        if search:
            query["$or"] = [
                {"order_number": {"$regex": search, "$options": "i"}},
                {"shipping_address.full_name": {"$regex": search, "$options": "i"}}
            ]
        
        total = await self.db.orders.count_documents(query)
        skip = (page - 1) * page_size
        
        orders = await self.db.orders.find(query, {"_id": 0})\
            .sort("created_at", -1)\
            .skip(skip)\
            .limit(page_size)\
            .to_list(page_size)
        
        return {
            "orders": orders,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }

    async def update_order_status(self, order_id: str, status: str, tracking_number: Optional[str] = None) -> Optional[dict]:
        """Update order status"""
        update_data = {
            "status": status,
            "updated_at": datetime.now(timezone.utc)
        }
        
        if tracking_number:
            update_data["tracking_number"] = tracking_number
        
        if status == OrderStatus.DELIVERED.value:
            update_data["delivered_at"] = datetime.now(timezone.utc)
        
        result = await self.db.orders.update_one(
            {"id": order_id},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            return None
        
        return await self.db.orders.find_one({"id": order_id}, {"_id": 0})

    # Users (Admin)
    async def get_all_users(self, page: int = 1, page_size: int = 20, search: Optional[str] = None) -> dict:
        """Get all users with pagination"""
        query = {}
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}},
                {"phone": {"$regex": search, "$options": "i"}}
            ]
        
        total = await self.db.users.count_documents(query)
        skip = (page - 1) * page_size
        
        users = await self.db.users.find(query, {"_id": 0, "password": 0})\
            .sort("created_at", -1)\
            .skip(skip)\
            .limit(page_size)\
            .to_list(page_size)
        
        return {
            "users": users,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }

    async def update_user_role(self, user_id: str, role: str) -> Optional[dict]:
        """Update user role"""
        result = await self.db.users.update_one(
            {"id": user_id},
            {"$set": {"role": role, "updated_at": datetime.now(timezone.utc)}}
        )
        
        if result.modified_count == 0:
            return None
        
        return await self.db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})

    # Brands
    async def create_brand(self, brand_data: BrandCreate) -> dict:
        """Create a new brand"""
        # Check if brand name already exists
        existing = await self.db.brands.find_one({"name": {"$regex": f"^{brand_data.name}$", "$options": "i"}})
        if existing:
            raise ValueError("Brand with this name already exists")
        
        brand = {
            "id": str(uuid.uuid4()),
            "name": brand_data.name,
            "description": brand_data.description,
            "logo": brand_data.logo,
            "website": brand_data.website,
            "is_active": brand_data.is_active,
            "product_count": 0,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        await self.db.brands.insert_one(brand)
        brand.pop("_id", None)
        return brand

    async def update_brand(self, brand_id: str, update_data: BrandUpdate) -> Optional[dict]:
        """Update a brand"""
        update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
        if not update_dict:
            return await self.db.brands.find_one({"id": brand_id}, {"_id": 0})
        
        # Check if updating name and it already exists
        if "name" in update_dict:
            existing = await self.db.brands.find_one({
                "name": {"$regex": f"^{update_dict['name']}$", "$options": "i"},
                "id": {"$ne": brand_id}
            })
            if existing:
                raise ValueError("Brand with this name already exists")
        
        update_dict["updated_at"] = datetime.now(timezone.utc)
        
        result = await self.db.brands.update_one(
            {"id": brand_id},
            {"$set": update_dict}
        )
        
        if result.matched_count == 0:
            return None
        
        return await self.db.brands.find_one({"id": brand_id}, {"_id": 0})

    async def delete_brand(self, brand_id: str) -> bool:
        """Delete a brand"""
        # Check if brand has products
        brand = await self.db.brands.find_one({"id": brand_id}, {"_id": 0})
        if not brand:
            return False
        
        product_count = await self.db.products.count_documents({"brand": brand["name"]})
        if product_count > 0:
            raise ValueError(f"Cannot delete brand with {product_count} products. Please reassign products first.")
        
        result = await self.db.brands.delete_one({"id": brand_id})
        return result.deleted_count > 0

    async def get_all_brands(self, include_inactive: bool = False) -> List[dict]:
        """Get all brands with product counts"""
        query = {} if include_inactive else {"is_active": True}
        brands = await self.db.brands.find(query, {"_id": 0}).sort("name", 1).to_list(500)
        
        # Update product counts
        for brand in brands:
            count = await self.db.products.count_documents({"brand": brand["name"], "is_active": True})
            brand["product_count"] = count
        
        return brands

    async def migrate_existing_brands(self) -> dict:
        """Migrate existing brands from products to brands collection"""
        # Get unique brands from products
        existing_brands = await self.db.products.distinct("brand", {"brand": {"$ne": None}})
        
        migrated = 0
        skipped = 0
        
        for brand_name in existing_brands:
            if not brand_name or not brand_name.strip():
                continue
            
            # Check if brand already exists
            existing = await self.db.brands.find_one({"name": {"$regex": f"^{brand_name}$", "$options": "i"}})
            if existing:
                skipped += 1
                continue
            
            # Create brand
            brand = {
                "id": str(uuid.uuid4()),
                "name": brand_name.strip(),
                "description": None,
                "logo": None,
                "website": None,
                "is_active": True,
                "product_count": 0,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            
            await self.db.brands.insert_one(brand)
            migrated += 1
        
        return {
            "migrated": migrated,
            "skipped": skipped,
            "total_brands": migrated + skipped
        }
