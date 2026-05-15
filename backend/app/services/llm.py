import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from functools import lru_cache

from app.config import settings

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    @abstractmethod
    def stream_chat(
        self, system_prompt: str, messages: list[dict[str, str]]
    ) -> AsyncIterator[str]:
        """Stream chat completion tokens as an async iterator."""


class OpenAILLMProvider(LLMProvider):
    def __init__(self) -> None:
        from openai import AsyncOpenAI

        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_chat_model

    async def stream_chat(
        self, system_prompt: str, messages: list[dict[str, str]]
    ) -> AsyncIterator[str]:
        full_messages = [{"role": "system", "content": system_prompt}, *messages]
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=full_messages,
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class AnthropicLLMProvider(LLMProvider):
    def __init__(self) -> None:
        from anthropic import AsyncAnthropic

        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = settings.anthropic_chat_model

    async def stream_chat(
        self, system_prompt: str, messages: list[dict[str, str]]
    ) -> AsyncIterator[str]:
        async with self.client.messages.stream(
            model=self.model,
            system=system_prompt,
            messages=messages,
            max_tokens=4096,
        ) as stream:
            async for text in stream.text_stream:
                yield text


@lru_cache(maxsize=1)
def get_llm_provider() -> LLMProvider:
    provider = settings.llm_provider.lower()
    if provider == "openai":
        return OpenAILLMProvider()
    elif provider == "anthropic":
        return AnthropicLLMProvider()
    else:
        raise ValueError(
            f"Unknown LLM provider: '{provider}'. Supported: 'openai', 'anthropic'."
        )
