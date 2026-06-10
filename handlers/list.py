from telegram import Update
from telegram.ext import ContextTypes

from services.recommendation_service import get_user_recommendations, get_statistics, get_or_create_user
from config import CATEGORIES
from db import get_session


async def list_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async for session in get_session():
        user = await get_or_create_user(session, update.message.from_user.id)
        stats = await get_statistics(session, user.id)
        results = await get_user_recommendations(session, user.id, limit=50)

        if not results:
            await update.message.reply_text(
                "📭 У тебя пока нет рекомендаций.\n\n"
                "➕ Нажми «Добавить», чтобы создать первую!"
            )
            return

        text = (
            f"📊 *Твои рекомендации*\n"
            f"📈 Всего: {stats['total']} | 🌍 Публичных: {stats['public']} | 🔒 Приватных: {stats['private']}\n\n"
        )

        for r in results:
            cat_name = CATEGORIES.get(r.category, r.category)
            visibility = "🌍" if r.is_public else "🔒"
            text += f"{visibility} ID:{r.id} | *{r.title}*\n📂 {cat_name}"
            if r.comment:
                text += f"\n💬 {r.comment[:50]}{'...' if len(r.comment) > 50 else ''}"
            text += "\n\n"

        await update.message.reply_text(text, parse_mode="Markdown")
