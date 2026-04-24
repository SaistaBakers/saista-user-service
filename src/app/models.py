from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = ""

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str
    full_name: str
    email: str
    role: str
    message: str

class ProductResponse(BaseModel):
    id: int
    name: str
    description: str
    price: float
    category: str

class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    category: str
    available: Optional[bool] = True

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    available: Optional[bool] = None

class AdminEmailRequest(BaseModel):
    customer_id: int
    subject: str
    message: str

class OrderStatusUpdate(BaseModel):
    order_id: int
    status: str
