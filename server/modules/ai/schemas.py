from pydantic import BaseModel
from typing import List
from datetime import datetime

class NewsInput(BaseModel):
    title: str
    description: str
    publish_date: datetime

class ClassificationNewOutput(BaseModel):
    title: str
    description: str
    publish_date: datetime
    pos: float
    neg: float
    neu: float

class MultipleNewsInput(BaseModel):
    news: List[NewsInput]

class ClassificationMultipleNewsOutput(BaseModel):
    news: List[ClassificationNewOutput]

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

    model_config = {
        "validate_by_name": True
    }
class NewsAnalysisInput(BaseModel):
    news: List[NewsAnalysisItem] = Field(..., min_length=1, description="Danh sách bài viết kèm pos/neg/neu")

class NewsAnalysisResponse(BaseModel):
    analysis: str = Field(..., description="Phân tích tổng hợp (chung) từ Gemini")

class ChatBotResponse(BaseModel):
    ok: str = Field(..., description="Trạng thái chat bot")
    code: str = Field(..., description="Code n8n chat bot")
    message: str = Field(..., description="Phản hồi chat bot")