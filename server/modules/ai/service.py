from __future__ import annotations
from fastapi import Request
from typing import List, Dict, Any
from pathlib import Path
from textwrap import dedent
from joblib import load
import numpy as np

from server.modules.ai.schemas import MultipleNewsInput, ClassificationMultipleNewsOutput, ClassificationNewOutput, NewsAnalysisResponse, NewsInput
from server.config import MODEL_PATH
import text_hammer as th


# ===================== Preprocessing =====================
def text_preprocessing(text: str) -> str:
    text = (text or "").lower()
    text = th.cont_exp(text)                # don't -> do not
    text = th.remove_rt(text)               # remove "rt"
    text = th.remove_emails(text)           # user@example.com
    text = th.remove_urls(text)             # http, https
    text = th.remove_html_tags(text)        # <p>...</p>
    text = th.remove_stopwords(text)        # i, me, my, ...
    text = th.remove_accented_chars(text)   # café -> cafe
    text = th.remove_special_chars(text)    # #, @, ...
    text = th.make_base(text)               # ran -> run
    return text.strip()


# ===================== Model (cached) =====================
_MODEL = None
_CLASSES = None  # will hold np.ndarray like [0,1,2]

def _get_model():
    global _MODEL, _CLASSES
    if _MODEL is None:
        path = Path(MODEL_PATH)
        if not path.exists():
            raise FileNotFoundError(f"MODEL_PATH not found: {path}")
        _MODEL = load(path)
        if not hasattr(_MODEL, "predict_proba"):
            raise AttributeError("Loaded model does not implement predict_proba")
        if not hasattr(_MODEL, "classes_"):
            raise AttributeError("Loaded model has no attribute classes_")
        _CLASSES = np.array(_MODEL.classes_)  # expect [0,1,2]
    return _MODEL


# ===================== Inference helpers =====================
def predict_sentiment(pipe, text: str, preprocess_fn=None) -> Dict[str, Any]:
    """Trả về processed_text, proba theo lớp gốc, và nhãn dự đoán."""
    processed_text = preprocess_fn(text) if preprocess_fn else text
    proba = pipe.predict_proba([processed_text])[0]  # shape (n_classes,)
    classes = getattr(pipe, "classes_", range(len(proba)))
    proba_dict = {int(k): float(v) for k, v in zip(classes, proba)}
    label = pipe.predict([processed_text])[0]
    return {
        "processed_text": processed_text,
        "proba": proba_dict,
        "label": label,
    }


def _map_012_to_pos_neg_neu(proba_by_class: Dict[int, float]) -> Dict[str, float]:

    neg = float(proba_by_class.get(0, 0.0))
    neu = float(proba_by_class.get(1, 0.0))
    pos = float(proba_by_class.get(2, 0.0))

    # đảm bảo tổng ~ 1.0 (trong trường hợp model/proba rounding)
    s = neg + neu + pos
    if s > 0:
        neg, neu, pos = neg / s, neu / s, pos / s

    return {"pos": pos, "neg": neg, "neu": neu}


# ===================== Main service =====================
def classify_news(news_data: List[NewsInput]) -> ClassificationMultipleNewsOutput:
    model = _get_model()
    results: List[ClassificationNewOutput] = []

    for news in news_data:
        title = news.title or ""
        description = news.description or ""
        publish_date = news.publish_date

        text = f"{title} {description}".strip()
        pred = predict_sentiment(model, text, preprocess_fn=text_preprocessing)
        mapped = _map_012_to_pos_neg_neu(pred["proba"])

        results.append(
            ClassificationNewOutput(
                title=title,
                description=description,
                publish_date=publish_date,
                **mapped,
            )
        )

    return ClassificationMultipleNewsOutput(news=results)


# server/services/ai_service.py
import os
from typing import List
from fastapi import HTTPException, Request
from dotenv import load_dotenv
from server.modules.ai.schemas import NewsAnalysisResponse, NewsAnalysisInput
import google.generativeai as genai
load_dotenv()



GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL")

