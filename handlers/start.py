from telegram import Update
from telegram.ext import CallbackContext

from keyboards.reply import main_menu_keyboard
from services.recommendation_service import get_or_create_user
from db import get_session


def start(update: Update, context: CallbackContext):
    user = update.effective_user
    async def _start():
        async for session in get_session():
            await get_or_create_user(
                session,
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name
            )
    import asyncio
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_start())
    except RuntimeError:
        asyncio.run(_start())

    update.message.reply_text(
        f"🎯 Привет, {user.first_name or 'друг'}!\n\n"
        f"Я — бот-рекомендатор. Храни фильмы, книги, музыку и делись с другими!\n\n"
        f"👇 Используй кнопки меню:",
        reply_markup=main_menu_keyboard()
    )
