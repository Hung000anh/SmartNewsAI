from fastapi import APIRouter, Request
from server.controllers.health_controller import HealthController

router = APIRouter()

@router.get("/ping", summary="Test API is alive")
async def ping():
    return await HealthController.ping()

@router.get("/db", summary="Check DB connectivity")
async def health_db(request: Request):  
    return await HealthController.db(request)  