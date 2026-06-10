from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, ConversationHandler

from services.recommendation_service import get_user_recommendations, delete_recommendation
from db import get_session

DELETE_CONFIRM = 1


def delete(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    import asyncio
    async def _list():
        async for session in get_session():
            records = await get_user_recommendations(session, user_id)

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

    asyncio.run(_list())
    return DELETE_CONFIRM


def confirm_delete(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    data = query.data

    if data.startswith("del_"):
        rec_id = int(data.replace("del_", ""))
        context.user_data['delete_id'] = rec_id

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Да, удалить", callback_data="yes"),
                InlineKeyboardButton("❌ Нет", callback_data="no")
            ]
        ])
        query.edit_message_text(
            "⚠️ *Точно удалить эту запись?*",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        return DELETE_CONFIRM

    elif data == "yes":
        rec_id = context.user_data.get('delete_id')
        user_id = query.from_user.id

        import asyncio
        async def _delete():
            async for session in get_session():
                success = await delete_recommendation(session, rec_id, user_id)
                if success:
                    await query.edit_message_text("✅ Запись удалена.")
                else:
                    await query.edit_message_text("❌ Не удалось удалить запись.")

        asyncio.run(_delete())
        return ConversationHandler.END

    else:
        query.edit_message_text("🚫 Удаление отменено.")
        return ConversationHandler.END
