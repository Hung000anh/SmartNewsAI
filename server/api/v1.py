from fastapi import APIRouter
from server.routes import health_routes, docs_routes, auth_routes

api_v1 = APIRouter()


# Health routes
api_v1.include_router(health_routes.router, prefix="/health", tags=["Health"])

# Auth routes
api_v1.include_router(auth_routes.router, prefix="/auth", tags=["Auth"])


# Docs routes
api_v1.include_router(docs_routes.router, prefix="/docs", tags=["Docs"])