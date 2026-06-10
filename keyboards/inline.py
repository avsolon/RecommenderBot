from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from config import CATEGORIES


def categories_keyboard():
    keys = list(CATEGORIES.keys())
    mid = (len(keys) + 1) // 2
    keyboard = []
    for i in range(mid):
        row = [InlineKeyboardButton(CATEGORIES[keys[i]], callback_data=f"cat_{keys[i]}")]
        j = i + mid
        if j < len(keys):
            row.append(InlineKeyboardButton(CATEGORIES[keys[j]], callback_data=f"cat_{keys[j]}"))
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)


def categories_with_all_keyboard():
    keyboard = [
        [InlineKeyboardButton("📂 Все категории", callback_data="cat_ALL")]
    ]
    keys = list(CATEGORIES.keys())
    for key in keys:
        keyboard.append([InlineKeyboardButton(CATEGORIES[key], callback_data=f"cat_{key}")])
    return InlineKeyboardMarkup(keyboard)


def search_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎲 Случайная", callback_data="random")],
        [InlineKeyboardButton("🔍 Поиск по слову", callback_data="search")]
    ])


def rating_keyboard(rec_id: int):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⭐", callback_data=f"rate_{rec_id}_1"),
            InlineKeyboardButton("⭐⭐", callback_data=f"rate_{rec_id}_2"),
            InlineKeyboardButton("⭐⭐⭐", callback_data=f"rate_{rec_id}_3"),
            InlineKeyboardButton("⭐⭐⭐⭐", callback_data=f"rate_{rec_id}_4"),
            InlineKeyboardButton("⭐⭐⭐⭐⭐", callback_data=f"rate_{rec_id}_5"),
        ]
    ])


def rec_actions_keyboard(rec_id: int, is_public: bool, is_owner: bool):
    buttons = []
    buttons.append([InlineKeyboardButton("⭐ Оценить", callback_data=f"showrate_{rec_id}")])
    if is_owner:
        status = "🔓 Сделать публичной" if not is_public else "🔒 Сделать приватной"
        buttons.append([InlineKeyboardButton(status, callback_data=f"toggle_{rec_id}")])
    return InlineKeyboardMarkup(buttons)


def pagination_keyboard(items, prefix: str, page: int, has_next: bool, category: str = None):
    keyboard = []
    for item in items:
        label = f"{item['rec'].title[:30]}"
        keyboard.append([InlineKeyboardButton(label, callback_data=f"{prefix}_{item['rec'].id}")])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀ Назад", callback_data=f"{prefix}_page_{page-1}_{category or 'ALL'}"))
    if has_next:
        nav.append(InlineKeyboardButton("Вперёд ▶", callback_data=f"{prefix}_page_{page+1}_{category or 'ALL'}"))
    if nav:
        keyboard.append(nav)

    return InlineKeyboardMarkup(keyboard)
