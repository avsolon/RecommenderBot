from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from keyboards.inline import categories_keyboard
from services.recommendation_service import get_user_recommendations, update_recommendation, get_or_create_user
from config import CATEGORIES
from db import get_session

SELECT_RECORD, SELECT_FIELD, ENTER_NEW_VALUE = range(3)


async def edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async for session in get_session():
        user = await get_or_create_user(session, update.message.from_user.id)
        records = await get_user_recommendations(session, user.id)

        if not records:
            await update.message.reply_text("📭 Нет записей для редактирования.")
            return ConversationHandler.END

        keyboard = [
            [InlineKeyboardButton(f"✏️ {r.title[:30]}", callback_data=f"edit_{r.id}")]
            for r in records
        ]
        await update.message.reply_text(
            "✏️ *Выбери запись для редактирования:*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    return SELECT_RECORD


async def select_record(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    rec_id = int(query.data.replace("edit_", ""))
    context.user_data['edit_id'] = rec_id

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📂 Изменить категорию", callback_data="field_category")],
        [InlineKeyboardButton("📖 Изменить название", callback_data="field_title")],
        [InlineKeyboardButton("💬 Изменить комментарий", callback_data="field_comment")],
    ])
    await query.edit_message_text(
        "✏️ *Что изменить?*",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    return SELECT_FIELD


async def select_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    field = query.data.replace("field_", "")
    context.user_data['field'] = field

    if field == "category":
        await query.edit_message_text(
            "📂 *Выбери новую категорию:*",
            reply_markup=categories_keyboard()
        )
    else:
        await query.edit_message_text("✏️ Введите новое значение:")
    return ENTER_NEW_VALUE


async def category_chosen_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category = query.data.replace("cat_", "")
    rec_id = context.user_data.get('edit_id')

    async for session in get_session():
        user = await get_or_create_user(session, query.from_user.id)
        success = await update_recommendation(session, rec_id, user.id, "category", category)
        if success:
            cat_name = CATEGORIES.get(category, category)
            await query.edit_message_text(f"✅ Категория изменена на «{cat_name}».")
        else:
            await query.edit_message_text("❌ Ошибка при обновлении.")

    return ConversationHandler.END


async def new_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    field = context.user_data.get('field')
    rec_id = context.user_data.get('edit_id')
    value = update.message.text

    async for session in get_session():
        user = await get_or_create_user(session, update.message.from_user.id)
        success = await update_recommendation(session, rec_id, user.id, field, value)
        if success:
            field_names = {"title": "название", "comment": "комментарий"}
            fname = field_names.get(field, field)
            await update.message.reply_text(f"✅ {fname.capitalize()} обновлено!")
        else:
            await update.message.reply_text("❌ Ошибка при обновлении.")

    return ConversationHandler.END
