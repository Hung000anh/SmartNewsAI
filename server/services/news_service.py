# server/services/news_service.py
from typing import Iterable, Optional, List
from datetime import datetime
from fastapi import Request
from server.repositories.news_repository import NewsRepository

class NewsService:
    @staticmethod
    async def list_news(
        request: Request,
        fields: Optional[Iterable[str]] = None,
        sections: Optional[List[str]] = None,   # đã normalize ở router
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        q: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        order_by: Optional[str] = "published_time",
        order_dir: Optional[str] = "DESC",
    ):
        # Chuẩn hoá tối thiểu
        q = (q or "").strip() or None
        order_dir = (order_dir or "DESC").upper()

        return await NewsRepository.list(
            request=request,
            fields=fields,
            sections=sections,       # List[str] hoặc None
            date_from=date_from,
            date_to=date_to,
            q=q,
            limit=limit,
            offset=offset,
            order_by=order_by,
            order_dir=order_dir,
        )