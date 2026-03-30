from telegram import ReplyKeyboardMarkup

def main_menu_keyboard():
    keyboard = [
        ["➕ Добавить", "🔍 Найти"],
        ["🎲 Случайная", "📋 Список"],
        ["🗑 Удалить", "✏️ Редактировать"],
        ["❓ Помощь"]
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )