from fastapi import Request
from server.repositories.health_repository import HealthRepository

class HealthService:
    @staticmethod
    async def ping():
        return {"pong": True}

    @staticmethod
    async def db(request: Request):
        return await HealthRepository.check_db(request)