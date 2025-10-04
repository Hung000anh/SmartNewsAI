from typing import Optional, List, Dict, Any
from pydantic import BaseModel, RootModel
from datetime import datetime


# Định nghĩa schema cho đăng nhập người dùng
class UserSignUp(BaseModel):
    email: str
    password: str
    
class UserSignIn(BaseModel):
    email: str
    password: str
