from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import JSONResponse
from server.schemas.ai_schema import MultipleNewsInputSchema, ClassificationResponseSchema, BulkNewsAnalysisResponse, BulkNewsAnalysisInput
from server.controllers.ai_controller import classify_news, analyze_bulk_news_controller
from typing import List
from dotenv import load_dotenv
import requests
import os
load_dotenv()
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")


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

@router.post("/chatbot")
async def chatbot_route(
    text: str,
    access_token: str = Header(..., description="Token xác thực")
):
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"text": text}

    r = requests.post(N8N_WEBHOOK_URL, json=payload, headers=headers, timeout=15)

    # Chuyển tiếp status + body từ n8n (tùy bạn muốn giữ status gốc hay ép 200)
    content_type = r.headers.get("content-type", "")
    try:
        body = r.json() if "application/json" in content_type else r.text
    except ValueError:
        body = r.text

    # Nếu muốn fail khi n8n báo lỗi
    if r.status_code >= 400:
        raise HTTPException(status_code=502, detail={"n8n_status": r.status_code, "n8n_body": body})

    return JSONResponse(
        status_code=200,
        content={
            "ok": True,
            "n8n_status": r.status_code,
            "n8n_body": body
        }
    )