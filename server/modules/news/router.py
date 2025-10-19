from typing import Optional, List, Iterable
from datetime import datetime
from fastapi import APIRouter, Request, Query, HTTPException, status
from server.modules.news.service import list_news, get_news_by_id
from server.modules.news.schemas import NewsListResponse, SectionItem, ChildSection, NewsDetailItemOut
from urllib.parse import unquote
router = APIRouter(prefix="/news", tags=["News"])

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

# def _parse_sections_csv(raw: Optional[str]) -> Optional[List[str]]:
#     """CSV -> List[str], giữ nguyên thứ tự, bỏ rỗng."""
#     if not raw:
#         return None
#     seen = set()
#     out: List[str] = []
#     for s in raw.split(","):
#         v = s.strip()
#         if v and v not in seen:
#             seen.add(v)
#             out.append(v)
#     return out or None

def _normalize_sections(sections):
    """
    Chuẩn hoá section:
    - Cho phép đầu vào là str hoặc list[str]
    - Giải mã URL (%2F → /)
    - Thay '/' bằng ' / ' để dễ đọc
    """
    if not sections:
        return None

    # Nếu đầu vào là chuỗi đơn, chuyển thành list có 1 phần tử
    if isinstance(sections, str):
        sections = [sections]

    normalized = []
    for s in sections:
        if not s:
            continue
        decoded = unquote(s.strip())  # decode %2F, %20, ...
        formatted = decoded.strip("/").replace("/", " / ")
        normalized.append(formatted)
    return normalized or None


@router.get(
    "/",
    summary="Query news with flexible filters/fields",
    response_model=NewsListResponse,
)
async def get_news(
    request: Request,
    fields: Optional[str] = Query(
        None,
        description="Comma-separated fields, e.g. id,title,section",
        examples={"only_basic": {"value": "id,title,published_time"}},
    ),
    sections: Optional[str] = Query(
        None,
        description="CSV of sections (case-insensitive), e.g. technology,science",
        examples={"multi": {"value": "technology,science"}},
    ),
    date_from: Optional[datetime] = Query(
        None, description="Published after (ISO 8601), e.g. 2025-09-01T00:00:00Z"
    ),
    date_to: Optional[datetime] = Query(
        None, description="Published before (ISO 8601)"
    ),
    q: Optional[str] = Query(
        None, description="Search keyword (title/description, ILIKE)"
    ),
    limit: int = Query(20, ge=1, le=1000, description="Page size"),
    offset: int = Query(0, ge=0, description="Offset"),
    order_by: Optional[str] = Query(
        "published_time",
        description="Order by: published_time | title | section | id | view_count",
    ),
    order_dir: Optional[str] = Query(
        "DESC", description="Sort direction: ASC | DESC"
    ),
):
    # Parse and normalize query params
    field_list = _parse_fields_csv(fields)
    section_list_norm = _normalize_sections(sections)
    # print(section_list_norm)
    order_dir_norm = (order_dir or "DESC").upper()
    if order_dir_norm not in ("ASC", "DESC"):
        order_dir_norm = "DESC"

    # --- Lấy dữ liệu từ service ---
    data = await list_news(
        request=request,
        fields=field_list,
        sections=section_list_norm,
        date_from=date_from,
        date_to=date_to,
        q=q.strip() if q else None,
        limit=limit,
        offset=offset,
        order_by=order_by,
        order_dir=order_dir_norm,
    )

    # --- Tự động sinh slug từ URL ---
    items = data.get("items", [])
    for item in items:
        url = item.get("url")
        if url:
            parts = url.rstrip("/").split("/")
            item["slug"] = parts[-1] if parts else None
        else:
            item["slug"] = None

    return data

