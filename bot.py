from telegram.ext import Updater, CommandHandler, ConversationHandler, CallbackQueryHandler, MessageHandler, Filters
from config import TOKEN, PROXY
from db import init_db

from handlers.start import start
from handlers.add import add, category_chosen, title_received, comment_received, CATEGORY, TITLE, COMMENT
from handlers.random import random_handler
from handlers.delete import delete, confirm_delete, DELETE_CONFIRM


def main():
    init_db()

    request_kwargs = {}
    if PROXY:
        request_kwargs['proxy_url'] = PROXY

    updater = Updater(TOKEN, request_kwargs=request_kwargs)
    dp = updater.dispatcher

    add_conv = ConversationHandler(
        entry_points=[CommandHandler('add', add)],
        states={
            CATEGORY: [CallbackQueryHandler(category_chosen)],
            TITLE: [MessageHandler(Filters.text & ~Filters.command, title_received)],
            COMMENT: [MessageHandler(Filters.text & ~Filters.command, comment_received)],
        },
        fallbacks=[]
    )

    del_conv = ConversationHandler(
        entry_points=[CommandHandler('del', delete)],
        states={DELETE_CONFIRM: [CallbackQueryHandler(confirm_delete)]},
        fallbacks=[]
    )

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(add_conv)
    dp.add_handler(del_conv)
    dp.add_handler(CommandHandler('random', random_handler))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()