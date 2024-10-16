import aiosqlite


async def is_user_exists(conn: aiosqlite.Connection, user_id: int) -> bool:
    async with conn.cursor() as cur:
        await cur.execute("SELECT 1 FROM user WHERE id=?", (user_id,))
        exists = await cur.fetchone()

    return exists is not None


async def add_user(conn: aiosqlite.Connection, user_id: int):
    await conn.execute_insert("INSERT INTO user(id) VALUES(?)", (user_id,))
    await conn.commit()


async def set_user_full_name(conn: aiosqlite.Connection, user_id: int, full_name: str):
    first_name, last_name = full_name.split(" ", 1)
    await conn.execute("UPDATE user SET first_name=?, last_name=? WHERE id=?", (first_name, last_name, user_id))
    await conn.commit()


async def set_user_curator(conn: aiosqlite.Connection, user_id: int, curator_id: int):
    await conn.execute("UPDATE user SET curator_id=? WHERE id=?", (curator_id, user_id))
    await conn.commit()


async def get_uncompleted_tasks(conn: aiosqlite.Connection, user_id: int) -> list[tuple[int, int]]:
    return await conn.execute_fetchall("SELECT t.id, t.title FROM task t WHERE t.id NOT IN (SELECT ut.task_id FROM user_task ut WHERE ut.user_id=?)", (user_id,))
