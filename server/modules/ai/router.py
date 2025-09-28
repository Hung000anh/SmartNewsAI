from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from server.modules.ai.schemas import MultipleNewsInput,ClassificationMultipleNewsOutput , ClassificationNewOutput, NewsAnalysisResponse, NewsAnalysisInput, ChatBotResponse
from server.modules.ai.service import classify_news, analyze_news
from server.dependencies import require_auth
from typing import List
from dotenv import load_dotenv
import requests
import os
load_dotenv()
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")


router = APIRouter(prefix="/ai", tags=["AI"])

@router.post(
    "/classify_news",
    response_model=ClassificationMultipleNewsOutput,
    dependencies=[Depends(require_auth)],
)
async def classify_news_route(news_data: MultipleNewsInput):
    return classify_news(news_data.news)

@router.post("/analyze-news", response_model=NewsAnalysisResponse, dependencies=[Depends(require_auth)])
async def analyze_news_route(payload: NewsAnalysisInput):
    return analyze_news(payload)

@router.post("/chatbot", response_model = ChatBotResponse, dependencies=[Depends(require_auth)])
async def chatbot_route( text: str, request: Request):
    access_token = request.cookies.get("access_token")
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"text": text}

    r = requests.post(N8N_WEBHOOK_URL, json=payload, headers=headers, timeout=100)

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