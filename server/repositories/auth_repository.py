#repository
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import jwt
from fastapi import HTTPException
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_API_KEY") # Use anon key for client-side ops, service_role key for admin ops
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_KEY")


supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def sign_up(email: str, password: str) :
    return supabase.auth.sign_up({"email": email, "password": password})

def sign_in(email: str, password: str) :
    return supabase.auth.sign_in_with_password({"email": email, "password": password})

def sign_out() :
    return supabase.auth.sign_out()

def get_user() :
    return supabase.auth.get_user()

def verify_access_token(access_token: str):
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