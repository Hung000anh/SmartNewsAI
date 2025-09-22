from server.services.ai_service import classify_news_service, analyze_bulk_news
from server.schemas.ai_schema import NewsInputSchema, ClassificationResponseSchema, BulkNewsAnalysisInput, BulkNewsAnalysisResponse
from typing import List

def classify_news(news_data: List[NewsInputSchema], access_token: str) -> List[ClassificationResponseSchema]:
    # Call the service to classify the news
    return classify_news_service(news_data, access_token)


def analyze_bulk_news_controller(payload: BulkNewsAnalysisInput, access_token: str) -> BulkNewsAnalysisResponse:
    return analyze_bulk_news(payload, access_token)