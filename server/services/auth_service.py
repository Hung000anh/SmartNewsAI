# app/services/auth_service.py
from fastapi import HTTPException, Response
from typing import Optional
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import jwt
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_API_KEY") # Use anon key for client-side ops, service_role key for admin ops
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def signup_user(email: str, password: str):
    try:
        user = supabase.auth.sign_up({"email": email, "password": password})
        if user.user:
            return {"message": "User signed up successfully. Please verify your email."}
        else:
            raise HTTPException(status_code=400, detail=user.error.message if user.error else "Sign up failed.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
def signin_user(email: str, password: str, response: Response):
    try:
        user = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if user.user:
            token = user.session.access_token
            # Lưu vào cookie an toàn (HTTPOnly)
            response.set_cookie(
                key="access_token",
                value=token,
                httponly=True,
                secure=True,
                samesite="Strict",
                max_age=60 * 60
            )
            return {"message": "User signed in successfully.", "access_token": user.session.access_token}
        else:
            raise HTTPException(status_code=401, detail=user.error.message if user.error else "Invalid credentials.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

def signout_user():
    supabase.auth.sign_out()
    return {"message": "User signed out successfully."}
    
def get_info_user():
    try:
        user = supabase.auth.get_user()
        return user
    except Exception as e:
        # Handle cases where no user is authenticated or token is invalid
        return {"error": str(e)}

def verify_access_token_user(access_token: str):
    try:
        # Decode the token using the Supabase JWT secret
        payload = jwt.decode(access_token, SUPABASE_JWT_SECRET, algorithms=["HS256"], audience="authenticated")
        
        # If the token is valid, return the payload (it contains the user info)
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )
