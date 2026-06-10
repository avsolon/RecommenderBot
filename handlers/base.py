from telegram import Update


async def send_or_edit_message(update: Update, text: str, reply_markup=None, parse_mode=None):
    if update.message and update.message.text:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    else:
        await update.effective_chat.send_message(text, reply_markup=reply_markup, parse_mode=parse_mode)
