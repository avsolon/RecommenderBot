from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, ConversationHandler, CallbackQueryHandler, MessageHandler, Filters

from handlers.base import send_or_edit_message
from keyboards.inline import categories_keyboard
from services.recommendation_service import add_recommendation
from db import get_session


CATEGORY, TITLE, COMMENT, VISIBILITY = range(4)


def add(update, context):
    send_or_edit_message(
        update,
        "📂 Выберите категорию:",
        reply_markup=categories_keyboard()
    )
    return CATEGORY


def add_category_chosen(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    key = query.data.replace("cat_", "")
    context.user_data['category'] = key
    query.edit_message_text("✏️ Введите название:")
    return TITLE


def title_received(update: Update, context: CallbackContext):
    context.user_data['title'] = update.message.text
    update.message.reply_text("💬 Введите комментарий (или отправьте '-' если без комментария):")
    return COMMENT


def comment_received(update: Update, context: CallbackContext):
    text = update.message.text
    context.user_data['comment'] = "" if text == "-" else text

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🌍 Публичная", callback_data="vis_public"),
            InlineKeyboardButton("🔒 Приватная", callback_data="vis_private")
        ]
    ])
    update.message.reply_text(
        "👀 Сделать рекомендацию публичной?\n"
        "Публичные увидят все пользователи.",
        reply_markup=keyboard
    )
    return VISIBILITY


def visibility_chosen(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    is_public = query.data == "vis_public"
    user_id = query.from_user.id
    category = context.user_data['category']
    title = context.user_data['title']
    comment = context.user_data.get('comment', "")

    async def _save():
        async for session in get_session():
            await add_recommendation(session, user_id, category, title, comment, is_public=is_public)

    import asyncio
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_save())
    except RuntimeError:
        asyncio.run(_save())

    status = "🌍 Публичная" if is_public else "🔒 Приватная"
    query.edit_message_text(f"✅ Сохранено! ({status})")
    return ConversationHandler.END
