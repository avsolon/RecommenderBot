import time
import requests
import logging
import asyncio
import json
import config
import db
from utils import get_main_keyboard

# Хранилище состояний пользователей
user_states = {}  # {chat_id: "add_category", "add_title", "add_comment", ...}
user_data = {}  # {chat_id: {"category": "...", "title": "...", ...}}


def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class FakeMessage:
    def __init__(self, chat_id, text, user_id, user_name):
        self.chat = type('obj', (object,), {'id': chat_id})()
        self.text = text
        self.from_user = type('obj', (object,), {'id': user_id, 'first_name': user_name})()

    async def reply_text(self, text, **kwargs):
        send_message(self.chat.id, text, **kwargs)


class FakeUpdate:
    def __init__(self, chat_id, user_id, user_name, text=None, callback_query=None):
        self.effective_user = type('obj', (object,), {'id': user_id, 'first_name': user_name})()
        self.message = FakeMessage(chat_id, text, user_id, user_name) if text else None
        self.callback_query = callback_query


class FakeContext:
    def __init__(self, chat_id):
        self.user_data = user_data.setdefault(chat_id, {})


class FakeCallbackQuery:
    def __init__(self, data, callback_id, message, user_id):
        self.data = data
        self.id = callback_id
        self.message = message
        self.from_user = type('obj', (object,), {'id': user_id})()

    async def answer(self, text=None, **kwargs):
        answer_callback(self.id, text)

    async def edit_message_text(self, text, **kwargs):
        edit_message(self.message.chat.id, self.message.message_id, text)


def send_message(chat_id, text, parse_mode="HTML", reply_markup=None):
    url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}

    if reply_markup:
        if hasattr(reply_markup, 'to_dict'):
            data["reply_markup"] = json.dumps(reply_markup.to_dict())
        else:
            data["reply_markup"] = json.dumps(reply_markup)

    try:
        requests.post(url, json=data, proxies=PROXY, timeout=10)
    except Exception as e:
        logging.error(f"Ошибка отправки: {e}")


def answer_callback(callback_id, text):
    url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/answerCallbackQuery"
    data = {"callback_query_id": callback_id, "text": text}
    try:
        requests.post(url, json=data, proxies=PROXY, timeout=10)
    except:
        pass


def edit_message(chat_id, message_id, text):
    url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/editMessageText"
    data = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, json=data, proxies=PROXY, timeout=10)
    except:
        pass


PROXY = None


