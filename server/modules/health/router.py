from fastapi import APIRouter, Request
from server.modules.health.service import ping, db

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("/ping", summary="Test API is alive")
async def ping_fastAPI():
    return await ping()

@router.get("/database", summary="Check DB connectivity")
async def health_db(request: Request):  
    return await db(request)   