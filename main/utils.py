import os
import openai
import aiofiles
from openai import OpenAI
from aiogram import Bot
from aiogram.types import Message
from settings.config import settings

openai_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY.get_secret_value())


async def download_voice(bot: Bot, message: Message) -> str:
    file = await bot.get_file(message.voice.file_id)
    file_path = f"downloads/{file.file_id}.ogg"

    os.makedirs("downloads", exist_ok=True)
    await bot.download_file(file.file_path, file_path)

    return file_path


async def transcribe_audio(file_path: str) -> str:
    with open(file_path, "rb") as audio_file:
        response = await openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    return response.text


async def get_assistant_response(prompt: str, language: str) -> str:
    instructions = {
        "English": "You are a personal assistant. Please answer on questions on English.",
        "Russian": "Вы персональный помощник. Пожалуйста, отвечайте на вопросы на русском языке."
    }

    assistant = await openai_client.beta.assistants.create(
        name="Clever guy",
        instructions=instructions.get(language, "You are a personal assistant. "
                                                "Please answer on questions on English."),        tools=[{"type": "code_interpreter"}],
        model="gpt-4o",
    )

    thread = await openai_client.beta.threads.create()

    await openai_client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=f"Answer a question: {prompt}"
    )

    run = await openai_client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id
    )

    while True:
        run_status = await openai_client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
        if run_status.status == "completed":
            break

    messages = await openai_client.beta.threads.messages.list(
        thread_id=thread.id
    )

    return messages.data[0].content[0].text.value


async def text_to_speech(text: str, language: str) -> str:
    voice = {
        "English": "alloy",
        "Russian": "onyx"
    }.get(language, "alloy")

    response = await openai_client.audio.speech.create(
        model="tts-1",
        input=text,
        voice=voice
    )

    file_path = "output.mp3"
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(response.content)

    return file_path
