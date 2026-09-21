from aiogram import F, Router
from aiogram.types import CallbackQuery

from services.storage import RecipeRepository
from utils.messages import build_favorite_keyboard

router = Router(name="favorites")


@router.callback_query(F.data.startswith("fav:"))
async def toggle_favorite(
    callback: CallbackQuery,
    recipe_repository: RecipeRepository,
) -> None:
    try:
        _, recipe_id_str = callback.data.split(":", maxsplit=1)
        recipe_id = int(recipe_id_str)
    except (ValueError, AttributeError):
        await callback.answer("Некорректный идентификатор рецепта", show_alert=True)
        return

    new_state = await recipe_repository.toggle_favorite(recipe_id)
    if new_state is None:
        await callback.answer("Рецепт не найден", show_alert=True)
        return

    markup = build_favorite_keyboard(recipe_id, new_state)
    await callback.message.edit_reply_markup(reply_markup=markup)
    await callback.answer("Добавлено в избранное" if new_state else "Удалено из избранного")

