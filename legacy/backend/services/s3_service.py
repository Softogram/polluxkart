# AWS S3 Image Storage Service
# Handles all image uploads for products, categories, and user avatars

import os
import boto3
import uuid
from datetime import datetime
from typing import Optional, Tuple
from botocore.exceptions import ClientError
import mimetypes

class S3Service:
    """
    S3 Image Storage Service for PolluxKart
    
    Folder Structure:
    - products/{product_id}/{filename}
    - categories/{category_id}/{filename}
    - users/{user_id}/avatar/{filename}
    - temp/{filename}  (for temporary uploads before entity creation)
    """
    
    def __init__(self):
        self.bucket_name = os.environ.get('S3_BUCKET_NAME', 'polluxkart-media-ap-south-1')
        self.region = os.environ.get('S3_REGION', 'ap-south-1')
        self.base_url = os.environ.get('S3_BASE_URL', f'https://{self.bucket_name}.s3.{self.region}.amazonaws.com')
        
        # Initialize S3 client
        # Uses IAM role credentials in production (EC2/ECS) or environment variables locally
        self.s3_client = boto3.client(
            's3',
            region_name=self.region,
            # AWS credentials are loaded from:
            # 1. Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
            # 2. IAM role (when running on EC2/ECS)
            # 3. AWS credentials file (~/.aws/credentials)
        )
        
        self._is_configured = self._check_configuration()
    
    def _check_configuration(self) -> bool:
        """Check if S3 is properly configured"""
        try:
            # Try to check if bucket exists
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            print(f"[S3] Connected to bucket: {self.bucket_name}")
            return True
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == '403':
                print(f"[S3] Access denied to bucket: {self.bucket_name}")
            elif error_code == '404':
                print(f"[S3] Bucket not found: {self.bucket_name}")
            else:
                print(f"[S3] Error connecting to bucket: {e}")
            return False
        except Exception as e:
            print(f"[S3] Configuration error: {e}")
            return False
    
    @property
    def is_configured(self) -> bool:
        return self._is_configured
    
    def _generate_unique_filename(self, original_filename: str) -> str:
        """Generate a unique filename while preserving extension"""
        ext = os.path.splitext(original_filename)[1].lower() or '.jpg'
        unique_id = uuid.uuid4().hex[:12]
        timestamp = datetime.utcnow().strftime('%Y%m%d')
        return f"{timestamp}_{unique_id}{ext}"
    
    def _get_content_type(self, filename: str) -> str:
        """Get content type from filename"""
        content_type, _ = mimetypes.guess_type(filename)
        return content_type or 'application/octet-stream'
    
    def get_product_key(self, product_id: str, filename: str) -> str:
        """Generate S3 key for product image"""
        safe_filename = self._generate_unique_filename(filename)
        return f"products/{product_id}/{safe_filename}"
    
    def get_category_key(self, category_id: str, filename: str) -> str:
        """Generate S3 key for category image"""
        safe_filename = self._generate_unique_filename(filename)
        return f"categories/{category_id}/{safe_filename}"
    
    def get_user_avatar_key(self, user_id: str, filename: str) -> str:
        """Generate S3 key for user avatar"""
        safe_filename = self._generate_unique_filename(filename)
        return f"users/{user_id}/avatar/{safe_filename}"
    
    def get_temp_key(self, filename: str) -> str:
        """Generate S3 key for temporary upload"""
        safe_filename = self._generate_unique_filename(filename)
        return f"temp/{safe_filename}"
    
    def build_url(self, key: str) -> str:
        """Build full URL from S3 key"""
        return f"{self.base_url}/{key}"
    
    async def upload_file(
        self,
        file_content: bytes,
        key: str,
        content_type: Optional[str] = None,
        filename: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Upload file to S3
        
        Args:
            file_content: File bytes
            key: S3 key (path)
            content_type: MIME type
            filename: Original filename (used to detect content type if not provided)
        
        Returns:
            Tuple of (success, url or error message, key if success)
        """
        if not self._is_configured:
            return False, "S3 is not configured", None
        
        try:
            # Detect content type if not provided
            if not content_type and filename:
                content_type = self._get_content_type(filename)
            content_type = content_type or 'application/octet-stream'
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=file_content,
                ContentType=content_type,
                # Cache for 1 year (images rarely change)
                CacheControl='max-age=31536000',
            )
            
            url = self.build_url(key)
            print(f"[S3] Uploaded: {key}")
            return True, url, key
            
        except ClientError as e:
            error_msg = str(e)
            print(f"[S3] Upload error: {error_msg}")
            return False, error_msg, None
        except Exception as e:
            error_msg = str(e)
            print(f"[S3] Unexpected error: {error_msg}")
            return False, error_msg, None
    
    async def upload_product_image(
        self,
        file_content: bytes,
        product_id: str,
        filename: str
    ) -> Tuple[bool, str, Optional[str]]:
        """Upload product image to S3"""
        key = self.get_product_key(product_id, filename)
        return await self.upload_file(file_content, key, filename=filename)
    
    async def upload_category_image(
        self,
        file_content: bytes,
        category_id: str,
        filename: str
    ) -> Tuple[bool, str, Optional[str]]:
        """Upload category image to S3"""
        key = self.get_category_key(category_id, filename)
        return await self.upload_file(file_content, key, filename=filename)
    
    async def upload_user_avatar(
        self,
        file_content: bytes,
        user_id: str,
        filename: str
    ) -> Tuple[bool, str, Optional[str]]:
        """Upload user avatar to S3"""
        key = self.get_user_avatar_key(user_id, filename)
        return await self.upload_file(file_content, key, filename=filename)
    
    async def upload_temp_image(
        self,
        file_content: bytes,
        filename: str
    ) -> Tuple[bool, str, Optional[str]]:
        """Upload temporary image (before entity is created)"""
        key = self.get_temp_key(filename)
        return await self.upload_file(file_content, key, filename=filename)
    
    async def delete_file(self, key: str) -> bool:
        """Delete file from S3"""
        if not self._is_configured:
            return False
        
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            print(f"[S3] Deleted: {key}")
            return True
        except Exception as e:
            print(f"[S3] Delete error: {e}")
            return False
    
    async def delete_by_url(self, url: str) -> bool:
        """Delete file by its full URL"""
        if not url.startswith(self.base_url):
            return False
        
        key = url.replace(f"{self.base_url}/", "")
        return await self.delete_file(key)
    
    async def move_temp_to_product(
        self,
        temp_url: str,
        product_id: str
    ) -> Tuple[bool, str]:
        """Move image from temp to product folder"""
        if not self._is_configured:
            return False, temp_url
        
        try:
            # Extract temp key from URL
            if not temp_url.startswith(self.base_url):
                return True, temp_url  # Not an S3 URL, return as-is
            
            old_key = temp_url.replace(f"{self.base_url}/", "")
            
            if not old_key.startswith("temp/"):
                return True, temp_url  # Not a temp file, return as-is
            
            # Generate new key in product folder
            filename = old_key.split("/")[-1]
            new_key = f"products/{product_id}/{filename}"
            
            # Copy to new location
            self.s3_client.copy_object(
                Bucket=self.bucket_name,
                CopySource={'Bucket': self.bucket_name, 'Key': old_key},
                Key=new_key,
                ACL='public-read',
                CacheControl='max-age=31536000',
            )
            
            # Delete old file
            await self.delete_file(old_key)
            
            new_url = self.build_url(new_key)
            print(f"[S3] Moved {old_key} -> {new_key}")
            return True, new_url
            
        except Exception as e:
            print(f"[S3] Move error: {e}")
            return False, temp_url
    
    def generate_presigned_url(
        self,
        key: str,
        expiration: int = 3600
    ) -> Optional[str]:
        """
        Generate a pre-signed URL for temporary access
        
        Args:
            key: S3 key
            expiration: URL expiration time in seconds (default 1 hour)
        
        Returns:
            Pre-signed URL or None if error
        """
        if not self._is_configured:
            return None
        
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': key
                },
                ExpiresIn=expiration
            )
            return url
        except Exception as e:
            print(f"[S3] Pre-signed URL error: {e}")
            return None
    
    def generate_presigned_upload_url(
        self,
        key: str,
        content_type: str = 'image/jpeg',
        expiration: int = 3600
    ) -> Optional[dict]:
        """
        Generate a pre-signed URL for direct upload from frontend
        
        Returns dict with 'url' and 'fields' for POST upload
        """
        if not self._is_configured:
            return None
        
        try:
            response = self.s3_client.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=key,
                Fields={
                    'Content-Type': content_type,
                    'acl': 'public-read',
                },
                Conditions=[
                    {'Content-Type': content_type},
                    {'acl': 'public-read'},
                    ['content-length-range', 1, 10 * 1024 * 1024],  # 1 byte to 10MB
                ],
                ExpiresIn=expiration
            )
            return response
        except Exception as e:
            print(f"[S3] Pre-signed upload URL error: {e}")
            return None


# Singleton instance
_s3_service: Optional[S3Service] = None

def get_s3_service() -> S3Service:
    """Get or create S3 service singleton"""
    global _s3_service
    if _s3_service is None:
        _s3_service = S3Service()
    return _s3_service