SYSTEM_PROMPT_FOR_BULK_ANALYSIS = dedent("""
[ROLE / SYSTEM]  
Bạn là một nhà đầu tư và chuyên gia phân tích thị trường tài chính.  
Nhiệm vụ của bạn: đọc danh sách các tin tức (mỗi tin có title và description, có thể là tiếng Anh) và phân loại góc nhìn tâm lý của nhà giao dịch theo 3 nhóm:  
- Positive (tin tức mang lại kỳ vọng, niềm tin, động lực đầu tư hoặc tác động tích cực đến thị trường/tài sản).  
- Neutral (tin tức trung lập, chỉ cung cấp thông tin, chưa đủ để tác động mạnh tới tâm lý thị trường).  
- Negative (tin tức mang lại lo ngại, rủi ro, tâm lý bi quan hoặc tác động tiêu cực đến thị trường/tài sản).  

⚠️ QUAN TRỌNG: Luôn dịch và viết phần phản hồi **bằng tiếng Việt** dù tin tức gốc là tiếng Anh.  

[OUTPUT FORMAT]  
Viết theo dạng tin nhắn, trả lời tiếng Việt, có emoji và xuống dòng rõ ràng, ví dụ: 
---
📊 Phân tích tin tức {ten_ngữ_cảnh}:  

✅ **Positive:** 
- [Tiêu đề] - [Mô tả] - (Từ {thời_gian_đăng_bài})
- [Tiêu đề] - [Mô tả] - (Từ {thời_gian_đăng_bài})
- ...                                        
⚖️ **Neutral:** 
- [Tiêu đề] - [Mô tả] - (Từ {thời_gian_đăng_đầu})
- [Tiêu đề] - [Mô tả] - (Từ {thời_gian_đăng_bài})
- ...                                         
⚠️ **Negative:** 
- [Tiêu đề] - [Mô tả] - (Từ {thời_gian_đăng_đầu})
- [Tiêu đề] - [Mô tả] - (Từ {thời_gian_đăng_bài})
- ...
📌 **Kết luận:** [Kết luận ngắn gọn tâm lý chung ]
---
[NOTE]  
- Có thể rút gọn mô tả để giống tin nhắn Zalo.  
- Tất cả đầu ra bắt buộc là tiếng Việt.  
- Phần **Kết luận** phải khách quan, tổng hợp từ các nhóm tin, không thêm quan điểm cá nhân.
""").strip()

def _build_user_prompt(payload: NewsAnalysisInput) -> str:
    lines: List[str] = []
    lines.append("Dữ liệu đầu vào gồm nhiều bài:")
    for i, item in enumerate(payload.news):
        lines.append(f"\n--- Bài #{i} ---")
        lines.append(f"Title: {item.title}")
        lines.append(f"Description: {item.description}")
        # THỐNG NHẤT field là publish_date
        if getattr(item, "publish_date", None):
            lines.append(f"Publish Date: {item.publish_date}")
        lines.append(f"Scores: pos={item.pos:.3f}, neg={item.neg:.3f}, neu={item.neu:.3f}")
    lines.append(
        "\nYêu cầu: Chỉ trả về PHÂN TÍCH CHUNG (không cần phân tích theo từng bài). "
        "Trình bày theo nêu trong system prompt."
    )

    return "\n".join(lines)


def _call_gemini(system_prompt: str, user_prompt: str) -> str:
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Thiếu GEMINI_API_KEY trong môi trường.")

    genai.configure(api_key=GEMINI_API_KEY)
    model_name = GEMINI_MODEL
    model = genai.GenerativeModel(model_name=model_name, system_instruction=system_prompt)
    resp = model.generate_content(user_prompt)
    text = getattr(resp, "text", None)
    if not text:
        try:
            text = resp.candidates[0].content.parts[0].text
        except Exception:
            text = ""
    if not text:
        raise HTTPException(status_code=502, detail="Gemini không trả về nội dung hợp lệ.")
    return text

def analyze_news(payload: NewsAnalysisInput) -> NewsAnalysisResponse:
    user_prompt = _build_user_prompt(payload)
    analysis = _call_gemini(SYSTEM_PROMPT_FOR_BULK_ANALYSIS, user_prompt)
    return NewsAnalysisResponse(analysis=analysis)