from telegram import Update
from telegram.ext import ContextTypes

from services.recommendation_service import get_random_recommendation
from config import CATEGORIES
from db import get_session


async def random_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async for session in get_session():
        rec = await get_random_recommendation(session, public_only=False)
        if not rec:
            await update.message.reply_text(
                "😕 Нет рекомендаций.\n\n"
                "➕ Добавь первую с помощью кнопки «Добавить»!"
            )
            return

        cat_name = CATEGORIES.get(rec.category, rec.category)
        text = f"🎲 *{cat_name}*\n📖 *{rec.title}*"
        if rec.comment:
            text += f"\n💬 {rec.comment}"
        if rec.is_public:
            author = rec.author.display_name if rec.author else "Неизвестно"
            text += f"\n👤 {author} · 🌍 Публичная"
        await update.message.reply_text(text, parse_mode="Markdown")
