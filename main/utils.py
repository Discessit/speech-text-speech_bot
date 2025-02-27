import os
import uuid
import openai
import aiofiles
from openai import OpenAI
from aiogram import Bot
from aiogram.types import Message
from settings.config import settings

openai_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY.get_secret_value())


def assistant_manager():

    assistant_id = None

    async def ensure_assistant_exists(language: str):
        nonlocal assistant_id

        if assistant_id:
            try:
                await openai_client.beta.assistants.retrieve(assistant_id)
                return assistant_id
            except openai.NotFoundError:
                assistant_id = None

        if not assistant_id:
            instructions = {
                "English": "You are a personal assistant. Please answer questions in English.",
                "Russian": "Вы персональный помощник. Пожалуйста, отвечайте на вопросы на русском языке."
            }.get(language, "You are a personal assistant. Please answer questions in English.")

            assistant = await openai_client.beta.assistants.create(
                name="Clever guy",
                instructions=instructions,
                model="gpt-4-turbo",
            )
            assistant_id = assistant.id

        return assistant_id

    return ensure_assistant_exists


ensure_assistant_exists = assistant_manager()


async def download_voice(bot: Bot, message: Message) -> str:
    file = await bot.get_file(message.voice.file_id)
    unique_id = uuid.uuid4()

    downloads_dir = os.path.join(os.path.dirname(__file__), "..", "data", "downloads")
    os.makedirs(downloads_dir, exist_ok=True)

    file_path = os.path.join(downloads_dir, f"{unique_id}.ogg")

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
    assistant_id = await ensure_assistant_exists(language)

    thread = await openai_client.beta.threads.create()

    await openai_client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=f"Answer a question: {prompt}"
    )

    run = await openai_client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant_id
    )

    if run.status == "completed":
        messages = await openai_client.beta.threads.messages.list(
            thread_id=thread.id
        )
        return messages.data[0].content[0].text.value
    else:
        raise Exception(f"Run did not complete successfully. Status: {run.status}")


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

    audio_responses_dir = os.path.join(os.path.dirname(__file__), "..", "data", "audio_responses")
    os.makedirs(audio_responses_dir, exist_ok=True)

    unique_id = uuid.uuid4()
    file_path = os.path.join(audio_responses_dir, f"output_{unique_id}.mp3")

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(response.content)

    return file_path
