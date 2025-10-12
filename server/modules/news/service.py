# server/services/news_service.py
from typing import Iterable, Optional, List, Tuple
from datetime import datetime
from fastapi import Request
import re
# Whitelist các cột cho phép SELECT & SORT
ALLOWED_FIELDS = {
    "id", "title", "url", "description", "published_time", "section", "thumbnail", "view_count"
}
ALLOWED_SORT = {"published_time", "title", "section", "id", "view_count"}

def _normalize_fields(fields: Optional[Iterable[str]]) -> List[str]:
    """
    Giữ lại những cột hợp lệ theo whitelist; nếu rỗng → trả bộ mặc định.
    """
    if not fields:
        return ["id", "title", "url", "description", "published_time", "section", "thumbnail", "view_count"]
    out: List[str] = []
    for f in fields:
        if not f:
            continue
        fx = f.strip()
        if fx in ALLOWED_FIELDS:
            out.append(fx)
    return out or ["id"]

def _normalize_sort(order_by: Optional[str], order_dir: Optional[str]) -> Tuple[str, str]:
    col = order_by if order_by in ALLOWED_SORT else "published_time"
    dir_ = (order_dir or "DESC").upper()
    if dir_ not in ("ASC", "DESC"):
        dir_ = "DESC"
    return col, dir_


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

    pool = request.app.state.pool

    # 1) SELECT
    select_cols = _normalize_fields(fields)
    select_sql = ", ".join(select_cols)

    # 2) WHERE + params
    where_parts: List[str] = []
    params: List[object] = []

    if sections:
        # Chuẩn hóa: bỏ hết ký tự đặc biệt, chỉ giữ chữ và số
        normalized_sections = []
        for s in sections:
            if not s:
                continue
            clean = re.sub(r'[^a-zA-Z0-9]', '', s).lower()
            normalized_sections.append(clean)

        params.append(normalized_sections)
        where_parts.append(
            f"regexp_replace(LOWER(section), '[^a-z0-9]', '', 'g') = ANY(${len(params)})"
        )


    if date_from:
        params.append(date_from)
        where_parts.append(f"published_time >= ${len(params)}")

    if date_to:
        params.append(date_to)
        where_parts.append(f"published_time <= ${len(params)}")

    if q:
        # Tìm trong title/description (partial)
        like = f"%{q}%"
        params.append(like); t_idx = len(params)
        params.append(like); d_idx = len(params)

        # Tìm theo ID:
        # - exact match: hữu ích khi q là số/UUID/mã chuẩn
        # - partial match: khi q chỉ nhớ 1 phần ID (KH123, ORD-2025, ...)
        params.append(q); id_eq_idx = len(params)
        params.append(like); id_like_idx = len(params)

        where_parts.append(
            f"(title ILIKE ${t_idx} "
            f"OR description ILIKE ${d_idx} "
            f"OR CAST(id AS TEXT) = ${id_eq_idx} "
            f"OR CAST(id AS TEXT) ILIKE ${id_like_idx})"
        )

    where_sql = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""

    # 3) SORT + PAGINATION
    sort_col, sort_dir = _normalize_sort(order_by, order_dir)
    if limit <= 0 or limit > 1000:
        limit = 20
    if offset < 0:
        offset = 0

    # 4) Query
    sql = f"""
        SELECT {select_sql}
        FROM news
        {where_sql}
        ORDER BY {sort_col} {sort_dir} NULLS LAST
        LIMIT {limit} OFFSET {offset}
    """
    count_sql = f"SELECT COUNT(*) FROM news {where_sql}"

    async with pool.acquire() as conn:
        rows = await conn.fetch(sql, *params)
        items = [dict(r) for r in rows]
        total = await conn.fetchval(count_sql, *params)

    return {
        "items": items,
        "page": {"limit": limit, "offset": offset, "total": total},
        "meta": {"fields": select_cols, "order_by": sort_col, "order_dir": sort_dir},
    }

async def get_news_by_id(request: Request, news_id: str):
    pool = request.app.state.pool
    sql = """
        SELECT 
            id,
            title,
            url,
            description,
            article,
            section,
            published_time,
            view_count
        FROM news
        WHERE id = $1
        LIMIT 1;
    """
    async with pool.acquire() as conn:
        row = await conn.fetchrow(sql, news_id)

    return dict(row) if row else None
