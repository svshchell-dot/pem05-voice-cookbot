import logging

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.state import default_state
from aiogram.types import Message

from services.recipe_generator import RecipeGenerationError, RecipeGenerator
from services.memory import ConversationMemory
from services.storage import RecipeRepository
from utils.recipes import publish_recipes

router = Router(name="text-recipe")
router.message.filter(StateFilter(default_state))
LOGGER = logging.getLogger(__name__)


async def process_text_request(
    message: Message,
    user_text: str,
    *,
    recipe_generator: RecipeGenerator,
    conversation_memory: ConversationMemory,
    recipe_repository: RecipeRepository,
    source_label: str = "Текстовый запрос",
) -> None:
    """Shared pipeline for any textual user request."""

    sanitized = (user_text or "").strip()
    if not sanitized:
        await message.answer("⚠️ Текст запроса пустой. Попробуй сформулировать иначе.")
        return

    chat_id = message.chat.id
    await message.bot.send_chat_action(chat_id=chat_id, action="typing")
    history = conversation_memory.format_history(chat_id)

    try:
        recipes = await recipe_generator.from_text(sanitized, history or None)
    except RecipeGenerationError:
        LOGGER.exception("Text recipe generation failed")
        await message.answer(
            "⚠️ Не удалось подготовить рецепты. Попробуй позже или переформулируй запрос."
        )
        return

    if not recipes:
        await message.answer("⚠️ Модель не прислала рецепты. Попробуй уточнить запрос.")
        return

    conversation_memory.add(chat_id, "user", sanitized)
    await publish_recipes(
        message.answer,
        chat_id,
        recipes,
        source=source_label,
        recipe_repository=recipe_repository,
        conversation_memory=conversation_memory,
    )


@router.message(F.text)
async def handle_text_recipe(
    message: Message,
    recipe_generator: RecipeGenerator,
    conversation_memory: ConversationMemory,
    recipe_repository: RecipeRepository,
) -> None:
    if not message.text or message.text.startswith("/"):
        return

    await process_text_request(
        message,
        message.text,
        recipe_generator=recipe_generator,
        conversation_memory=conversation_memory,
        recipe_repository=recipe_repository,
        source_label="Текстовый запрос",
    )

