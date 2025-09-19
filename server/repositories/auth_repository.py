import os
from dotenv import load_dotenv
from supabase import create_client, Client


load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_API_KEY") # Use anon key for client-side ops, service_role key for admin ops

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def sign_up(email: str, password: str) :
    return supabase.auth.sign_up({"email": email, "password": password})

def sign_in(email: str, password: str) :
    return supabase.auth.sign_in_with_password({"email": email, "password": password})

def sign_out() :
    return supabase.auth.sign_out()

def get_user() :
    return supabase.auth.get_user()