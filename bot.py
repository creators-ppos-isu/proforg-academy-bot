#!/usr/bin/env python3
import argparse
import asyncio
import logging
import re

import aiosqlite
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

import messages
import settings
from db import curator, user

logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.basicConfig(
    level=logging.INFO,
    format=" %(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
# bot = Bot(token=settings.BOT_TOKEN)
# dp = Dispatcher(bot, storage=MemoryStorage())
# sql = sqlmanager.Sql()


FULL_NAME, COURSE, SET_CURATOR, FEEDBACK = range(4)


# async def get_tasks(message: types.Message):
#     all_task = sql.select(f"SELECT TASK_ID FROM task", 0)
#     completed_tasks = sql.select(f"SELECT task_id FROM users_tasks WHERE user_id={message.from_user.id}", 0)
#     available_tasks = [task[0] for task in all_task if task not in completed_tasks]

#     user_id = message.from_user.id
#     buttons = []
#     for task in available_tasks:
#         title = sql.select(f"SELECT title FROM task WHERE TASK_ID={task}")[0]
#         buttons.append({"text": title, "callback": f"settask;{user_id};{task};0"})
#     return buttons


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text("Отменено!")
    return ConversationHandler.END


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    if user_id in settings.CURATORS.keys():
        return await update.effective_message.reply_text("Приветствую тебя, куратор!")

    await update.effective_message.reply_html(messages.WELCOME)

    async with aiosqlite.connect(settings.DB_NAME) as conn:
        if not await user.is_user_exists(conn, user_id):
            await user.add_user(conn, user_id)
            logger.info(f"Added user {user_id}")

    await update.effective_message.reply_text("Введи свое имя и фамилию, чтобы мы точно начислили баллы именно тебе!")
    return FULL_NAME


async def process_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not re.match(r"^[а-я]+ [а-я ]+$", update.message.text, re.I):
        await update.message.reply_text("Полное имя может содержать только буквы русского алфавита или пробелы.")
        return FULL_NAME

    async with aiosqlite.connect(settings.DB_NAME) as conn:
        await user.set_user_full_name(conn, user_id=update.effective_user.id, full_name=update.message.text)
        logger.info(f"Set full name {update.effective_user.id}: {update.message.text}")

    await update.effective_message.reply_text(
        "Приятно, познакомиться😉\n\nТеперь, выбери свой курс",
        reply_markup=InlineKeyboardMarkup.from_column(
            [InlineKeyboardButton(text=f"{course}", callback_data=f"set_course:{course}") for course in range(1, 6)]
        ),
    )

    return COURSE


async def process_course(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    _, course = query.data.split(":")

    await update.effective_message.edit_text(f"Ты выбрал курс: {course}")

    async with aiosqlite.connect(settings.DB_NAME) as conn:
        curators_info = await curator.get_all_curators(conn)
    
    logger.info(f"Set course {update.effective_user.id}: {course}")

    await update.effective_message.reply_text(
        "Теперь, выбери своего куратора:",
        reply_markup=InlineKeyboardMarkup.from_column(
            [
                InlineKeyboardButton(text=f"{first_name} {last_name}", callback_data=f"set_curator:{curator_id}")
                for curator_id, first_name, last_name in curators_info
            ]
        ),
    )
    return SET_CURATOR


async def process_curator(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    _, curator_id = query.data.split(":")

    async with aiosqlite.connect(settings.DB_NAME) as conn:
        await user.set_user_curator(conn, user_id=update.effective_user.id, curator_id=curator_id)
        _, first_name, last_name = await curator.get_curator(conn, curator_id=curator_id)

    logger.info(f"Set curator {update.effective_user.id}: {curator_id}")

    await update.effective_message.edit_text(f"Ты выбрал куратора: {first_name} {last_name}")
    await update.effective_message.reply_text(
        "Для выбора задания используй кнопку внизу 👇", reply_markup=ReplyKeyboardMarkup.from_column(["Выбрать задание"])
    )

    return ConversationHandler.END


# @dp.message_handler(state=Form.feedback)
# async def resend_feedback(message: types.Message, state: FSMContext):
#     await message.answer("Спасибо за обратную связь 😉")
#     uid, name, curator_id = sql.select(
#         f"SELECT user_id, name, curator_id FROM user WHERE user_id={message.from_user.id}"
#     )
#     await bot.send_message(curator_id, f"Отзыв от {name} UID: {uid}:\n\n{message.text}")
#     logger.info(f"Feedback from {uid} {name}")
#     await state.finish()


# @dp.message_handler(
#     lambda message: message.from_user.id == settings.OWNER,
#     commands=["atask", "dtask", "feedback"],
# )
# async def do_request(message: types.Message):
#     if "atask" in message.text:
#         title, max_score = message.text.split(" ", 1)[1].split(";")
#         max_score = int(max_score)
#         sql.update(f"INSERT INTO task(title, max_score) VALUES('{title}', {max_score})")
#         tid = sql.select(f"SELECT TASK_ID FROM task WHERE title='{title}'")[0]
#         await message.answer(f"Добавленно задание: {title}\nTID: {tid}")
#         logger.info(f"Add task: {title} TID: {tid}")

#     if "dtask" in message.text:
#         task_id = int(message.text.split(" ", 1)[1])
#         if sql.select(f"SELECT * FROM task WHERE TASK_ID={task_id}") is None:
#             await message.answer("Задачи с таким ID не сущетвует!")
#             return
#         try:
#             sql.update(f"DELETE FROM task WHERE TASK_ID={task_id}")
#             logger.info(f"Delete task: {task_id}")
#             await message.answer(f"Задание {task_id} удалено")
#         except Exception as e:
#             await message.answer(f"Не удалось удалить задание: {e}")

#     if "feedback" in message.text:
#         user = sql.select(f"SELECT id FROM user", 0)
#         buttons = [{"text": "Отправить отзыв", "callback": "send_feedback"}]
#         for user in user:
#             try:
#                 await bot.send_message(
#                     user[0],
#                     "Лекция закончилась! Нажми на кнопку ниже, если хочешь оставить комментарий 👇",
#                     reply_markup=modules.markup.inline(buttons),
#                 )
#             except Exception as e:
#                 logger.error(f"UID: {user[0]} message: {e}")
#         logger.warning("Send feedback to each user")


async def choose_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with aiosqlite.connect(settings.DB_NAME) as conn:
        tasks = await user.get_uncompleted_tasks(conn, user_id=update.effective_user.id)

    if not tasks:
        return await update.effective_message.answer("Больше нет доступных заданий!")

    # if sql.select(f"SELECT curator_id FROM user WHERE user_id={message.from_user.id}")[0] is None:
    #     await message.answer(
    #         "Чтобы выбрать задание, для начала нужно выбрать куратора, сделать это можно с помощью команды /start"
    #     )
    #     return

    await update.effective_message.reply_text("Выбери задание", reply_markup=InlineKeyboardMarkup.from_column(
        [
            InlineKeyboardButton(text=task_title, callback_data=f"set_task:{task_id}")
            for task_id, task_title in tasks
        ]
    ))


# @dp.message_handler(content_types=["photo"])
# async def verify_task(message: types.Message):
#     if sql.select(f"SELECT current_task FROM user WHERE user_id={message.from_user.id}")[0] is None:
#         await message.answer("Нужно выбрать задание нажав на кнопку под полем ввода сообщений!")
#         return

#     user_id, task_id, curator_id = sql.select(
#         f"SELECT user_id, current_task, curator_id FROM user WHERE user_id={message.from_user.id}"
#     )
#     task_title = sql.select(f"SELECT title FROM task WHERE TASK_ID={task_id}")[0]
#     task_score = sql.select(f"SELECT score FROM users_tasks WHERE task_id={task_id} AND user_id={user_id}")

#     if not task_score:
#         sql.update(f"INSERT INTO users_tasks(user_id, task_id, score) VALUES({user_id}, {task_id}, 0)")

#     elif task_score[0] == 0:
#         await message.answer(messages.ERR_ANSWER_ALREADY_SENT)
#         return

#     await message.answer("Отправляю фотографию куратору...")

#     max_score = int(sql.select(f"SELECT max_score FROM task WHERE TASK_ID={task_id}")[0])
#     buttons = [
#         {"text": "⭐️" * value, "callback": f"rate;{user_id};{task_id};{value}"} for value in range(1, max_score + 1)
#     ]
#     buttons.append({"text": "Отклонить задание", "callback": f"reject;{user_id};{task_id};0"})

#     await bot.send_photo(
#         curator_id,
#         message.photo[-1].file_id,
#         caption=f"Ответ по заданию {task_title}\n\nID пользователя: {user_id}\nID задания: {task_id}",
#         reply_markup=modules.markup.inline(buttons),
#     )
#     logger.info(f"Send photo: {message.from_user.id} -> {curator_id}; Task ID: {task_id}")


# @dp.callback_query_handler()
# async def callback_check(callback: types.CallbackQuery):
#     await bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id)

#     if callback.data.startswith("send_feedback"):
#         await callback.message.answer("Напиши свой отзыв о лекции в ответ на это сообщение")
#         await Form.feedback.set()

#     action, user_id, task_id, score = callback.data.split(";")
#     user_id, task_id, score = int(user_id), int(task_id), int(score)

#     task_title = sql.select(f"SELECT title FROM task WHERE TASK_ID={task_id}")[0]
#     tg_id = user_id

#     if action == "rate":
#         sql.update(f"UPDATE users_tasks SET score={score} WHERE task_id={task_id} AND user_id={user_id}")
#         sql.update(f"UPDATE user SET score=score+{score}, current_task=NULL WHERE user_id={user_id}")
#         logger.info(f"Rate UID: {user_id} TID: {task_id} SCORE: {score}")

#         await bot.send_message(tg_id, f"Вам начисленно {score} баллов!")

#     if action == "reject":
#         sql.update(f"DELETE FROM users_tasks WHERE task_id={task_id} AND user_id={user_id} LIMIT 1")
#         # sql.update(f"DELETE FROM {user_table} WHERE task={task_id}")
#         logger.info(f"Reject UID: {user_id} TID: {task_id} SCORE: {score}")

#         await bot.send_message(tg_id, f"Задание {task_title} отклоненно куратором")

#     if action == "settask":
#         sql.update(f"UPDATE user SET current_task={task_id} WHERE user_id={user_id}")

#         await callback.message.answer(f"Вы выбрали {task_title} в качестве активного задания!")


HANDLERS = [
    ConversationHandler(
        entry_points=[CommandHandler("start", cmd_start)],
        states={
            FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_full_name)],
            COURSE: [CallbackQueryHandler(process_course, pattern="^set_course:")],
            SET_CURATOR: [CallbackQueryHandler(process_curator, pattern="^set_curator:")],
        },
        fallbacks=[CommandHandler("cancel", cmd_cancel)],
    ),
    MessageHandler(filters.Text("Выбрать задание"), choose_task),
]


async def migrate():
    async with aiosqlite.connect(settings.DB_NAME) as db:
        await db.executescript(open(settings.BASE_DIR / "db" / "migrations" / "init.sql", "r").read())
        await db.commit()


def run_bot():
    application = Application.builder().token(settings.BOT_TOKEN).build()
    application.add_handlers(HANDLERS)
    application.run_polling()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["run", "migrate", "set-commands"])
    args = parser.parse_args()

    if args.action == "migrate":
        asyncio.run(migrate())
    else:
        run_bot()