def main():
    global PROXY

    logging.basicConfig(level=logging.INFO)
    db.init_db()

    if config.PROXY_URL:
        PROXY = {'http': config.PROXY_URL, 'https': config.PROXY_URL}
        print(f"✅ Прокси: {config.PROXY_URL}")

    print("🚀 Бот запущен! Отправьте /start\n")

    last_update_id = 0

    while True:
        try:
            url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/getUpdates"
            params = {"offset": last_update_id + 1, "timeout": 30}
            response = requests.get(url, params=params, proxies=PROXY, timeout=35)

            if response.status_code == 200:
                data = response.json()
                if data["ok"] and data["result"]:
                    for update in data["result"]:
                        last_update_id = update["update_id"]

                        # Обработка сообщений
                        if "message" in update:
                            msg = update["message"]
                            chat_id = msg["chat"]["id"]
                            user_id = msg["from"]["id"]
                            user_name = msg["from"].get("first_name", "Пользователь")
                            text = msg.get("text", "")
                            print(f"📨 {text} от {user_id}")

                            # Обработка команд
                            if text == "/start":
                                send_message(chat_id, f"Привет, {user_name}! 👋\n\nЯ бот для рекомендаций.",
                                             reply_markup=get_main_keyboard().to_dict())

                            elif text == "/add" or text == "➕ Добавить":
                                # Показываем категории
                                from utils import get_categories_keyboard
                                keyboard = get_categories_keyboard(include_all=False)
                                send_message(chat_id, "Выберите категорию:", reply_markup=keyboard.to_dict())
                                user_states[chat_id] = "add_category"

                            elif text == "/list" or text == "📋 Мои рекомендации":
                                recs = db.get_recommendations(chat_id)
                                if recs:
                                    msg = "📋 *Ваши рекомендации:*\n\n"
                                    for r in recs:
                                        msg += f"`{r[0]}`. {r[1]}: {r[2]}\n"
                                    msg += "\nИспользуй /edit ID или /del ID"
                                    send_message(chat_id, msg, parse_mode="Markdown")
                                else:
                                    send_message(chat_id, "У вас пока нет рекомендаций.")

                            elif text == "/random" or text == "🎲 Случайная":
                                rec = db.get_random_recommendation(chat_id)
                                if rec:
                                    msg = f"🎲 *Случайная:*\n{rec[1]}: {rec[2]}\n💬 {rec[3] or 'Без комментария'}"
                                    send_message(chat_id, msg, parse_mode="Markdown")
                                else:
                                    send_message(chat_id, "Нет рекомендаций.")

                            elif text == "/find" or text == "🔍 Найти":
                                from utils import get_categories_keyboard
                                send_message(chat_id, "Выберите категорию:",
                                             reply_markup=get_categories_keyboard().to_dict())
                                user_states[chat_id] = "find_category"

                            # Обработка диалогов
                            elif chat_id in user_states:
                                state = user_states[chat_id]

                                if state == "add_category":
                                    # Категория уже выбрана через callback, этот блок не нужен
                                    pass

                                elif state == "add_title":
                                    user_data[chat_id]["title"] = text
                                    user_states[chat_id] = "add_comment"
                                    send_message(chat_id, "Введите комментарий (или '-' чтобы пропустить):")

                                elif state == "add_comment":
                                    comment = "" if text == "-" else text
                                    category = user_data[chat_id]["category"]
                                    title = user_data[chat_id]["title"]

                                    rec_id = db.add_recommendation(chat_id, category, title, comment)
                                    send_message(chat_id, f"✅ Рекомендация добавлена! ID: {rec_id}")

                                    del user_states[chat_id]
                                    del user_data[chat_id]
                                    send_message(chat_id, "Что дальше?", reply_markup=get_main_keyboard().to_dict())

                                elif state == "find_keyword":
                                    keyword = text
                                    category = user_data[chat_id].get("category")
                                    results = db.search_recommendations(chat_id, keyword, category)

                                    if results:
                                        msg = f"🔍 *Результаты по '{keyword}':*\n\n"
                                        for r in results:
                                            msg += f"`{r[0]}`. {r[1]}: {r[2]}\n"
                                        send_message(chat_id, msg, parse_mode="Markdown")
                                    else:
                                        send_message(chat_id, f"Ничего не найдено по '{keyword}'")

                                    del user_states[chat_id]
                                    del user_data[chat_id]
                                    send_message(chat_id, "Что дальше?", reply_markup=get_main_keyboard().to_dict())

                            else:
                                send_message(chat_id, "Используй /start для меню")

                        # Обработка callback запросов
                        elif "callback_query" in update:
                            cb = update["callback_query"]
                            chat_id = cb["message"]["chat"]["id"]
                            user_id = cb["from"]["id"]
                            data_cb = cb["data"]
                            callback_id = cb["id"]
                            message_id = cb["message"]["message_id"]

                            print(f"🔘 Callback: {data_cb} от {user_id}")

                            if data_cb.startswith("cat_"):
                                category = data_cb.split("_")[1]

                                if category == "all":
                                    category = None

                                # Сохраняем состояние для поиска или добавления
                                if chat_id in user_states and user_states[chat_id] == "find_category":
                                    user_data[chat_id] = {"category": category}
                                    user_states[chat_id] = "find_keyword"
                                    edit_message(chat_id, message_id,
                                                 f"Категория: {category or 'Все'}\n\nВведите ключевое слово:")
                                else:
                                    # Это добавление
                                    user_data[chat_id] = {"category": category}
                                    user_states[chat_id] = "add_title"
                                    edit_message(chat_id, message_id, f"Категория: {category}\n\nВведите название:")

                                answer_callback(callback_id, "Категория выбрана")

                            elif data_cb.startswith("find_"):
                                mode = data_cb.split("_")[1]
                                if mode == "random":
                                    # Случайная рекомендация
                                    category = user_data.get(chat_id, {}).get("category")
                                    rec = db.get_random_recommendation(chat_id, category)
                                    if rec:
                                        msg = f"🎲 *Случайная:*\n{rec[1]}: {rec[2]}\n💬 {rec[3] or 'Без комментария'}"
                                        edit_message(chat_id, message_id, msg, parse_mode="Markdown")
                                    else:
                                        edit_message(chat_id, message_id, "Ничего не найдено")
                                    answer_callback(callback_id, "Готово")
                                elif mode == "keyword":
                                    user_states[chat_id] = "find_keyword"
                                    edit_message(chat_id, message_id, "Введите ключевое слово для поиска:")
                                    answer_callback(callback_id, "Введите слово")

        except requests.exceptions.Timeout:
            pass
        except Exception as e:
            logging.error(f"Ошибка: {e}")
            time.sleep(5)

        time.sleep(0.5)


