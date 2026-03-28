from telegram import InlineKeyboardMarkup, InlineKeyboardButton

CATEGORIES = ["Фильмы", "Книги", "Сериалы", "Музыка", "Еда", "Товары", "Другое"]

def categories_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(cat, callback_data=cat)] for cat in CATEGORIES
    ])