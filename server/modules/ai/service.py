from __future__ import annotations
from fastapi import Request
from typing import List, Dict, Any
from pathlib import Path
from textwrap import dedent
from joblib import load
import numpy as np
import json
from server.modules.ai.schemas import MultipleNewsInput, ClassificationMultipleNewsOutput, ClassificationNewOutput, NewsAnalysisResponse, NewsInput
from server.config import TOKENIZER_PATH, MODEL_PATH
import text_hammer as th
from tensorflow.keras import backend as K
from tensorflow.keras.layers import Layer
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences
import pickle

class Attention(Layer):
    def __init__(self, **kwargs):
        super(Attention, self).__init__(**kwargs)

    def build(self, input_shape):
        self.W = self.add_weight(name="att_weight", shape=(input_shape[-1], 1),
                                 initializer="normal")
        self.b = self.add_weight(name="att_bias", shape=(input_shape[1], 1),
                                 initializer="zeros")
        super(Attention, self).build(input_shape)

    def call(self, x):
        e = K.tanh(K.dot(x, self.W) + self.b)
        a = K.softmax(e, axis=1)
        output = x * a
        return K.sum(output, axis=1)

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


MAX_LEN = 81

_MODEL = None
_TOKENIZER = None

def _get_model_and_tokenizer():
    """Cache model và tokenizer."""
    global _MODEL, _TOKENIZER

    if _TOKENIZER is None:
        if not TOKENIZER_PATH.exists():
            raise FileNotFoundError(f"Tokenizer not found: {TOKENIZER_PATH}")
        with open(TOKENIZER_PATH, "rb") as f:
            _TOKENIZER = pickle.load(f)

    if _MODEL is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Model not found: {MODEL_PATH}")
        _MODEL = load_model(MODEL_PATH, custom_objects={"Attention": Attention})

    return _MODEL, _TOKENIZER

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


def _predict_sentiment_keras(model, tokenizer, text_list: List[str]):
    """Trả về list dict [{pos, neg, neu}, ...]"""
    from tensorflow.keras.preprocessing.text import Tokenizer

    if not text_list:
        return []

    # Encode
    seq = tokenizer.texts_to_sequences(text_list)
    X_pad = pad_sequences(seq, maxlen=MAX_LEN, padding="post")

    # Predict
    preds = model.predict(X_pad, verbose=0)  # (n_samples, 3)

    results = []
    for p in preds:
        pos, neg, neu = map(float, p)
        s = pos + neg + neu
        if s > 0:
            pos, neg, neu = pos / s, neg / s, neu / s
        results.append({"pos": pos, "neg": neg, "neu": neu})

    return results


def classify_news(news_data: List[NewsInput]) -> ClassificationMultipleNewsOutput:
    model, tokenizer = _get_model_and_tokenizer()

    texts = [
        text_preprocessing(f"{n.title or ''} {n.description or ''}".strip())
        for n in news_data
    ]

    predictions = _predict_sentiment_keras(model, tokenizer, texts)

    results: List[ClassificationNewOutput] = []
    for news, pred in zip(news_data, predictions):
        results.append(
            ClassificationNewOutput(
                title=news.title or "",
                description=news.description or "",
                publish_date=news.publish_date,
                pos=pred["pos"],
                neg=pred["neg"],
                neu=pred["neu"],
            )
        )

    return ClassificationMultipleNewsOutput(news=results)


# server/services/ai_service.py
import os
from typing import List
from fastapi import HTTPException, Request
from dotenv import load_dotenv
from openai import OpenAI
load_dotenv()



OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL   = os.getenv("OPENAI_MODEL", "gpt-5-nano")

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
⚖️ **Neutral:** 
- ...
⚠️ **Negative:** 
- ...
📌 **Kết luận:** [Kết luận ngắn gọn tâm lý chung ]
---
[NOTE]  
- Có thể rút gọn mô tả để giống tin nhắn Zalo.  
- Tất cả đầu ra bắt buộc là tiếng Việt.  
- Phần **Kết luận** phải khách quan, tổng hợp từ các nhóm tin, không thêm quan điểm cá nhân.
""").strip()


def _build_user_prompt(payload):
    lines: List[str] = []
    lines.append("Dữ liệu đầu vào gồm nhiều bài:")
    for i, item in enumerate(payload.news):
        lines.append(f"\n--- Bài #{i} ---")
        lines.append(f"Title: {item.title}")
        lines.append(f"Description: {item.description}")
        if getattr(item, "publish_date", None):
            lines.append(f"Publish Date: {item.publish_date}")
        lines.append(f"Scores: pos={item.pos:.3f}, neg={item.neg:.3f}, neu={item.neu:.3f}")
    lines.append(
        "\nYêu cầu: Chỉ trả về PHÂN TÍCH CHUNG (không cần phân tích theo từng bài). "
        "Trình bày theo nêu trong system prompt."
    )
    return "\n".join(lines)


def _call_chatgpt(system_prompt: str, user_prompt: str) -> str:
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="Thiếu OPENAI_API_KEY trong môi trường.")
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    
    text = resp.choices[0].message.content.strip()
    if not text:
        raise HTTPException(status_code=502, detail="ChatGPT không trả về nội dung hợp lệ.")
    return text


def analyze_news(payload):
    user_prompt = _build_user_prompt(payload)
    analysis = _call_chatgpt(SYSTEM_PROMPT_FOR_BULK_ANALYSIS, user_prompt)
    return {"analysis": analysis}


async def get_chat_history(
    request: Request,
    session_id: str,
    limit: int = 100,
    offset: int = 0,
):
    pool = request.app.state.pool

    sql = """
        SELECT 
            id,
            session_id,
            message
        FROM n8n_chat_histories
        WHERE session_id = $1
        ORDER BY id ASC
        LIMIT $2 OFFSET $3
    """

    async with pool.acquire() as conn:
        rows = await conn.fetch(sql, session_id, limit, offset)

    items = []
    for r in rows:
        msg = r["message"]
        # Nếu message bị lưu dưới dạng string JSON, parse lại
        if isinstance(msg, str):
            try:
                msg = json.loads(msg)
            except json.JSONDecodeError:
                pass

        items.append({
            "id": r["id"],
            "session_id": r["session_id"],
            "message": msg,
        })

    return {
        "session_id": session_id,
        "items": items,
        "page": {"limit": limit, "offset": offset, "total": len(items)},
    }
