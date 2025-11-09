"""OpenAI API client for text rewriting."""

from typing import Optional

import aiohttp
from loguru import logger

from app.config import get_settings


class LLMClient:
    """Async client for OpenAI-compatible API."""

    def __init__(self):
        """Initialize LLM client."""
        self.settings = get_settings()
        self.base_url = self.settings.openai_base_url
        self.api_key = self.settings.openai_api_key
        self.model = self.settings.openai_model

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Optional[str]:
        """Send chat completion request."""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(
                            f"OpenAI API error: {response.status} - {error_text}"
                        )
                        return None

                    data = await response.json()
                    
                    if "choices" in data and len(data["choices"]) > 0:
                        content = data["choices"][0]["message"]["content"]
                        return content.strip()
                    
                    logger.error(f"Unexpected API response: {data}")
                    return None

        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Unexpected error in chat_completion: {e}", exc_info=True)
            return None

    async def rewrite_text(
        self,
        text: str,
        system_prompt: str,
        temperature: float = 0.7,
    ) -> Optional[str]:
        """Rewrite text using GPT."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ]

        logger.debug(f"Rewriting text (length: {len(text)} chars)")
        
        result = await self.chat_completion(
            messages=messages,
            temperature=temperature,
        )

        if result:
            logger.debug(f"Rewrite successful (result length: {len(result)} chars)")
        else:
            logger.warning("Rewrite failed, no result from API")

        return result


# Global client instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get or create global LLM client."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client

