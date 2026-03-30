from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler, CallbackQueryHandler, MessageHandler, Filters

from handlers.base import send_or_edit_message
from keyboards.inline import categories_keyboard
from services.recommendation_service import add_recommendation


CATEGORY, TITLE, COMMENT = range(3)

def add(update, context):
    send_or_edit_message(
        update,
        "Выберите категорию:",
        reply_markup=categories_keyboard()
    )
    return CATEGORY

def add_category_chosen(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    key = query.data.replace("cat_", "")
    context.user_data['category'] = key

    query.edit_message_text("Введите название:")
    return TITLE

def title_received(update: Update, context: CallbackContext):
    context.user_data['title'] = update.message.text
    update.message.reply_text("Введите комментарий:")
    return COMMENT


def comment_received(update: Update, context: CallbackContext):
    add_recommendation(update.message.from_user.id,
                       context.user_data['category'],
                       context.user_data['title'],
                       update.message.text)
    update.message.reply_text("Сохранено")
    return ConversationHandler.END
