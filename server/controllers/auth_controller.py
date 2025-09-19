# app/controllers/auth_controller.py
from server.services.auth_service import signin_user, signout_user, signup_user, get_current_user
from server.schemas.auth_schema import UserCreate, UserLogin
from fastapi import HTTPException

def sign_up_controller(user: UserCreate):
    try:
        return signup_user(user.email, user.password)
    except HTTPException as e:
        raise e

def sign_in_controller(user: UserLogin):
    try:
        return signin_user(user.email, user.password)
    except HTTPException as e:
        raise e

def sign_out_controller():
    return signout_user()

def get_current_user_controller():
    return get_current_user()
