# app/routes/auth_routes.py
from fastapi import APIRouter, Depends
from server.controllers.auth_controller import sign_up_controller, sign_in_controller, sign_out_controller, get_current_user_controller
from server.schemas.auth_schema import UserCreate, UserLogin
from server.schemas.auth_schema import AuthResponseSignUp, AuthResponseSignIn, AuthResponseSignOut
router = APIRouter()

@router.post(
        "/sign_up",
        summary="Sign up a new user",
        response_model=AuthResponseSignUp
)
async def sign_up(user: UserCreate):
    return sign_up_controller(user)

@router.post(
    "/sign_in",
    summary="Sign in an existing user",
    response_model=AuthResponseSignIn
)
async def sign_in(user: UserLogin):
    return sign_in_controller(user)

@router.post(
    "/sign_out",
    summary="Sign out the current user",
    response_model=AuthResponseSignOut
)
async def sign_out():
    return sign_out_controller()

@router.get(
    "/current_user",
    summary="Get info current user",
)
async def get_current_user():
    return get_current_user_controller()