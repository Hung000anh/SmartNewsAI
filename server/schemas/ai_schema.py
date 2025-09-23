from pydantic import BaseModel
from typing import List

class NewsInputSchema(BaseModel):
    title: str
    description: str

class ClassificationResponseSchema(BaseModel):
    pos: float
    neg: float
    neu: float

class MultipleNewsInputSchema(BaseModel):
    news: List[NewsInputSchema]

# server/schemas/ai_schema.py
from pydantic import BaseModel, Field
from typing import List, Optional

class NewsAnalysisItem(BaseModel):
    title: str = Field(..., description="Tiêu đề bài viết")
    description: str = Field(..., description="Mô tả/tóm tắt nội dung")
    # Hỗ trợ cả 'publish_data' từ client và chuẩn hoá về publish_date
    publish_date: Optional[str] = Field(None, alias="publish_data", description="Ngày xuất bản (ISO 8601)")
    pos: float = Field(..., ge=0.0, le=1.0)
    neg: float = Field(..., ge=0.0, le=1.0)
    neu: float = Field(..., ge=0.0, le=1.0)

    class Config:
        allow_population_by_field_name = True  # cho phép nạp dữ liệu bằng field_name hoặc alias

class BulkNewsAnalysisInput(BaseModel):
    news: List[NewsAnalysisItem] = Field(..., min_items=1, description="Danh sách bài viết kèm pos/neg/neu")

class BulkNewsAnalysisResponse(BaseModel):
    analysis: str = Field(..., description="Phân tích tổng hợp (chung) từ Gemini")