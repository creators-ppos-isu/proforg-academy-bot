from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup


def inline(inline_buttons, markup_width=1):
    buttons = [InlineKeyboardButton(text=btn.get('text'),
                                            callback_data=btn.get('callback'),
                                            url=btn.get('url'))
                for btn in inline_buttons]
    return InlineKeyboardMarkup(row_width=markup_width).add(*buttons)


def reply(reply_buttons):
    return ReplyKeyboardMarkup(resize_keyboard=True).add(*reply_buttons)