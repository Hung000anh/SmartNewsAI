# ========== BUILD STAGE ==========
FROM python:3.9-slim

WORKDIR /app

# Copy toàn bộ source code server/
COPY . /app

# Cài đặt dependencies
RUN pip install --no-cache-dir -r requirements.txt

# ====== FIX cho spaCy và NLTK ======
# Đặt thư mục data cho NLTK
ENV NLTK_DATA=/usr/local/nltk_data

# Tải model spaCy và NLTK data
RUN python -m spacy download en_core_web_sm && \
    python - <<'PY'
import nltk
nltk.download('punkt')
try:
    nltk.download('punkt_tab')
except Exception as e:
    print("WARN: punkt_tab not available:", e)
PY

# ========== RUN ==========
EXPOSE 8000
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]