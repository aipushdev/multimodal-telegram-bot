import telebot

import db
from prompts.metaphor import TEMPLATE
from providers import get_llm, get_image_gen
from session_lifecycle import start_session
from prompts.card_session import SYSTEM as CARD_SYSTEM
from tg_utils import keep_typing


def _build_image_prompt(sessions: list[dict], llm) -> str:
    """Генерирует промпт для Imagen на основе system_report прошлых сессий."""
    if not sessions:
        return (
            "A dreamlike watercolor landscape with soft light filtering through ancient trees, "
            "a quiet path leading into misty distance, symbolizing inner exploration and openness."
        )
    parts = []
    for s in sessions:
        sr = s.get("system_report") or {}
        themes = ", ".join(sr.get("themes", []))
        emotions = ", ".join(sr.get("emotions", []))
        if themes or emotions:
            parts.append(f"Themes: {themes}. Emotions: {emotions}.")

    context = " ".join(parts)
    dialogue_stub = f"[Context from recent sessions: {context}]"
    prompt_text = TEMPLATE.format(dialogue=dialogue_stub)

    try:
        return llm.complete([{"role": "user", "content": prompt_text}], temperature=0.8)
    except Exception:
        return context


def register(bot: telebot.TeleBot) -> None:
    llm = get_llm()
    image_gen = get_image_gen()

    @bot.message_handler(commands=["card"])
    def cmd_card(message):
        user_id = message.from_user.id
        chat_id = message.chat.id

        existing = db.get_active_session(user_id)
        if existing:
            bot.send_message(chat_id, "Сначала заверши текущую сессию — она ещё идёт.")
            return

        # Берём последние 3 session + 3 diary не старше 2 недель
        sessions = db.get_recent_closed_sessions(
            user_id, types=["session", "diary"], limit=6, weeks=2
        )

        try:
            with keep_typing(bot, chat_id):
                image_prompt = _build_image_prompt(sessions, llm)
                image_bytes = image_gen.generate(image_prompt)
        except Exception as e:
            bot.send_message(chat_id, "Не удалось создать карту. Попробуй позже.")
            return

        bot.send_photo(chat_id, image_bytes)

        # Спрашиваем хочет ли начать сессию
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("Да, начать сессию", callback_data="card_session_yes"),
            telebot.types.InlineKeyboardButton("Нет", callback_data="card_session_no"),
        )
        bot.send_message(chat_id, "Хочешь поработать с этой картой?", reply_markup=markup)

        _pending_cards[user_id] = {"prompt": image_prompt, "image_bytes": image_bytes}

    @bot.callback_query_handler(func=lambda c: c.data in ("card_session_yes", "card_session_no"))
    def handle_card_choice(call):
        user_id = call.from_user.id
        chat_id = call.message.chat.id

        bot.answer_callback_query(call.id)
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)

        pending = _pending_cards.pop(user_id, {})

        if call.data == "card_session_no":
            bot.send_message(chat_id, "Хорошо. Когда захочешь — возвращайся.")
            return

        image_prompt = pending.get("prompt", "")
        image_bytes = pending.get("image_bytes")
        session = start_session(user_id, chat_id, "card", image_prompt=image_prompt)
        minutes = session["max_duration_minutes"]

        if image_bytes:
            try:
                db.save_gen_image(user_id, "card", image_prompt, image_bytes,
                                  session_id=session["id"])
            except Exception as e:
                print(f"[WARN] save_gen_image card: {e}")

        bot.send_message(
            chat_id,
            f"Сессия началась — {minutes} минут.\n\n"
            "Посмотри на эту карту. Что первым бросается в глаза? Что в тебе откликается?",
        )


# In-memory хранилище до старта сессии (user_id → {prompt, image_bytes})
_pending_cards: dict[int, dict] = {}
