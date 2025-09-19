from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Request, Query
from server.controllers.news_controller import NewsController
from server.schemas.news_schema import NewsListResponse, NewsItemOut

router = APIRouter()

@router.get("/", 
            summary="Query news with flexible filters/fields"
            , response_model=NewsListResponse
            )
async def get_news(
    request: Request,
    # chọn cột trả về: ?fields=id,title,section
    fields: Optional[str] =  Query(
        None,
        description="Comma-separated fields, e.g. id,title,section",
        examples={"only_basic": {"value": "id,title,published_time"}},
    ),
    # lọc 1 section: ?section=world
    section: Optional[str] = Query(
        None, description="Filter by a single section (case-insensitive)"
    ),
    # hoặc nhiều section: ?sections=world&sections=business
    sections: Optional[List[str]] = Query(
        None, description="Filter by multiple sections (case-insensitive)"
    ),
    # thời gian: ISO 8601, ví dụ 2025-09-01T00:00:00Z (FastAPI sẽ parse)
    date_from: Optional[datetime] = Query(
        None, description="Published after (ISO 8601), e.g. 2025-09-01T00:00:00Z"
    ),
    date_to: Optional[datetime] = Query(
        None, description="Published before (ISO 8601)"
    ),
    # tìm kiếm đơn giản: ?q=apple
    q: Optional[str] = Query(
        None, description="Search keyword (title/description, ILIKE)"
    ),
    # phân trang
    limit: int = Query(20, ge=1, le=1000, description="Page size"),
    offset: int = Query(0, ge=0, description="Offset"),
    # sắp xếp (whitelist trong repo)
    order_by: Optional[str] = Query(
        "published_time", description="Order by: published_time | title | section | id"
    ),
    order_dir: Optional[str] = Query("DESC", description="Sort direction"),
):
    # parse fields CSV thành list
    field_list = [f.strip() for f in fields.split(",")] if fields else None
    return await NewsController.list_news(
        request=request,
        fields=field_list,
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