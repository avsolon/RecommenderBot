# 🤖 Мой Рекомендатор (Recommendation Bot)

Telegram-бот для хранения, поиска и обмена рекомендациями  
(фильмы, книги, сериалы, музыка, еда, игры, места и др.)

## 🚀 Возможности

- ➕ **Добавление** рекомендаций (с выбором публичная/приватная)
- 🔍 **Поиск** по категории и ключевым словам
- 🎲 **Случайная** рекомендация
- 📋 **Список** всех записей со статистикой
- ✏️ **Редактирование** записей
- 🗑 **Удаление** с подтверждением
- 🌍 **Общие рекомендации** — просмотр публичных записей других пользователей
- ⭐ **Оценка** рекомендаций (1–5)
- 🏆 **Топ** — самые популярные рекомендации (по рейтингу)
- ❓ Встроенная помощь

## 🏗 Архитектура

```
├── bot.py                           # Точка входа Telegram-бота
├── config.py                        # Конфигурация (токен, БД, категории)
├── db.py                            # Подключение к БД (SQLAlchemy async)
├── models.py                        # Модели: User, Recommendation, Rating
├── requirements.txt                 # Зависимости
├── Dockerfile                       # Образ для бота
├── docker-compose.yml               # Стек: PostgreSQL + Bot + FastAPI
│
├── handlers/                        # Обработчики команд Telegram
│   ├── start.py                     # /start
│   ├── add.py                       # /add — добавление
│   ├── find.py                      # /find — поиск
│   ├── list.py                      # /list — список
│   ├── edit.py                      # /edit — редактирование
│   ├── delete.py                    # /del — удаление
│   ├── random.py                    # /random — случайная
│   ├── help.py                      # /help — помощь
│   ├── public.py                    # /public — общие рекомендации
│   ├── rate.py                      # Оценка рекомендаций
│   └── top.py                       # /top — топ по рейтингу
│
├── keyboards/                       # Клавиатуры
│   ├── inline.py                    # Inline-клавиатуры
│   └── reply.py                     # Reply-клавиатуры
│
├── services/                        # Бизнес-логика
│   ├── recommendation_service.py    # Работа с рекомендациями
│   └── rating_service.py            # Система оценок
│
├── web/                             # FastAPI веб-слой
│   └── main.py                      # REST API /docs
│
└── tests/                           # Тесты (pytest, без Telegram API)
    └── test_services.py
```

## 🧠 Как это работает

- Каждый пользователь видит свои приватные записи
- Публичные записи доступны всем в разделе **«Общие»**
- Пользователи могут **оценивать** публичные рекомендации (1–5)
- **Топ** формируется по средней оценке
- Данные хранятся в PostgreSQL (SQLAlchemy async)

## 🛠 Установка и запуск

### Локально (для разработки)

```bash
# 1. Установить PostgreSQL и создать БД
createdb recommender

# 2. Настроить .env
cp .env.example .env
# Отредактировать .env: указать TELEGRAM_TOKEN и DATABASE_URL

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Запустить бота
python bot.py

# 5. Запустить API (опционально)
uvicorn web.main:app --reload --port 8000
```

### Через Docker (продакшн)

```bash
docker-compose up -d --build
```

Запустится:
- **PostgreSQL 16** — база данных
- **Telegram Bot** — сам бот
- **FastAPI** — REST API на порту 8000

## 📱 Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Начало работы |
| `/add` | Добавить рекомендацию |
| `/find` | Поиск по категории |
| `/random` | Случайная рекомендация |
| `/list` | Список всех записей |
| `/edit` | Редактировать запись |
| `/del` | Удалить запись |
| `/public` | Общие рекомендации |
| `/top` | Топ по рейтингу |
| `/help` | Помощь |

## 🌐 API (FastAPI)

После запуска API доступно по адресу `http://localhost:8000`

- `GET /` — информация
- `GET /categories` — список категорий
- `GET /recommendations` — публичные рекомендации
- `GET /recommendations/top` — топ рекомендаций
- `GET /recommendations/{id}` — детали рекомендации
- `GET /users/{telegram_id}` — информация о пользователе

Документация: `http://localhost:8000/docs`

## 🧪 Тестирование

```bash
pytest tests/ -v
# или
python -m pytest tests/test_services.py -v
```

Тесты используют SQLite in-memory, не требуют PostgreSQL и Telegram API.

## 🔒 Безопасность

- Все операции с приватными записями проверяют `user_id`
- API отдаёт только публичные рекомендации
- SQL-инъекции предотвращены использованием ORM
- Поддержка прокси для регионов с блокировками Telegram (переменная `PROXY_URL`)

## 📦 Переменные окружения (.env)

| Переменная | Описание | По умолчанию |
|-----------|----------|-------------|
| `TELEGRAM_TOKEN` | Токен бота Telegram | — |
| `PROXY_URL` | URL прокси (Socks5/HTTP) | — |
| `DATABASE_URL` | URL подключения к БД | `postgresql+asyncpg://postgres:postgres@localhost:5432/recommender` |
| `BOT_USERNAME` | Имя бота | `MyRecommenderBot` |
