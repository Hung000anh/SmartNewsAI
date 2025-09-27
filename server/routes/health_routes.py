from fastapi import APIRouter, Request
from server.services.health_service import HealthService

router = APIRouter()

@router.get("/ping", summary="Test API is alive")
async def ping_fastAPI():
    return await HealthService.ping()

@router.get("/db", summary="Check DB connectivity")
async def health_db(request: Request):  
    return await HealthService.db(request)   