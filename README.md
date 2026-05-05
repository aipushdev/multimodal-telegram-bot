# Multimodal AI Telegram Bot

> Telegram bot that understands text, voice, and photos — and speaks back as an AI assistant. Built for a gestalt therapy use case, but the architecture works for any domain.

---

## What it does

Clients interact however is natural for them:

| Input | How it works |
|-------|-------------|
| **Text** | Direct to LLM |
| **Voice message** | Whisper STT transcription -> LLM |
| **Photo** (handwritten notes, diary pages) | Gemini Vision OCR -> LLM |
| **/card command** | LLM generates image prompt -> Gemini Imagen 4 |

All modalities feed into a **single conversation history** — the assistant remembers context across message types within a session.

---

## Architecture

```
Telegram User
      |
      +-- text  --------------------+
      |                             |
      +-- voice (ogg) -> Whisper -> +-> Session History -> Google Gemini -> Response
      |                             |
      +-- photo -> Gemini Vision -> +
      |
      +-- /card -> LLM prompt -> Gemini Imagen 4 -> Image
```

**Key design decision:** all modalities are normalized to text before reaching the LLM. This keeps the core logic simple and makes the system easy to extend with new input types.

---

## Stack

- **Python 3.11** - core
- **python-telegram-bot** - Telegram integration
- **Whisper** (self-hosted) - Speech-to-Text for voice messages
- **Google Gemini** (`gemini-2.0-flash`) - LLM + Vision
- **Gemini Imagen 4 Fast** - image generation
- **PostgreSQL** - conversation history persistence
- **Docker Compose** - all services: bot + whisper + db

---

## Key Implementation Notes

**Voice processing:**
```python
# ogg -> wav -> Whisper transcription
audio = await bot.get_file(message.voice.file_id)
transcript = whisper_client.transcribe(audio_bytes)
```

**Photo processing (Gemini Vision):**
```python
prompt = """Read and transcribe all text from this image exactly as written.
If handwritten - transcribe as accurately as possible.
Return only the text, no commentary."""
```

**Polling fix for callback queries:**
```python
# Required for inline keyboard callbacks to work
bot.infinity_polling(allowed_updates=["message", "callback_query"])
```

---

## Setup

```bash
git clone https://github.com/aipushdev/multimodal-telegram-bot
cd multimodal-telegram-bot

cp .env.example .env
# TELEGRAM_TOKEN, GEMINI_API_KEY, POSTGRES_URL

docker-compose up -d
```

Services started:
- `app` - Python Telegram bot
- `whisper` - self-hosted STT server
- `db` - PostgreSQL

---

## Project Structure

```
.
- bot.py                    # entry point, handler registration
- handlers/
  - text.py                 # text message handler
  - voice.py                # voice -> Whisper -> text
  - photo.py                # photo -> Gemini Vision -> text
  - commands.py             # /start, /clear, /card, /report
- providers/
  - gemini_llm.py           # LLM generation
  - gemini_vision.py        # Vision OCR
  - whisper_client.py       # STT client
  - imagen.py               # image generation
- db/
  - session.py              # conversation history
- docker-compose.yml
```

---

## Results

- Voice handler built in ~30 min with AI-assisted coding (vs 2-3 hours manually)
- All 3 input modalities working in unified conversation flow
- Image generation on `/card` command with LLM-enhanced prompts
- Deployed via Docker Compose, polling mode

---

_Built during Module 4 of AI Engineering course. Domain: gestalt therapy assistant._
