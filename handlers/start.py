from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

from config import get_settings

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    settings = get_settings()
    webapp_url = settings.webapp_url
    reply_markup = None

    if webapp_url:
        reply_markup = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(
                        text="🚀 Mini App",
                        web_app=WebAppInfo(url=webapp_url),
                    )
                ]
            ],
            resize_keyboard=True,
        )

    await message.answer(
        (
            "👩‍🍳 Привет! Я AI Cooking Assistant.\n\n"
            "Я умею:\n"
            "• превращать список продуктов в 3 подробных рецепта;\n"
            "• анализировать фото ингредиентов и подсказывать, что приготовить;\n"
            "• определять готовое блюдо на фото и давать рецепт с вариациями;\n"
            "• вести интерактивный диалог (/chef), задавать уточняющие вопросы и выдавать рецепт;\n"
            "• сохранять понравившееся блюдо по нажатию на ⭐ под каждым рецептом.\n\n"
            "Примеры:\n"
            "• «куриная грудка, брокколи, сливки, пармезан»;\n"
            "• фото содержимого холодильника;\n"
            "• фото готового блюда в ресторане.\n\n"
            "Просто напиши список продуктов или пришли фото. "
            "После фото выбери вариант обработки на кнопках ниже сообщения."
        ),
        reply_markup=reply_markup,
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        (
            "ℹ️ Быстрый гайд:\n"
            "1. Текст — пришли список продуктов, и я верну 3 структурированных рецепта.\n"
            "2. Фото ингредиентов — отправь снимок, затем выбери «Это ингредиенты».\n"
            "3. Фото готового блюда — отправь фото и нажми «Готовое блюдо».\n"
            "4. /chef — запусти режим уточняющих вопросов: я соберу требования и выдам рецепт.\n"
            "5. Жми на ⭐ под блюдом, чтобы сохранить его в локальную базу SQLite.\n\n"
            "Советы: добавляй уточнения (например, «хочу без глютена»), "
            "а перед запуском не забудь заполнить .env с токенами."
        )
    )


@router.message(Command("miniapp"))
async def cmd_miniapp(message: Message) -> None:
    settings = get_settings()
    if not settings.webapp_url:
        await message.answer(
            "WEBAPP_URL не настроен. Укажи публичный адрес мини-приложения в .env и перезапусти бота."
        )
        return

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть Mini App",
                    web_app=WebAppInfo(url=settings.webapp_url),
                )
            ]
        ]
    )
    await message.answer(
        "Mini App открывается внутри Telegram. Нажми кнопку, чтобы заполнить форму с продуктами.",
        reply_markup=markup,
    )

