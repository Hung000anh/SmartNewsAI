from server.schemas.ai_schema import NewsInputSchema, ClassificationResponseSchema
from server.services.auth_service import verify_access_token_user
import requests
from typing import List

def classify_news_service(news_data: List[NewsInputSchema], access_token: str) -> List[ClassificationResponseSchema]:
    # Verify access token with Supabase
    user_data = verify_access_token_user(access_token)

    if not user_data:
        raise ValueError("Invalid Access Token")

    # Process the news and classify
    results = []
    for news in news_data:
        # Call your AI model here (for example, a REST API or Python model)
        # Placeholder for AI classification
        ai_response = {
            'pos': 0.3,  # Dummy values
            'neg': 0.2,
            'neu': 0.5,
        }
        results.append(ClassificationResponseSchema(**ai_response))
    
    return results
