from typing import Optional, List, Iterable
from datetime import datetime
from fastapi import APIRouter, Request, Query
from server.services.news_service import NewsService
from server.schemas.news_schema import NewsListResponse

router = APIRouter()

def _parse_fields_csv(raw: Optional[str]) -> Optional[List[str]]:
    if not raw:
        return None
    seen = set()
    out: List[str] = []
    for s in raw.split(","):
        v = s.strip()
        if v and v not in seen:
            seen.add(v)
            out.append(v)
    return out or None

def _parse_sections_csv(raw: Optional[str]) -> Optional[List[str]]:
    """CSV -> List[str], giữ nguyên thứ tự, bỏ rỗng."""
    if not raw:
        return None
    seen = set()
    out: List[str] = []
    for s in raw.split(","):
        v = s.strip()
        if v and v not in seen:
            seen.add(v)
            out.append(v)
    return out or None

def _normalize_sections(sections: Optional[Iterable[str]]) -> Optional[List[str]]:
    """lowercase + trim + dedup (giữ thứ tự)."""
    if not sections:
        return None
    seen = set()
    out: List[str] = []
    for s in sections:
        if not s:
            continue
        k = s.strip().lower()
        if k and k not in seen:
            seen.add(k)
            out.append(k)
    return out or None

@router.get(
    "/",
    summary="Query news with flexible filters/fields",
    response_model=NewsListResponse,
)
async def get_news(
    request: Request,
    # chọn cột trả về: ?fields=id,title,section
    fields: Optional[str] = Query(
        None,
        description="Comma-separated fields, e.g. id,title,section",
        examples={"only_basic": {"value": "id,title,published_time"}},
    ),
    # nhiều section qua CSV: ?sections=technology,science
    sections: Optional[str] = Query(
        None,
        description="CSV of sections (case-insensitive), e.g. technology,science",
        examples={"multi": {"value": "technology,science"}},
    ),
    # thời gian: ISO 8601, ví dụ 2025-09-01T00:00:00Z
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
    order_dir: Optional[str] = Query(
        "DESC", description="Sort direction: ASC | DESC"
    ),
):
    field_list = _parse_fields_csv(fields)

    # CSV -> list -> normalize (lowercase, dedup)
    section_list_raw = _parse_sections_csv(sections)
    section_list_norm = _normalize_sections(section_list_raw)  # Optional[List[str]]

    order_dir_norm = (order_dir or "DESC").upper()
    if order_dir_norm not in ("ASC", "DESC"):
        order_dir_norm = "DESC"

    return await NewsService.list_news(
        request=request,
        fields=field_list,
        sections=section_list_norm,   # <-- truyền List[str] đã normalize
        date_from=date_from,
        date_to=date_to,
        q=q.strip() if q else None,
        limit=limit,
        offset=offset,
        order_by=order_by,
        order_dir=order_dir_norm,
    )
