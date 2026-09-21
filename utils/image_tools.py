from __future__ import annotations

import base64
import io

from aiogram import Bot
from PIL import Image


async def telephoto_to_base64(bot: Bot, file_id: str) -> str:
    """
    Download a Telegram photo, normalize it to JPEG and return a data URI.
    """

    telegram_file = await bot.get_file(file_id)
    buffer = io.BytesIO()
    await bot.download_file(telegram_file.file_path, buffer)
    buffer.seek(0)

    image = Image.open(buffer)
    processed = io.BytesIO()
    image.convert("RGB").save(processed, format="JPEG", quality=90)
    processed.seek(0)

    encoded = base64.b64encode(processed.read()).decode("utf-8")
    return f"data:image/jpeg;base64,{encoded}"

