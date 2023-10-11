from os import environ
from dotenv import load_dotenv

load_dotenv()


DEBUG = True
TOKEN = environ.get('BOT_TOKEN')

D_TOKEN = environ.get('D_TOKEN')
R_TOKEN = environ.get('R_TOKEN')
OWNER = int(environ.get('OWNER'))

CURATORS = {
    1350212597: 'Вишнякова Анастасия',
    979892958: 'Старцев Евгений',
    582528695: 'Стенцова Валентина',
    993163323: 'Михалев Даниил',
}