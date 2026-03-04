import logging
from abc import ABC, abstractmethod
from collections.abc import Generator

from app.config import settings

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    @abstractmethod
    def stream_chat(
        self, system_prompt: str, messages: list[dict[str, str]]
    ) -> Generator[str, None, None]:
        """Stream chat completion tokens."""


class OpenAILLMProvider(LLMProvider):
    def __init__(self) -> None:
        from openai import OpenAI

        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_chat_model

    def stream_chat(
        self, system_prompt: str, messages: list[dict[str, str]]
    ) -> Generator[str, None, None]:
        full_messages = [{"role": "system", "content": system_prompt}, *messages]
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=full_messages,
            stream=True,
        )
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class AnthropicLLMProvider(LLMProvider):
    def __init__(self) -> None:
        from anthropic import Anthropic

        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.anthropic_chat_model

    def stream_chat(
        self, system_prompt: str, messages: list[dict[str, str]]
    ) -> Generator[str, None, None]:
        with self.client.messages.stream(
            model=self.model,
            system=system_prompt,
            messages=messages,
            max_tokens=4096,
        ) as stream:
            yield from stream.text_stream


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
