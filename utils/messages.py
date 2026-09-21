from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from services.recipes.schemas import RecipeData


def render_recipe(recipe: RecipeData) -> str:
    parts: list[str] = [f"🍽️ <b>{recipe.title}</b>"]
    if recipe.cook_time:
        parts.append(f"⏱ {recipe.cook_time}")
    parts.append("")

    if recipe.ingredients:
        parts.append("<b>Ингредиенты:</b>")
        parts.extend(f"• {item}" for item in recipe.ingredients)
        parts.append("")

    if recipe.steps:
        parts.append("<b>Шаги:</b>")
        for idx, step in enumerate(recipe.steps, start=1):
            parts.append(f"{idx}. {step}")
        parts.append("")

    if recipe.missing_items:
        parts.append("<b>Докупить:</b>")
        parts.extend(f"• {item}" for item in recipe.missing_items)
        parts.append("")

    if recipe.variations:
        parts.append("<b>Вариации:</b>")
        parts.extend(f"• {variant}" for variant in recipe.variations)
        parts.append("")

    if recipe.serving_tips:
        parts.append("<b>Советы по подаче:</b>")
        parts.extend(f"• {tip}" for tip in recipe.serving_tips)

    return "\n".join(part for part in parts if part)


def build_favorite_keyboard(recipe_id: int, is_favorite: bool) -> InlineKeyboardMarkup:
    label = "★ В избранном" if is_favorite else "☆ В избранное"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, callback_data=f"fav:{recipe_id}")]
        ]
    )

