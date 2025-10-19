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

def normalize_section(section: str) -> str:
    if not section:
        return ""
    s = section.strip().lower()
    s = s.replace("&", "and")
    s = s.replace("-", " ")           # ✅ thêm bước này
    s = re.sub(r"[,]", " ", s)       # thay dấu phẩy bằng khoảng trắng
    s = re.sub(r"\s+", " ", s)       # xóa khoảng trắng thừa
    s = s.replace("/", " / ")         # thêm khoảng trắng quanh /
    s = re.sub(r"\s+/+\s+", " / ", s)  # đảm bảo chỉ 1 khoảng trắng xung quanh /
    return s.strip()

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
        normalized_sections = [normalize_section(s) for s in sections if s]
        # print(">>> Original sections:", sections)
        # print(">>> Normalized sections:", normalized_sections)

        # Chỉ dùng section đầu tiên (hoặc bạn có thể loop từng section nếu cần)
        sec = normalized_sections[0]
        params.append(sec)

        where_parts.append(f"""
            regexp_replace(
                lower(replace(section, '&', 'and')),
                '[^a-z0-9/]', '', 'g'
            ) ILIKE '%' || regexp_replace(
                lower(replace(${len(params)}, '&', 'and')),
                '[^a-z0-9/]', '', 'g'
            ) || '%'
        """)

    if date_from:
        params.append(date_from)
        where_parts.append(f"published_time >= ${len(params)}")

    if date_to:
        params.append(date_to)
        where_parts.append(f"published_time <= ${len(params)}")

    if q:
        # 🧹 Loại bỏ ký tự đặc biệt, chỉ giữ lại chữ, số và khoảng trắng
        cleaned_q = re.sub(r"[^a-zA-Z0-9\s]", " ", q)
        keywords = cleaned_q.split()
        where_like_parts = []

        for word in keywords:
            like = f"%{word}%"
            params.append(like); t_idx = len(params)
            params.append(like); d_idx = len(params)
            params.append(like); id_idx = len(params)
            print(f"LIKE conditions: title={like}, description={like}, id={like}")
            where_like_parts.append(
                f"(title ILIKE ${t_idx} OR description ILIKE ${d_idx} OR CAST(id AS TEXT) ILIKE ${id_idx})"
            )

        # 🔄 Chuyển sang tìm kiếm rộng (chỉ cần khớp 1 từ khóa)
        where_parts.append("(" + " OR ".join(where_like_parts) + ")")

    # ✅ Ghép WHERE SQL cuối cùng (ngoài if)
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
