# Детальна інструкція з встановлення News Relay Bot

## Крок 1: Підготовка

### 1.1. Отримання Telegram Bot Token

1. Відкрийте Telegram та знайдіть @BotFather
2. Відправте команду `/newbot`
3. Введіть назву бота (наприклад, "My News Relay Bot")
4. Введіть username бота (має закінчуватися на `bot`, наприклад `my_news_relay_bot`)
5. Збережіть отриманий токен (формат: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 1.2. Отримання Telegram API credentials

1. Перейдіть на https://my.telegram.org
2. Увійдіть з вашим номером телефону
3. Оберіть "API development tools"
4. Створіть новий додаток (або використайте існуючий)
5. Збережіть:
   - `api_id` (числовий ID)
   - `api_hash` (строка з літер і цифр)

### 1.3. Отримання OpenAI API Key

1. Перейдіть на https://platform.openai.com
2. Зареєструйтеся або увійдіть
3. Перейдіть в розділ "API keys"
4. Натисніть "Create new secret key"
5. Збережіть ключ (формат: `sk-proj-...`)

⚠️ **Важливо**: OpenAI API платний. Переконайтеся, що у вас є кошти на рахунку або використовуйте альтернативні OpenAI-сумісні API (наприклад, OpenRouter, Together AI).

## Крок 2: Встановлення системних вимог

### Linux (Ubuntu/Debian)

```bash
# Оновіть систему
sudo apt update && sudo apt upgrade -y

# Встановіть Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Додайте користувача до групи docker
sudo usermod -aG docker $USER

# Встановіть Docker Compose
sudo apt install docker-compose -y

# Перелогіньтеся або виконайте
newgrp docker
```

### macOS

```bash
# Встановіть Docker Desktop для Mac
# Завантажте з https://www.docker.com/products/docker-desktop

# Або через Homebrew
brew install --cask docker
```

### Windows

1. Завантажте Docker Desktop: https://www.docker.com/products/docker-desktop
2. Встановіть WSL 2: https://docs.microsoft.com/en-us/windows/wsl/install
3. Перезавантажте комп'ютер

## Крок 3: Завантаження проекту

```bash
# Клонуйте репозиторій (замініть URL на ваш)
git clone https://github.com/yourusername/news-relay-bot.git
cd news-relay-bot

# Або завантажте ZIP архів і розпакуйте
```

## Крок 4: Конфігурація

### 4.1. Створення .env файлу

```bash
# Linux/Mac
cp .env.example .env

# Windows (PowerShell)
Copy-Item .env.example .env
```

### 4.2. Редагування .env

Відкрийте `.env` у текстовому редакторі та замініть значення:

```env
# Telegram Bot Configuration
TG_BOT_TOKEN=ВАШ_ТОКЕН_БОТА_ТУТ
TG_API_ID=ВАШ_API_ID
TG_API_HASH=ВАШ_API_HASH
TG_SESSION_PATH=.tg_session/session.session

# OpenAI Configuration
OPENAI_API_KEY=ВАШ_OPENAI_KEY
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# Database Configuration (можна залишити як є)
DATABASE_URL=postgresql+asyncpg://news_relay:password@postgres:5432/news_relay

# Redis Configuration (можна залишити як є)
REDIS_URL=redis://redis:6379/0

# Application Configuration
TIMEZONE=Europe/Kyiv  # Змініть на ваш часовий пояс
LOG_LEVEL=INFO
```

### 4.3. (Опціонально) Змініть паролі БД

Відредагуйте `docker-compose.yml`:

```yaml
postgres:
  environment:
    POSTGRES_PASSWORD: your_secure_password_here  # Змініть цей пароль
```

І відповідно у `.env`:

```env
DATABASE_URL=postgresql+asyncpg://news_relay:your_secure_password_here@postgres:5432/news_relay
```

## Крок 5: Запуск

### Автоматичний запуск (Linux/Mac)

```bash
chmod +x setup.sh
./setup.sh
```

Скрипт автоматично:
- Створить необхідні директорії
- Запустить Docker контейнери
- Виконає міграції БД

### Ручний запуск

```bash
# 1. Створіть директорії
mkdir -p logs media_storage .tg_session

# 2. Запустіть контейнери
docker-compose up -d --build

# 3. Дочекайтеся запуску БД (10-15 секунд)
sleep 15

# 4. Виконайте міграції
docker-compose exec bot alembic upgrade head
```

## Крок 6: Перевірка

```bash
# Перевірте статус контейнерів
docker-compose ps

# Всі сервіси повинні бути "Up"
# Очікуваний вивід:
# news_relay_bot      Up
# news_relay_worker   Up
# news_relay_postgres Up (healthy)
# news_relay_redis    Up (healthy)
```

```bash
# Перегляньте логи бота
docker-compose logs bot

# Ви повинні побачити щось схоже:
# "News Relay Bot started successfully"
# "Starting bot polling..."
```

## Крок 7: Налаштування Telethon (перший запуск)

При першому запуску Telethon (для читання Telegram каналів) може попросити авторизацію:

```bash
# Перегляньте логи
docker-compose logs -f bot

# Якщо побачите запит на phone number:
# 1. Зупиніть бота: Ctrl+C
# 2. Запустіть інтерактивну сесію:
docker-compose run --rm bot python -c "from telethon import TelegramClient; client = TelegramClient('.tg_session/session.session', YOUR_API_ID, 'YOUR_API_HASH'); client.start()"

# Введіть ваш номер телефону (з кодом країни, +380...)
# Введіть код з Telegram
# Якщо ввімкнена 2FA - введіть пароль

# 3. Після успішної авторизації перезапустіть:
docker-compose restart bot
```

## Крок 8: Тестування

1. Знайдіть вашого бота в Telegram (за username)
2. Натисніть "Start" або відправте `/start`
3. Ви повинні побачити вітальне повідомлення з меню

**Вітаємо! Бот встановлено і працює! 🎉**

## Наступні кроки

1. Додайте канал (див. README.md розділ "Використання бота")
2. Додайте джерело новин
3. Створіть зв'язок
4. Чекайте на автоматичні публікації!

## Troubleshooting

### Проблема: "Cannot connect to Docker daemon"

```bash
# Запустіть Docker service
sudo systemctl start docker

# Або перезапустіть Docker Desktop (macOS/Windows)
```

### Проблема: Port 5432 already in use

У вас вже запущений PostgreSQL локально. Два варіанти:

1. Зупинити локальний PostgreSQL:
```bash
sudo systemctl stop postgresql
```

2. Або змінити порт у `docker-compose.yml`:
```yaml
postgres:
  ports:
    - "5433:5432"  # Використовуйте 5433 замість 5432
```

### Проблема: "Bot token is invalid"

Перевірте, що ви правильно скопіювали токен в `.env` без зайвих пробілів.

### Проблема: Бот не відповідає

```bash
# Перегляньте логи на наявність помилок
docker-compose logs bot

# Перезапустіть бота
docker-compose restart bot
```

## Додаткова допомога

- Відкрийте issue на GitHub
- Перевірте логи: `docker-compose logs -f`
- Приєднайтеся до Telegram групи підтримки (якщо є)

