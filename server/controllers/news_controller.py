from typing import Iterable, Optional
from datetime import datetime
from fastapi import Request
from server.services.news_service import NewsService

class NewsController:
    @staticmethod
    async def list_news(
        request: Request,
        fields: Optional[Iterable[str]] = None,
        section: Optional[str] = None,
        sections: Optional[Iterable[str]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        q: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        order_by: Optional[str] = "published_time",
        order_dir: Optional[str] = "DESC",
    ):
        return await NewsService.list_news(
            request=request,
            fields=fields,
            section=section,
            sections=sections,
            date_from=date_from,
            date_to=date_to,
            q=q,
            limit=limit,
            offset=offset,
            order_by=order_by,
            order_dir=order_dir,
        )
