#!/usr/bin/env python3
import argparse
import asyncio
import logging
from importlib import import_module

import aiosqlite
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
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
from db import task, user
from handlers.command import cmd_cancel

logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger("bot")
logging.basicConfig(
    level=logging.INFO,
    format=" %(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

APPS = ("user",)
TASK_RESPONSE = 20


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
#     commands=["feedback"],
# )
# async def do_request(message: types.Message):
# user = sql.select(f"SELECT id FROM user", 0)
# buttons = [{"text": "Отправить отзыв", "callback": "send_feedback"}]
# for user in user:
#     try:
#         await bot.send_message(
#             user[0],
#             "Лекция закончилась! Нажми на кнопку ниже, если хочешь оставить комментарий 👇",
#             reply_markup=modules.markup.inline(buttons),
#         )
#     except Exception as e:
#         logger.error(f"UID: {user[0]} message: {e}")
# logger.warning("Send feedback to each user")


async def get_available_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with aiosqlite.connect(settings.DB_NAME) as conn:
        tasks = await user.get_uncompleted_tasks(conn, user_id=update.effective_user.id)

    if not tasks:
        return await update.effective_message.answer("Больше нет доступных заданий!")

    await update.effective_message.reply_text(
        "Выбери задание",
        reply_markup=InlineKeyboardMarkup.from_column(
            [
                InlineKeyboardButton(text=task_title, callback_data=f"set_task:{task_id}")
                for task_id, task_title in tasks
            ]
        ),
    )


async def set_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    _, task_id = query.data.split(":")

    async with aiosqlite.connect(settings.DB_NAME) as conn:
        _, task_title, _ = await task.get_task_info(conn, task_id=task_id)

    context.user_data["current_task_id"] = task_id
    await update.effective_message.edit_text(
        f"Вы выбрали '{task_title}' в качестве активного задания! Отправьте фото в качестве ответа."
    )

    return TASK_RESPONSE


async def process_task_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if "current_task_id" not in context.user_data:
        return await update.effective_message.reply_text("Не выбрано активное задание")

    task_id = int(context.user_data["current_task_id"])
    user_id = update.effective_message.id

    async with aiosqlite.connect(settings.DB_NAME) as conn:
        if await task.is_task_response_exists(conn, task_id=task_id, user_id=update.effective_user.id):
            return await update.effective_message.reply_text(messages.ERR_TASK_RESPONSE_ALREADY_SENT)

        await task.add_task_response(conn, task_id=task_id, user_id=update.effective_user.id)
        _, _, _, _, curator_id = await user.get_user_info(conn, user_id=user_id)
        _, task_title, task_max_score = await task.get_task_info(conn, task_id=task_id)

    await update.effective_message.reply_text("Отправляю фотографию куратору...")

    await update.effective_message.copy(
        chat_id=curator_id,
        caption=f"Ответ по заданию {task_title}\n\nID пользователя: {user_id}\nID задания: {task_id}",
        reply_markup=InlineKeyboardMarkup.from_column([
            *[
                InlineKeyboardButton(text=f"{value} ⭐️", callback_data=f"task_rate:{user_id}:{task_id}:{value}")
                for value in range(1, task_max_score + 1)
            ],
            InlineKeyboardButton(text="Отклонить", callback_data=f"task_rate:{user_id}:{task_id}:-1")
        ])
    )

    logger.info(f"Sent <Task {task_id}> response from {user_id} to {curator_id}")


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


HANDLERS = [
    MessageHandler(filters.Text("Выбрать задание"), get_available_tasks),
    ConversationHandler(
        entry_points=[CallbackQueryHandler(set_task, pattern="^set_task:")],
        states={
            TASK_RESPONSE: [MessageHandler(filters.PHOTO, process_task_response)],
        },
        fallbacks=[CommandHandler("cancel", cmd_cancel)],
    ),
]


async def migrate():
    async with aiosqlite.connect(settings.DB_NAME) as db:
        await db.executescript(open(settings.BASE_DIR / "db" / "migrations" / "init.sql", "r").read())
        await db.commit()


def run_bot():
    application = Application.builder().token(settings.BOT_TOKEN).build()
    application.add_handlers(HANDLERS)

    for app_name in APPS:
        application.add_handlers(import_module(f"handlers.{app_name}").HANDLERS)

    application.run_polling()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["run", "migrate", "set-commands"])
    args = parser.parse_args()

    if args.action == "migrate":
        asyncio.run(migrate())
    else:
        run_bot()
