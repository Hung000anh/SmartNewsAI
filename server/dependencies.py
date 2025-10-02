import os
import jwt
from fastapi import HTTPException, status, Request

SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_KEY", "")
SUPABASE_API_SECRET = os.getenv("SUPABASE_API_SECRET", "")
AUDIENCE = "authenticated"

def require_auth(request: Request) -> dict:
    # 1) Nếu có header X-API-Key đúng => cho qua
    api_key = request.headers.get("X-API-Key")
    print(api_key)
    if api_key and SUPABASE_API_SECRET and api_key == SUPABASE_API_SECRET:
        # payload giả định cho service call
        return {"sub": "api-service", "role": "api_bot"}

    # 2) Nếu có cookie access_token thì check JWT
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience=AUDIENCE
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")