from __future__ import annotations

from typing import List, Dict, Any
from pathlib import Path

from joblib import load
import numpy as np

from server.schemas.ai_schema import NewsInputSchema, ClassificationResponseSchema
from server.services.auth_service import verify_access_token_user
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
        print("Đường dẫn mô hình: ", path)
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
    """
    Giả định chuẩn sklearn: classes_ = [0, 1, 2] -> [neg, neu, pos].
    """
    neg = float(proba_by_class.get(0, 0.0))
    neu = float(proba_by_class.get(1, 0.0))
    pos = float(proba_by_class.get(2, 0.0))

    # đảm bảo tổng ~ 1.0 (trong trường hợp model/proba rounding)
    s = neg + neu + pos
    if s > 0:
        neg, neu, pos = neg / s, neu / s, pos / s

    return {"pos": pos, "neg": neg, "neu": neu}


# ===================== Main service =====================
def classify_news_service(
    news_data: List[NewsInputSchema],
    access_token: str
) -> List[ClassificationResponseSchema]:
    # 1) Verify access token (Supabase)
    user_data = verify_access_token_user(access_token)
    if not user_data:
        raise ValueError("Invalid Access Token")

    # 2) Load model (cached)
    model = _get_model()

    # 3) Inference từng bản tin
    results: List[ClassificationResponseSchema] = []
    for news in news_data:
        title = getattr(news, "title", "") or ""
        description = getattr(news, "description", "") or ""
        text = f"{title} {description}".strip()

        pred = predict_sentiment(model, text, preprocess_fn=text_preprocessing)
        proba_by_class = pred["proba"]  # {0: x, 1: y, 2: z}

        mapped = _map_012_to_pos_neg_neu(proba_by_class)
        ai_response = ClassificationResponseSchema(**mapped)
        results.append(ai_response)

    return results