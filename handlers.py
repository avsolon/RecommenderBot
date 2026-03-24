import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler
import db
import utils
import parsing
import logging

logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
CATEGORY, TITLE, COMMENT = range(3)
EDIT_SELECT, EDIT_FIELD, EDIT_VALUE = range(3, 6)
DELETE_CONFIRM = range(6, 7)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    print(f"🔵🔵🔵 ПОЛУЧЕНА КОМАНДА START от {user.id} 🔵🔵🔵")

    # Создаем клавиатуру
    keyboard = [
        ['➕ Добавить', '🔍 Найти'],
        ['📋 Мои рекомендации', '🎲 Случайная'],
        ['✏️ Редактировать', '❌ Удалить'],
        ['❓ Помощь']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        f"Привет, {user.first_name}! 👋\n\n"
        "Я бот для хранения рекомендаций.\n"
        "Используй кнопки меню для навигации:",
        reply_markup=reply_markup
    )
    print(f"✅ Ответ отправлен пользователю {user.id}")

# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     user = update.effective_user
#     await update.message.reply_text(f"Привет, {user.first_name}! Бот работает.")
#     print(f"🔵 Получена команда /start от {user.first_name} (ID: {user.id})")
#
#     # Создаем клавиатуру
#     keyboard = [
#         ['➕ Добавить', '🔍 Найти'],
#         ['📋 Мои рекомендации', '🎲 Случайная'],
#         ['✏️ Редактировать', '❌ Удалить'],
#         ['❓ Помощь']
#     ]
#     reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
#
#     await update.message.reply_text(
#         f"Привет, {user.first_name}! 👋\n\n"
#         "Я бот для хранения рекомендаций.\n"
#         "Ты можешь добавлять фильмы, книги, музыку и многое другое.\n\n"
#         "Используй кнопки меню для навигации:",
#         reply_markup=reply_markup
#     )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📚 *Доступные команды:*\n"
        "/start – начать работу\n"
        "/help – эта справка\n"
        "/add – добавить рекомендацию\n"
        "/find – найти рекомендации\n"
        "/list – мои рекомендации\n"
        "/random – случайная рекомендация\n"
        "/edit – редактировать рекомендацию\n"
        "/del – удалить рекомендацию\n\n"
        "Используй кнопки меню для быстрого доступа."
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)


async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Выбери категорию:", reply_markup=utils.get_categories_keyboard(include_all=False))
    return CATEGORY


async def add_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category = query.data.split('_')[1]
    context.user_data['add_category'] = category
    await query.edit_message_text(f"Категория: {category}\nТеперь введи название:")
    return TITLE


async def add_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title = update.message.text
    context.user_data['add_title'] = title
    await update.message.reply_text("Введи комментарий (можно пропустить, отправив '-'):")
    return COMMENT


async def add_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    comment = update.message.text
    if comment == '-':
        comment = ''
    user_id = update.effective_user.id
    category = context.user_data['add_category']
    title = context.user_data['add_title']
    rec_id = db.add_recommendation(user_id, category, title, comment)
    await update.message.reply_text(f"✅ Рекомендация добавлена! ID: {rec_id}")
    # Очистка данных
    del context.user_data['add_category']
    del context.user_data['add_title']
    return ConversationHandler.END


async def add_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Добавление отменено.")
    return ConversationHandler.END


async def find_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Выбери категорию для поиска:", reply_markup=utils.get_categories_keyboard())
    return


async def find_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category = query.data.split('_')[1]
    context.user_data['find_category'] = None if category == 'all' else category
    # Показываем inline кнопки для выбора режима
    keyboard = [
        [InlineKeyboardButton("Случайная рекомендация", callback_data="find_random")],
        [InlineKeyboardButton("Поиск по ключевому слову", callback_data="find_keyword")]
    ]
    await query.edit_message_text("Как хочешь найти?", reply_markup=InlineKeyboardMarkup(keyboard))
    return


async def find_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    mode = query.data
    if mode == "find_random":
        user_id = update.effective_user.id
        category = context.user_data.get('find_category')
        rec = db.get_random_recommendation(user_id, category)
        if rec:
            msg = utils.format_recommendation(rec)
            await query.edit_message_text(msg, parse_mode=ParseMode.HTML)
        else:
            await query.edit_message_text("Ничего не найдено.")
    else:  # find_keyword
        await query.edit_message_text("Введи ключевое слово для поиска:")
        context.user_data['awaiting_keyword'] = True
    return


