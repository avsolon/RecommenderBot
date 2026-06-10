from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler

from handlers.base import send_or_edit_message
from keyboards.inline import categories_with_all_keyboard
from services.recommendation_service import get_popular_recommendations
from config import CATEGORIES
from db import get_session

CATEGORY_TOP = range(1)


async def top_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_or_edit_message(
        update,
        "🏆 *Топ рекомендаций*\n\nВыбери категорию:",
        reply_markup=categories_with_all_keyboard()
    )
    return CATEGORY_TOP


async def top_category_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    key = query.data.replace("cat_", "")

    async for session in get_session():
        popular = await get_popular_recommendations(session, category=key, limit=10)

        if not popular:
            cat_name = CATEGORIES.get(key, "все") if key != "ALL" else "всех категориях"
            await query.edit_message_text(f"😕 В {cat_name} пока нет оценённых рекомендаций.")
            return CATEGORY_TOP

        cat_name = CATEGORIES.get(key, "Все") if key != "ALL" else "Все категории"
        text = f"🏆 *Топ рекомендаций — {cat_name}*\n\n"

        for i, item in enumerate(popular, 1):
            rec = item["rec"]
            avg_score = item["avg_score"]
            rating_count = item["rating_count"]
            author = rec.author.display_name if rec.author else "Неизвестно"
            stars = "⭐" * round(avg_score) + "☆" * (5 - round(avg_score))
            text += f"{i}. *{rec.title}* {stars} ({avg_score})\n"
            text += f"   👤 {author} · 📂 {CATEGORIES.get(rec.category, rec.category)}\n"
            text += f"   💬 {rec.comment or '—'}\n\n"

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 К категориям", callback_data="top_back")]
            ]),
            parse_mode="Markdown"
        )

    return CATEGORY_TOP


async def top_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🏆 *Топ рекомендаций*\n\nВыбери категорию:",
        reply_markup=categories_with_all_keyboard(),
        parse_mode="Markdown"
    )
    return CATEGORY_TOP
