from fastapi import APIRouter, Depends, Response, Request
from server.modules.auth.service import signup_user, signin_user, signout_user
from server.modules.auth.schemas import UserSignUp, UserSignIn
from server.modules.auth.service import get_info_user
from server.dependencies import require_auth
router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post(
        "/sign_up",
        summary="Sign up a new user",
)
async def sign_up(user: UserSignUp):
    return signup_user(user.email, user.password)

@router.post(
    "/sign_in",
    summary="Sign in an existing user",
)
async def sign_in(user: UserSignIn, response: Response):
    return signin_user(user.email, user.password, response)

@router.post(
    "/sign_out",
    summary="Sign out the current user",
)
async def sign_out(response: Response):
    return signout_user(response)

@router.get(
    "/current_user",
    summary="Get info current user",
    dependencies=[Depends(require_auth)]
)
async def get_current_user(request: Request):
    return get_info_user(request)