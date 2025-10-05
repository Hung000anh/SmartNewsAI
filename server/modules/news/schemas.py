from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

class NewsItemOut(BaseModel):
    id: Optional[str] = None
    title: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    published_time: Optional[datetime] = None 
    section: Optional[str] = None
    thumbnail: Optional[str] = None
    view_count: Optional[int] = None

class PageInfo(BaseModel):
    limit: int
    offset: int
    total: int

class MetaInfo(BaseModel):
    fields: Optional[List[str]] = None
    order_by: Optional[Literal["published_time","created_time","title","section","id","view_count"]] = None
    order_dir: Optional[Literal["ASC","DESC"]] = None

class NewsListResponse(BaseModel):
    items: List[NewsItemOut]
    page: PageInfo
    meta: MetaInfo

class ChildSection(BaseModel):
    label: str = Field(..., examples=["China"])
    href: str  = Field(..., examples=["/china"])

class SectionItem(BaseModel):
    label: str = Field(..., examples=["World"])
    href: str  = Field(..., examples=["/world"])
    childSection: List[ChildSection] = Field(default_factory=list)    