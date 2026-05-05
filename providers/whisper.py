import requests

from config import config
from .base import STTProvider


class WhisperProvider(STTProvider):
    """
    Использует локальный сервис onerahmet/openai-whisper-asr-webservice.
    Docker: http://whisper:9000
    """

    def transcribe(self, audio_bytes: bytes, filename: str = "audio.ogg") -> str:
        response = requests.post(
            f"{config.whisper_url}/asr",
            params={"encode": "true", "task": "transcribe", "language": "ru", "output": "txt"},
            files={"audio_file": (filename, audio_bytes, "audio/ogg")},
            timeout=60,
        )
        response.raise_for_status()
        return response.text.strip()
