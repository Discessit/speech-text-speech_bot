from aiogram import Bot
from aiogram.types import Message
from utils import download_voice, transcribe_audio, get_assistant_response, text_to_speech
from aiogram.types import FSInputFile


async def process_voice(bot: Bot, message: Message, language: str):
    file_path = await download_voice(bot, message)
    text = await transcribe_audio(file_path)
    response_text = await get_assistant_response(text, language)
    audio_path = await text_to_speech(response_text, language)

    await message.answer(f"You ask: {text}")
    voice_file = FSInputFile(audio_path)
    await message.answer_voice(voice=voice_file)