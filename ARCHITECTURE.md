# ARCHITECTURE.md — PsychoAI Bot

## Обзор

Telegram-бот для гештальт-терапии. Пользователь ведёт три типа сессий: терапевтическую, дневниковую и сессию по метафорической карте. Все сессии автоматически закрываются по таймеру, генерируют отчёт и сохраняют его в БД.

---

## Команды

| Команда | Описание |
|---------|----------|
| `/session` | Начать терапевтическую сессию (60 мин) |
| `/diary` | Начать сессию дневника (30 мин) |
| `/card` | Сгенерировать метафорическую карту и предложить сессию (25 мин) |
| `/report` | Сводный отчёт за выбранный период (карта + текст) |

---

## Типы сессий

### `/session` — Терапевтическая сессия (60 мин)
- Пользователь может писать текст, голосовые, фото рукописей
- Контекст для модели: системные репорты прошлых session-сессий + текущая переписка
- Промпт: гештальт-терапевт (открытые вопросы, без советов, работа с чувствами)

### `/diary` — Дневниковая сессия (30 мин)
- Те же типы ввода
- Контекст: системные репорты прошлых diary-сессий + текущая переписка
- Промпт: другой стиль — сбор чувств и событий дня, менее аналитичный

### `/card` — Сессия по метафорической карте (25 мин)
- **Флоу:**
  1. Берёт последние 3 session + 3 diary (не старше 2 недель)
  2. Генерирует метафорическую карту через Gemini Imagen
  3. Отправляет карту + inline: **[Да, начать сессию] [Нет]**
  4. При "Да": стартует сессия, бот спрашивает "Что ты видишь? Что откликается?"
  5. Модель проводит 3–4 вопроса в стиле МАК-мастера (не хардкод — генерит по ситуации)
  6. Затем органично переходит в диалог гештальт-терапевта
- Контекст: только сообщения текущей сессии + контент прошлых 3+3 сессий
- В `sessions` хранится `image_prompt` — промпт, использованный для генерации карты

---

## Жизненный цикл сессии

```
/session или /diary
    │
    ▼
INSERT sessions (status='active', started_at, ends_at = started_at + max_minutes)
    │
    ▼
Сообщение пользователя (текст / голос / фото)
    │
    ├─ Проверка: есть ли активная сессия?
    │       Нет → "Начни: /session, /diary или /card"
    │       Да  → продолжаем
    │
    ├─ save_message(session_id, user_id, chat_id, role, content)
    ├─ LLM ответ (с контекстом прошлых репортов + текущей переписки)
    └─ save_message(session_id, ..., role='assistant', content)
         │
         ▼
    [cron каждые ~1 мин]
         │
         ├─ SELECT sessions WHERE status='active' AND ends_at <= now()
         │
         ├─ Нет переписки?
         │       Да  → DELETE session (не фиксируем)
         │       Нет → generate_report() → UPDATE sessions SET status='closed', reports
         │             bot.send_message(chat_id, "Сессия завершена" + user_report)
         └─
```

---

## База данных

БД: `psychoai` (PostgreSQL 16 + pgvector)

### `messages`
```sql
id, user_id, chat_id, role, content, ts, session_id (FK), created_at
```

### `sessions`
```sql
id, user_id, chat_id,
type          -- 'session' | 'diary' | 'card'
status        -- 'active' | 'closed'
started_at, ends_at, closed_at,
max_duration_minutes,
image_prompt  -- только для card-сессий
system_report JSONB,   -- для контекста будущих сессий и /report
user_report   JSONB    -- отправляется пользователю
```

### `reports`
```sql
id, user_id, chat_id,
period_label  -- 'неделя', '2 недели', ...
period_start,
image_data BYTEA,
report_text,
system_report JSONB,
created_at
```

---

## Репорты

### Репорт по сессии (генерится при закрытии)
Промпт отправляется модели с полной перепиской. Возвращает JSON:
```json
{
  "system": {
    "themes": ["потеря контроля", "страх отвержения"],
    "emotions": ["тревога", "злость"],
    "patterns": ["избегание конфликта"],
    "key_moments": ["клиент сказал что не умеет злиться"]
  },
  "user": {
    "summary": "Сегодня мы исследовали тему контроля...",
    "observations": "Я заметил, что когда ты говоришь о маме...",
    "suggestion": "Попробуй на этой неделе..."
  }
}
```