async def find_keyword(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('awaiting_keyword'):
        keyword = update.message.text
        user_id = update.effective_user.id
        category = context.user_data.get('find_category')
        results = db.search_recommendations(user_id, keyword, category)
        if results:
            context.user_data['search_results'] = results
            context.user_data['search_page'] = 0
            await send_search_page(update, context)
        else:
            await update.message.reply_text("Ничего не найдено.")
        context.user_data['awaiting_keyword'] = False
    else:
        await update.message.reply_text("Начни поиск через /find")


async def send_search_page(update: Update, context: ContextTypes.DEFAULT_TYPE, page=0):
    results = context.user_data.get('search_results', [])
    if not results:
        await update.message.reply_text("Ничего не найдено.")
        return

    total = len(results)
    per_page = 5
    start = page * per_page
    end = start + per_page
    page_results = results[start:end]

    msg = "🔍 *Результаты поиска:*\n"
    for rec in page_results:
        msg += f"`{rec[0]}`. {rec[1]}: {rec[2]}\n"

    total_pages = (total - 1) // per_page + 1
    msg += f"\nСтраница {page + 1} из {total_pages}"

    keyboard = utils.get_pagination_keyboard('search', page, total_pages)
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)


async def search_pagination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split('_')
    direction = data[1]
    current_page = int(data[2])
    if direction == 'next':
        new_page = current_page + 1
    else:
        new_page = current_page - 1
    context.user_data['search_page'] = new_page
    # Отредактировать сообщение с результатами
    results = context.user_data['search_results']
    per_page = 5
    start = new_page * per_page
    end = start + per_page
    page_results = results[start:end]
    msg = "🔍 *Результаты поиска:*\n"
    for rec in page_results:
        msg += f"`{rec[0]}`. {rec[1]}: {rec[2]}\n"
    total = len(results)
    total_pages = (total - 1) // per_page + 1
    msg += f"\nСтраница {new_page + 1} из {total_pages}"
    keyboard = utils.get_pagination_keyboard('search', new_page, total_pages)
    await query.edit_message_text(msg, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)


async def list_recommendations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    recs = db.get_recommendations(user_id, limit=5)
    if recs:
        msg = "📋 *Ваши последние рекомендации:*\n"
        for r in recs:
            msg += f"`{r[0]}`. {r[1]}: {r[2]}\n"
        msg += "\nИспользуй /list для полного списка (с пагинацией) или /edit /del для управления."
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text("У вас пока нет рекомендаций. Добавьте через /add")


async def random_recommendation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    rec = db.get_random_recommendation(user_id)
    if rec:
        msg = utils.format_recommendation(rec)
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text("У вас пока нет рекомендаций.")


async def edit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Показать список рекомендаций для выбора
    user_id = update.effective_user.id
    recs = db.get_recommendations(user_id, limit=10)
    if not recs:
        await update.message.reply_text("Нет рекомендаций для редактирования.")
        return ConversationHandler.END
    keyboard = []
    for rec in recs:
        keyboard.append([InlineKeyboardButton(f"{rec[1]}: {rec[2]}", callback_data=f"edit_{rec[0]}")])
    keyboard.append([InlineKeyboardButton("Отмена", callback_data="edit_cancel")])
    await update.message.reply_text("Выберите рекомендацию для редактирования:",
                                    reply_markup=InlineKeyboardMarkup(keyboard))
    return EDIT_SELECT


async def edit_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "edit_cancel":
        await query.edit_message_text("Редактирование отменено.")
        return ConversationHandler.END
    rec_id = int(data.split('_')[1])
    context.user_data['edit_id'] = rec_id
    # Получить рекомендацию
    user_id = update.effective_user.id
    rec = db.get_recommendation_by_id(user_id, rec_id)
    if not rec:
        await query.edit_message_text("Рекомендация не найдена.")
        return ConversationHandler.END
    msg = utils.format_recommendation(rec)
    keyboard = [
        [InlineKeyboardButton("Изменить категорию", callback_data="edit_field_category")],
        [InlineKeyboardButton("Изменить название", callback_data="edit_field_title")],
        [InlineKeyboardButton("Изменить комментарий", callback_data="edit_field_comment")],
        [InlineKeyboardButton("Отмена", callback_data="edit_cancel")]
    ]
    await query.edit_message_text(f"Редактируем:\n{msg}\n\nЧто хотите изменить?", parse_mode=ParseMode.HTML,
                                  reply_markup=InlineKeyboardMarkup(keyboard))
    return EDIT_FIELD


