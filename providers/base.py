from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    def complete(
        self,
        messages: list[dict],
        system: str | None = None,
        temperature: float = 0.7,
    ) -> str: ...


class ImageProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> bytes: ...


class STTProvider(ABC):
    @abstractmethod
    def transcribe(self, audio_bytes: bytes, filename: str = "audio.ogg") -> str: ...


class VisionProvider(ABC):
    @abstractmethod
    def read_text(self, image_bytes: bytes) -> str: ...
