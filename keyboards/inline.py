from telegram import InlineKeyboardMarkup, InlineKeyboardButton

# CATEGORIES = ["Фильмы", "Книги", "Сериалы", "Музыка", "Еда", "Товары", "Другое"]

CATEGORIES = {
    "films": "Фильмы",
    "books": "Книги",
    "series": "Сериалы",
    "music": "Музыка",
    "food": "Еда",
    "goods": "Товары",
    "other": "Другое"
}

# def categories_keyboard():
#     return InlineKeyboardMarkup([
#         [InlineKeyboardButton(cat, callback_data=cat)] for cat in CATEGORIES
#     ])

# def categories_keyboard():
#     return InlineKeyboardMarkup([
#         [InlineKeyboardButton(cat, callback_data=f"cat_{cat}")] for cat in CATEGORIES
#     ])

def categories_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(name, callback_data=f"cat_{key}")]
        for key, name in CATEGORIES.items()
    ])

def search_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎲 Случайная", callback_data="random")],
        [InlineKeyboardButton("🔍 Поиск по слову", callback_data="search")]
    ])