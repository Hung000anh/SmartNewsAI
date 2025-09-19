from fastapi import Request
from server.services.health_service import HealthService

class HealthController:
    @staticmethod
    async def ping():
        return await HealthService.ping()

    @staticmethod
    async def db(request: Request):  
        return await HealthService.db(request)   