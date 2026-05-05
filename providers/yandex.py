from openai import OpenAI

from config import config
from .base import LLMProvider


class YandexProvider(LLMProvider):
    def __init__(self):
        self._client = OpenAI(
            api_key=config.yandex_api_key,
            base_url="https://ai.api.cloud.yandex.net/v1",
        )
        self._model = f"gpt://{config.yandex_folder_id}/{config.yandex_model}"

    def complete(
        self,
        messages: list[dict],
        system: str | None = None,
        temperature: float = 0.7,
    ) -> str:
        all_messages = []
        if system:
            all_messages.append({"role": "system", "content": system})
        all_messages.extend(messages)

        response = self._client.chat.completions.create(
            model=self._model,
            messages=all_messages,
            temperature=temperature,
            max_tokens=500,
        )
        return response.choices[0].message.content
