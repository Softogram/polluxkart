# OTP Routes - Simple MongoDB-based OTP verification
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from config.database import get_db
from datetime import datetime, timezone, timedelta
import random
import string

router = APIRouter(prefix="/otp", tags=["OTP"])

# OTP expires in 5 minutes
OTP_EXPIRY_MINUTES = 5

class SendOTPRequest(BaseModel):
    phone: str

class VerifyOTPRequest(BaseModel):
    phone: str
    code: str

class OTPResponse(BaseModel):
    success: bool
    message: str

def generate_otp() -> str:
    """Generate a 6-digit OTP code"""
    return ''.join(random.choices(string.digits, k=6))

@router.post("/send", response_model=OTPResponse)
async def send_otp(request: SendOTPRequest):
    """
    Generate and store OTP for a phone number.
    In production, this would also send SMS via Twilio/AWS SNS.
    For now, it just stores in DB and returns success.
    """
    db = get_db()
    phone = request.phone.strip()
    
    if not phone or len(phone) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid phone number"
        )
    
    # Generate OTP
    otp_code = generate_otp()
    expiry_time = datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRY_MINUTES)
    
    # Remove any existing OTP for this phone
    await db.otps.delete_many({"phone": phone})
    
    # Store new OTP
    await db.otps.insert_one({
        "phone": phone,
        "code": otp_code,
        "created_at": datetime.now(timezone.utc),
        "expires_at": expiry_time,
    })
    
    # Create TTL index if it doesn't exist (auto-delete expired OTPs)
    await db.otps.create_index("expires_at", expireAfterSeconds=0)
    
    # In production, send SMS here using Twilio/AWS SNS
    # For now, we'll log it (visible in backend logs)
    print(f"[OTP] Generated OTP {otp_code} for phone {phone} (expires at {expiry_time})")
    
    return OTPResponse(
        success=True,
        message=f"OTP sent to {phone}. Valid for {OTP_EXPIRY_MINUTES} minutes."
    )

@router.post("/verify", response_model=OTPResponse)
async def verify_otp(request: VerifyOTPRequest):
    """
    Verify OTP code for a phone number.
    """
    db = get_db()
    phone = request.phone.strip()
    code = request.code.strip()
    
    if not phone or not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number and OTP code are required"
        )
    
    if len(code) != 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP must be 6 digits"
        )
    
    # Find OTP record
    otp_record = await db.otps.find_one({
        "phone": phone,
        "code": code,
        "expires_at": {"$gt": datetime.now(timezone.utc)}
    })
    
    if not otp_record:
        # Check if OTP exists but expired or wrong code
        existing = await db.otps.find_one({"phone": phone})
        if existing:
            expires_at = existing.get("expires_at")
            # Handle timezone-aware comparison
            if expires_at:
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
                if expires_at < datetime.now(timezone.utc):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="OTP has expired. Please request a new one."
                    )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OTP code"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No OTP found for this phone number. Please request OTP first."
            )
    
    # OTP is valid - delete it (one-time use)
    await db.otps.delete_one({"_id": otp_record["_id"]})
    
    print(f"[OTP] Successfully verified OTP for phone {phone}")
    
    return OTPResponse(
        success=True,
        message="Phone number verified successfully"
    )

@router.get("/debug/{phone}")
async def debug_otp(phone: str):
    """
    Debug endpoint to see current OTP (REMOVE IN PRODUCTION).
    This helps during development to see what OTP was generated.
    """
    db = get_db()
    
    otp_record = await db.otps.find_one(
        {"phone": phone},
        {"_id": 0, "phone": 1, "code": 1, "expires_at": 1}
    )
    
    if not otp_record:
        return {"message": "No OTP found for this phone number"}
    
    # Convert datetime to string for JSON serialization
    otp_record["expires_at"] = otp_record["expires_at"].isoformat()
    
    return {
        "otp": otp_record,
        "note": "This endpoint should be removed in production!"
    }
