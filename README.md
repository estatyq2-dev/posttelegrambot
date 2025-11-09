# News Relay Bot (Multi-User Version)

🤖 **Telegram-бот для автоматичного репостингу та переписування новин з підтримкою багатьох користувачів.**

## 🎯 Можливості

- ✅ **Багатокористувацька архітектура** - повна ізоляція даних між користувачами
- ✅ **Підтримка джерел**: Telegram-канали, RSS, веб-сайти
- ✅ **Автоматичне переписування** через GPT API (OpenAI)
- ✅ **Гнучкий планувальник** публікацій з налаштуванням інтервалів
- ✅ **Управління через Telegram bot** - зручний інтерфейс
- ✅ **Підтримка медіа-контенту** - фото, відео
- ✅ **Дедуплікація** та модерація контенту
- ✅ **Docker-ready** - легке розгортання

## 📋 Вимоги

- Docker і Docker Compose
- Telegram Bot Token (отримайте через @BotFather)
- Telegram API credentials (отримайте на https://my.telegram.org)
- OpenAI API Key
- PostgreSQL (через Docker)
- Redis (через Docker)

## 🚀 Швидкий старт

### Автоматичне встановлення (Linux/Mac)

```bash
# 1. Клонуйте репозиторій
git clone <repository-url>
cd news_relay

# 2. Запустіть setup script
bash setup.sh

# Скрипт створить .env файл - відредагуйте його з вашими токенами
# Потім запустіть знову:
bash setup.sh
```

### Ручне встановлення

#### 1. Налаштуйте змінні оточення

Створіть файл `.env` з наступним вмістом:

```env
# Telegram Bot Configuration
TG_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TG_API_ID=12345678
TG_API_HASH=0123456789abcdef0123456789abcdef
TG_SESSION_PATH=.tg_session/session.session

# OpenAI Configuration
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# Database Configuration
DATABASE_URL=postgresql+asyncpg://news_relay:password@postgres:5432/news_relay

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Application Configuration
TIMEZONE=Europe/Kyiv
LOG_LEVEL=INFO
```

#### 2. Запустіть Docker контейнери

```bash
docker-compose up -d --build
```

#### 3. Виконайте міграції БД

```bash
docker-compose exec bot alembic upgrade head
```

#### 4. Перевірте статус

```bash
docker-compose ps
docker-compose logs -f bot
```

## 📖 Використання бота

### 1️⃣ Початкове налаштування

1. Знайдіть свого бота в Telegram
2. Відправте `/start`
3. Оберіть "📢 Мої канали"

### 2️⃣ Додайте канал

1. Додайте бота як адміністратора вашого каналу з правами публікації
2. У боті натисніть "➕ Додати канал"
3. Переслати будь-яке повідомлення з каналу боту
4. Канал буде додано автоматично

### 3️⃣ Додайте джерело новин

1. Оберіть "📰 Мої джерела" → "➕ Додати джерело"
2. Виберіть тип джерела:
   - **Telegram-канал**: введіть @username або t.me/username
   - **RSS-стрічка**: введіть URL RSS feed
   - **Веб-сайт**: введіть URL сайту

### 4️⃣ Створіть зв'язок

1. Оберіть "🔗 Зв'язки" → "➕ Створити зв'язок"
2. Виберіть джерело
3. Виберіть канал для публікації
4. Зв'язок створено!

### 5️⃣ Налаштування

- **Інтервал публікацій**: за замовчуванням 60 хвилин, можна змінити
- **Мова**: автоматичне визначення або ручне налаштування
- **Стиль**: нейтральний, офіційний, неформальний, стислий

## 🛠️ Команди Make (для розробки)

```bash
make help          # Показати всі команди
make up            # Запустити всі сервіси
make down          # Зупинити всі сервіси
make logs          # Показати логи
make logs-bot      # Логи бота
make logs-worker   # Логи worker
make shell-bot     # Shell в контейнері бота
make db-migrate    # Застосувати міграції
make db-revision   # Створити нову міграцію
make clean         # Очистити все (видаляє дані!)
```

## 🏗️ Архітектура

```
┌─────────────────────────────────────────────────────┐
│                  Telegram User                       │
│                       ↓                              │
│                   Admin Bot                          │
│              (управління через Telegram)             │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│                   PostgreSQL                         │
│  (users, channels, sources, bindings, posts)        │
└─────────────────────────────────────────────────────┘
                         ↓
┌──────────────┬──────────────────┬───────────────────┐
│   Worker     │    Connectors    │    Publisher      │
│              │                  │                   │
│ • Ingestion  │ • Telegram       │ • Scheduler       │
│ • Rewriting  │ • RSS            │ • Formatter       │
│ • Publishing │ • Website        │ • Bot API         │
└──────────────┴──────────────────┴───────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│                   OpenAI API                         │
│              (переписування контенту)                │
└─────────────────────────────────────────────────────┘
```

### Модулі

- **`app/adminbot/`** - Telegram bot інтерфейс для користувачів
- **`app/connectors/`** - Збір контенту з джерел (Telegram, RSS, сайти)
- **`app/db/`** - Моделі БД та репозиторій з ізоляцією даних
- **`app/llm/`** - Інтеграція з GPT API для переписування
- **`app/publisher/`** - Публікація постів у канали
- **`app/worker/`** - Фонові задачі (ingestion, rewriting)
- **`app/processing/`** - Обробка контенту (нормалізація, дедуплікація)
- **`app/media/`** - Робота з медіа-файлами

## 🔒 Безпека

- ✅ **Ізоляція даних**: кожен користувач бачить тільки свої канали та джерела
- ✅ **Перевірка прав**: бот публікує тільки в канали, де він адміністратор
- ✅ **Захист БД**: всі запити включають `owner_user_id`
- ✅ **Модерація**: автоматична перевірка контенту перед публікацією

## 📊 Моніторинг

### Перегляд логів

```bash
# Всі логи
docker-compose logs -f

# Тільки бот
docker-compose logs -f bot

# Тільки worker
docker-compose logs -f worker

# Тільки БД
docker-compose logs -f postgres
```

### Файли логів

Логи також зберігаються в директорії `logs/`:
- `logs/news_relay_YYYY-MM-DD.log` - всі логи
- `logs/errors_YYYY-MM-DD.log` - тільки помилки

## 🔧 Розробка

### Локальний запуск (без Docker)

```bash
# Встановіть Poetry
pip install poetry

# Встановіть залежності
poetry install

# Запустіть PostgreSQL та Redis локально або через Docker
docker-compose up -d postgres redis

# Відредагуйте .env для локального підключення
export DATABASE_URL="postgresql+asyncpg://news_relay:password@localhost:5432/news_relay"
export REDIS_URL="redis://localhost:6379/0"

# Застосуйте міграції
poetry run alembic upgrade head

# Запустіть бота
poetry run python -m app.main

# У іншому терміналі - worker
poetry run python -m app.worker.queue
```

### Створення міграцій

```bash
# Автоматична генерація після зміни моделей
docker-compose exec bot alembic revision --autogenerate -m "Your message"

# Або через Make
make db-revision

# Застосувати міграції
make db-migrate
```

### Тестування

```bash
# Запустити тести
docker-compose exec bot poetry run pytest

# Запустити з coverage
docker-compose exec bot poetry run pytest --cov=app
```

## 🚀 Production Deployment

### Рекомендації

1. **Змініть паролі БД** в `docker-compose.yml` та `.env`
2. **Використовуйте secrets** для чутливих даних
3. **Налаштуйте backup БД** (pg_dump)
4. **Додайте reverse proxy** (nginx) для веб-інтерфейсу (майбутня функція)
5. **Моніторинг**: Prometheus + Grafana
6. **Ліміти**: додайте обмеження на кількість джерел/каналів

### Масштабування

Для великого навантаження:

1. Винесіть worker в окремі контейнери (можна запустити кілька)
2. Використовуйте Celery або RQ замість APScheduler
3. Додайте Redis Cluster
4. Використовуйте PostgreSQL реплікацію

## ❓ Troubleshooting

### Бот не відповідає

```bash
# Перевірте статус
docker-compose ps

# Перегляньте логи
docker-compose logs bot

# Перезапустіть
docker-compose restart bot
```

### Помилка підключення до БД

```bash
# Перевірте, чи запущена БД
docker-compose ps postgres

# Перевірте логи БД
docker-compose logs postgres

# Рестарт БД
docker-compose restart postgres
```

### Telethon session помилки

```bash
# Видаліть session файл
rm -rf .tg_session/*

# Рестарт бота (Telethon попросить авторизацію)
docker-compose restart bot
```

## 📝 TODO / Майбутні функції

- [ ] Веб-панель адміністрування (FastAPI + React)
- [ ] Користувацькі GPT ключі (кожен користувач може додати свій)
- [ ] Монетизація (Telegram Payments)
- [ ] Публікація в кілька каналів одночасно
- [ ] Фільтри контенту (теми, ключові слова, стоп-слова)
- [ ] Планування публікацій на конкретний час
- [ ] Статистика та аналітика
- [ ] Підтримка більше джерел (Twitter, Facebook, Instagram)

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 Ліцензія

MIT License - використовуйте вільно для комерційних та некомерційних проектів.

## 👨‍💻 Автор

Created with ❤️ for the Ukrainian tech community

---

**⭐ Якщо проект корисний - поставте зірку на GitHub!**

