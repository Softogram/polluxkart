from typing import Optional, List
from datetime import datetime, timezone
import uuid
import re
from config.database import get_db, COLLECTIONS
from models.product import (
    ProductCreate, ProductUpdate, ProductResponse, ProductListResponse,
    CategoryCreate, CategoryResponse, CategoryWithSubs, SubCategory,
    ReviewCreate, ReviewResponse
)

class ProductService:
    def __init__(self):
        self.db = get_db()
        self.products = self.db[COLLECTIONS['products']]
        self.categories = self.db[COLLECTIONS['categories']]
        self.reviews = self.db[COLLECTIONS['reviews']]
        self.inventory = self.db[COLLECTIONS['inventory']]
    
    # ============ Categories ============
    
    async def create_category(self, category_data: CategoryCreate) -> CategoryResponse:
        """Create a new category"""
        category_id = str(uuid.uuid4())
        slug = re.sub(r'[^a-z0-9]+', '-', category_data.name.lower()).strip('-')
        
        category_dict = {
            "id": category_id,
            "name": category_data.name,
            "description": category_data.description,
            "image": category_data.image,
            "parent_id": category_data.parent_id,
            "slug": slug,
            "product_count": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        
        await self.categories.insert_one(category_dict)
        return CategoryResponse(**category_dict)
    
    async def get_categories(self, include_subcategories: bool = True) -> List[CategoryWithSubs]:
        """Get all categories with optional subcategories"""
        # Get main categories (no parent)
        main_categories = await self.categories.find(
            {"parent_id": None}, {"_id": 0}
        ).to_list(100)
        
        if not include_subcategories:
            return [CategoryWithSubs(**cat) for cat in main_categories]
        
        # Get all subcategories
        all_subcategories = await self.categories.find(
            {"parent_id": {"$ne": None}}, {"_id": 0}
        ).to_list(500)
        
        # Group subcategories by parent
        subs_by_parent = {}
        for sub in all_subcategories:
            parent_id = sub.get("parent_id")
            if parent_id not in subs_by_parent:
                subs_by_parent[parent_id] = []
            subs_by_parent[parent_id].append(SubCategory(id=sub["id"], name=sub["name"]))
        
        # Combine
        result = []
        for cat in main_categories:
            cat_with_subs = CategoryWithSubs(**cat)
            cat_with_subs.subcategories = subs_by_parent.get(cat["id"], [])
            result.append(cat_with_subs)
        
        return result
    
    async def get_category_by_id(self, category_id: str) -> Optional[CategoryResponse]:
        """Get category by ID"""
        category = await self.categories.find_one({"id": category_id}, {"_id": 0})
        if not category:
            return None
        return CategoryResponse(**category)
    
    # ============ Products ============
    
    async def create_product(self, product_data: ProductCreate) -> ProductResponse:
        """Create a new product"""
        product_id = str(uuid.uuid4())
        sku = product_data.sku or f"SKU-{product_id[:8].upper()}"
        
        # Get category name
        category = await self.get_category_by_id(product_data.category_id)
        category_name = category.name if category else "General"
        
        product_dict = {
            "id": product_id,
            "name": product_data.name,
            "description": product_data.description,
            "price": product_data.price,
            "original_price": product_data.original_price,
            "category_id": product_data.category_id,
            "category_name": category_name,
            "brand": product_data.brand,
            "sku": sku,
            "images": product_data.images,
            "image": product_data.images[0] if product_data.images else None,
            "features": product_data.features,
            "stock": product_data.stock,
            "in_stock": product_data.stock > 0,
            "rating": 0.0,
            "review_count": 0,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        
        await self.products.insert_one(product_dict)
        
        # Create inventory record
        await self.inventory.insert_one({
            "id": str(uuid.uuid4()),
            "product_id": product_id,
            "quantity": product_data.stock,
            "reserved": 0,
            "low_stock_threshold": 10,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })
        
        # Update category product count
        await self.categories.update_one(
            {"id": product_data.category_id},
            {"$inc": {"product_count": 1}}
        )
        
        return ProductResponse(**product_dict)
    
    async def get_products(
        self,
        page: int = 1,
        page_size: int = 12,
        category_id: Optional[str] = None,
        brand: Optional[str] = None,
        search: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        sort_by: str = "default",
        in_stock_only: bool = False
    ) -> ProductListResponse:
        """Get products with filtering, sorting, and pagination"""
        query = {"is_active": True}
        
        # Filters
        if category_id:
            query["category_id"] = category_id
        
        if brand:
            query["brand"] = brand
        
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}},
                {"brand": {"$regex": search, "$options": "i"}},
            ]
        
        if min_price is not None:
            query["price"] = query.get("price", {})
            query["price"]["$gte"] = min_price
        
        if max_price is not None:
            query["price"] = query.get("price", {})
            query["price"]["$lte"] = max_price
        
        if in_stock_only:
            query["in_stock"] = True
        
        # Sorting
        sort_options = {
            "default": [("created_at", -1)],
            "price_asc": [("price", 1)],
            "price_desc": [("price", -1)],
            "rating": [("rating", -1)],
            "newest": [("created_at", -1)],
            "name_asc": [("name", 1)],
            "name_desc": [("name", -1)],
        }
        sort = sort_options.get(sort_by, sort_options["default"])
        
        # Count total
        total = await self.products.count_documents(query)
        
        # Get paginated results
        skip = (page - 1) * page_size
        products = await self.products.find(query, {"_id": 0}).sort(sort).skip(skip).limit(page_size).to_list(page_size)
        
        return ProductListResponse(
            products=[ProductResponse(**p) for p in products],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )
    
    async def get_product_by_id(self, product_id: str) -> Optional[ProductResponse]:
        """Get product by ID"""
        product = await self.products.find_one({"id": product_id, "is_active": True}, {"_id": 0})
        if not product:
            return None
        return ProductResponse(**product)
    
    async def update_product(self, product_id: str, update_data: ProductUpdate) -> Optional[ProductResponse]:
        """Update a product"""
        update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
        
        if not update_dict:
            return await self.get_product_by_id(product_id)
        
        update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Handle stock update
        if "stock" in update_dict:
            update_dict["in_stock"] = update_dict["stock"] > 0
            # Also update inventory
            await self.inventory.update_one(
                {"product_id": product_id},
                {"$set": {"quantity": update_dict["stock"], "updated_at": update_dict["updated_at"]}}
            )
        
        # Handle images update
        if "images" in update_dict and update_dict["images"]:
            update_dict["image"] = update_dict["images"][0]
        
        result = await self.products.update_one(
            {"id": product_id},
            {"$set": update_dict}
        )
        
        if result.matched_count == 0:
            return None
        
        return await self.get_product_by_id(product_id)
    
    async def delete_product(self, product_id: str) -> bool:
        """Soft delete a product"""
        result = await self.products.update_one(
            {"id": product_id},
            {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        return result.modified_count > 0
    
    async def get_brands(self) -> List[str]:
        """Get all active brands from brands collection"""
        # First try to get from brands collection
        brands_collection = self.db["brands"]
        brands = await brands_collection.find({"is_active": True}, {"name": 1, "_id": 0}).sort("name", 1).to_list(500)
        
        if brands:
            return [b["name"] for b in brands if b.get("name")]
        
        # Fallback: get unique brands from products if brands collection is empty
        brands = await self.products.distinct("brand", {"is_active": True, "brand": {"$ne": None}})
        return sorted([b for b in brands if b])
    
    # ============ Reviews ============
    
    async def add_review(self, user_id: str, user_name: str, review_data: ReviewCreate, user_avatar: Optional[str] = None) -> ReviewResponse:
        """Add a review to a product"""
        review_id = str(uuid.uuid4())
        
        # Check if user already reviewed this product
        existing = await self.reviews.find_one({
            "product_id": review_data.product_id,
            "user_id": user_id
        })
        
        if existing:
            raise ValueError("You have already reviewed this product")
        
        # Check if user purchased this product (for verified purchase badge)
        # This would require checking orders - simplified for now
        verified_purchase = False
        
        review_dict = {
            "id": review_id,
            "product_id": review_data.product_id,
            "user_id": user_id,
            "user_name": user_name,
            "user_avatar": user_avatar,
            "rating": review_data.rating,
            "title": review_data.title,
            "comment": review_data.comment,
            "helpful_count": 0,
            "verified_purchase": verified_purchase,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        
        await self.reviews.insert_one(review_dict)
        
        # Update product rating
        await self._update_product_rating(review_data.product_id)
        
        return ReviewResponse(**review_dict)
    
    async def get_product_reviews(self, product_id: str, page: int = 1, page_size: int = 10) -> List[ReviewResponse]:
        """Get reviews for a product"""
        skip = (page - 1) * page_size
        reviews = await self.reviews.find(
            {"product_id": product_id}, {"_id": 0}
        ).sort("created_at", -1).skip(skip).limit(page_size).to_list(page_size)
        
        return [ReviewResponse(**r) for r in reviews]
    
    async def _update_product_rating(self, product_id: str):
        """Update product's average rating"""
        pipeline = [
            {"$match": {"product_id": product_id}},
            {"$group": {
                "_id": None,
                "avg_rating": {"$avg": "$rating"},
                "count": {"$sum": 1}
            }}
        ]
        
        result = await self.reviews.aggregate(pipeline).to_list(1)
        
        if result:
            avg_rating = round(result[0]["avg_rating"], 1)
            count = result[0]["count"]
            
            await self.products.update_one(
                {"id": product_id},
                {"$set": {"rating": avg_rating, "review_count": count}}
            )
