from google import genai
from google.genai import types

from config import config
from .base import LLMProvider, VisionProvider


class GeminiLLMProvider(LLMProvider, VisionProvider):
    def __init__(self):
        self._client = genai.Client(api_key=config.gemini_api_key)
        self._model = config.gemini_llm_model

    def complete(
        self,
        messages: list[dict],
        system: str | None = None,
        temperature: float = 0.7,
    ) -> str:
        # конвертируем из OpenAI-формата в Gemini-формат
        contents = [
            types.Content(
                role="user" if m["role"] == "user" else "model",
                parts=[types.Part(text=m["content"])],
            )
            for m in messages
        ]

        response = self._client.models.generate_content(
            model=self._model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system,
                temperature=temperature,
            ),
        )
        return response.text

    def read_text(self, image_bytes: bytes) -> str:
        part_image = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
        part_prompt = types.Part(
            text="Прочитай и перепиши весь текст с изображения дословно. "
                 "Если текст рукописный — расшифруй как можно точнее. "
                 "Верни только текст, без комментариев."
        )
        response = self._client.models.generate_content(
            model=config.gemini_vision_model,
            contents=[types.Content(parts=[part_image, part_prompt])],
        )
        return response.text
