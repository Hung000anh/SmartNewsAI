from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from server.modules.ai.schemas import ChatBotInput, MultipleNewsInput,ClassificationMultipleNewsOutput, NewsInput, NewsFetchOutput , NewsAnalysisResponse, NewsAnalysisInput, ChatBotResponse
from server.modules.ai.service import classify_news, analyze_news, get_chat_history
from server.modules.news.service import list_news
from server.dependencies import require_auth
from typing import List
from dotenv import load_dotenv
import requests
import httpx

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from datetime import datetime

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

@router.get("/chat-history/{session_id}", dependencies=[Depends(require_auth)])
async def get_user_chat_history(
    request: Request,
    session_id: str,
    limit: int = 100,
    offset: int = 0,
):
    return await get_chat_history(request, session_id, limit, offset)


@router.post("/chatbot", response_model=ChatBotResponse, dependencies=[Depends(require_auth)])
async def chatbot_route(payload: ChatBotInput, request: Request):
    access_token = request.cookies.get("access_token")
    headers = {}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                N8N_WEBHOOK_URL,
                json=payload.model_dump(),
                headers=headers,
                timeout=httpx.Timeout(60.0, connect=5.0)
            )
    except httpx.ConnectTimeout:
        raise HTTPException(status_code=504, detail="n8n connect timeout")
    except httpx.ReadTimeout:
        raise HTTPException(status_code=504, detail="n8n read timeout")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"n8n request error: {e}")

    ct = r.headers.get("content-type", "")
    body = r.text
    if "application/json" in ct:
        try:
            body = r.json()
        except ValueError:
            pass

    if r.status_code >= 400:
        raise HTTPException(status_code=502, detail={"n8n_status": r.status_code, "n8n_body": body})

    return JSONResponse(status_code=200, content={"ok": True, "n8n_status": r.status_code, "n8n_body": body})

@router.get("/fetch_and_classify_news", response_model=NewsFetchOutput)
async def fetch_and_classify_news(
    request: Request,
    q: Optional[str] = Query(None, description="Keyword tìm kiếm tin tức (tùy chọn)"),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    order_by: str = "published_time",
    order_dir: str = "DESC",
):
    """
    ✅ Lấy tin tức trực tiếp từ DB (qua list_news)
    ✅ Phân loại cảm xúc bằng mô hình glove+textcnn+lstm
    """
    try:
        # 1️⃣ Gọi trực tiếp hàm list_news() để lấy dữ liệu từ DB
        result = await list_news(
            request=request,
            fields=["title", "description", "published_time"],
            sections=None,
            date_from=date_from,
            date_to=date_to,
            q=q,
            limit=limit,
            offset=offset,
            order_by=order_by,
            order_dir=order_dir,
        )

        items = result.get("items", [])
        if not items:
            raise HTTPException(status_code=404, detail="Không tìm thấy tin tức phù hợp.")

        # 2️⃣ Chuyển đổi sang dạng NewsInput
        news_list = [
            NewsInput(
                title=item.get("title") or "",
                description=item.get("description") or "",
                publish_date=item.get("published_time"),
            )
            for item in items
        ]

        # 3️⃣ Phân loại cảm xúc
        classified = classify_news(news_list)

        # 4️⃣ Gộp thông tin phân trang và meta
        return {
            "news": classified.news,
            "page": result.get("page"),
            "meta": result.get("meta"),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý: {e}")