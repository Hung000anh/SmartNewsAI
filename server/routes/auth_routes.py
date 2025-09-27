# app/routes/auth_routes.py
from fastapi import APIRouter, Depends, Response, Request
from server.services.auth_service import signup_user, signin_user, signout_user, get_info_user
from server.schemas.auth_schema import UserCreate, UserLogin
from server.schemas.auth_schema import AuthResponseSignUp, AuthResponseSignIn, AuthResponseSignOut
router = APIRouter()

@router.post(
        "/sign_up",
        summary="Sign up a new user",
        response_model=AuthResponseSignUp
)
async def sign_up(user: UserCreate):
    return signup_user(user)

@router.post(
    "/sign_in",
    summary="Sign in an existing user",
    response_model=AuthResponseSignIn
)
async def sign_in(user: UserLogin, response: Response):
    return signin_user(user.email, user.password, response)

@router.post(
    "/sign_out",
    summary="Sign out the current user",
    response_model=AuthResponseSignOut
)
async def sign_out():
    return signout_user()

@router.get(
    "/current_user",
    summary="Get info current user",
)
async def get_current_user(request: Request):
    return get_info_user(request)