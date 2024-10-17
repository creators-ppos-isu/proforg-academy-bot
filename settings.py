from os import environ
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
BOT_TOKEN = environ.get("BOT_TOKEN")
DB_NAME = environ.get("DB_NAME", "db.sqlite3")
