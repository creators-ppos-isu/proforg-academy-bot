import aiosqlite


async def get_task_info(conn: aiosqlite.Connection, task_id: int):
    async with conn.cursor() as cur:
        await cur.execute("SELECT id, title, max_score FROM task WHERE id=?", (task_id,))
        task = await cur.fetchone()

    return task


async def add_task_response(conn: aiosqlite.Connection, task_id: int, user_id: int):
    await conn.execute_insert("INSERT INTO user_task(task_id, user_id) VALUES(?, ?)", (task_id, user_id))
    await conn.commit()


async def is_task_response_exists(conn: aiosqlite.Connection, task_id: int, user_id: int) -> bool:
    async with conn.cursor() as cur:
        await cur.execute("SELECT 1 FROM user_task WHERE task_id=? AND user_id=?", (task_id, user_id))
        task_info = await cur.fetchone()

    return task_info is not None
