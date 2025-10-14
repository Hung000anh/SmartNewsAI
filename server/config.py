import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[0]
MODEL_DIR = Path(os.getenv("MODEL_DIR", BASE_DIR / "models"))
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "model-textcnn-lstm.h5")
DEFAULT_TOKENIZER = os.getenv("DEFAULT_TOKENIZER", "tokenizer.pkl")
MODEL_PATH = MODEL_DIR / DEFAULT_MODEL
TOKENIZER_PATH = MODEL_DIR / DEFAULT_TOKENIZER

CERTS_DIR = os.getenv("CERTS_DIR", BASE_DIR / "certs")
SSL_FILE = os.getenv("SSL_FILE", CERTS_DIR / "prod-ca-2021.crt")

SSL_PATH = CERTS_DIR / SSL_FILE