async def edit_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    field = query.data.split('_')[2]  # edit_field_XXX
    context.user_data['edit_field'] = field
    field_name = {'category': 'категорию', 'title': 'название', 'comment': 'комментарий'}[field]
    await query.edit_message_text(f"Введите новое значение для {field_name}:")
    return EDIT_VALUE


async def edit_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_value = update.message.text
    user_id = update.effective_user.id
    rec_id = context.user_data['edit_id']
    field = context.user_data['edit_field']
    success = db.update_recommendation(user_id, rec_id, field, new_value)
    if success:
        await update.message.reply_text("✅ Рекомендация обновлена!")
    else:
        await update.message.reply_text("❌ Ошибка обновления.")
    # Очистка данных
    del context.user_data['edit_id']
    del context.user_data['edit_field']
    return ConversationHandler.END


async def delete_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    recs = db.get_recommendations(user_id, limit=10)
    if not recs:
        await update.message.reply_text("Нет рекомендаций для удаления.")
        return ConversationHandler.END
    keyboard = []
    for rec in recs:
        keyboard.append([InlineKeyboardButton(f"{rec[1]}: {rec[2]}", callback_data=f"del_{rec[0]}")])
    keyboard.append([InlineKeyboardButton("Отмена", callback_data="del_cancel")])
    await update.message.reply_text("Выберите рекомендацию для удаления:", reply_markup=InlineKeyboardMarkup(keyboard))
    return DELETE_CONFIRM


async def delete_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "del_cancel":
        await query.edit_message_text("Удаление отменено.")
        return ConversationHandler.END
    rec_id = int(data.split('_')[1])
    context.user_data['del_id'] = rec_id
    # Запрашиваем подтверждение
    keyboard = [
        [InlineKeyboardButton("Да, удалить", callback_data="del_yes")],
        [InlineKeyboardButton("Нет, отмена", callback_data="del_no")]
    ]
    await query.edit_message_text("Вы уверены, что хотите удалить эту рекомендацию?",
                                  reply_markup=InlineKeyboardMarkup(keyboard))
    return DELETE_CONFIRM


async def delete_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "del_yes":
        user_id = update.effective_user.id
        rec_id = context.user_data['del_id']
        success = db.delete_recommendation(user_id, rec_id)
        if success:
            await query.edit_message_text("✅ Рекомендация удалена.")
        else:
            await query.edit_message_text("❌ Ошибка удаления.")
    else:
        await query.edit_message_text("Удаление отменено.")
    # Очистка
    del context.user_data['del_id']
    return ConversationHandler.END


async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Если пользователь отправил ссылку вне диалога, предложить добавить."""
    text = update.message.text
    if text.startswith(('http://', 'https://')):
        title, desc = parsing.extract_info_from_url(text)
        if title:
            msg = f"🔗 Обнаружена ссылка.\nЗаголовок: {title}\nОписание: {desc}\n\nДобавить как рекомендацию?"
            keyboard = [[InlineKeyboardButton("Да", callback_data="url_yes")],
                        [InlineKeyboardButton("Нет", callback_data="url_no")]]
            context.user_data['url_title'] = title
            context.user_data['url_desc'] = desc
            await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await update.message.reply_text("Не удалось извлечь информацию из ссылки.")


async def url_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "url_yes":
        # Запускаем процесс добавления с предзаполненными данными
        title = context.user_data['url_title']
        desc = context.user_data['url_desc']
        # Запрашиваем категорию
        await query.edit_message_text("Выберите категорию:",
                                      reply_markup=utils.get_categories_keyboard(include_all=False))
        context.user_data['add_title'] = title
        context.user_data['add_comment_prefill'] = desc
        return CATEGORY
    else:
        await query.edit_message_text("Добавление отменено.")
        return ConversationHandler.END


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.error(msg="Exception while handling an update:", exc_info=context.error)
    if update and update.effective_message:
        await update.effective_message.reply_text("Произошла ошибка. Попробуйте позже.")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик всех текстовых сообщений (для отладки)"""
    user = update.effective_user
    text = update.message.text
    logger.info(f"📝 Получен текст от {user.id}: {text}")

    # Игнорируем команды (они уже обработаны)
    if text.startswith('/'):
        return

    # Если это не команда и не обработано другими обработчиками
    await update.message.reply_text(
        "❓ Неизвестная команда.\n"
        "Используй /start для меню или /help для списка команд."
    )