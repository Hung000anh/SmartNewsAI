from fastapi import APIRouter, Depends
from server.schemas.ai_schema import MultipleNewsInputSchema, ClassificationResponseSchema
from server.controllers.ai_controller import classify_news
from typing import List

router = APIRouter()

@router.post("/classify_news", response_model=List[ClassificationResponseSchema])
async def classify_news_route(news_data: MultipleNewsInputSchema, access_token: str):
    return classify_news(news_data.news, access_token)
