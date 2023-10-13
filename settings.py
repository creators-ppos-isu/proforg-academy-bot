from os import environ
from dotenv import load_dotenv

load_dotenv()


DEBUG = bool(environ.get('DEBUG', False))
TOKEN = environ.get('BOT_TOKEN')

D_TOKEN = environ.get('D_TOKEN')
R_TOKEN = environ.get('R_TOKEN')
OWNER = int(environ.get('OWNER') or 596546865)

CURATORS = {
    1350212597: 'Вишнякова Анастасия',
    979892958: 'Старцев Евгений',
    1864894050: 'Лекомцева Мария',
    993163323: 'Михалев Даниил',
}