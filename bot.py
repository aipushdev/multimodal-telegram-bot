import telebot

from config import config
from handlers import start, session_cmd, card, report, voice, photo, text_handler
import scheduler


def create_bot() -> telebot.TeleBot:
    bot = telebot.TeleBot(config.bot_token)

    # Порядок регистрации важен: команды и media — до catch-all текстового хендлера
    start.register(bot)
    session_cmd.register(bot)
    card.register(bot)
    report.register(bot)
    voice.register(bot)
    photo.register(bot)
    text_handler.register(bot)  # catch-all text — последний

    bot.set_my_commands([
        telebot.types.BotCommand("session", "Терапевтическая сессия (60 мин)"),
        telebot.types.BotCommand("diary", "Дневниковая сессия (30 мин)"),
        telebot.types.BotCommand("card", "Метафорическая карта + сессия (25 мин)"),
        telebot.types.BotCommand("report", "Сводный отчёт за период"),
    ])
    return bot


def run_polling(bot: telebot.TeleBot) -> None:
    print("[BOT] polling...")
    bot.infinity_polling(allowed_updates=["message", "callback_query"])


def run_webhook(bot: telebot.TeleBot) -> None:
    from flask import Flask, request

    app = Flask(__name__)
    secret = config.bot_token

    bot.remove_webhook()
    bot.set_webhook(url=f"{config.webhook_url}/{secret}")

    @app.route(f"/{secret}", methods=["POST"])
    def webhook():
        update = telebot.types.Update.de_json(request.get_json())
        bot.process_new_updates([update])
        return "ok"

    print(f"[BOT] webhook on :{config.webhook_port}...")
    app.run(host="0.0.0.0", port=config.webhook_port)


if __name__ == "__main__":
    bot = create_bot()
    scheduler.start(bot)

    try:
        if config.mode == "webhook":
            run_webhook(bot)
        else:
            run_polling(bot)
    finally:
        scheduler.stop()
