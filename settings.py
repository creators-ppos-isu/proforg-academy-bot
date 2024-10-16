from os import environ

from dotenv import load_dotenv
from pathlib import Path


load_dotenv()

BASE_DIR = Path(__file__).parent
BOT_TOKEN = environ.get("BOT_TOKEN")
OWNER = int(environ.get("OWNER", 596546865))
DB_NAME = environ.get("DB_NAME", "db.sqlite3")

CURATORS = {
    1350212597: "Вишнякова Анастасия",
    979892958: "Старцев Евгений",
    1864894050: "Лекомцева Мария",
    993163323: "Михалев Даниил",
}
