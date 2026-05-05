import telebot

import db
from session_lifecycle import start_session, close_session_with_report, SESSION_DURATIONS
from tg_utils import send_error


def _end_button() -> telebot.types.InlineKeyboardMarkup:
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("Завершить сессию", callback_data="end_session"))
    return markup


def register(bot: telebot.TeleBot) -> None:

    @bot.message_handler(commands=["session"])
    def cmd_session(message):
        user_id = message.from_user.id
        chat_id = message.chat.id
        existing = db.get_active_session(user_id)
        if existing:
            minutes = existing["max_duration_minutes"]
            bot.send_message(chat_id,
                f"Сессия уже идёт — {minutes} минут.\nПросто пиши, я здесь.",
                reply_markup=_end_button())
            return
        session = start_session(user_id, chat_id, "session")
        minutes = session["max_duration_minutes"]
        bot.send_message(chat_id,
            f"Сессия началась — {minutes} минут.\n\n"
            "Я здесь. Расскажи — с чем ты пришёл сегодня?",
            reply_markup=_end_button())

    @bot.message_handler(commands=["diary"])
    def cmd_diary(message):
        user_id = message.from_user.id
        chat_id = message.chat.id
        existing = db.get_active_session(user_id)
        if existing:
            minutes = existing["max_duration_minutes"]
            bot.send_message(chat_id,
                f"Сессия уже идёт — {minutes} минут.\nПросто пиши, я здесь.",
                reply_markup=_end_button())
            return
        session = start_session(user_id, chat_id, "diary")
        minutes = session["max_duration_minutes"]
        bot.send_message(chat_id,
            f"Дневниковая сессия началась — {minutes} минут.\n\n"
            "Как прошёл твой день? Что зацепило — хорошее или нет?",
            reply_markup=_end_button())

    @bot.callback_query_handler(func=lambda c: c.data == "end_session")
    def handle_end_session(call):
        user_id = call.from_user.id
        chat_id = call.message.chat.id

        bot.answer_callback_query(call.id)
        try:
            bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
        except Exception:
            pass

        session = db.get_active_session(user_id)
        if not session:
            bot.send_message(chat_id, "Активной сессии нет.")
            return

        if db.count_user_messages(session["id"]) == 0:
            db.delete_session(session["id"])
            bot.send_message(chat_id, "Сессия отменена.")
            return

        bot.send_message(chat_id, "Завершаю сессию, генерирую отчёт...")
        try:
            close_session_with_report(session, bot)
        except Exception as e:
            print(f"[ERROR] end_session callback: {e}")
            send_error(bot, chat_id, user_id, e)
