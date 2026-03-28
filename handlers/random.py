from telegram import Update
from telegram.ext import CallbackContext
from services.recommendation_service import get_random


def random_handler(update: Update, context: CallbackContext):
    rec = get_random(update.message.from_user.id)
    if not rec:
        update.message.reply_text("Нет рекомендаций")
        return
    update.message.reply_text(f"🎲 {rec[0]} | {rec[1]}\n{rec[2]}")