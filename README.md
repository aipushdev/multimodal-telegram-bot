# Multimodal Telegram Bot

> AI-powered Telegram bot for gestalt therapy sessions.  
> Understands text, voice, and photos — all in a single conversation thread.

---

## What it does

A therapist or client opens Telegram and starts a session. They can type a message, send a voice note, or share a photo — the bot handles all three natively, maintains full session context, and responds as a gestalt-aware AI companion.

Three session modes: **therapy session**, **reflective diary**, and **metaphorical card work**.

---

## Architecture

```
Telegram
   │
   ├── text message  ──► Gemini Flash (LLM)
   │
   ├── voice message ──► Whisper STT ──► Gemini Flash (LLM)
   │
   └── photo         ──► Gemini Vision ──► Gemini Flash (LLM)
                                │
                         session context
                         (DB + past reports)
                                │
                           Response
```

Each modality goes through the same session context layer — the bot knows who the user is, what session type is active, and what was discussed in previous sessions.

---

## Key features

- **True multimodality** — voice, photo, and text handled in one unified session
- **Session lifecycle** — explicit start/end, session type selection (`/session`, `/diary`, `/card`)
- **Context continuity** — past session reports are injected into every new session prompt
- **Pluggable providers** — Whisper (OpenAI) or Yandex for STT; Gemini for LLM and Vision
- **Structured prompt system** — separate system prompts per session type (therapist, diary, card)
- **PostgreSQL + Alembic** — full session and message history with versioned migrations
- **Session scheduler** — automated session reminders and lifecycle management
- **Fully containerized** — one `docker compose up` to run everything

---

## Session types

| Mode | Command | Description |
|------|---------|-------------|
| Therapy session | `/session` | Full gestalt therapy dialogue with therapist-mode prompts |
| Reflective diary | `/diary` | Daily emotional reflection and journaling |
| Metaphorical card | `/card` | Image-based projection and metaphor work |

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| LLM | Gemini 2.0 Flash |
| Vision | Gemini Vision |
| STT | OpenAI Whisper |
| Bot framework | pyTelegramBotAPI |
| Database | PostgreSQL |
| Migrations | Alembic |
| Infra | Docker, Docker Compose |
| Package manager | uv |

---

## Project structure

```
handlers/
├── voice.py          # Voice → STT → LLM
├── photo.py          # Photo → Vision → LLM
├── text_handler.py   # Text → LLM
├── session.py        # Session start/end logic
└── report.py         # Session report generation

providers/
├── whisper.py        # OpenAI Whisper STT
├── gemini_llm.py     # Gemini text generation
├── gemini.py         # Gemini Vision
└── yandex.py         # Yandex STT (alternative)

prompts/
├── therapist.py      # Gestalt therapy session prompt
├── diary.py          # Reflective diary prompt
├── card_session.py   # Metaphorical card prompt
├── period_report.py  # Session summary prompt
└── session_report.py # End-of-session report prompt

session_lifecycle.py  # Context building across sessions
scheduler.py          # Automated session reminders
```

---

## Quick start

```bash
git clone https://github.com/aipushdev/multimodal-telegram-bot
cd multimodal-telegram-bot

cp .env.example .env
# Fill in: TELEGRAM_BOT_TOKEN, GEMINI_API_KEY, OPENAI_API_KEY, DATABASE_URL

docker compose up -d
docker compose exec bot python migrate.py
```

---

## Background

Built as the client-facing component of the PsychoAI platform.  
The bot serves as a daily emotional companion between therapy sessions — helping clients reflect, process, and track their inner work through whatever input feels natural in the moment.

---

*Author: [Alexander Kirilov](https://www.linkedin.com/in/kirilovu/) · [aipush.dev](https://aipush.dev)*
