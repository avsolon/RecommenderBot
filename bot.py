from telegram.ext import Updater, CommandHandler, ConversationHandler, CallbackQueryHandler, MessageHandler, Filters
from config import TOKEN, PROXY
from db import init_db

from handlers.start import start
from handlers.help import help_handler
from handlers.add import add, add_category_chosen, title_received, comment_received, visibility_chosen, \
    CATEGORY, TITLE, COMMENT, VISIBILITY
from handlers.random import random_handler
from handlers.find import find, find_category_chosen, mode_chosen, keyword_entered, \
    CHOOSE_CATEGORY, CHOOSE_MODE, ENTER_KEYWORD
from handlers.list import list_handler
from handlers.edit import edit, select_record, select_field, new_value, category_chosen_edit, \
    SELECT_RECORD, SELECT_FIELD, ENTER_NEW_VALUE
from handlers.delete import delete, confirm_delete, DELETE_CONFIRM
from handlers.public import public_start, public_category_chosen, public_paginate, public_view_rec, \
    public_back_to_categories, public_back_to_list, public_toggle, \
    CATEGORY_BROWSE, VIEW_REC
from handlers.top import top_start, top_category_chosen, top_back, CATEGORY_TOP
from handlers.rate import show_rating, rate_recommendation_handler


def main():
    import asyncio
    asyncio.run(init_db())
    print("✅ Database initialized")

    request_kwargs = {}
    if PROXY:
        request_kwargs['proxy_url'] = PROXY

    updater = Updater(TOKEN, request_kwargs=request_kwargs)
    dp = updater.dispatcher

    def _run_async(fn):
        def wrapper(update, context):
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(fn(update, context))
            except RuntimeError:
                asyncio.run(fn(update, context))
        return wrapper

    def _run_async_conv(fn):
        def wrapper(update, context):
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                coro = fn(update, context)
                if hasattr(coro, '__await__'):
                    return asyncio.run(coro)
                return coro
            except RuntimeError:
                if hasattr(update, '__await__'):
                    return asyncio.run(fn(update, context))
                return fn(update, context)
        return wrapper

    # ============ ADD ============
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
            VISIBILITY: [
                CallbackQueryHandler(visibility_chosen, pattern="^vis_")
            ]
        },
        fallbacks=[]
    )

    # ============ DELETE ============
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

    # ============ FIND ============
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
            ]
        },
        fallbacks=[]
    )

    # ============ EDIT ============
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
            ]
        },
        fallbacks=[]
    )

    # ============ PUBLIC BROWSE ============
    public_conv = ConversationHandler(
        entry_points=[
            CommandHandler('public', public_start),
            MessageHandler(Filters.regex("^🌍 Общие$"), public_start)
        ],
        states={
            CATEGORY_BROWSE: [
                CallbackQueryHandler(public_category_chosen, pattern="^cat_"),
                CallbackQueryHandler(public_back_to_categories, pattern="^pub_back_cat$"),
            ],
            VIEW_REC: [
                CallbackQueryHandler(public_paginate, pattern="^pubrec_page_"),
                CallbackQueryHandler(public_view_rec, pattern="^pubrec_\\d+$"),
                CallbackQueryHandler(public_back_to_categories, pattern="^pub_back_cat$"),
                CallbackQueryHandler(public_back_to_list, pattern="^pub_back_list$"),
                CallbackQueryHandler(public_toggle, pattern="^toggle_"),
                CallbackQueryHandler(show_rating, pattern="^showrate_"),
                CallbackQueryHandler(rate_recommendation_handler, pattern="^rate_"),
            ]
        },
        fallbacks=[]
    )

    # ============ TOP ============
    top_conv = ConversationHandler(
        entry_points=[
            CommandHandler('top', top_start),
            MessageHandler(Filters.regex("^🏆 Топ$"), top_start)
        ],
        states={
            CATEGORY_TOP: [
                CallbackQueryHandler(top_category_chosen, pattern="^cat_"),
                CallbackQueryHandler(top_back, pattern="^top_back$"),
            ]
        },
        fallbacks=[]
    )

    # ============ REGISTER HANDLERS ============
    dp.add_handler(CommandHandler('start', start))

    dp.add_handler(add_conv)
    dp.add_handler(del_conv)
    dp.add_handler(find_conv)
    dp.add_handler(edit_conv)
    dp.add_handler(public_conv)
    dp.add_handler(top_conv)

    # Simple commands
    dp.add_handler(CommandHandler('random', random_handler))
    dp.add_handler(CommandHandler('list', list_handler))
    dp.add_handler(CommandHandler('help', help_handler))

    # Message handlers for menu buttons
    dp.add_handler(MessageHandler(Filters.regex("^🎲 Случайная$"), random_handler))
    dp.add_handler(MessageHandler(Filters.regex("^📋 Список$"), list_handler))
    dp.add_handler(MessageHandler(Filters.regex("^❓ Помощь$"), help_handler))

    # Toggle and Rating callbacks (catch-all for actions outside conversations)
    dp.add_handler(CallbackQueryHandler(public_toggle, pattern="^toggle_"))
    dp.add_handler(CallbackQueryHandler(show_rating, pattern="^showrate_"))
    dp.add_handler(CallbackQueryHandler(rate_recommendation_handler, pattern="^rate_\\d+_\\d+$"))

    print("🤖 Bot started! Press Ctrl+C to stop.")
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
