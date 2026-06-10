from telegram import Update
from telegram.ext import ContextTypes

from keyboards.reply import main_menu_keyboard
from db import get_session
from services.recommendation_service import get_or_create_user


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    async for session in get_session():
        await get_or_create_user(
            session,
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name
        )

    await update.message.reply_text(
        f"🎯 Привет, {user.first_name or 'друг'}!\n\n"
        "Я — бот-рекомендатор. Храни фильмы, книги, музыку и делись с другими!\n\n"
        "👇 Используй кнопки меню:",
        reply_markup=main_menu_keyboard()
    )
