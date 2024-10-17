import logging

import aiosqlite
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
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
from handlers.states import TASK_RESPONSE

logger = logging.getLogger("task")


async def get_available_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with aiosqlite.connect(settings.DB_NAME) as conn:
        tasks = await user.get_uncompleted_tasks(conn, user_id=update.effective_user.id)

    if not tasks:
        await update.effective_message.reply_text("Больше нет доступных заданий!")
        return

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
    """Пользователь отправляет ответ на задание"""

    if "current_task_id" not in context.user_data:
        return await update.effective_message.reply_text("Не выбрано активное задание")

    task_id = int(context.user_data["current_task_id"])
    user_id = update.effective_user.id

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
        reply_markup=InlineKeyboardMarkup.from_column(
            [
                *[
                    InlineKeyboardButton(text=f"{value} ⭐️", callback_data=f"task_rate:{user_id}:{task_id}:{value}")
                    for value in range(1, task_max_score + 1)
                ],
                InlineKeyboardButton(text="Отклонить", callback_data=f"task_rate:{user_id}:{task_id}:-1"),
            ]
        ),
    )

    logger.info(f"Sent <Task {task_id}> response from {user_id} to {curator_id}")

    return ConversationHandler.END


async def task_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка оценки задания от куратора"""

    query = update.callback_query
    await query.answer()

    _, user_id, task_id, score = query.data.split(":")
    bot = update.get_bot()

    user_notify_text = None

    async with aiosqlite.connect(settings.DB_NAME) as conn:
        _, task_title, _ = await task.get_task_info(conn, task_id=task_id)

        if score == -1:
            # Куратор отклонил задание
            await task.delete_task_response(conn, task_id=task_id, user_id=user_id)
            user_notify_text = f"Ответ на задание '{task_title}' отклонен куратором"
        else:
            # Куратор выставил ответ на задание
            await task.rate_task_response(conn, task_id=task_id, user_id=user_id, score=score)
            user_notify_text = f"Вам начисленно {score} баллов за ответ на задание '{task_title}'!"

    await bot.send_message(chat_id=user_id, text=user_notify_text)
    await update.effective_message.edit_reply_markup()
    logger.info(
        f"<Curator {update.effective_user.id}> rate <Task {task_id}> response from <User {user_id}> for {score}"
    )


HANDLERS = [
    MessageHandler(filters.Text("Выбрать задание"), get_available_tasks),
    ConversationHandler(
        entry_points=[CallbackQueryHandler(set_task, pattern="^set_task:")],
        states={
            TASK_RESPONSE: [MessageHandler(filters.PHOTO, process_task_response)],
        },
        fallbacks=[CommandHandler("cancel", cmd_cancel)],
    ),
    CallbackQueryHandler(task_rate, pattern="^task_rate:"),
]
