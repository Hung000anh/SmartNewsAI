from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel

class NewsItemOut(BaseModel):
    id: Optional[str] = None
    title: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    published_time: datetime = None
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