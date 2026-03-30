def send_or_edit_message(update, text, reply_markup=None):

    if update.message:
        update.message.reply_text(
            text,
            reply_markup=reply_markup
        )
    else:
        query = update.callback_query
        query.answer()
        query.edit_message_text(
            text,
            reply_markup=reply_markup
        )