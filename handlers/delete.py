from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, ConversationHandler, CallbackQueryHandler
from services.recommendation_service import delete_by_id, get_user_recommendations

DELETE_CONFIRM = 1


def delete(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    records = get_user_recommendations(user_id)

    if not records:
        update.message.reply_text("У тебя нет записей")
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton(f"{r[0]} | {r[2]}", callback_data=f"del_{r[0]}")]
        for r in records
    ]

    update.message.reply_text(
        "Выбери запись для удаления:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return DELETE_CONFIRM


def confirm_delete(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    data = query.data

    if data.startswith("del_"):
        rec_id = int(data.replace("del_", ""))
        context.user_data['delete_id'] = rec_id

        keyboard = [
            [
                InlineKeyboardButton("Да", callback_data="yes"),
                InlineKeyboardButton("Нет", callback_data="no")
            ]
        ]

        query.edit_message_text(
            "Удалить запись?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return DELETE_CONFIRM

    elif data == "yes":
        delete_by_id(query.from_user.id, context.user_data['delete_id'])
        query.edit_message_text("Удалено")
        return ConversationHandler.END

    else:
        query.edit_message_text("Отмена")
        return ConversationHandler.END
