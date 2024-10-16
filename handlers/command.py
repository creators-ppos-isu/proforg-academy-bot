from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text("Отменено!")
    return ConversationHandler.END
