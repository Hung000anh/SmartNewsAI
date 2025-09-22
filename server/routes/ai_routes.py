from fastapi import APIRouter, Depends
from server.schemas.ai_schema import MultipleNewsInputSchema, ClassificationResponseSchema, BulkNewsAnalysisResponse, BulkNewsAnalysisInput
from server.controllers.ai_controller import classify_news, analyze_bulk_news_controller
from typing import List

router = APIRouter()

@router.post("/classify_news", response_model=List[ClassificationResponseSchema])
async def classify_news_route(news_data: MultipleNewsInputSchema, access_token: str):
    return classify_news(news_data.news, access_token)

@router.post("/analyze-bulk", response_model=BulkNewsAnalysisResponse)
async def analyze_bulk_route(payload: BulkNewsAnalysisInput, access_token: str):
    """
    Phân tích tin tức CHUNG bằng Gemini (system prompt hard-code trong services).
    Input: danh sách bản tin {title, description, publish_data, pos, neg, neu}.
    Output: một đoạn phân tích chung.
    """
    return analyze_bulk_news_controller(payload, access_token)