import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
import settings
import modules
import messages

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] - %(asctime)s - %(message)s", encoding='utf-8', filename='log.log')
token = settings.D_TOKEN if settings.DEBUG else settings.R_TOKEN
bot = Bot(token=token)
dp = Dispatcher(bot, storage=MemoryStorage())
sql = modules.sqlmanager.Sql()


class Form(StatesGroup):
    name = State()
    feedback = State()

async def get_tasks(message: types.Message):
    all_task = sql.select(f"SELECT TASK_ID FROM tasks", 0)
    completed_tasks = sql.select(f"SELECT task FROM user_{message.from_user.id}", 0)
    available_tasks = [task[0] for task in all_task if task not in completed_tasks]

    user_id = sql.select(f"SELECT USER_ID FROM users WHERE TG_ID={message.from_user.id}")[0]
    buttons = []
    for task in available_tasks:
        title = sql.select(f"SELECT title FROM tasks WHERE TASK_ID={task}")[0]
        buttons.append({'text': title,'callback': f'settask;{user_id};{task};0'})
    return buttons


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    if message.from_user.id in settings.CURATORS.keys():
        await message.answer('Приветствую тебя, куратор!')

        return

    await message.answer(messages.WELCOME)
    if sql.select(f"SELECT USER_ID FROM users WHERE TG_ID={message.from_user.id}") is None:
        sql.update(f'INSERT INTO users(TG_ID) VALUES({message.from_user.id});')
        sql.create_table(f"user_{message.from_user.id}", """
            task INT PRIMARY KEY, 
            score INT
        """)
        await message.answer("Введи свое имя и фамилию, чтобы мы точно начислили баллы именно тебе!")
        await Form.name.set()


@dp.message_handler(state=Form.name)
async def name_reg(message: types.Message, state: FSMContext):
    sql.update(f"UPDATE users SET name='{message.text}' WHERE TG_ID={message.from_user.id}")
    user_id = sql.select(f"SELECT USER_ID FROM users WHERE TG_ID={message.from_user.id}")[0]

    buttons = [{'text': settings.CURATORS[curator], 'callback': f"setcurator;{user_id};{curator}"} for curator in settings.CURATORS.keys()]
    if settings.DEBUG: 
        buttons.append({'text': 'test', 'callback': f'setcurator;{user_id};596546865'})
    log.info(f'New user: {message.text}; UID: {user_id}')
    await message.answer("Приятно, познакомиться😉\n\nТеперь, выбери своего куратора:", reply_markup=modules.markup.inline(buttons))
    await state.finish()


@dp.message_handler(state=Form.feedback)
async def resend_feedback(message: types.Message, state: FSMContext):
    await message.answer('Спасибо за обратную связь 😉') 
    uid, name, curator = sql.select(f"SELECT USER_ID, name, curator FROM users WHERE TG_ID={message.from_user.id}")
    await bot.send_message(curator, f"Отзыв от {name} UID: {uid}:\n\n{message.text}")
    log.info(f'Feedback from {uid} {name}')
    await state.finish()


@dp.message_handler(lambda message: message.from_user.id == settings.OWNER, commands=['atask', 'dtask', 'feedback'])
async def do_request(message: types.Message):
    if 'atask' in message.text:
        title, max_score = message.text.split(' ', 1)[1].split(';')
        max_score = int(max_score)
        sql.update(f"INSERT INTO tasks(title, max_score) VALUES('{title}', {max_score})")
        tid = sql.select(f"SELECT TASK_ID FROM tasks WHERE title='{title}'")[0]
        await message.answer(f"Добавленно задание: {title}\nTID: {tid}")
        log.info(f"Add task: {title} TID: {tid}")

    if 'dtask' in message.text:
        task_id = int(message.text.split(' ', 1)[1])
        if sql.select(f"SELECT * FROM tasks WHERE TASK_ID={task_id}") is None:
            await message.answer('Задачи с таким ID не сущетвует!')
            return
        try:
            sql.update(f"DELETE FROM tasks WHERE TASK_ID={task_id}")
            log.info(f"Delete task: {task_id}")
            await message.answer(f'Задание {task_id} удалено')
        except Exception as e:
            await message.answer(f"Не удалось удалить задание: {e}")
    
    if 'feedback' in message.text: 
        users = sql.select(f"SELECT tg_id FROM users", 0)
        buttons = [{'text': 'Отправить отзыв', 'callback': 'send_feedback'}]
        for user in users:
            try: 
                await bot.send_message(user[0], "Лекция закончилась! Нажми на кнопку ниже, если хочешь оставить комментарий 👇", reply_markup=modules.markup.inline(buttons))
            except Exception as e:
                log.error(f'UID: {user[0]} message: {e}')
        log.warning("Send feedback to each user")


