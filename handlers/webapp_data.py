import json
import logging

from aiogram import F, Router
from aiogram.types import Message

from services.memory import ConversationMemory
from services.recipe_generator import RecipeGenerationError, RecipeGenerator
from services.storage import RecipeRepository
from utils.recipes import publish_recipes

router = Router(name="webapp-data")
LOGGER = logging.getLogger(__name__)


def _compose_prompt(payload: dict) -> str:
    ingredients = payload.get("ingredients", "").strip()
    diet = payload.get("diet", "").strip()
    goal = payload.get("goal", "").strip()
    extras = payload.get("extras", [])

    details = []
    if diet:
        details.append(f"Предпочтения: {diet}")
    if goal:
        details.append(f"Цель/контекст: {goal}")
    if extras:
        details.append("Дополнительно: " + ", ".join(extras))

    if details:
        return f"{ingredients}\n" + "\n".join(details)
    return ingredients


@router.message(F.web_app_data)
async def handle_web_app_payload(
    message: Message,
    recipe_generator: RecipeGenerator,
    conversation_memory: ConversationMemory,
    recipe_repository: RecipeRepository,
) -> None:
    raw = message.web_app_data.data

    try:
        payload = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        LOGGER.warning("Invalid web app payload: %s", raw)
        await message.answer("⚠️ Не удалось прочитать данные из мини-приложения.")
        return

    ingredients = payload.get("ingredients", "").strip()
    if not ingredients:
        await message.answer("⚠️ Мини-приложение не прислало список продуктов. Попробуй снова.")
        return

    user_prompt = _compose_prompt(payload)
    chat_id = message.chat.id
    history = conversation_memory.format_history(chat_id)

    await message.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        recipes = await recipe_generator.from_text(user_prompt, history or None)
    except RecipeGenerationError:
        LOGGER.exception("Failed to handle miniapp payload")
        await message.answer("⚠️ Не получилось обработать данные мини-приложения. Повтори попытку.")
        return

    if not recipes:
        await message.answer("⚠️ Модель не вернула рецепты. Попробуй отправить форму ещё раз.")
        return

    conversation_memory.add(chat_id, "user", f"[MiniApp] {user_prompt}")
    await publish_recipes(
        message.answer,
        chat_id,
        recipes,
        source="Mini App",
        recipe_repository=recipe_repository,
        conversation_memory=conversation_memory,
    )