from typing import List, Dict, Any, Union
import re
def slugify(label: str) -> str:
    s = (label or "").strip().lower()
    s = s.replace("&", "and")
    s = re.sub(r"[^a-z0-9\s\-_/]", "", s)
    s = re.sub(r"[\s/]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s

def build_sections_nav(items: List[Union[Dict[str, Any], str]]) -> List[SectionItem]:
    """
    Input: list news (dict{'section': 'A / B'}) hoặc list[str] section.
    Output: List[SectionItem] (bỏ parent không có child; bỏ child thiếu label/href).
    """
    parents: Dict[str, SectionItem] = {}

    for row in items:
        sec = ""
        if isinstance(row, dict):
            sec = (row.get("section") or "").strip()
        elif isinstance(row, str):
            sec = row.strip()
        if not sec:
            continue

        parts = [p.strip() for p in sec.split("/") if p.strip()]
        if not parts:
            continue

        parent_label = parts[0]
        parent_slug = slugify(parent_label)
        if not parent_label or not parent_slug:
            continue  # parent không hợp lệ

        if parent_label not in parents:
            parents[parent_label] = SectionItem(
                label=parent_label,
                href=f"/{parent_slug}",
                childSection=[],
            )

        # chỉ lấy cấp 2 theo yêu cầu
        if len(parts) >= 2:
            child_label = parts[1]
            child_slug = slugify(child_label)

            # skip child nếu thiếu label hoặc href
            if not child_label or not child_slug:
                continue

            child_href = f"/{parent_slug}/{child_slug}"

            # dedup theo href
            existing_hrefs = {c.href for c in parents[parent_label].childSection}
            if child_href not in existing_hrefs:
                parents[parent_label].childSection.append(
                    ChildSection(label=child_label, href=child_href)
                )

    # lọc bỏ parent không có childSection hoặc childSection toàn phần tử rỗng (phòng xa)
    result: List[SectionItem] = []
    for parent in parents.values():
        # giữ lại chỉ những child hợp lệ
        parent.childSection = [
            c for c in parent.childSection
            if getattr(c, "label", None) and getattr(c, "href", None)
        ]
        if parent.childSection:  # chỉ add parent nếu có ít nhất 1 child hợp lệ
            result.append(parent)

    return result


@router.get(
    "/sections",
    summary="Navigation tree for sections",
    response_model=List[SectionItem],
)
async def get_sections_nav(request: Request):
    response_data = await list_news(
        request=request,
        fields=["section"],
        sections=None,
        date_from=None,
        date_to=None,
        q=None,
        limit=500,
        offset=0,
        order_by="published_time",
        order_dir="DESC",
    )

    # list_news returns a dict {'items': [...]}, pass the items list to build_sections_nav
    news_items = response_data.get("items", [])
    nav = build_sections_nav(news_items)
    return nav

@router.post("/{news_id}/seen", summary="Increase view count for a news item")
async def increase_view(news_id: str, request: Request):
    pool = request.app.state.pool
    sql = """
        UPDATE news
        SET view_count = COALESCE(view_count, 0) + 1
        WHERE id = $1
        RETURNING view_count;
    """
    async with pool.acquire() as conn:
        new_count = await conn.fetchval(sql, news_id)

    if new_count is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="News not found")

    return {"id": news_id, "view_count": new_count}

"""
Author: Thắng
"""

@router.get(
    "/{slug:path}",
    summary="Get detailed information for a news item by full URL slug",
    response_model=NewsDetailItemOut,
)
async def get_news_detail(slug: str, request: Request):
    pool = request.app.state.pool

    # Làm sạch slug, bỏ domain nếu người dùng dán full URL
    normalized_slug = slug.strip("/")
    if "://" in normalized_slug:
        normalized_slug = normalized_slug.split("://", 1)[-1].split("/", 1)[-1]
    normalized_slug = normalized_slug.strip("/")

    # Truy vấn bài viết có URL gần giống slug
    sql = """
        SELECT 
            id,
            title,
            description,
            article,
            section,
            thumbnail,
            published_time,
            view_count,
            url
        FROM news
        WHERE url ILIKE '%' || $1 || '%'
        ORDER BY published_time DESC
        LIMIT 1;
    """

    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(sql, normalized_slug)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

    if not row:
        raise HTTPException(status_code=404, detail="News not found")

    news = dict(row)

    # --- Chỉ lấy phần slug cuối cùng từ URL ---
    url = news.get("url")
    if url:
        # Tách phần cuối cùng sau dấu "/"
        slug_last = url.rstrip("/").split("/")[-1]
        news["slug"] = slug_last
    else:
        news["slug"] = None

    return news