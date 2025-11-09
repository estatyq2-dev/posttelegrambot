# Архітектура News Relay Bot

## Загальний огляд

News Relay Bot - це мультитенантний сервіс для автоматичного збору, обробки та публікації новин з різних джерел у Telegram канали користувачів.

## Ключові принципи

### 1. Мультитенантність

Кожен користувач має повну ізоляцію даних:

- Всі таблиці БД містять `owner_user_id`
- Всі запити фільтруються по власнику
- Користувачі не можуть бачити або змінювати дані інших користувачів

### 2. Асинхронність

Весь код використовує async/await для ефективної роботи з IO-операціями:

- aiogram для Telegram Bot API
- asyncpg для PostgreSQL
- aiohttp для HTTP запитів
- Telethon для читання Telegram каналів

### 3. Модульність

Проект розділений на логічні модулі з чіткою відповідальністю.

## Компоненти системи

### 1. Admin Bot (`app/adminbot/`)

**Призначення**: Інтерфейс користувача через Telegram

**Компоненти**:
- `router.py` - handlers для команд і callback
- `keyboards.py` - inline клавіатури
- `states.py` - FSM states для діалогів
- `access.py` - middleware для автентифікації

**Взаємодія**:
```
User → Telegram → Admin Bot → DB Repository
```

**Ключові функції**:
- Створення/редагування каналів
- Створення/редагування джерел
- Управління зв'язками (bindings)
- Налаштування інтервалів та стилів

### 2. Database (`app/db/`)

**Призначення**: Зберігання даних та бізнес-логіка

**Моделі**:

#### User
- Telegram користувач (власник даних)
- Створюється автоматично при першому контакті з ботом

#### Channel
- Telegram канал для публікацій
- Налаштування: інтервал, мова, стиль
- `owner_user_id` - ізоляція

#### Source
- Джерело контенту (Telegram/RSS/Website)
- Налаштування: інтервал перевірки
- `owner_user_id` - ізоляція

#### Binding
- Зв'язок Source → Channel
- Багато-до-багатьох через проміжну таблицю

#### RawMessage
- Сирий контент з джерела
- Зберігається до обробки
- Дедуплікація через `content_hash`

#### Post
- Готовий пост для публікації
- Статуси: RAW → PROCESSING → READY → PUBLISHED
- Пов'язаний з RawMessage та Channel

**Repository Pattern**:

```python
# Всі методи приймають owner_user_id для ізоляції
async def get_channels(owner_user_id: int) -> List[Channel]:
    stmt = select(Channel).where(Channel.owner_user_id == owner_user_id)
    ...
```

### 3. Connectors (`app/connectors/`)

**Призначення**: Збір контенту з різних джерел

#### Telegram Ingestor (Telethon)
```python
async def ingest_telegram_source(source: Source, repo: Repository) -> int:
    # 1. Підключення до Telegram через Telethon
    # 2. Читання останніх N повідомлень
    # 3. Завантаження медіа (якщо є)
    # 4. Збереження у raw_messages
    # 5. Дедуплікація
```

**Особливості**:
- Використовує Telegram User API (не Bot API)
- Потребує API_ID та API_HASH
- Сесія зберігається для повторного використання

#### RSS Ingestor
```python
async def ingest_rss_source(source: Source, repo: Repository) -> int:
    # 1. Завантаження RSS feed
    # 2. Парсинг через feedparser
    # 3. Витяг тексту з HTML
    # 4. Збереження у raw_messages
```

**Особливості**:
- Підтримка різних RSS форматів
- Витяг тексту з HTML через BeautifulSoup
- Додавання посилання на оригінал

### 4. LLM Integration (`app/llm/`)

**Призначення**: Переписування контенту через GPT

**Архітектура**:

```
Original Text → System Prompt + User Prompt → OpenAI API → Rewritten Text
```

**Prompts**:

```python
# System Prompt
"Ти — редактор новин. Перепиши текст своїми словами..."

# Модифікатори
- Style: neutral, formal, casual, brief
- Language: uk, en, ru
- Custom: користувацький prompt з налаштувань каналу
```

**Клієнт**:

```python
class LLMClient:
    async def chat_completion(messages, temperature=0.7) -> str:
        # Асинхронний запит до OpenAI API
        # Підтримка OpenAI-сумісних API
```

### 5. Worker (`app/worker/`)

**Призначення**: Фонові задачі

#### Tasks:

1. **Ingestion Task**
   - Періодично (кожні 10 хв) перевіряє всі активні джерела
   - Збирає новий контент
   - Зберігає у `raw_messages`

2. **Rewriting Task**
   - Періодично (кожні 2 хв) обробляє необроблені повідомлення
   - Переписує через GPT для кожного зв'язаного каналу
   - Створює готові пости зі статусом READY

