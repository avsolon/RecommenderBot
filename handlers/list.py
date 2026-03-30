from telegram import Update
from telegram.ext import CallbackContext
from services.recommendation_service import get_user_recommendations


def list_handler(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    results = get_user_recommendations(user_id)

    if not results:
        update.message.reply_text("У тебя пока нет рекомендаций")
        return

    text = ""

    for r in results:
        text += f"📌 ID: {r[0]}\n"
        text += f"📂 {r[1]}\n"
        text += f"📖 {r[2]}\n"
        if r[3]:
            text += f"💬 {r[3]}\n"
        text += "\n"

    update.message.reply_text(text)