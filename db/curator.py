import aiosqlite


async def get_all_curators(conn: aiosqlite.Connection) -> list[tuple[int, str]]:
    return await conn.execute_fetchall("SELECT id, first_name, last_name FROM curator")


async def get_curator(conn: aiosqlite.Connection, curator_id: int) -> tuple[int, str, str]:
    async with conn.cursor() as cur:
        await cur.execute("SELECT id, first_name, last_name FROM curator WHERE id=?", (curator_id,))
        curator_info = await cur.fetchone()

    return curator_info
