from fastapi import FastAPI
from server.core.db import lifespan
from server.api.v1 import api_v1
import os
from fastapi.staticfiles import StaticFiles

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # ra ngoài app/
STATIC_DIR = os.path.join(BASE_DIR, "server", "static")

app = FastAPI(title="Supa-FastAPI", version="1.0.0", lifespan=lifespan, docs_url=None)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(api_v1, prefix="/api/v1")
