from typing import Iterable, List, Optional, Tuple
from fastapi import Request
from datetime import datetime

# Whitelist các cột cho phép select & sort
ALLOWED_FIELDS = {
    "id", "title", "url", "description", "published_time", "section", "thumbnail"
}
ALLOWED_SORT = {"published_time", "title", "section", "id"}

def _normalize_fields(fields: Optional[Iterable[str]]) -> List[str]:
    if not fields:
        return ["id", "title", "url", "description", "published_time", "section", "thumbnail"]
    clean = [f.strip() for f in fields if f and f.strip() in ALLOWED_FIELDS]
    return clean or ["id"]  # tối thiểu trả 'id' nếu người dùng gửi cột lạ

def _normalize_sort(order_by: Optional[str], order_dir: Optional[str]) -> Tuple[str, str]:
    col = order_by if order_by in ALLOWED_SORT else "published_time"
    direction = "DESC" if (order_dir or "").lower() not in ("asc", "desc") else order_dir.upper()
    return col, direction

class NewsRepository:
    @staticmethod
    async def list(
        request: Request,
        fields: Optional[Iterable[str]] = None,
        section: Optional[str] = None,
        sections: Optional[Iterable[str]] = None,       # hỗ trợ nhiều section
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        q: Optional[str] = None,                        # full-text đơn giản (ILIKE)
        limit: int = 20,
        offset: int = 0,
        order_by: Optional[str] = "published_time",
        order_dir: Optional[str] = "DESC",
    ):
        pool = request.app.state.pool

        # 1) Build SELECT
        select_cols = _normalize_fields(fields)
        select_sql = ", ".join(select_cols)

        # 2) Build WHERE + params
        where = []
        params = []
        if section:  # 1 giá trị
            params.append(f"%{section}%")
            where.append(f"section ILIKE ${len(params)}")

        if sections:  # nhiều giá trị -> ILIKE ANY(array)
            sects = [f"%{s}%" for s in sections if s]
            if sects:
                params.append(sects)                       # truyền cả list làm 1 param
                where.append(f"section ILIKE ANY(${len(params)})")
        if date_from:
            params.append(date_from)
            where.append(f"published_time >= ${len(params)}")
        if date_to:
            params.append(date_to)
            where.append(f"published_time < ${len(params)}")

        if q:
            # Tìm trong title/description (ILIKE)
            params.append(f"%{q}%")
            like1 = f"title ILIKE ${len(params)}"
            params.append(f"%{q}%")
            like2 = f"description ILIKE ${len(params)}"
            where.append(f"({like1} OR {like2})")

        where_sql = f"WHERE {' AND '.join(where)}" if where else ""

        # 3) Sort + Pagination (whitelist)
        sort_col, sort_dir = _normalize_sort(order_by, order_dir)
        if limit <= 0 or limit > 1000:  # chặn limit quá lớn
            limit = 20
        if offset < 0:
            offset = 0

        # 4) Query chính
        sql = f"""
            SELECT {select_sql}
            FROM news
            {where_sql}
            ORDER BY {sort_col} {sort_dir} NULLS LAST
            LIMIT {limit} OFFSET {offset}
        """

        async with pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)
            data = [dict(r) for r in rows]

            # 5) (tùy chọn) Đếm tổng để client biết có bao nhiêu bản ghi
            count_sql = f"SELECT COUNT(*) FROM news {where_sql}"
            total = await conn.fetchval(count_sql, *params)

        return {
            "items": data,
            "page": {"limit": limit, "offset": offset, "total": total},
            "meta": {"fields": select_cols, "order_by": sort_col, "order_dir": sort_dir},
        }