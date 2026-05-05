# PsychoAI-C — Telegram-бот гештальт-терапевта

Экспериментальный бот для терапевтических сессий. Понимает текст и голос, генерирует метафорические карты.

## Что умеет

- **Диалог** — гештальт-терапевт отвечает открытыми вопросами, не даёт советов
- **Голос** — голосовые сообщения распознаёт через Whisper и передаёт в LLM
- **Метафорические карты** — `/generate_map` генерирует изображение через Gemini Imagen
- **История** — хранит контекст диалога в PostgreSQL
- **/show_all** — показывает все карты пользователя

## Провайдеры

Все провайдеры переключаются через `.env` без изменения кода.

| Тип | Провайдер | Переменная |
|-----|-----------|------------|
| LLM | YandexGPT или Gemini | `LLM_PROVIDER=yandex\|gemini` |
| Генерация изображений | Gemini Imagen 4 | `IMAGE_PROVIDER=gemini` |
| Распознавание речи | Whisper (локальный) | `STT_PROVIDER=whisper` |

## Стек

- Python + pyTelegramBotAPI
- PostgreSQL + pgvector
- Whisper ASR (Docker)
- Alembic (миграции)
- uv (пакетный менеджер)

---

## Локальный запуск

### 1. Требования

- Docker + Docker Compose
- uv (`curl -LsSf https://astral.sh/uv/install.sh | sh`)

### 2. Настройка

```bash
cp .env.example .env
```

Заполни `.env`:
```
BOT_TOKEN=токен_от_BotFather
GEMINI_API_KEY=ключ_от_Google_AI_Studio
LLM_PROVIDER=gemini
WHISPER_MODEL=medium   # tiny | base | small | medium | large-v3
```

### 3. Запуск

```bash
docker compose up -d db whisper   # поднять БД и Whisper
uv sync                            # установить зависимости
uv run python migrate.py           # накатить миграции
uv run python bot.py               # запустить бота
```

> Whisper скачает модель при первом старте. `medium` — 1.5 GB, `large-v3` — 2.9 GB.

### Модели Whisper

| Модель | Размер | Скорость (CPU) | Качество RU |
|--------|--------|----------------|-------------|
| small | 466 MB | быстро | приемлемо |
| medium | 1.5 GB | ~25 мин / 50 мин аудио | хорошо |
| large-v3 | 2.9 GB | ~1 час / 50 мин аудио | отлично |

---

## Запуск на VPS

### 1. Установка Docker

```bash
apt update && apt install -y docker.io docker-compose-plugin
```

### 2. Клонирование и настройка

```bash
git clone https://github.com/ivproduction/pe-06-homework-demo.git
cd pe-06-homework-demo
cp .env.example .env
nano .env
```

Добавь в `.env`:
```
MODE=webhook
WEBHOOK_URL=https://твой-домен.com
BOT_TOKEN=...
GEMINI_API_KEY=...
```

### 3. Настройка домена и SSL (Nginx + Certbot)

```bash
apt install -y nginx certbot python3-certbot-nginx
```

Конфиг `/etc/nginx/sites-available/bot`:
```nginx
server {
    listen 80;
    server_name твой-домен.com;

    location / {
        proxy_pass http://127.0.0.1:8443;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
ln -s /etc/nginx/sites-available/bot /etc/nginx/sites-enabled/
certbot --nginx -d твой-домен.com
nginx -s reload
```

### 4. Запуск

```bash
docker compose up -d
```

Миграции накатятся автоматически при старте контейнера.

### 5. Обновление кода

```bash
git pull
docker compose up -d --build app
```

---

## Ключи

- **BOT_TOKEN** — [@BotFather](https://t.me/BotFather)
- **GEMINI_API_KEY** — [aistudio.google.com](https://aistudio.google.com) → Get API key
- **YANDEX_API_KEY / YANDEX_FOLDER_ID** — [console.yandex.cloud](https://console.yandex.cloud) → Сервисные аккаунты
