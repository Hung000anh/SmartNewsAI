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