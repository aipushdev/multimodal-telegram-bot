import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    bot_token: str
    database_url: str

    # LLM
    llm_provider: str
    yandex_api_key: str
    yandex_folder_id: str
    yandex_model: str

    # Image generation
    image_provider: str
    gemini_api_key: str
    gemini_image_model: str
    gemini_llm_model: str
    gemini_vision_model: str

    # Speech-to-text
    stt_provider: str
    whisper_url: str

    # Bot mode
    mode: str           # polling | webhook
    webhook_url: str    # https://yourdomain.com — only for webhook mode
    webhook_port: int

    history_limit: int
    admin_user_id: int

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            bot_token=os.environ["BOT_TOKEN"],
            database_url=os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5441/psychoai"),
            llm_provider=os.getenv("LLM_PROVIDER", "yandex"),
            yandex_api_key=os.getenv("YANDEX_API_KEY", ""),
            yandex_folder_id=os.getenv("YANDEX_FOLDER_ID", ""),
            yandex_model=os.getenv("YANDEX_MODEL", "yandexgpt-lite"),
            image_provider=os.getenv("IMAGE_PROVIDER", "gemini"),
            gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
            gemini_image_model=os.getenv("GEMINI_IMAGE_MODEL", "imagen-4.0-fast-generate-001"),
            gemini_llm_model=os.getenv("GEMINI_LLM_MODEL", "gemini-2.0-flash"),
            gemini_vision_model=os.getenv("GEMINI_VISION_MODEL", "gemini-2.0-flash"),
            stt_provider=os.getenv("STT_PROVIDER", "whisper"),
            whisper_url=os.getenv("WHISPER_URL", "http://whisper:9000"),
            mode=os.getenv("MODE", "polling"),
            webhook_url=os.getenv("WEBHOOK_URL", ""),
            webhook_port=int(os.getenv("WEBHOOK_PORT", "8443")),
            history_limit=int(os.getenv("HISTORY_LIMIT", "10")),
            admin_user_id=int(os.getenv("ADMIN_USER_ID", "0")),
        )


config = Config.from_env()