3. **Publishing Task**
   - Не використовується (замінено на scheduler)

**Scheduler**:

```python
# APScheduler for periodic tasks
scheduler.add_job(
    ingest_all_sources_task,
    trigger=IntervalTrigger(minutes=10),
    ...
)
```

### 6. Publisher (`app/publisher/`)

**Призначення**: Публікація готових постів

**Scheduler**:

```python
# Для кожного активного каналу створюється job
scheduler.add_job(
    run_channel_tick,
    trigger=IntervalTrigger(minutes=channel.publish_interval_minutes),
    args=[channel.id],
    ...
)
```

**Publishing Flow**:

```
1. run_channel_tick(channel_id)
2. Get next READY post for channel
3. Publish to Telegram (text + media)
4. Update post status to PUBLISHED
5. Update channel.last_published_at
```

**Media Handling**:

```python
if len(media_paths) == 1:
    # Single photo
    await bot.send_photo(chat_id, photo, caption=text)
else:
    # Media group (2-10 items)
    await bot.send_media_group(chat_id, media_group)
```

## Потоки даних

### 1. Ingestion Flow

```
Source → Connector → RawMessage → Worker (Rewrite) → Post → Publisher → Channel
```

Детально:

```
1. User creates Source and Binding
2. Worker periodically checks Source
3. Connector fetches new content
4. Content saved as RawMessage
5. Worker processes RawMessage
6. LLM rewrites for each bound Channel
7. Post created with status READY
8. Publisher publishes at interval
```

### 2. User Management Flow

```
User sends /start → Middleware checks User exists → If not, create User
                                                 → Add to context
                                                 → Pass to handler
```

### 3. Channel Creation Flow

```
1. User: "Add channel"
2. Bot: "Forward message from channel"
3. User forwards message
4. Bot checks if from channel
5. Bot checks if bot is admin
6. Bot creates Channel record
7. Bot shows channel details
```

## Планувальники (Schedulers)

Система використовує два scheduler:

### 1. Worker Scheduler

```python
# app/worker/queue.py
# Періодичні задачі:
- Ingestion (кожні 10 хв)
- Rewriting (кожні 2 хв)
```

### 2. Publisher Scheduler

```python
# app/publisher/scheduler.py
# Динамічні задачі:
- Для кожного активного каналу
- Interval = channel.publish_interval_minutes
- Додається/видаляється при зміні каналу
```

## Безпека та ізоляція

### Middleware

```python
class EnsureUserMiddleware:
    async def __call__(self, handler, event, data):
        # 1. Extract telegram_id from event
        # 2. Get or create User in DB
        # 3. Add User and Repository to context
        # 4. Call handler
```

### Repository

```python
# Всі методи вимагають owner_user_id
async def get_channels(owner_user_id: int):
    return select(Channel).where(
        Channel.owner_user_id == owner_user_id
    )
```

### Database Constraints

```sql
-- Унікальність на рівні БД
UNIQUE (owner_user_id, telegram_id)

-- Індекси для швидкого пошуку
INDEX (owner_user_id, is_active)
```

## Масштабування

### Горизонтальне

1. **Multiple Workers**
   ```bash
   # Run multiple worker containers
   docker-compose up -d --scale worker=3
   ```

2. **Separate Publisher**
   ```bash
   # Publisher as separate service
   docker-compose up -d bot worker publisher
   ```

### Вертикальне

1. **Database**
   - PostgreSQL connection pool
   - Read replicas для читання
   - Connection pooling (PgBouncer)

2. **Redis**
   - Redis Cluster для великих черг
   - Separate Redis для різних цілей

### Оптимізації

1. **Caching**
   - Redis для кешування користувачів
   - Кешування конфігурації каналів

2. **Batch Processing**
   - Обробка повідомлень пакетами
   - Bulk insert для постів

3. **Rate Limiting**
   - Ліміти на Telegram API
   - Ліміти на OpenAI API
   - Per-user rate limits

## Моніторинг

### Логування

```python
# Structured logging через loguru
logger.info(
    f"Post {post_id} published to channel {channel_id}",
    extra={"user_id": user_id, "post_id": post_id}
)
```

### Metrics (майбутнє)

- Кількість активних користувачів
- Кількість джерел/каналів
- Швидкість обробки
- Помилки публікацій

## Технічний стек

- **Python 3.11+**
- **aiogram 3** - Telegram Bot API
- **SQLAlchemy 2** - ORM
- **asyncpg** - PostgreSQL driver
- **Telethon** - Telegram User API
- **APScheduler** - Task scheduling
- **aiohttp** - HTTP client
- **loguru** - Logging
- **Alembic** - Migrations
- **Docker** - Containerization

