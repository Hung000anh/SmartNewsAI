from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel

class NewsItemOut(BaseModel):
    id: str
    title: str
    url: str
    description: Optional[str] = None
    published_time: datetime
    section: Optional[str] = None
    thumbnail: Optional[str] = None

class PageInfo(BaseModel):
    limit: int
    offset: int
    total: int

class MetaInfo(BaseModel):
    fields: Optional[List[str]] = None
    order_by: Optional[Literal["published_time","created_time","title","section","id"]] = None
    order_dir: Optional[Literal["ASC","DESC"]] = None

class NewsListResponse(BaseModel):
    items: List[NewsItemOut]
    page: PageInfo
    meta: MetaInfo