import asyncio
import logging
import traceback

from telegram import Update
from telegram.ext import (
    Application, CommandHandler, ConversationHandler,
    CallbackQueryHandler, MessageHandler, filters, ContextTypes
)

from config import TOKEN, PROXY
from db import init_db

from handlers.start import start
from handlers.help import help_handler
from handlers.add import (
    add, add_category_chosen, title_received, comment_received, visibility_chosen,
    CATEGORY, TITLE, COMMENT, VISIBILITY
)
from handlers.random import random_handler
from handlers.find import (
    find, find_category_chosen, mode_chosen, keyword_entered,
    CHOOSE_CATEGORY, CHOOSE_MODE, ENTER_KEYWORD
)
from handlers.list import list_handler
from handlers.edit import (
    edit, select_record, select_field, new_value, category_chosen_edit,
    SELECT_RECORD, SELECT_FIELD, ENTER_NEW_VALUE
)
from handlers.delete import delete, confirm_delete, DELETE_CONFIRM
from handlers.public import (
    public_start, public_category_chosen, public_paginate,
    public_view_rec, public_back_to_categories, public_back_to_list,
    public_toggle, CATEGORY_BROWSE, VIEW_REC
)
from handlers.top import top_start, top_category_chosen, top_back, CATEGORY_TOP
from handlers.rate import show_rating, rate_recommendation_handler

logger = logging.getLogger(__name__)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


async def post_init(app: Application):
    await init_db()
    print("✅ Database initialized")


def build_app() -> Application:
    builder = Application.builder().token(TOKEN).post_init(post_init)
    if PROXY:
        builder = builder.connect_kwargs(proxy_url=PROXY)

    app = builder.build()

    # === ADD ===
    add_conv = ConversationHandler(
        entry_points=[
            CommandHandler("add", add),
            MessageHandler(filters.Regex("^➕ Добавить$"), add),
        ],
        states={
            CATEGORY: [CallbackQueryHandler(add_category_chosen, pattern="^cat_")],
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, title_received)],
            COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, comment_received)],
            VISIBILITY: [CallbackQueryHandler(visibility_chosen, pattern="^vis_")],
        },
        fallbacks=[], per_message=False, allow_reentry=True,
    )

    # === DELETE ===
    del_conv = ConversationHandler(
        entry_points=[
            CommandHandler("del", delete),
            MessageHandler(filters.Regex("^🗑 Удалить$"), delete),
        ],
        states={
            DELETE_CONFIRM: [CallbackQueryHandler(confirm_delete)],
        },
        fallbacks=[], per_message=False, allow_reentry=True,
    )

    # === FIND ===
    find_conv = ConversationHandler(
        entry_points=[
            CommandHandler("find", find),
            MessageHandler(filters.Regex("^🔍 Найти$"), find),
        ],
        states={
            CHOOSE_CATEGORY: [CallbackQueryHandler(find_category_chosen, pattern="^cat_")],
            CHOOSE_MODE: [CallbackQueryHandler(mode_chosen, pattern="^(random|search)$")],
            ENTER_KEYWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, keyword_entered)],
        },
        fallbacks=[], per_message=False, allow_reentry=True,
    )

    # === EDIT ===
    edit_conv = ConversationHandler(
        entry_points=[
            CommandHandler("edit", edit),
            MessageHandler(filters.Regex("^✏️ Редактировать$"), edit),
        ],
        states={
            SELECT_RECORD: [CallbackQueryHandler(select_record, pattern="^edit_")],
            SELECT_FIELD: [CallbackQueryHandler(select_field, pattern="^field_")],
            ENTER_NEW_VALUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, new_value),
                CallbackQueryHandler(category_chosen_edit, pattern="^cat_"),
            ],
        },
        fallbacks=[], per_message=False, allow_reentry=True,
    )

    # === PUBLIC ===
    public_conv = ConversationHandler(
        entry_points=[
            CommandHandler("public", public_start),
            MessageHandler(filters.Regex("^🌍 Общие$"), public_start),
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
            ],
        },
        fallbacks=[], per_message=False, allow_reentry=True,
    )

    # === TOP ===
    top_conv = ConversationHandler(
        entry_points=[
            CommandHandler("top", top_start),
            MessageHandler(filters.Regex("^🏆 Топ$"), top_start),
        ],
        states={
            CATEGORY_TOP: [
                CallbackQueryHandler(top_category_chosen, pattern="^cat_"),
                CallbackQueryHandler(top_back, pattern="^top_back$"),
            ],
        },
        fallbacks=[], per_message=False, allow_reentry=True,
    )

    # === REGISTER ===
    app.add_handler(CommandHandler("start", start))

    app.add_handler(add_conv)
    app.add_handler(del_conv)
    app.add_handler(find_conv)
    app.add_handler(edit_conv)
    app.add_handler(public_conv)
    app.add_handler(top_conv)

    app.add_handler(CommandHandler("random", random_handler))
    app.add_handler(CommandHandler("list", list_handler))
    app.add_handler(CommandHandler("help", help_handler))

    app.add_handler(MessageHandler(filters.Regex("^🎲 Случайная$"), random_handler))
    app.add_handler(MessageHandler(filters.Regex("^📋 Список$"), list_handler))
    app.add_handler(MessageHandler(filters.Regex("^❓ Помощь$"), help_handler))

    app.add_handler(CallbackQueryHandler(public_toggle, pattern="^toggle_"))
    app.add_handler(CallbackQueryHandler(show_rating, pattern="^showrate_"))
    app.add_handler(CallbackQueryHandler(rate_recommendation_handler, pattern="^rate_\\d+_\\d+$"))

    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        print(f"FATAL: {type(context.error).__name__}: {context.error}", flush=True)
        traceback.print_exception(type(context.error), context.error, context.error.__traceback__)
        logger.error("Exception while handling an update", exc_info=context.error)
        if update and isinstance(update, Update) and update.effective_message:
            try:
                await update.effective_message.reply_text("❌ Произошла внутренняя ошибка. Попробуй ещё раз.")
            except Exception:
                pass

    app.add_error_handler(error_handler)

    return app


def main():
    app = build_app()
    print("🤖 Bot started! Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
