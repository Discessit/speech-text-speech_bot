import logging
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message
from aiogram import F
from aiogram.client.default import DefaultBotProperties
from settings.config import settings
from handlers import process_voice

bot_token = settings.BOT_TOKEN.get_secret_value()

logging.basicConfig(level=logging.INFO)

bot = Bot(
    token=bot_token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML))

dp = Dispatcher()

user_language = {}


@dp.message(Command('start'))
async def cmd_start(message: Message):
    await message.reply("Hello! Send me a voice message and I will convert it into text. "
                        "Use /language to choose your language.")


@dp.message(Command('language'))
async def cmd_language(message: Message):
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="English")],
            [types.KeyboardButton(text="Russian")],
        ],
        resize_keyboard=True
    )
    await message.reply("Please choose your language:", reply_markup=keyboard)


@dp.message(F.text.in_(["English", "Russian"]))
async def set_language(message: Message):
    user_id = message.from_user.id
    language = message.text
    user_language[user_id] = language
    await message.reply(f"Language set to {language}.", reply_markup=types.ReplyKeyboardRemove())


@dp.message(F.voice)
async def handle_voice(message: Message):
    user_id = message.from_user.id
    language = user_language.get(user_id, "English")
    await process_voice(bot, message, language)

if __name__ == '__main__':
    try:
        logging.info("OK")
        dp.run_polling(bot)
    except Exception as e:
        logging.error(f"Error: {e}")