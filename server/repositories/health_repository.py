from fastapi import Request

class HealthRepository:
    @staticmethod
    async def check_db(request: Request):
        pool = request.app.state.pool
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT now() AS ts")
            return {"ok": True, "server_time": row["ts"], "error": None}
