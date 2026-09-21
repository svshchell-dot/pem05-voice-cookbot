import logging

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.state import default_state
from aiogram.types import Message

from services.memory import ConversationMemory
from services.openai_client import OpenAIClient, OpenAIClientError
from services.recipe_generator import RecipeGenerator
from services.storage import RecipeRepository
from utils.audio import download_voice

from .text_recipe import process_text_request

router = Router(name="voice-recipe")
router.message.filter(StateFilter(default_state))
LOGGER = logging.getLogger(__name__)


@router.message(F.voice)
async def handle_voice_recipe(
    message: Message,
    openai_client: OpenAIClient,
    recipe_generator: RecipeGenerator,
    conversation_memory: ConversationMemory,
    recipe_repository: RecipeRepository,
) -> None:
    if not message.voice:
        return

    chat_id = message.chat.id
    await message.bot.send_chat_action(chat_id=chat_id, action="record_voice")

    try:
        voice_bytes = await download_voice(message.bot, message.voice.file_id)
    except Exception:  # pragma: no cover - telegram network failure
        LOGGER.exception("Voice download failed")
        await message.answer("⚠️ Не удалось скачать голосовое сообщение. Попробуй ещё раз.")
        return

    filename = f"{message.voice.file_unique_id}.ogg"

    try:
        transcript = await openai_client.transcribe_audio(voice_bytes, filename)
    except OpenAIClientError:
        LOGGER.exception("Voice transcription failed")
        await message.answer("⚠️ Не получилось распознать голос. Запиши сообщение ещё раз.")
        return

    if not transcript.strip():
        await message.answer(
            "⚠️ Не удалось распознать текст в голосовом сообщении. Попробуй ещё раз."
        )
        return

    await process_text_request(
        message,
        transcript,
        recipe_generator=recipe_generator,
        conversation_memory=conversation_memory,
        recipe_repository=recipe_repository,
        source_label="Голосовой запрос",
    )

