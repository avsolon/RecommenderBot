from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

def get_main_keyboard():
    keyboard = [
        ['➕ Добавить', '🔍 Найти'],
        ['📋 Мои рекомендации', '🎲 Случайная'],
        ['✏️ Редактировать', '❌ Удалить'],
        ['❓ Помощь']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_categories_keyboard(include_all=True):
    categories = ['Фильмы', 'Книги', 'Сериалы', 'Музыка', 'Еда/Рестораны', 'Товары', 'Другое']
    buttons = []
    for cat in categories:
        buttons.append([InlineKeyboardButton(cat, callback_data=f"cat_{cat}")])
    if include_all:
        buttons.append([InlineKeyboardButton("Все категории", callback_data="cat_all")])
    return InlineKeyboardMarkup(buttons)

def get_pagination_keyboard(data_type, page, total_pages, rec_id=None):
    """data_type: 'list' or 'search', page: current page, total_pages: total pages"""
    keyboard = []
    if page > 0:
        keyboard.append(InlineKeyboardButton("◀️ Назад", callback_data=f"{data_type}_prev_{page}"))
    if page < total_pages - 1:
        keyboard.append(InlineKeyboardButton("Вперёд ▶️", callback_data=f"{data_type}_next_{page}"))
    if rec_id:
        # For edit/delete selection inline
        keyboard.append(InlineKeyboardButton("Выбрать", callback_data=f"select_{rec_id}"))
    return InlineKeyboardMarkup([keyboard]) if keyboard else None

def format_recommendation(rec):
    return f"📌 <b>{rec[2]}</b> ({rec[1]})\n💬 {rec[3] or 'Без комментария'}\n🕒 {rec[4]}\nID: <code>{rec[0]}</code>"