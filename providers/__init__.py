from config import config
from .base import LLMProvider, ImageProvider, STTProvider, VisionProvider


def get_llm() -> LLMProvider:
    if config.llm_provider == "yandex":
        from .yandex import YandexProvider
        return YandexProvider()
    if config.llm_provider == "gemini":
        from .gemini_llm import GeminiLLMProvider
        return GeminiLLMProvider()
    raise ValueError(f"Unknown LLM provider: {config.llm_provider!r}")


def get_image_gen() -> ImageProvider:
    if config.image_provider == "gemini":
        from .gemini import GeminiImageProvider
        return GeminiImageProvider()
    raise ValueError(f"Unknown image provider: {config.image_provider!r}")


def get_vision() -> VisionProvider:
    if config.llm_provider == "gemini":
        from .gemini_llm import GeminiLLMProvider
        return GeminiLLMProvider()
    raise ValueError(f"Vision not supported for provider: {config.llm_provider!r}")


def get_stt() -> STTProvider:
    if config.stt_provider == "whisper":
        from .whisper import WhisperProvider
        return WhisperProvider()
    raise ValueError(f"Unknown STT provider: {config.stt_provider!r}")
