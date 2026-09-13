from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import settings

class Database:
    client: AsyncIOMotorClient = None
    
    @classmethod
    def get_client(cls) -> AsyncIOMotorClient:
        if cls.client is None:
            cls.client = AsyncIOMotorClient(settings.MONGO_URL)
        return cls.client
    
    @classmethod
    def get_db(cls):
        return cls.get_client()[settings.DB_NAME]
    
    @classmethod
    async def close(cls):
        if cls.client:
            cls.client.close()
            cls.client = None

# Convenience function
def get_db():
    return Database.get_db()

# Collection names
COLLECTIONS = {
    'users': 'users',
    'products': 'products',
    'categories': 'categories',
    'carts': 'carts',
    'orders': 'orders',
    'reviews': 'reviews',
    'wishlists': 'wishlists',
    'inventory': 'inventory',
    'payments': 'payments',
    'stock_movements': 'stock_movements',
    'promotions': 'promotions',
}
