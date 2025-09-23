# app/schemas/auth_schema.py
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, RootModel
from datetime import datetime


# Định nghĩa schema cho đăng ký người dùng
class UserCreate(BaseModel):
    email: str
    password: str

# Định nghĩa schema cho đăng nhập người dùng
class UserLogin(BaseModel):
    email: str
    password: str
    
class AuthResponseSignUp(BaseModel):
    message: Optional[str]       # Thông báo

class AuthResponseSignIn(BaseModel):
    message: Optional[str] 
    access_token: Optional[str] 

class AuthResponseSignOut(BaseModel):
    message: Optional[str] 
