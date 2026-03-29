from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler, CallbackQueryHandler, MessageHandler, Filters
from keyboards.inline import categories_keyboard, search_menu_keyboard
from services.recommendation_service import search_recommendations, get_random

CHOOSE_CATEGORY, CHOOSE_MODE, ENTER_KEYWORD = range(3)


def find(update: Update, context: CallbackContext):
    update.message.reply_text("Выбери категорию:", reply_markup=categories_keyboard())
    return CHOOSE_CATEGORY


def find_category_chosen(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    context.user_data['category'] = query.data

    query.edit_message_text("Выбери режим:", reply_markup=search_menu_keyboard())
    return CHOOSE_MODE


def mode_chosen(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    if query.data == "random":
        rec = get_random(query.from_user.id)

        if not rec:
            query.edit_message_text("Нет рекомендаций")
            return ConversationHandler.END

        query.edit_message_text(f"🎲 {rec[0]} | {rec[1]}\n{rec[2]}")
        return ConversationHandler.END

    elif query.data == "search":
        query.edit_message_text("Введи ключевое слово:")
        return ENTER_KEYWORD


def keyword_entered(update: Update, context: CallbackContext):
    keyword = update.message.text
    category = context.user_data.get('category')

    results = search_recommendations(
        user_id=update.message.from_user.id,
        keyword=keyword,
        category=category
    )

    if not results:
        update.message.reply_text("Ничего не найдено")
        return ConversationHandler.END

    text = "\n".join([f"{r[0]} | {r[1]} | {r[2]}" for r in results[:10]])
    update.message.reply_text(text)

    return ConversationHandler.END