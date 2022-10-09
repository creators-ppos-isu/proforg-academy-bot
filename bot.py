import logging
from aiogram import Bot, Dispatcher, executor, types
import settings
import modules


log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
token = settings.D_TOKEN if settings.DEBUG else settings.R_TOKEN
bot = Bot(token=token)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.reply("Hi!\nI'm EchoBot!\nPowered by aiogram.")


@dp.message_handler(content_types=["photo"])
async def a(message: types.Message): 
    await message.answer('Перекидываем фото...')
    await bot.send_photo(596546865, message.photo[-1].file_id)
    log.info(f'Recieve photo: {message.from_user.id} -> 596546865')


if __name__ == '__main__':
    executor.start_polling(dp)