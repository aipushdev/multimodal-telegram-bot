import random
import threading
from contextlib import contextmanager

import telebot

_ERROR_MESSAGES = [
    "Что-то прервалось. Попробуй написать снова.",
    "Контакт прервался. Я здесь — попробуй ещё раз.",
    "Небольшой сбой на моей стороне. Напиши снова.",
    "Что-то случилось в процессе. Давай ещё раз.",
    "Что-то нарушило связь. Попробуй снова.",
    "Не получилось. Я здесь — напиши ещё раз.",
    "Прервалось. Я никуда не ухожу — попробуй снова.",
    "Небольшая помеха. Напиши снова — я здесь.",
    "Что-то не сложилось. Давай попробуем ещё раз.",
    "Что-то случилось у меня. Попробуй написать снова.",
    "Небольшой сбой. Продолжим — напиши ещё раз.",
    "Что-то прервало наш контакт. Попробуй снова.",
    "Не вышло. Но я здесь — попробуй ещё раз.",
    "Что-то помешало прямо сейчас. Напиши снова.",
    "Прервалось что-то на моей стороне. Давай ещё раз.",
    "Небольшой сбой. Я никуда не денусь — попробуй снова.",
    "Что-то сбилось. Напиши мне снова.",
    "Контакт нарушился. Попробуй ещё раз.",
    "Что-то случилось между нами. Давай ещё раз.",
    "Не вышло с первого раза. Попробуй снова.",
]


def send_error(bot: telebot.TeleBot, chat_id: int, user_id: int, e: Exception) -> None:
    """Send a friendly error message; if user is admin, also send the technical details."""
    from config import config
    bot.send_message(chat_id, random.choice(_ERROR_MESSAGES))
    if config.admin_user_id and user_id == config.admin_user_id:
        bot.send_message(chat_id, f"🔧 `{type(e).__name__}: {e}`", parse_mode="Markdown")


@contextmanager
def keep_typing(bot: telebot.TeleBot, chat_id: int):
    """Keeps sending 'typing' action every 4 seconds until the block finishes."""
    stop = threading.Event()

    def _loop():
        while not stop.wait(4):
            try:
                bot.send_chat_action(chat_id, "typing")
            except Exception:
                pass

    t = threading.Thread(target=_loop, daemon=True)
    bot.send_chat_action(chat_id, "typing")
    t.start()
    try:
        yield
    finally:
        stop.set()
