from server.services.ai_service import classify_news_service
from server.schemas.ai_schema import NewsInputSchema, ClassificationResponseSchema
from typing import List

def classify_news(news_data: List[NewsInputSchema], access_token: str) -> List[ClassificationResponseSchema]:
    # Call the service to classify the news
    return classify_news_service(news_data, access_token)
