import logging
from typing import Dict, List

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from services.interactive_chef import InteractiveChef, InteractiveResponse
from services.memory import ConversationMemory
from services.storage import RecipeRepository
from utils.recipes import publish_recipes

router = Router(name="interactive-flow")
LOGGER = logging.getLogger(__name__)


class InteractiveStates(StatesGroup):
    collecting = State()


INITIAL_PROMPT = (
    "Запускаем режим уточняющих вопросов. Я буду задавать до трёх вопросов, "
    "чтобы понять детали, а затем подготовлю рецепт. Поехали!"
)


async def _proceed_dialog(
    message: Message,
    state: FSMContext,
    interactive_chef: InteractiveChef,
    recipe_repository: RecipeRepository,
    conversation_memory: ConversationMemory,
) -> None:
    data = await state.get_data()
    history: List[Dict[str, str]] = data.get("history", [])
    asked = data.get("questions", 0)
    remaining = interactive_chef.max_questions - asked

    try:
        response: InteractiveResponse = await interactive_chef.next_step(history, remaining)
    except Exception:  # pragma: no cover - network failure
        LOGGER.exception("Interactive flow failed")
        await message.answer("⚠️ Ошибка диалога с ассистентом. Попробуем позже.")
        await state.clear()
        return

    if response.kind == "ask" and remaining > 0:
        history.append({"role": "assistant", "content": response.content})
        await state.update_data(history=history, questions=asked + 1)
        await message.answer(response.content)
        return

    recipes = response.recipes or []
    if not recipes:
        await message.answer("⚠️ Не удалось сформировать рецепт. Попробуй запустить /chef заново.")
        await state.clear()
        return

    chat_id = message.chat.id
    await publish_recipes(
        message.answer,
        chat_id,
        recipes,
        source="Интерактивный режим",
        recipe_repository=recipe_repository,
        conversation_memory=conversation_memory,
    )
    await state.clear()


@router.message(Command("chef"))
async def start_interactive_dialog(
    message: Message,
    state: FSMContext,
    interactive_chef: InteractiveChef,
    recipe_repository: RecipeRepository,
    conversation_memory: ConversationMemory,
) -> None:
    await state.clear()
    await state.set_state(InteractiveStates.collecting)
    await state.update_data(history=[{"role": "assistant", "content": INITIAL_PROMPT}], questions=0)
    await message.answer(INITIAL_PROMPT)
    await _proceed_dialog(message, state, interactive_chef, recipe_repository, conversation_memory)


@router.message(InteractiveStates.collecting)
async def continue_interactive_dialog(
    message: Message,
    state: FSMContext,
    interactive_chef: InteractiveChef,
    recipe_repository: RecipeRepository,
    conversation_memory: ConversationMemory,
) -> None:
    if not message.text:
        await message.answer("Пожалуйста, ответь текстом, чтобы я понял детали блюда.")
        return

    data = await state.get_data()
    history: List[Dict[str, str]] = data.get("history", [])
    history.append({"role": "user", "content": message.text})
    await state.update_data(history=history)

    conversation_memory.add(message.chat.id, "user", f"[chef] {message.text}")
    await _proceed_dialog(message, state, interactive_chef, recipe_repository, conversation_memory)