@dp.message_handler(lambda message: message.text == 'Выбрать задание')
async def choose_task(message: types.Message):
    tasks = await get_tasks(message)
    if sql.select(f"SELECT curator FROM users WHERE tg_id={message.from_user.id}")[0] is None:
        await message.answer("Чтобы выбрать задание, для начала нужно выбрать куратора, сделать это можно с помощью команды /start")
        return
    if not tasks:
        await message.answer('Больше нет доступных заданий!')
        return
    await message.answer('Выберите задание', reply_markup=modules.markup.inline(tasks))


@dp.message_handler(content_types=["photo"])
async def verify_task(message: types.Message): 
    if sql.select(f"SELECT current_task FROM users WHERE TG_ID={message.from_user.id}")[0] is None:
        await message.answer('Нужно выбрать задание нажав на кнопку под полем ввода сообщений!')
        return 
    
    user_id, task_id, curator = sql.select(f"SELECT USER_ID, current_task, curator FROM users WHERE TG_ID={message.from_user.id}")
    task_title = sql.select(f"SELECT title FROM tasks WHERE TASK_ID={task_id}")[0]
    user_table = f"user_{message.from_user.id}"
    task_score = sql.select(f"SELECT score FROM {user_table} WHERE task={task_id}")
    
    if not task_score:
        sql.update(f"INSERT INTO {user_table}(task, score) VALUES({task_id}, 0);")

    elif task_score[0] == 0:
        await message.answer(messages.ERR_ANSWER_ALREADY_SENT)
        return

    await message.answer('Отправляю фотографию куратору...')

    max_score = int(sql.select(f"SELECT max_score FROM tasks WHERE TASK_ID={task_id}")[0])
    buttons = [{'text': '⭐️'*value,'callback': f'rate;{user_id};{task_id};{value}'} for value in range(1, max_score+1)]
    buttons.append({'text': 'Отклонить задание', 'callback': f'reject;{user_id};{task_id};0'})
    
    await bot.send_photo(curator, message.photo[-1].file_id, 
                        caption=f"Ответ по заданию {task_title}\n\nID пользователя: {user_id}\nID задания: {task_id}",
                        reply_markup=modules.markup.inline(buttons))
    log.info(f'Send photo: {message.from_user.id} -> {curator}; Task ID: {task_id}')


@dp.callback_query_handler()
async def callback_check(callback: types.CallbackQuery):
    await bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id)

    if callback.data.split(';')[0] == 'setcurator': 
        action, user_id, curator =  callback.data.split(';')
        user_id, curator = int(user_id), int(curator)
        sql.update(f"UPDATE users SET curator={curator} WHERE USER_ID={user_id}")
        await callback.message.answer(f'Твой куратор: {settings.CURATORS.get(curator)}!', reply_markup=modules.markup.reply(['Выбрать задание']))

        return

    if callback.data.startswith('send_feedback'):
        await callback.message.answer('Напиши свой отзыв о лекции в ответ на это сообщение')
        await Form.feedback.set()

    action, user_id, task_id, value =  callback.data.split(';')
    user_id, task_id, value = int(user_id), int(task_id), int(value)

    task_title = sql.select(f"SELECT title FROM tasks WHERE TASK_ID={task_id}")[0]
    tg_id = sql.select(f"SELECT TG_ID FROM users WHERE USER_ID={user_id}")[0]
    user_table = f"user_{tg_id}"

    if action == 'rate':
        sql.update(f"UPDATE {user_table} SET score={value} WHERE task={task_id}")
        sql.update(f"UPDATE users SET score=score+{value}, current_task=NULL WHERE USER_ID={user_id}")
        log.info(f'Rate UID: {user_id} TID: {task_id} SCORE: {value}')

        await bot.send_message(tg_id, f'Вам начисленно {value} баллов!')

    if action == 'reject':
        sql.update(f"DELETE FROM {user_table} WHERE task={task_id}")
        log.info(f'Reject UID: {user_id} TID: {task_id} SCORE: {value}')

        await bot.send_message(tg_id, f"Задание {task_title} отклоненно куратором")

    if action == 'settask':
        sql.update(f'UPDATE users SET current_task={task_id} WHERE USER_ID={user_id}')

        await callback.message.answer(f'Вы выбрали {task_title} в качестве активного задания!')


if __name__ == '__main__':
    if settings.DEBUG == False:
        log.warning("Start On Release Bot")

    sql.create_table("users", """
        USER_ID INTEGER PRIMARY KEY AUTOINCREMENT, 
        TG_ID INT, 
        current_task INT, 
        curator INT,
        name TEXT,
        score INT DEFAULT 0 NOT NULL
    """)
    sql.create_table("tasks", """
        TASK_ID INTEGER PRIMARY KEY AUTOINCREMENT, 
        title TEXT,
        max_score INT NOT NULL
    """)

    executor.start_polling(dp)