from __future__ import annotations
from fastapi import Request
from typing import List, Dict, Any
from pathlib import Path

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

load_dotenv()

# Gemini SDK
try:
    import google.generativeai as genai
    from google.api_core.exceptions import NotFound
    _HAS_GENAI = True
except Exception:
    _HAS_GENAI = False

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

SYSTEM_PROMPT_FOR_BULK_ANALYSIS = (
    "Bạn là chuyên gia phân tích tin tức kinh tế/tài chính. "
    "Nhiệm vụ: đọc nhiều mẩu tin (tiêu đề, mô tả, ngày xuất bản, điểm cảm xúc pos/neg/neu) "
    "và đưa ra một bản phân tích CHUNG, cô đọng, có cấu trúc:\n"
    "1) Bức tranh tổng quan (sentiment chủ đạo, mức độ tin cậy suy theo ngày & độ đồng nhất nội dung),\n"
    "2) Các điểm nổi bật/đáng chú ý (bullet),\n"
    "3) Tác động tiềm năng (cơ hội/rủi ro),\n"
    "4) Khuyến nghị hành động ngắn gọn.\n"
    "Giữ văn phong rõ ràng, súc tích, tránh lặp lại nội dung thô."
)

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
        "Trình bày theo 4 mục đã nêu trong system prompt."
    )
    return "\n".join(lines)

def _pick_available_model(preferred=("gemini-1.5-flash","gemini-1.5-pro","gemini-1.0-pro")) -> str:
    names = [m.name for m in genai.list_models() if "generateContent" in m.supported_generation_methods]
    short = {n.split("/")[-1] for n in names}
    for m in preferred:
        if m in short:
            return m
    # Fallback: CHỈ chọn model bắt đầu bằng gemini-
    for n in short:
        if n.startswith("gemini-"):
            return n
    # Nếu không có model gemini nào -> ném lỗi rõ ràng
    raise HTTPException(status_code=502, detail="No Gemini model available for generateContent on this API key.")

def _call_gemini(system_prompt: str, user_prompt: str) -> str:
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Thiếu GEMINI_API_KEY trong môi trường.")
    if not _HAS_GENAI:
        raise HTTPException(status_code=500, detail="Thiếu thư viện google-generativeai. Cài: pip install google-generativeai")

    genai.configure(api_key=GEMINI_API_KEY)
    model_name = GEMINI_MODEL or _pick_available_model()
    model = genai.GenerativeModel(model_name=model_name, system_instruction=system_prompt)

    try:
        resp = model.generate_content(user_prompt)
    except NotFound as e:
        # Fallback thử model khác nếu model_name không tồn tại
        alt = _pick_available_model()
        if alt != model_name:
            model = genai.GenerativeModel(model_name=alt, system_instruction=system_prompt)
            resp = model.generate_content(user_prompt)
        else:
            raise HTTPException(status_code=502, detail=f"Gemini model '{model_name}' not found.") from e
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Gemini error: {str(e)}") from e

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