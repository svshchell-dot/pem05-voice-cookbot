from __future__ import annotations

import io

from aiogram import Bot


async def download_voice(bot: Bot, file_id: str) -> bytes:
    """Download Telegram voice message into raw bytes."""

    telegram_file = await bot.get_file(file_id)
    buffer = io.BytesIO()
    await bot.download_file(telegram_file.file_path, buffer)
    return buffer.getvalue()

