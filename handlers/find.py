from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler, CallbackQueryHandler, MessageHandler, Filters

from handlers.base import send_or_edit_message
from keyboards.inline import categories_keyboard, search_menu_keyboard
from services.recommendation_service import search_recommendations, get_random

CHOOSE_CATEGORY, CHOOSE_MODE, ENTER_KEYWORD = range(3)


def find(update, context):
    send_or_edit_message(
        update,
        "Выбери категорию:",
        reply_markup=categories_keyboard()
    )
    return CHOOSE_CATEGORY

def find_category_chosen(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    # получаем "cat_films"
    key = query.data.replace("cat_", "")

    context.user_data['category'] = key

    query.edit_message_text(
        "Выбери режим:",
        reply_markup=search_menu_keyboard()
    )

    return CHOOSE_MODE

def mode_chosen(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    mode = query.data  # "random" или "search"
    context.user_data['mode'] = mode

    if mode == "random":
        user_id = query.from_user.id
        category = context.user_data.get('category')

        rec = get_random(user_id, category)

        if not rec:
            query.edit_message_text("Нет рекомендаций")
            return ConversationHandler.END

        text = f"🎲 {rec[0]} | {rec[1]}\n{rec[2]}"
        query.edit_message_text(text)

        return ConversationHandler.END
    # поиск
    query.edit_message_text("Введите ключевое слово:")
    return ENTER_KEYWORD

def keyword_entered(update: Update, context: CallbackContext):
    keyword = update.message.text
    user_id = update.message.from_user.id
    category = context.user_data.get('category')

    results = search_recommendations(user_id, keyword, category)

    if not results:
        update.message.reply_text("Ничего не найдено")
        return ConversationHandler.END

    text = "\n\n".join([
        f"🎯 {r[2]}\n{r[3]}"
        for r in results
    ])

    update.message.reply_text(text)
    return ConversationHandler.END