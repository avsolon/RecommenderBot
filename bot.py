from telegram.ext import Updater, CommandHandler, ConversationHandler, CallbackQueryHandler, MessageHandler, Filters
from config import TOKEN, PROXY
from db import init_db

from handlers.start import start
from handlers.help import help_handler
from handlers.add import add, add_category_chosen, title_received, comment_received, CATEGORY, TITLE, COMMENT
from handlers.random import random_handler
from handlers.find import find, find_category_chosen, mode_chosen, keyword_entered, CHOOSE_CATEGORY, CHOOSE_MODE, ENTER_KEYWORD
from handlers.list import list_handler
from handlers.edit import edit, select_record, select_field, new_value, category_chosen_edit, \
    SELECT_RECORD, SELECT_FIELD, ENTER_NEW_VALUE
from handlers.delete import delete, confirm_delete, DELETE_CONFIRM


def main():
    init_db()

    request_kwargs = {}
    if PROXY:
        request_kwargs['proxy_url'] = PROXY

    updater = Updater(TOKEN, request_kwargs=request_kwargs)
    dp = updater.dispatcher

    add_conv = ConversationHandler(
        entry_points=[
            CommandHandler('add', add),
            MessageHandler(Filters.regex("^➕ Добавить$"), add)
        ],
        states={
            CATEGORY: [
                CallbackQueryHandler(add_category_chosen, pattern="^cat_")
            ],
            TITLE: [
                MessageHandler(Filters.text & ~Filters.command, title_received)
            ],
            COMMENT: [
                MessageHandler(Filters.text & ~Filters.command, comment_received)
            ],
        },
        fallbacks=[]
    )

    del_conv = ConversationHandler(
        entry_points=[
            CommandHandler('del', delete),
            MessageHandler(Filters.regex("^🗑 Удалить$"), delete)
        ],
        states={
            DELETE_CONFIRM: [
                CallbackQueryHandler(confirm_delete)
            ]
        },
        fallbacks=[]
    )

    find_conv = ConversationHandler(
        entry_points=[
            CommandHandler('find', find),
            MessageHandler(Filters.regex("^🔍 Найти$"), find)
        ],
        states={
            CHOOSE_CATEGORY: [
                CallbackQueryHandler(find_category_chosen, pattern="^cat_")
            ],
            CHOOSE_MODE: [
                CallbackQueryHandler(mode_chosen, pattern="^(random|search)$")
            ],
            ENTER_KEYWORD: [
                MessageHandler(Filters.text & ~Filters.command, keyword_entered)
            ],
        },
        fallbacks=[]
    )

    edit_conv = ConversationHandler(
        entry_points=[
            CommandHandler('edit', edit),
            MessageHandler(Filters.regex("^✏️ Редактировать$"), edit)
        ],
        states={
            SELECT_RECORD: [
                CallbackQueryHandler(select_record, pattern="^edit_")
            ],
            SELECT_FIELD: [
                CallbackQueryHandler(select_field, pattern="^field_")
            ],
            ENTER_NEW_VALUE: [
                MessageHandler(Filters.text & ~Filters.command, new_value),
                CallbackQueryHandler(category_chosen_edit, pattern="^cat_")
            ],
        },
        fallbacks=[]
    )

    dp.add_handler(CommandHandler('start', start))

    dp.add_handler(add_conv)
    dp.add_handler(del_conv)
    dp.add_handler(find_conv)
    dp.add_handler(edit_conv)

    dp.add_handler(CommandHandler('random', random_handler))
    dp.add_handler(CommandHandler('list', list_handler))
    dp.add_handler(CommandHandler('help', help_handler))

    dp.add_handler(MessageHandler(Filters.regex("^🎲 Случайная$"), random_handler))
    dp.add_handler(MessageHandler(Filters.regex("^📋 Список$"), list_handler))
    MessageHandler(Filters.regex("^✏️ Редактировать$"), edit)
    dp.add_handler(MessageHandler(Filters.regex("^🗑 Удалить$"), delete))
    dp.add_handler(MessageHandler(Filters.regex("^❓ Помощь$"), help_handler))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()