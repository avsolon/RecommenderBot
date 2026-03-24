import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, \
    ConversationHandler, ContextTypes
import config
import db
from handlers import (
    start, help_command, add_start, add_category, add_title, add_comment, add_cancel,
    find_start, find_category, find_mode, find_keyword, search_pagination,
    list_recommendations, random_recommendation, edit_start, edit_select,
    edit_field, edit_value, delete_start, delete_confirm, delete_final,
    handle_url, url_confirm, error_handler,
    CATEGORY, TITLE, COMMENT, EDIT_SELECT, EDIT_FIELD, EDIT_VALUE, DELETE_CONFIRM
)


def main():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    db.init_db()

    # Создаем приложение
    application = Application.builder().token(config.BOT_TOKEN).build()

    # Conversation для добавления
    add_conv = ConversationHandler(
        entry_points=[
            CommandHandler('add', add_start),
            MessageHandler(filters.Regex(r'^➕ Добавить$'), add_start),
            CallbackQueryHandler(url_confirm, pattern='url_yes')
        ],
        states={
            CATEGORY: [CallbackQueryHandler(add_category, pattern='cat_')],
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_title)],
            COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_comment)],
        },
        fallbacks=[CommandHandler('cancel', add_cancel), MessageHandler(filters.Regex('^Отмена$'), add_cancel)],
    )
    application.add_handler(add_conv)

    # Conversation для редактирования
    edit_conv = ConversationHandler(
        entry_points=[
            CommandHandler('edit', edit_start),
            MessageHandler(filters.Regex(r'^✏️ Редактировать$'), edit_start)
        ],
        states={
            EDIT_SELECT: [CallbackQueryHandler(edit_select, pattern='edit_')],
            EDIT_FIELD: [CallbackQueryHandler(edit_field, pattern='edit_field_')],
            EDIT_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_value)],
        },
        fallbacks=[CommandHandler('cancel', add_cancel), CallbackQueryHandler(edit_select, pattern='edit_cancel')],
    )
    application.add_handler(edit_conv)

    # Conversation для удаления
    del_conv = ConversationHandler(
        entry_points=[
            CommandHandler('del', delete_start),
            MessageHandler(filters.Regex(r'^❌ Удалить$'), delete_start)
        ],
        states={
            DELETE_CONFIRM: [
                CallbackQueryHandler(delete_confirm, pattern='del_'),
                CallbackQueryHandler(delete_final, pattern='del_yes'),
                CallbackQueryHandler(delete_final, pattern='del_no')
            ],
        },
        fallbacks=[CommandHandler('cancel', add_cancel), CallbackQueryHandler(delete_confirm, pattern='del_cancel')],
    )
    application.add_handler(del_conv)

    # Остальные команды
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('find', find_start))
    application.add_handler(CommandHandler('list', list_recommendations))
    application.add_handler(CommandHandler('random', random_recommendation))

    # Callback handlers
    application.add_handler(CallbackQueryHandler(find_category, pattern='cat_'))
    application.add_handler(CallbackQueryHandler(find_mode, pattern='find_'))
    application.add_handler(CallbackQueryHandler(search_pagination, pattern='search_'))

    # Message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, find_keyword))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))

    application.add_error_handler(error_handler)

    # Запуск бота
    application.run_polling()


if __name__ == '__main__':
    main()


# import logging
# import asyncio
# from telegram import Update
# from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
# from telegram.request import HTTPXRequest
# import config
# import db
# from handlers import (
#     start, help_command, add_start, add_category, add_title, add_comment, add_cancel,
#     find_start, find_category, find_mode, find_keyword, search_pagination,
#     list_recommendations, random_recommendation, edit_start, edit_select,
#     edit_field, edit_value, delete_start, delete_confirm, delete_final,
#     handle_url, url_confirm, error_handler,
#     CATEGORY, TITLE, COMMENT, EDIT_SELECT, EDIT_FIELD, EDIT_VALUE, DELETE_CONFIRM
# )
#
#
# def main():
#     logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
#     db.init_db()
#
#     # Настройка request с прокси
#     if config.PROXY_URL:
#         print(f"Используется прокси: {config.PROXY_URL}")
#         # Для версии 20.7 используем параметр proxy вместо proxy_url
#         request = HTTPXRequest(
#             connect_timeout=30.0,
#             read_timeout=30.0,
#             proxy=config.PROXY_URL  # socks5://127.0.0.1:1080
#         )
#     else:
#         request = HTTPXRequest(
#             connect_timeout=30.0,
#             read_timeout=30.0
#         )
#
#     # Создаем приложение
#     application = Application.builder().token(config.BOT_TOKEN).request(request).build()
#
#     # Conversation для добавления
#     add_conv = ConversationHandler(
#         entry_points=[
#             CommandHandler('add', add_start),
#             MessageHandler(filters.Regex(r'^➕ Добавить$'), add_start),
#             CallbackQueryHandler(url_confirm, pattern='url_yes')
#         ],
#         states={
#             CATEGORY: [CallbackQueryHandler(add_category, pattern='cat_')],
#             TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_title)],
#             COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_comment)],
#         },
#         fallbacks=[CommandHandler('cancel', add_cancel), MessageHandler(filters.Regex('^Отмена$'), add_cancel)],
#         per_message=False,
#     )
#     application.add_handler(add_conv)
#
#     # Conversation для редактирования
#     edit_conv = ConversationHandler(
#         entry_points=[
#             CommandHandler('edit', edit_start),
#             MessageHandler(filters.Regex(r'^✏️ Редактировать$'), edit_start)
#         ],
#         states={
#             EDIT_SELECT: [CallbackQueryHandler(edit_select, pattern='edit_')],
#             EDIT_FIELD: [CallbackQueryHandler(edit_field, pattern='edit_field_')],
#             EDIT_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_value)],
#         },
#         fallbacks=[CommandHandler('cancel', add_cancel), CallbackQueryHandler(edit_select, pattern='edit_cancel')],
#         per_message=False,
#     )
#     application.add_handler(edit_conv)
#
#     # Conversation для удаления
#     del_conv = ConversationHandler(
#         entry_points=[
#             CommandHandler('del', delete_start),
#             MessageHandler(filters.Regex(r'^❌ Удалить$'), delete_start)
#         ],
#         states={
#             DELETE_CONFIRM: [
#                 CallbackQueryHandler(delete_confirm, pattern='del_'),
#                 CallbackQueryHandler(delete_final, pattern='del_yes'),
#                 CallbackQueryHandler(delete_final, pattern='del_no')
#             ],
#         },
#         fallbacks=[CommandHandler('cancel', add_cancel), CallbackQueryHandler(delete_confirm, pattern='del_cancel')],
#         per_message=False,
#     )
#     application.add_handler(del_conv)
#
#     # Остальные команды
#     application.add_handler(CommandHandler('start', start))
#     application.add_handler(CommandHandler('help', help_command))
#     application.add_handler(CommandHandler('find', find_start))
#     application.add_handler(CommandHandler('list', list_recommendations))
#     application.add_handler(CommandHandler('random', random_recommendation))
#
#     # Callback handlers
#     application.add_handler(CallbackQueryHandler(find_category, pattern='cat_'))
#     application.add_handler(CallbackQueryHandler(find_mode, pattern='find_'))
#     application.add_handler(CallbackQueryHandler(search_pagination, pattern='search_'))
#
#     # Message handlers
#     application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, find_keyword))
#     application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
#
#     application.add_error_handler(error_handler)
#
#     # Запуск бота
#     print("Бот запускается...")
#     application.run_polling()
#
#
# if __name__ == '__main__':
#     main()
