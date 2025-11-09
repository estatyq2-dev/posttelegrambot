# News Relay Bot - Швидкий старт ⚡

## За 5 хвилин від нуля до працюючого бота

### Крок 1: Отримайте токени (3 хв)

#### Telegram Bot Token
1. Telegram → @BotFather → `/newbot`
2. Назва: "My News Bot"
3. Username: `my_news_relay_bot`
4. Збережіть токен: `123456:ABC...`

#### Telegram API (my.telegram.org)
1. https://my.telegram.org → Login
2. API development tools → Create app
3. Збережіть `api_id` та `api_hash`

#### OpenAI Key
1. https://platform.openai.com → API keys
2. Create new key
3. Збережіть `sk-proj-...`

### Крок 2: Встановіть (1 хв)

```bash
# Завантажте проект
git clone <your-repo>
cd news-relay-bot

# Створіть .env
cat > .env << EOF
TG_BOT_TOKEN=YOUR_BOT_TOKEN
TG_API_ID=YOUR_API_ID
TG_API_HASH=YOUR_API_HASH
OPENAI_API_KEY=YOUR_OPENAI_KEY
DATABASE_URL=postgresql+asyncpg://news_relay:password@postgres:5432/news_relay
REDIS_URL=redis://redis:6379/0
TIMEZONE=Europe/Kyiv
LOG_LEVEL=INFO
EOF

# Відредагуйте .env і вставте реальні токени
nano .env
```

### Крок 3: Запустіть (1 хв)

```bash
# Linux/Mac - автоматично
bash setup.sh

# Або вручну
docker-compose up -d --build
sleep 15
docker-compose exec bot alembic upgrade head
```

### Крок 4: Користуйтеся!

#### У Telegram боті:

1. **Знайдіть бота** → `/start`

2. **Додайте канал**:
   - "📢 Мої канали" → "➕ Додати канал"
   - Спочатку додайте бота адміном вашого каналу!
   - Перешліть будь-яке повідомлення з каналу боту

3. **Додайте джерело**:
   - "📰 Мої джерела" → "➕ Додати джерело"
   - Оберіть тип (Telegram/RSS)
   - Введіть @channel або URL

4. **Створіть зв'язок**:
   - "🔗 Зв'язки" → "➕ Створити зв'язок"
   - Оберіть джерело та канал

5. **Готово!** 🎉
   - Бот автоматично збирає новини
   - Переписує через GPT
   - Публікує в ваш канал

## Приклади

### Додати Telegram канал як джерело

```
Бот: Оберіть тип джерела
Ви: [📱 Telegram-канал]
Бот: Введіть username каналу
Ви: @unian або t.me/unian
Бот: ✅ Джерело додано!
```

### Додати RSS

```
Бот: Оберіть тип джерела
Ви: [📡 RSS-стрічка]
Бот: Введіть URL RSS feed
Ви: https://example.com/rss
Бот: ✅ Джерело додано!
```

### Налаштування інтервалу

```
Мої канали → [Ваш канал] → ✏️ Редагувати
→ Встановіть інтервал (наприклад, "30m" або "2h")
```

## Перевірка

```bash
# Статус сервісів
docker-compose ps

# Логи бота
docker-compose logs -f bot

# Логи worker
docker-compose logs -f worker

# Все працює, якщо бачите:
# ✅ "News Relay Bot started successfully"
# ✅ "Starting bot polling..."
# ✅ "Worker scheduler started"
```

## Troubleshooting

### Бот не відповідає?
```bash
docker-compose restart bot
docker-compose logs bot
```

### "Invalid bot token"?
Перевірте `.env` - токен без пробілів та лапок:
```env
TG_BOT_TOKEN=123456:ABCdef  ✅
TG_BOT_TOKEN="123456:ABCdef"  ❌
```

### "Can't connect to database"?
```bash
docker-compose restart postgres
sleep 10
docker-compose restart bot
```

### Telethon авторизація?
При першому запуску може попросити номер телефону:
```bash
docker-compose logs -f bot
# Якщо бачите "Enter phone number":
docker-compose run --rm bot python -c "from telethon import TelegramClient; ..."
```

## Корисні команди

```bash
# Зупинити
docker-compose down

# Рестарт
docker-compose restart

# Переглянути логи
docker-compose logs -f

# Shell в контейнері
docker-compose exec bot bash

# Видалити все (включно з даними!)
docker-compose down -v
```

## Що далі?

1. 📖 Повна документація: [README.md](README.md)
2. 🔧 Детальна інструкція: [INSTALL.md](INSTALL.md)
3. 🏗️ Архітектура: [ARCHITECTURE.md](ARCHITECTURE.md)

## Підтримка

- GitHub Issues для багів
- Telegram: @yourusername
- Email: your@email.com

---

**Успіхів з автоматизацією контенту! 🚀**

