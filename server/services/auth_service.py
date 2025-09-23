# app/services/auth_service.py
from fastapi import HTTPException
from server.repositories.auth_repository import sign_up, sign_in, sign_out, get_user, verify_access_token


def signup_user(email: str, password: str):
    try:
        user = sign_up(email,password)
        if user.user:
            return {"message": "User signed up successfully. Please verify your email."}
        else:
            raise HTTPException(status_code=400, detail=user.error.message if user.error else "Sign up failed.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
def signin_user(email: str, password: str):
    try:
        user = sign_in(email,password)
        if user.user:
            return {"message": "User signed in successfully.", "access_token": user.session.access_token}
        else:
            raise HTTPException(status_code=401, detail=user.error.message if user.error else "Invalid credentials.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

def signout_user():
    sign_out()
    return {"message": "User signed out successfully."}
    
def get_current_user():
    try:
        user = get_user()
        return user
    except Exception as e:
        # Handle cases where no user is authenticated or token is invalid
        return {"error": str(e)}

def verify_access_token_user(access_token: str):
    try:
        # Gọi hàm verify_access_token từ repository để giải mã và xác thực token
        user_data = verify_access_token(access_token)
        return user_data
    except HTTPException as e:
        raise e  # Trả lại lỗi HTTPException nếu token không hợp lệ
