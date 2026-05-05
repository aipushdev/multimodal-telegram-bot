from google import genai
from google.genai import types

from config import config
from .base import ImageProvider


class GeminiImageProvider(ImageProvider):
    def __init__(self):
        self._client = genai.Client(api_key=config.gemini_api_key)

    def generate(self, prompt: str) -> bytes:
        result = self._client.models.generate_images(
            model=config.gemini_image_model,
            prompt=prompt,
            config=types.GenerateImagesConfig(number_of_images=1),
        )
        return result.generated_images[0].image.image_bytes
