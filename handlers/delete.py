from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, ConversationHandler, CallbackQueryHandler
from services.recommendation_service import delete_by_id

DELETE_CONFIRM = 1


def delete(update: Update, context: CallbackContext):
    rec_id = int(context.args[0])
    context.user_data['delete_id'] = rec_id

    keyboard = [[InlineKeyboardButton("Да", callback_data="yes"),
                 InlineKeyboardButton("Нет", callback_data="no")]]
    update.message.reply_text("Удалить?", reply_markup=InlineKeyboardMarkup(keyboard))
    return DELETE_CONFIRM


def confirm_delete(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    if query.data == "yes":
        delete_by_id(query.from_user.id, context.user_data['delete_id'])
        query.edit_message_text("Удалено")
    else:
        query.edit_message_text("Отмена")

    return ConversationHandler.END