- `system_report` → используется в контексте будущих сессий и для `/report`
- `user_report` → отправляется пользователю в Telegram

### Периодический отчёт `/report`
1. Inline keyboard: Неделя | 2 недели | 3 недели | Месяц | 2 мес | 3 мес
2. Берёт все `system_report` закрытых сессий за период
3. Генерит: метафорическая карта (Imagen) + текстовый анализ (LLM)
4. Сохраняет в `reports`, отправляет пользователю

---

## Стек

| Компонент | Технология |
|-----------|------------|
| Telegram Bot | pyTelegramBotAPI (telebot, sync) |
| LLM | Gemini 2.0 Flash (via google-genai) |
| Image generation | Gemini Imagen 4 (imagen-4.0-fast-generate-001) |
| Vision (фото/рукописи) | Gemini 2.0 Flash (multimodal) |
| STT (голос) | Whisper в Docker (onerahmet/openai-whisper-asr-webservice) |
| БД | PostgreSQL 16 + pgvector |
| Миграции | Alembic (raw SQL) |
| Cron | APScheduler внутри app-контейнера |
| Package manager | uv |
| Deployment | Docker Compose |

---

## Структура проекта

```
pem06/
├── bot.py                    # точка входа, регистрация хендлеров
├── config.py                 # все настройки из .env
├── db.py                     # все операции с БД
├── session_lifecycle.py      # core: старт/закрытие/репорт сессии
├── scheduler.py              # APScheduler cron для авто-закрытия
├── migrate.py                # запуск Alembic
│
├── handlers/
│   ├── start.py              # /start — приветствие
│   ├── session_cmd.py        # /session, /diary
│   ├── card.py               # /card — карта + старт сессии
│   ├── report.py             # /report — периодический отчёт
│   ├── voice.py              # голосовые сообщения
│   ├── photo.py              # фото/рукописи
│   └── text_handler.py       # catch-all текст (бывший session.py)
│
├── providers/
│   ├── base.py               # LLMProvider, ImageProvider, STTProvider, VisionProvider ABCs
│   ├── __init__.py           # фабрики get_llm(), get_image_gen(), get_stt(), get_vision()
│   ├── gemini_llm.py         # Gemini LLM + Vision
│   ├── gemini.py             # Gemini Imagen
│   ├── whisper.py            # Whisper STT
│   └── yandex.py             # YandexGPT (legacy, отключён)
│
├── prompts/
│   ├── therapist.py          # системный промпт для /session
│   ├── diary.py              # системный промпт для /diary
│   ├── card_session.py       # МАК-мастер → гештальт-терапевт
│   ├── metaphor.py           # промпт для генерации карты (Imagen)
│   ├── session_report.py     # промпт для репорта по сессии
│   └── period_report.py      # промпт для периодического отчёта
│
└── alembic/
    └── versions/
        ├── 0001_initial.py           # messages + pgvector
        ├── 0002_add_sessions.py      # sessions + session_id в messages
        └── 0003_add_reports.py       # reports
```

---

## Переменные окружения (.env)

```env
BOT_TOKEN=
DATABASE_URL=postgresql://postgres:postgres@db:5432/psychoai

LLM_PROVIDER=gemini
GEMINI_API_KEY=
GEMINI_LLM_MODEL=gemini-2.0-flash
GEMINI_VISION_MODEL=gemini-2.0-flash
GEMINI_IMAGE_MODEL=imagen-4.0-fast-generate-001
IMAGE_PROVIDER=gemini

STT_PROVIDER=whisper
WHISPER_URL=http://whisper:9000
WHISPER_MODEL=large-v3   # tiny|base|small|medium|large-v3

MODE=polling              # polling | webhook
WEBHOOK_URL=https://yourdomain.com
WEBHOOK_PORT=8443

HISTORY_LIMIT=10
```
