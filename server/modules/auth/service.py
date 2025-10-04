from fastapi import HTTPException, Response, Request
from typing import Optional
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from server.dependencies import require_auth
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_API_KEY") # Use anon key for client-side ops, service_role key for admin ops

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def signup_user(email: str, password: str, username: str):
    try:
        user = supabase.auth.sign_up({
            "email": email, 
            "password": password,
            "options": {
                "data": {
                "full_name": username,
                },
            },
            })
        print(user)
        if user.user:
            return user
        else:
            raise HTTPException(status_code=400, detail=user.error.message if user.error else "Sign up failed.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
def signin_user(email: str, password: str, response: Response):
    try:
        user = supabase.auth.sign_in_with_password({"email": email, "password": password})
        print
        if user.user:
            token = user.session.access_token
            # Lưu vào cookie an toàn (HTTPOnly)
            response.set_cookie(
                key="access_token",
                value=token,
                httponly=True,
                secure=True,      # dev HTTP
                samesite="None",    # hoặc "None" nếu backend ↔ frontend khác origin hoàn toàn
                max_age=60 * 60,
            )

            return user
        else:
            raise HTTPException(status_code=401, detail=user.error.message if user.error else "Invalid credentials.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

def signout_user(response: Response):
    supabase.auth.sign_out()
    response.delete_cookie("access_token", path="/")
    return {"message": "User signed out successfully."}
    
def get_info_user(request: Request):
    user_data = require_auth(request)
    return user_data

    
