from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler

from handlers.base import send_or_edit_message
from keyboards.inline import categories_with_all_keyboard, rec_actions_keyboard, pagination_keyboard
from services.recommendation_service import get_public_recommendations, get_recommendation_by_id, toggle_public, get_or_create_user
from services.rating_service import get_recommendation_rating_stats, get_user_rating
from config import CATEGORIES, DEFAULT_PAGE_SIZE
from db import get_session

CATEGORY_BROWSE, VIEW_REC = range(2)


async def _fetch_public(session, category: str, page: int):
    offset = page * DEFAULT_PAGE_SIZE
    recs = await get_public_recommendations(session, category=category, limit=DEFAULT_PAGE_SIZE + 1, offset=offset)
    has_next = len(recs) > DEFAULT_PAGE_SIZE
    return recs[:DEFAULT_PAGE_SIZE], has_next


async def public_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['public_page'] = 0
    await send_or_edit_message(
        update,
        "🌍 *Общие рекомендации*\n\nВыбери категорию:",
        reply_markup=categories_with_all_keyboard()
    )
    return CATEGORY_BROWSE


async def public_category_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    key = query.data.replace("cat_", "")
    context.user_data['public_category'] = key
    context.user_data['public_page'] = 0

    async for session in get_session():
        recs, has_next = await _fetch_public(session, key, 0)
        if not recs:
            await query.edit_message_text("😕 В этой категории пока нет публичных рекомендаций.")
            return VIEW_REC

        cat_name = CATEGORIES.get(key, "Все") if key != "ALL" else "Все категории"
        text = f"🌍 *Общие рекомендации — {cat_name}*\n\n"
        for i, rec in enumerate(recs, 1):
            text += f"{i}. *{rec.title}* — {rec.author.display_name if rec.author else 'Неизвестно'}\n"

        keyboard = pagination_keyboard(
            [{"rec": r} for r in recs],
            prefix="pubrec", page=0, has_next=has_next, category=key
        )
        rows = [list(r) for r in keyboard.inline_keyboard]
        rows.insert(0, [
            InlineKeyboardButton("🔙 Назад к категориям", callback_data="pub_back_cat")
        ])
        keyboard = InlineKeyboardMarkup(rows)

        await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")

    return VIEW_REC


async def public_paginate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    parts = data.split("_")
    page = int(parts[2])
    category = parts[3] if len(parts) > 3 and parts[3] != "None" else "ALL"
    context.user_data['public_category'] = category
    context.user_data['public_page'] = page

    async for session in get_session():
        recs, has_next = await _fetch_public(session, category, page)
        if not recs:
            await query.edit_message_text("😕 Нет рекомендаций на этой странице.")
            return VIEW_REC

        cat_name = CATEGORIES.get(category, "Все") if category != "ALL" else "Все категории"
        text = f"🌍 *Общие рекомендации — {cat_name}* (стр. {page + 1})\n\n"
        for i, rec in enumerate(recs, 1):
            text += f"{i}. *{rec.title}* — {rec.author.display_name if rec.author else 'Неизвестно'}\n"

        keyboard = pagination_keyboard(
            [{"rec": r} for r in recs],
            prefix="pubrec", page=page, has_next=has_next, category=category
        )
        rows = [list(r) for r in keyboard.inline_keyboard]
        rows.insert(0, [
            InlineKeyboardButton("🔙 Назад к категориям", callback_data="pub_back_cat")
        ])
        keyboard = InlineKeyboardMarkup(rows)

        await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")

    return VIEW_REC


async def public_view_rec(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    rec_id = int(query.data.replace("pubrec_", ""))
    context.user_data['view_rec_id'] = rec_id

    async for session in get_session():
        user = await get_or_create_user(session, query.from_user.id)
        text, keyboard = await _build_rec_detail_view(session, rec_id, user.id)
        if not text:
            await query.edit_message_text("Рекомендация не найдена или удалена.")
            return VIEW_REC

        await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")

    return VIEW_REC


async def _build_rec_detail_view(session, rec_id: int, user_id: int):
    rec = await get_recommendation_by_id(session, rec_id)
    if not rec:
        return None, None

    stats = await get_recommendation_rating_stats(session, rec_id)
    user_rating = await get_user_rating(session, user_id, rec_id)
    is_owner = rec.user_id == user_id
    cat_name = CATEGORIES.get(rec.category, rec.category)
    author_name = rec.author.display_name if rec.author else "Неизвестно"

    text = (
        f"📂 *{cat_name}*\n"
        f"📖 *{rec.title}*\n"
        f"💬 {rec.comment or '—'}\n\n"
        f"👤 Автор: {author_name}\n"
        f"⭐ Рейтинг: {stats['avg_score']} (голосов: {stats['count']})"
    )
    if user_rating:
        text += f"\n👍 Твоя оценка: {user_rating}/5"

    keyboard = rec_actions_keyboard(rec_id, rec.is_public, is_owner)
    rows = [list(r) for r in keyboard.inline_keyboard]
    if user_rating:
        rows.append([
            InlineKeyboardButton("Изменить оценку", callback_data=f"showrate_{rec_id}")
        ])
    rows.append([
        InlineKeyboardButton("🔙 К списку", callback_data="pub_back_list")
    ])

    return text, InlineKeyboardMarkup(rows)


async def public_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    rec_id = int(query.data.replace("toggle_", ""))

    async for session in get_session():
        try:
            user = await get_or_create_user(session, query.from_user.id)
            new_status = await toggle_public(session, rec_id, user.id)
            text, keyboard = await _build_rec_detail_view(session, rec_id, user.id)
            if text and keyboard:
                await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")
            else:
                status_text = "🌍 Публичная" if new_status else "🔒 Приватная"
                await query.edit_message_text(f"✅ Статус изменён: {status_text}")
        except ValueError:
            await query.edit_message_text("❌ Не удалось изменить статус.")


async def public_back_to_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🌍 *Общие рекомендации*\n\nВыбери категорию:",
        reply_markup=categories_with_all_keyboard(),
        parse_mode="Markdown"
    )
    return CATEGORY_BROWSE


async def public_back_to_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category = context.user_data.get('public_category', 'ALL')
    page = context.user_data.get('public_page', 0)

    async for session in get_session():
        recs, has_next = await _fetch_public(session, category, page)
        if not recs:
            await query.edit_message_text("😕 Нет рекомендаций.")
            return VIEW_REC

        cat_name = CATEGORIES.get(category, "Все") if category != "ALL" else "Все категории"
        text = f"🌍 *Общие рекомендации — {cat_name}*\n\n"
        for i, rec in enumerate(recs, 1):
            text += f"{i}. *{rec.title}* — {rec.author.display_name if rec.author else 'Неизвестно'}\n"

        keyboard = pagination_keyboard(
            [{"rec": r} for r in recs],
            prefix="pubrec", page=page, has_next=has_next, category=category
        )
        rows = [list(r) for r in keyboard.inline_keyboard]
        rows.insert(0, [
            InlineKeyboardButton("🔙 Назад к категориям", callback_data="pub_back_cat")
        ])
        keyboard = InlineKeyboardMarkup(rows)

        await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")

    return VIEW_REC
