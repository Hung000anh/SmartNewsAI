from fastapi import APIRouter
from server.routes import health_routes, docs_routes

api_v1 = APIRouter()


# Health routes
api_v1.include_router(health_routes.router, prefix="/health", tags=["Health"])

# Docs routes
api_v1.include_router(docs_routes.router, prefix="/docs", tags=["Docs"])