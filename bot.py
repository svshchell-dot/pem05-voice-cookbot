import asyncio
import logging
from pathlib import Path
from typing import Optional

from aiohttp import web
from aiogram import BaseMiddleware, Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config import get_settings
from handlers import (
    dish_identify,
    favorites,
    image_ingredients,
    interactive_flow,
    start,
    text_recipe,
    voice_recipe,
    webapp_data,
)
from services.interactive_chef import InteractiveChef
from services.memory import ConversationMemory
from services.openai_client import OpenAIClient
from services.recipe_generator import RecipeGenerator
from services.storage import RecipeRepository

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
LOGGER = logging.getLogger("bot")


class DependencyMiddleware(BaseMiddleware):
    """Inject shared services into handler kwargs."""

    def __init__(self, **dependencies) -> None:
        super().__init__()
        self._dependencies = dependencies

    async def __call__(self, handler, event, data):
        data.update(self._dependencies)
        return await handler(event, data)


async def set_commands(bot: Bot) -> None:
    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="help", description="Как работает ассистент"),
        BotCommand(command="chef", description="Интерактивный сбор требований"),
        BotCommand(command="miniapp", description="Открыть мини-приложение"),
    ]
    await bot.set_my_commands(commands)


async def start_miniapp_server(
    directory: Path,
    host: str,
    port: int,
) -> Optional[web.AppRunner]:
    if not directory.exists():
        LOGGER.warning("Miniapp directory %s не найден, сервер не запущен", directory)
        return None

    app = web.Application()

    async def index(_: web.Request):
        return web.FileResponse(directory / "index.html")

    app.router.add_get("/", index)
    app.router.add_static("/static/", path=directory, name="miniapp-static")

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=host, port=port)
    await site.start()
    LOGGER.info("Miniapp доступен по адресу http://%s:%s", host, port)
    return runner


async def main() -> None:
    settings = get_settings()
    bot = Bot(
        token=settings.telegram_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    openai_client = OpenAIClient(
        api_key=settings.openai_api_key,
        text_model=settings.openai_text_model,
        vision_model=settings.openai_vision_model,
        transcribe_model=settings.openai_transcribe_model,
    )
    recipe_generator = RecipeGenerator(openai_client)
    conversation_memory = ConversationMemory(limit=12)
    interactive_chef = InteractiveChef(openai_client, max_questions=3)
    recipe_repository = RecipeRepository(settings.database_path)
    await recipe_repository.init()

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dependency_middleware = DependencyMiddleware(
        recipe_generator=recipe_generator,
        conversation_memory=conversation_memory,
        interactive_chef=interactive_chef,
        recipe_repository=recipe_repository,
        openai_client=openai_client,
    )

    for router in (
        start.router,
        text_recipe.router,
        voice_recipe.router,
        image_ingredients.router,
        dish_identify.router,
        interactive_flow.router,
        webapp_data.router,
        favorites.router,
    ):
        router.message.middleware(dependency_middleware)
        router.callback_query.middleware(dependency_middleware)
        dp.include_router(router)

    await set_commands(bot)
    web_runner = await start_miniapp_server(
        settings.miniapp_path,
        settings.webapp_host,
        settings.webapp_port,
    )

    try:
        LOGGER.info("Bot started. Waiting for updates...")
        await dp.start_polling(bot)
    finally:
        if web_runner:
            LOGGER.info("Останавливаем miniapp сервер...")
            await web_runner.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        LOGGER.info("Bot stopped.")

