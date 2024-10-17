#!/usr/bin/env python3
import argparse
import asyncio
import logging
from importlib import import_module

import aiosqlite
from telegram.ext import Application

import settings

logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger("bot")
logging.basicConfig(
    level=logging.INFO,
    format=" %(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

APPS = (
    "user",
    "task",
    # "feedback",
)


async def migrate():
    migration_dir = settings.BASE_DIR / "db" / "migrations"
    async with aiosqlite.connect(settings.DB_NAME) as db:
        with open(migration_dir / "init.sql", "r") as migration:
            await db.executescript(migration.read())
        await db.commit()


def run_bot():
    application = Application.builder().token(settings.BOT_TOKEN).build()

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
