from os import environ
from dotenv import load_dotenv

load_dotenv()


DEBUG = True

D_TOKEN = environ.get('D_TOKEN')
R_TOKEN = environ.get('R_TOKEN')

TASKS = (
    ('Почистить зубы', 'Почистить зубы сегодня с утра, потому что это очень важно!'), 
    ('Убрать посуду', 'Убрать посуду, потому что это тоже очень важно!')
)