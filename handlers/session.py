from datetime import datetime

import telebot

import db
from config import config
from prompts.therapist import SYSTEM
from providers import get_llm


def register(bot: telebot.TeleBot) -> None:
    llm = get_llm()

    @bot.message_handler(func=lambda m: True, content_types=["text"])
    def handle_text(message):
        user_id = message.from_user.id
        ts = datetime.now().strftime("%H:%M")

        db.save_message(user_id, "user", message.text, ts)
        history = db.get_history(user_id, limit=config.history_limit * 2)
        messages = [{"role": m["role"], "content": m["content"]} for m in history]

        try:
            reply = llm.complete(messages, system=SYSTEM)
            db.save_message(user_id, "assistant", reply, datetime.now().strftime("%H:%M"))
            bot.reply_to(message, reply)
        except Exception as e:
            print(f"[ERROR] session: {e}")
            bot.reply_to(message, f"Ошибка: {e}")