if __name__ == '__main__':
    main()

# import logging
# import asyncio
# from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
# from telegram.request import HTTPXRequest
# import config
# import db
# from handlers import (
#     start, help_command, add_start, add_category, add_title, add_comment, add_cancel,
#     find_start, find_category, find_mode, find_keyword, search_pagination,
#     list_recommendations, random_recommendation, edit_start, edit_select,
#     edit_field, edit_value, delete_start, delete_confirm, delete_final,
#     handle_url, url_confirm, error_handler, handle_text,
#     CATEGORY, TITLE, COMMENT, EDIT_SELECT, EDIT_FIELD, EDIT_VALUE, DELETE_CONFIRM
# )
#
#
# def main():
#     # Настройка логирования
#     logging.basicConfig(
#         format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#         level=logging.INFO
#     )
#     logger = logging.getLogger(__name__)
#
#     # Инициализация БД
#     db.init_db()
#
#     # Настройка прокси
#     request_kwargs = {
#         'connect_timeout': 30.0,
#         'read_timeout': 30.0,
#     }
#
#     if config.PROXY_URL:
#         request_kwargs['proxy'] = config.PROXY_URL
#         print(f"✅ Бот работает через прокси: {config.PROXY_URL}")
#     else:
#         print("✅ Бот работает напрямую (без прокси)")
#
#     request = HTTPXRequest(**request_kwargs)
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
#     # Основные команды
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
#     # Обработчики текста
#     application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, find_keyword))
#     application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
#     application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
#
#     application.add_error_handler(error_handler)
#
#     # Запуск
#     print("🚀 Бот запускается...")
#     print("📋 Ожидание команд от Telegram...")
#
#     # Запускаем polling с явными параметрами
#     application.run_polling(
#         drop_pending_updates=True,
#         allowed_updates=["message", "callback_query"],
#         poll_interval=1.0,  # Опрашиваем каждую секунду
#         timeout=30
#     )
#
#
# if __name__ == '__main__':
#     main()


# import logging
# import asyncio
# from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
# from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, \
#     ConversationHandler, ContextTypes
# from telegram.request import HTTPXRequest
#
# import config
# import db
# from handlers import (
#     start, help_command, add_start, add_category, add_title, add_comment, add_cancel,
#     find_start, find_category, find_mode, find_keyword, search_pagination,
#     list_recommendations, random_recommendation, edit_start, edit_select,
#     edit_field, edit_value, delete_start, delete_confirm, delete_final,
#     handle_url, url_confirm, error_handler,
#     CATEGORY, TITLE, COMMENT, EDIT_SELECT, EDIT_FIELD, EDIT_VALUE, DELETE_CONFIRM, handle_text
# )
#
#
# def main():
#     logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
#     db.init_db()
#
#     # Универсальная настройка
#     request_kwargs = {
#         'connect_timeout': 30.0,
#         'read_timeout': 30.0,
#     }
#
#     # Добавляем прокси ТОЛЬКО если он указан в .env
#     if config.PROXY_URL:
#         request_kwargs['proxy'] = config.PROXY_URL
#         print(f"✅ Бот работает через прокси: {config.PROXY_URL}")
#     else:
#         print("✅ Бот работает напрямую (без прокси)")
#
#     request = HTTPXRequest(**request_kwargs)
#     application = Application.builder().token(config.BOT_TOKEN).request(request).build()
#
# # def main():
# #     logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
# #     db.init_db()
# #
# #     # Создаем приложение
# #     application = Application.builder().token(config.BOT_TOKEN).build()
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
#     application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
#
#     application.add_error_handler(error_handler)
#
#     # Запуск бота
#     # application.run_polling()
#
#     # Запуск
#     print("🚀 Бот запускается...")
#     print("📋 Ожидание команд от Telegram...")
#
#     # Важно: drop_pending_updates=True очищает старые обновления
#     application.run_polling(
#         drop_pending_updates=True,
#         allowed_updates=["message", "callback_query"]
#     )
#
#
# if __name__ == '__main__':
#     main()


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
