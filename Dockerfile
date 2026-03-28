FROM python:3.11-slim

# Логи сразу в stdout (важно для docker logs)
ENV PYTHONUNBUFFERED=1
ENV TZ=UTC

# Рабочая директория
WORKDIR /app

# Системные зависимости (минимум)
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем проект
COPY . .

# Создаём папку для БД
RUN mkdir -p /app/data

# Запуск бота
CMD ["python", "bot.py"]