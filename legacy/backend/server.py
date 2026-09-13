from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import os

from config.settings import settings
from config.database import Database
from routes import (
    auth_router, products_router, cart_router, 
    orders_router, payments_router, inventory_router
)
from routes.admin import router as admin_router
from routes.cloudinary_upload import router as cloudinary_router
from routes.otp import router as otp_router
from routes.s3_upload import router as s3_upload_router

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    logger.info("Starting up PolluxKart API...")
    logger.info(f"MongoDB URL: {settings.MONGO_URL}")
    logger.info(f"Database: {settings.DB_NAME}")
    
    # Test database connection
    try:
        db = Database.get_db()
        await db.command("ping")
        logger.info("Successfully connected to MongoDB")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down PolluxKart API...")
    await Database.close()

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    PolluxKart E-Commerce API
    
    ## Features
    - 🔐 JWT Authentication
    - 📦 Product Management (CRUD, Search, Filter, Sort)
    - 🛒 Shopping Cart
    - ❤️ Wishlist
    - 📋 Order Management
    - 💳 Razorpay Payment Integration
    - 📊 Inventory Management
    - ⭐ Product Reviews & Ratings
    - 📧 Email Notifications
    """,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS middleware
origins = settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with /api prefix
app.include_router(auth_router, prefix="/api")
app.include_router(products_router, prefix="/api")
app.include_router(cart_router, prefix="/api")
app.include_router(orders_router, prefix="/api")
app.include_router(payments_router, prefix="/api")
app.include_router(inventory_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(cloudinary_router, prefix="/api")
app.include_router(otp_router, prefix="/api")
app.include_router(s3_upload_router, prefix="/api")

# Serve uploaded images
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/api/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        db = Database.get_db()
        await db.command("ping")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database": db_status
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to PolluxKart API",
        "version": settings.APP_VERSION,
        "docs": "/api/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
