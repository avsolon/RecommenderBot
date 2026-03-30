from telegram import Update
from telegram.ext import CallbackContext

def help_handler(update: Update, context: CallbackContext):
    text = """
📌 Доступные команды:

➕ Добавить — добавить рекомендацию  
🔍 Найти — поиск по категории и слову  
🎲 Случайная — случайная рекомендация  
📋 Список — список всех рекомендаций
✏️ Редактировать - изменение записи  
🗑 Удалить — удалить запись  

Команды:
/add — добавить  
/find — найти  
/random — случайная  
/list — список
/edit - редактировать  
/del — удалить  
"""
    update.message.reply_text(text)