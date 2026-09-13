# Cloudinary Upload Routes
from fastapi import APIRouter, Query, HTTPException, Depends
from utils.auth import get_current_user
import cloudinary
import cloudinary.utils
import cloudinary.uploader
import os
import time

router = APIRouter(prefix="/cloudinary", tags=["Cloudinary"])

# Initialize Cloudinary
def init_cloudinary():
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
    api_key = os.getenv("CLOUDINARY_API_KEY")
    api_secret = os.getenv("CLOUDINARY_API_SECRET")
    
    if cloud_name and api_key and api_secret:
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True
        )
        return True
    return False

# Allowed folders for uploads
ALLOWED_FOLDERS = ("products/", "categories/", "users/", "uploads/")

@router.get("/signature")
async def generate_signature(
    resource_type: str = Query("image", enum=["image", "video"]),
    folder: str = Query("products"),
    current_user: dict = Depends(get_current_user)
):
    """Generate a signed upload signature for Cloudinary"""
    
    # Check if Cloudinary is configured
    if not init_cloudinary():
        raise HTTPException(
            status_code=503,
            detail="Cloudinary is not configured. Please set CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET environment variables."
        )
    
    # Validate folder
    folder_path = f"{folder}/" if not folder.endswith("/") else folder
    if not any(folder_path.startswith(allowed) for allowed in ALLOWED_FOLDERS):
        raise HTTPException(status_code=400, detail="Invalid folder path")
    
    timestamp = int(time.time())
    params = {
        "timestamp": timestamp,
        "folder": folder,
        "resource_type": resource_type
    }
    
    signature = cloudinary.utils.api_sign_request(
        params,
        os.getenv("CLOUDINARY_API_SECRET")
    )
    
    return {
        "signature": signature,
        "timestamp": timestamp,
        "cloud_name": os.getenv("CLOUDINARY_CLOUD_NAME"),
        "api_key": os.getenv("CLOUDINARY_API_KEY"),
        "folder": folder,
        "resource_type": resource_type
    }

@router.get("/config")
async def get_cloudinary_config():
    """Check if Cloudinary is configured (public endpoint)"""
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
    return {
        "configured": bool(cloud_name and os.getenv("CLOUDINARY_API_KEY") and os.getenv("CLOUDINARY_API_SECRET")),
        "cloud_name": cloud_name if cloud_name else None
    }
