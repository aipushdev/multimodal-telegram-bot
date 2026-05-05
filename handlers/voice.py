from datetime import datetime

import telebot

import db
from prompts.therapist import SYSTEM as THERAPIST_SYSTEM
from prompts.diary import SYSTEM as DIARY_SYSTEM
from prompts.card_session import SYSTEM as CARD_SYSTEM
from providers import get_llm, get_stt
from session_lifecycle import get_session_context, build_past_reports_context
from tg_utils import keep_typing, send_error


def _end_button() -> telebot.types.InlineKeyboardMarkup:
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("Завершить сессию", callback_data="end_session"))
    return markup

_SYSTEM_BY_TYPE = {
    "session": THERAPIST_SYSTEM,
    "diary": DIARY_SYSTEM,
    "card": CARD_SYSTEM,
}

NO_SESSION_MSG = "Выбери с чего начать:\n/session — терапевтическая сессия\n/diary — дневник\n/card — метафорическая карта"


def register(bot: telebot.TeleBot) -> None:
    llm = get_llm()
    stt = get_stt()

    @bot.message_handler(content_types=["voice"])
    def handle_voice(message):
        user_id = message.from_user.id
        chat_id = message.chat.id

        session = db.get_active_session(user_id)
        if not session:
            bot.send_message(chat_id, NO_SESSION_MSG)
            return

        session_id = session["id"]
        session_type = session["type"]

        try:
            with keep_typing(bot, chat_id):
                file_info = bot.get_file(message.voice.file_id)
                audio_bytes = bot.download_file(file_info.file_path)
                text = stt.transcribe(audio_bytes)

            if not text:
                bot.reply_to(message, "Не смог разобрать голос.")
                return

            bot.send_message(chat_id, f"🎙 _{text}_", parse_mode="Markdown")

            ts = datetime.now().strftime("%H:%M")
            db.save_message(user_id, chat_id, "user", text, ts, session_id)

            history = get_session_context(session_id)
            messages = [{"role": m["role"], "content": m["content"]} for m in history]

            past_context = build_past_reports_context(user_id, session_type)
            system = _SYSTEM_BY_TYPE.get(session_type, THERAPIST_SYSTEM)
            if past_context:
                system = f"{system}\n\n{past_context}"

            with keep_typing(bot, chat_id):
                reply = llm.complete(messages, system=system)
            db.save_message(user_id, chat_id, "assistant", reply,
                            datetime.now().strftime("%H:%M"), session_id)
            bot.send_message(chat_id, reply, reply_markup=_end_button())
        except Exception as e:
            print(f"[ERROR] voice: {e}")
            send_error(bot, chat_id, user_id, e)
