from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from keyboards.inline import rating_keyboard
from services.rating_service import rate_recommendation, get_recommendation_rating_stats
from services.recommendation_service import get_recommendation_by_id
from config import CATEGORIES
from db import get_session


async def show_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    rec_id = int(query.data.replace("showrate_", ""))

    async for session in get_session():
        rec = await get_recommendation_by_id(session, rec_id)
        if not rec:
            await query.edit_message_text("Рекомендация не найдена.")
            return

        cat_name = CATEGORIES.get(rec.category, rec.category)
        text = (
            f"⭐ *Оцени рекомендацию*\n\n"
            f"📂 *{cat_name}*\n"
            f"📖 {rec.title}\n\n"
            f"Выбери оценку:"
        )
        await query.edit_message_text(text, reply_markup=rating_keyboard(rec_id), parse_mode="Markdown")


async def rate_recommendation_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    parts = data.split("_")
    rec_id = int(parts[1])
    score = int(parts[2])
    user_id = query.from_user.id

    async for session in get_session():
        try:
            await rate_recommendation(session, user_id, rec_id, score)
            stats = await get_recommendation_rating_stats(session, rec_id)
            rec = await get_recommendation_by_id(session, rec_id)

            cat_name = CATEGORIES.get(rec.category, rec.category) if rec else ""
            text = (
                f"✅ Оценка сохранена: {score}/5\n\n"
                f"📂 *{cat_name}*\n"
                f"📖 *{rec.title}*\n"
                f"⭐ Средняя оценка: {stats['avg_score']} (голосов: {stats['count']})\n\n"
                f"🙏 Спасибо за твой голос!"
            )
            await query.edit_message_text(text, parse_mode="Markdown")
        except Exception as e:
            await query.edit_message_text(f"❌ Ошибка: {e}")
