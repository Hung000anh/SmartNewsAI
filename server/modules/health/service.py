from fastapi import Request


async def ping():
        return {"pong": True}

async def db(request: Request):
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT now() AS ts")
        return {"ok": True, "server_time": row["ts"], "error": None}