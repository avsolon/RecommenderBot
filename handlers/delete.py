from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler

from services.recommendation_service import get_user_recommendations, delete_recommendation, get_or_create_user
from db import get_session

DELETE_CONFIRM = 1


async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async for session in get_session():
        user = await get_or_create_user(session, update.message.from_user.id)
        records = await get_user_recommendations(session, user.id)

        if not records:
            await update.message.reply_text("📭 У тебя нет записей для удаления.")
            return ConversationHandler.END

        keyboard = [
            [InlineKeyboardButton(f"🗑 {r.title[:30]}", callback_data=f"del_{r.id}")]
            for r in records
        ]

        await update.message.reply_text(
            "🗑 *Выбери запись для удаления:*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    return DELETE_CONFIRM


async def confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("del_"):
        rec_id = int(data.replace("del_", ""))
        context.user_data['delete_id'] = rec_id

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Да, удалить", callback_data="yes"),
                InlineKeyboardButton("❌ Нет", callback_data="no"),
            ]
        ])
        await query.edit_message_text(
            "⚠️ *Точно удалить эту запись?*",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        return DELETE_CONFIRM

    elif data == "yes":
        rec_id = context.user_data.get('delete_id')

        async for session in get_session():
            user = await get_or_create_user(session, query.from_user.id)
            success = await delete_recommendation(session, rec_id, user.id)
            if success:
                await query.edit_message_text("✅ Запись удалена.")
            else:
                await query.edit_message_text("❌ Не удалось удалить запись.")

        return ConversationHandler.END

    else:
        await query.edit_message_text("🚫 Удаление отменено.")
        return ConversationHandler.END
