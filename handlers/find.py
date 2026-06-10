from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from handlers.base import send_or_edit_message
from keyboards.inline import categories_keyboard, search_menu_keyboard
from services.recommendation_service import search_recommendations, get_random_recommendation
from config import CATEGORIES
from db import get_session

CHOOSE_CATEGORY, CHOOSE_MODE, ENTER_KEYWORD = range(3)


async def find(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_or_edit_message(
        update,
        "🔍 *Поиск*\n\nВыбери категорию:",
        reply_markup=categories_keyboard()
    )
    return CHOOSE_CATEGORY


async def find_category_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    key = query.data.replace("cat_", "")
    context.user_data['category'] = key

    await query.edit_message_text(
        "🎯 Выбери режим:",
        reply_markup=search_menu_keyboard()
    )
    return CHOOSE_MODE


async def mode_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    mode = query.data
    context.user_data['mode'] = mode

    if mode == "random":
        user_id = query.from_user.id
        category = context.user_data.get('category')

        async for session in get_session():
            rec = await get_random_recommendation(session, user_id=user_id, category=category, public_only=False)
            if not rec:
                await query.edit_message_text("😕 Нет рекомендаций в этой категории.")
                return ConversationHandler.END

            cat_name = CATEGORIES.get(rec.category, rec.category)
            text = f"🎲 *{cat_name}* | *{rec.title}*\n{rec.comment or ''}"
            await query.edit_message_text(text, parse_mode="Markdown")

        return ConversationHandler.END

    await query.edit_message_text("✏️ Введите ключевое слово для поиска:")
    return ENTER_KEYWORD


async def keyword_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyword = update.message.text
    user_id = update.message.from_user.id
    category = context.user_data.get('category')

    async for session in get_session():
        results = await search_recommendations(session, user_id=user_id, keyword=keyword, category=category)

        if not results:
            await update.message.reply_text("😕 Ничего не найдено.")
            return ConversationHandler.END

        text = f"🔍 Найдено: {len(results)}\n\n"
        for r in results:
            cat_name = CATEGORIES.get(r.category, r.category)
            text += f"📌 *{r.title}*\n📂 {cat_name}\n💬 {r.comment or '—'}\n\n"

        await update.message.reply_text(text, parse_mode="Markdown")

    return ConversationHandler.END
