from os import environ
from dotenv import load_dotenv

load_dotenv()


DEBUG = True

D_TOKEN = environ.get('D_TOKEN')
R_TOKEN = environ.get('R_TOKEN')
OWNER = int(environ.get('OWNER'))

CURATORS = {
    993163323: 'Михалев Даниил',
    432502676: 'Моторина Кристина',
    969074375: 'Дардаев Константин'
}