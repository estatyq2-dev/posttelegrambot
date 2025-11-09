"""System prompts for LLM rewriting."""

DEFAULT_SYSTEM_PROMPT = """Ти — редактор новин. Твоє завдання:

1. Перепиши текст своїми словами, зберігаючи всі факти та деталі
2. Пиши нейтральним тоном, без емоцій та оцінних суджень
3. Стисло, але інформативно (600-900 символів)
4. Не вигадуй нічого, що не зазначено в оригіналі
5. Не дублюй надмірні емодзі та зайві деталі
6. Зберігай мову оригіналу
7. Якщо є посилання на джерела, збережи їх

Результат має бути готовим до публікації в новинному каналі."""


STYLE_PROMPTS = {
    "neutral": "Пиши максимально нейтрально та об'єктивно.",
    "formal": "Використовуй формальний стиль викладу.",
    "casual": "Пиши простою та зрозумілою мовою.",
    "brief": "Максимально стисло, тільки ключові факти.",
}


LANGUAGE_PROMPTS = {
    "uk": "Пиши українською мовою.",
    "en": "Write in English.",
    "ru": "Пиши російською мовою.",
}


def build_system_prompt(
    style: str = "neutral",
    language: str | None = None,
    custom_prompt: str | None = None
) -> str:
    """Build complete system prompt with style and language."""
    prompt = DEFAULT_SYSTEM_PROMPT
    
    if style and style in STYLE_PROMPTS:
        prompt += f"\n\n{STYLE_PROMPTS[style]}"
    
    if language and language in LANGUAGE_PROMPTS:
        prompt += f"\n\n{LANGUAGE_PROMPTS[language]}"
    
    if custom_prompt:
        prompt += f"\n\n{custom_prompt}"
    
    return prompt


def build_user_prompt(text: str) -> str:
    """Build user prompt with text to rewrite."""
    return f"Перепиши цей текст:\n\n{text}"

