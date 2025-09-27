from fastapi import APIRouter
from fastapi.openapi.docs import get_swagger_ui_html

router = APIRouter(prefix="/docs", tags=["Docs"])

@router.get("", include_in_schema=False)
def custom_docs():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="API v1 Docs",
        swagger_favicon_url="/static/image.png",
        swagger_ui_parameters={
            "deepLinking": True,
            "displayRequestDuration": True,
            "docExpansion": "none",
            "tryItOutEnabled": True,
            "persistAuthorization": True,
            "defaultModelsExpandDepth": -1,
            "tagsSorter": "none"
        },
    )