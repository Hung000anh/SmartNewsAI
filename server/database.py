import os, ssl, asyncpg
from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv
import asyncio

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
SSL_PATH = os.getenv("SSL_PATH")

ssl_ctx = ssl.create_default_context(cafile = SSL_PATH)
ssl_ctx.check_hostname = True
ssl_ctx.verify_mode = ssl.CERT_REQUIRED

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Tạo pool và gắn vào app.state
    app.state.pool = await asyncpg.create_pool(
        dsn=DATABASE_URL, 
        ssl=ssl_ctx,
        min_size=1,
        max_size=5,
        statement_cache_size=0,  # Để tránh lỗi khi đi qua PgBouncer
    )
    try:
        yield
    finally:
        # Đóng pool khi ứng dụng dừng
        if app.state.pool:
            try:
                await asyncio.wait_for(app.state.pool.close(), timeout=5)
            except asyncio.TimeoutError:
                print("Pool.close() timeout, force exit")
            app.state.pool = None

# Hàm để lấy pool kết nối từ app.state
def get_db(app: FastAPI):
    return app.state.pool