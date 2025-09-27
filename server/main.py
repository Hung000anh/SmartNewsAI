from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server.database import lifespan
import os
from fastapi.staticfiles import StaticFiles
from server.modules.docs.router import router as docs_router
from server.modules.health.router import router as health_router
from server.modules.users.router import router as users_router
from server.modules.news.router import router as news_router
from server.modules.ai.router import router as ai_router


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # ra ngoài app/
STATIC_DIR = os.path.join(BASE_DIR, "server", "static")

app = FastAPI(title="Supa-FastAPI", version="1.0.0", lifespan=lifespan, docs_url=None)

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    # "https://myfrontend.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(health_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(news_router, prefix="/api/v1")
app.include_router(docs_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")
