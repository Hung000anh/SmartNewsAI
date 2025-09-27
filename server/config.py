import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[0]
MODEL_DIR = Path(os.getenv("MODEL_DIR", BASE_DIR / "models_AI"))
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "selfcontained_logreg.joblib")
MODEL_PATH = MODEL_DIR / DEFAULT_MODEL

CERTS_DIR = os.getenv("CERTS_DIR", MODEL_DIR / "certs")
SSL_FILE = os.getenv("CERTS_DIR", "prod-ca-2021.crt")

SSL_PATH = CERTS_DIR / SSL_FILE