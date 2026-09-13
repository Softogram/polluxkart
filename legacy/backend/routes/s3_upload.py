# S3 Upload Routes
# Handles image uploads to AWS S3 for products, categories, and users

from fastapi import APIRouter, HTTPException, status, UploadFile, File, Depends, Query
from typing import Optional, List
from pydantic import BaseModel
from services.s3_service import get_s3_service
from utils.auth import get_current_user
import uuid

router = APIRouter(prefix="/upload", tags=["Upload"])

# Response Models
class UploadResponse(BaseModel):
    success: bool
    url: str
    key: Optional[str] = None
    message: Optional[str] = None

class MultiUploadResponse(BaseModel):
    success: bool
    urls: List[str]
    keys: List[str]
    failed: List[str] = []

class PresignedUrlResponse(BaseModel):
    success: bool
    upload_url: str
    fields: dict
    final_url: str
    key: str

# Allowed image types
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def validate_image(file: UploadFile) -> None:
    """Validate uploaded image file"""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided"
        )
    
    ext = '.' + file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    if file.content_type and not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )


@router.post("/product/{product_id}", response_model=UploadResponse)
async def upload_product_image(
    product_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload a product image to S3
    
    - Requires admin role
    - Stores in: products/{product_id}/{filename}
    - Returns the public S3 URL
    """
    # Check admin role
    if current_user.get('role') not in ['admin', 'super_admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    validate_image(file)
    
    s3_service = get_s3_service()
    
    if not s3_service.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="S3 storage is not configured"
        )
    
    # Read file content
    content = await file.read()
    
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # Upload to S3
    success, url_or_error, key = await s3_service.upload_product_image(
        content, product_id, file.filename
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {url_or_error}"
        )
    
    return UploadResponse(success=True, url=url_or_error, key=key)


@router.post("/product/{product_id}/multiple", response_model=MultiUploadResponse)
async def upload_multiple_product_images(
    product_id: str,
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload multiple product images to S3
    
    - Requires admin role
    - Maximum 10 images per request
    """
    if current_user.get('role') not in ['admin', 'super_admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    if len(files) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 images per upload"
        )
    
    s3_service = get_s3_service()
    
    if not s3_service.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="S3 storage is not configured"
        )
    
    urls = []
    keys = []
    failed = []
    
    for file in files:
        try:
            validate_image(file)
            content = await file.read()
            
            if len(content) > MAX_FILE_SIZE:
                failed.append(f"{file.filename}: File too large")
                continue
            
            success, url_or_error, key = await s3_service.upload_product_image(
                content, product_id, file.filename
            )
            
            if success:
                urls.append(url_or_error)
                keys.append(key)
            else:
                failed.append(f"{file.filename}: {url_or_error}")
                
        except HTTPException as e:
            failed.append(f"{file.filename}: {e.detail}")
        except Exception as e:
            failed.append(f"{file.filename}: {str(e)}")
    
    return MultiUploadResponse(
        success=len(urls) > 0,
        urls=urls,
        keys=keys,
        failed=failed
    )


@router.post("/category/{category_id}", response_model=UploadResponse)
async def upload_category_image(
    category_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload a category image to S3
    
    - Requires admin role
    - Stores in: categories/{category_id}/{filename}
    """
    if current_user.get('role') not in ['admin', 'super_admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    validate_image(file)
    
    s3_service = get_s3_service()
    
    if not s3_service.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="S3 storage is not configured"
        )
    
    content = await file.read()
    
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    success, url_or_error, key = await s3_service.upload_category_image(
        content, category_id, file.filename
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {url_or_error}"
        )
    
    return UploadResponse(success=True, url=url_or_error, key=key)


@router.post("/avatar", response_model=UploadResponse)
async def upload_user_avatar(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload user avatar to S3
    
    - Stores in: users/{user_id}/avatar/{filename}
    """
    validate_image(file)
    
    s3_service = get_s3_service()
    
    if not s3_service.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="S3 storage is not configured"
        )
    
    content = await file.read()
    
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    user_id = current_user.get('sub') or current_user.get('id')
    
    success, url_or_error, key = await s3_service.upload_user_avatar(
        content, user_id, file.filename
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {url_or_error}"
        )
    
    return UploadResponse(success=True, url=url_or_error, key=key)


@router.post("/temp", response_model=UploadResponse)
async def upload_temp_image(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload temporary image (before entity creation)
    
    - Useful when creating a new product and need to upload images first
    - Images can be moved to proper folder after product creation
    - Stores in: temp/{filename}
    """
    if current_user.get('role') not in ['admin', 'super_admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    validate_image(file)
    
    s3_service = get_s3_service()
    
    if not s3_service.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="S3 storage is not configured"
        )
    
    content = await file.read()
    
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    success, url_or_error, key = await s3_service.upload_temp_image(
        content, file.filename
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {url_or_error}"
        )
    
    return UploadResponse(success=True, url=url_or_error, key=key)


@router.get("/presigned-url", response_model=PresignedUrlResponse)
async def get_presigned_upload_url(
    type: str = Query(..., description="Type: product, category, avatar, temp"),
    entity_id: Optional[str] = Query(None, description="Product/Category/User ID"),
    filename: str = Query(..., description="Original filename"),
    content_type: str = Query("image/jpeg", description="Content type"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get a pre-signed URL for direct browser upload to S3
    
    This allows the frontend to upload directly to S3 without going through the backend.
    Useful for large files and reduces server load.
    """
    if type in ['product', 'category', 'temp']:
        if current_user.get('role') not in ['admin', 'super_admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
    
    s3_service = get_s3_service()
    
    if not s3_service.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="S3 storage is not configured"
        )
    
    # Generate key based on type
    if type == 'product':
        if not entity_id:
            raise HTTPException(status_code=400, detail="entity_id required for product")
        key = s3_service.get_product_key(entity_id, filename)
    elif type == 'category':
        if not entity_id:
            raise HTTPException(status_code=400, detail="entity_id required for category")
        key = s3_service.get_category_key(entity_id, filename)
    elif type == 'avatar':
        user_id = current_user.get('sub') or current_user.get('id')
        key = s3_service.get_user_avatar_key(user_id, filename)
    elif type == 'temp':
        key = s3_service.get_temp_key(filename)
    else:
        raise HTTPException(status_code=400, detail="Invalid type")
    
    presigned_data = s3_service.generate_presigned_upload_url(key, content_type)
    
    if not presigned_data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate pre-signed URL"
        )
    
    return PresignedUrlResponse(
        success=True,
        upload_url=presigned_data['url'],
        fields=presigned_data['fields'],
        final_url=s3_service.build_url(key),
        key=key
    )


@router.get("/config")
async def get_upload_config():
    """
    Get S3 upload configuration (public endpoint)
    
    Returns the base URL and whether S3 is configured
    """
    s3_service = get_s3_service()
    
    return {
        "s3_configured": s3_service.is_configured,
        "base_url": s3_service.base_url if s3_service.is_configured else None,
        "max_file_size_mb": MAX_FILE_SIZE // (1024 * 1024),
        "allowed_extensions": list(ALLOWED_EXTENSIONS),
    }
