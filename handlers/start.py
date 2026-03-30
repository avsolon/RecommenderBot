from telegram import Update
from telegram.ext import CallbackContext

from keyboards.reply import main_menu_keyboard


def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Привет! Я твой Бот-Рекомендатор. Используй клавиатуру в Меню 👇",
        reply_markup=main_menu_keyboard()
    )