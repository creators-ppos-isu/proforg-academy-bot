import sqlite3


class Sql:
    def __init__(self, database_name="data.db"):
        self.database_name = database_name

    def _get_cursor(self):
        db = sqlite3.connect(self.database_name)
        return db.cursor()

    def select(self, query: str, size=1):
        cursor = self._get_cursor()
        cursor.execute(query)
        if size == 1:
            return cursor.fetchone()
        if size == -1:
            return cursor.fetchall()
        return cursor.fetchmany(size)

    def create_table(self, table_name: str, columns: str):
        db = sqlite3.connect(self.database_name)
        cursor = db.cursor()
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name}(
            {columns}
        );""")
        db.commit()

    def update(self, query: str):
        db = sqlite3.connect(self.database_name)
        cursor = db.cursor()
        cursor.execute(query)
        db.commit()


class User:
    def __init__(self, user_id: int):
        self.user_id = user_id

    def is_authorized(self):
        return True