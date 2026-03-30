from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, ConversationHandler

from keyboards.inline import categories_keyboard
from services.recommendation_service import get_user_recommendations, update_recommendation


SELECT_RECORD, SELECT_FIELD, ENTER_NEW_VALUE = range(3)

def edit(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    records = get_user_recommendations(user_id)

    if not records:
        update.message.reply_text("Нет записей")
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton(f"{r[0]} | {r[2]}", callback_data=f"edit_{r[0]}")]
        for r in records
    ]
    update.message.reply_text(
        "Выбери запись для редактирования:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECT_RECORD

def select_record(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    rec_id = int(query.data.replace("edit_", ""))
    context.user_data['edit_id'] = rec_id

    keyboard = [
        [InlineKeyboardButton("Категория", callback_data="field_category")],
        [InlineKeyboardButton("Название", callback_data="field_title")],
        [InlineKeyboardButton("Комментарий", callback_data="field_comment")]
    ]
    query.edit_message_text(
        "Что изменить?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECT_FIELD

def select_field(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    field = query.data.replace("field_", "")
    context.user_data['field'] = field

    if field == "category":
        query.edit_message_text(
            "Выбери новую категорию:",
            reply_markup=categories_keyboard()
        )
    else:
        query.edit_message_text("Введите новое значение:")
    return ENTER_NEW_VALUE

def category_chosen_edit(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    category = query.data.replace("cat_", "")
    rec_id = context.user_data.get('edit_id')
    user_id = query.from_user.id
    update_recommendation(user_id, rec_id, "category", category)
    query.edit_message_text("Категория обновлена ✅")
    return ConversationHandler.END

def new_value(update: Update, context: CallbackContext):
    field = context.user_data.get('field')
    rec_id = context.user_data.get('edit_id')
    user_id = update.message.from_user.id
    value = update.message.text
    update_recommendation(user_id, rec_id, field, value)
    update.message.reply_text("Обновлено ✅")
    return ConversationHandler.END