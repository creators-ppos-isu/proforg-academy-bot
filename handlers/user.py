import logging
import re

import aiosqlite
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
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
from db import curator, user
from handlers.command import cmd_cancel
from handlers.states import COURSE, FULL_NAME, SET_CURATOR

logger = logging.getLogger("user")


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    async with aiosqlite.connect(settings.DB_NAME) as conn:
        if await curator.is_user_curator(conn, user_id):
            await update.effective_message.reply_text("Приветствую тебя, куратор!")
            return ConversationHandler.END

        await update.effective_message.reply_html(messages.WELCOME)

        if not await user.is_user_exists(conn, user_id):
            await user.add_user(conn, user_id)
            logger.info(f"Added user {user_id}")

    await update.effective_message.reply_text("Введи свое имя и фамилию, чтобы мы точно начислили баллы именно тебе!")
    return FULL_NAME


async def process_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not re.match(r"^[а-яё]+ [а-яё ]+$", update.message.text, re.I):
        await update.message.reply_text("Полное имя может содержать только буквы русского алфавита или пробелы.")
        return FULL_NAME

    async with aiosqlite.connect(settings.DB_NAME) as conn:
        await user.set_user_full_name(conn, user_id=update.effective_user.id, full_name=update.message.text)
        logger.info(f"Set full name {update.effective_user.id}: {update.message.text}")

    await update.effective_message.reply_text(
        f"Приятно познакомиться, {update.message.text}😉\n\nТеперь, выбери свой курс",
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
        await user.set_user_course(conn, user_id=update.effective_user.id, course=int(course))

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
        "Для выбора задания используй кнопку внизу 👇",
        reply_markup=ReplyKeyboardMarkup.from_column(["Выбрать задание"], resize_keyboard=True),
    )

    return ConversationHandler.END


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
]
