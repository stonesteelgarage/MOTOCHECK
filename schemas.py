from pydantic import BaseModel, EmailStr
from typing import Optional

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class PayPalCreateOrderRequest(BaseModel):
    package_id: str

class PayPalCaptureRequest(BaseModel):
    paypal_order_id: str

class CreateJobRequest(BaseModel):
    tool_name: str

class VerifyJobRequest(BaseModel):
    job_id: str
    token: str

class CompleteJobRequest(BaseModel):
    job_id: str
    token: str
    pdf_name: Optional[str] = None

class FailJobRequest(BaseModel):
    job_id: str
    token: str
    error_message: Optional[str] = None
