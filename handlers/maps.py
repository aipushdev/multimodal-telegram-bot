import io

import telebot

import db
from config import config
from prompts.metaphor import TEMPLATE
from providers import get_llm, get_image_gen


def register(bot: telebot.TeleBot) -> None:
    llm = get_llm()
    image_gen = get_image_gen()

    @bot.message_handler(commands=["generate_map"])
    def cmd_generate_map(message):
        user_id = message.from_user.id
        if not db.get_history(user_id, limit=1):
            bot.reply_to(message, "Сначала поговори со мной — тогда смогу создать карту.")
            return
        try:
            bot.send_chat_action(message.chat.id, "typing")

            history = db.get_history(user_id, limit=config.history_limit * 2)
            lines = [
                f"[{m['ts']}] {'Клиент' if m['role'] == 'user' else 'Терапевт'}: {m['content']}"
                for m in history
            ]
            prompt = llm.complete(
                [{"role": "user", "content": TEMPLATE.format(dialogue="\n".join(lines))}],
                temperature=0.9,
            )

            bot.send_chat_action(message.chat.id, "upload_photo")
            image_bytes = image_gen.generate(prompt)

            db.save_map(user_id, prompt, image_bytes)
            print(f"[PROMPT] {prompt}")
            bot.send_photo(message.chat.id, io.BytesIO(image_bytes))
        except Exception as e:
            print(f"[ERROR] generate_map: {e}")
            bot.reply_to(message, f"Ошибка: {e}")

    @bot.message_handler(commands=["show_all"])
    def cmd_show_all(message):
        user_id = message.from_user.id
        maps = db.get_maps(user_id)
        if not maps:
            bot.reply_to(message, "Карт пока нет.")
            return
        for m in maps:
            try:
                bot.send_photo(message.chat.id, io.BytesIO(bytes(m["image_data"])))
            except Exception as e:
                print(f"[ERROR] show_all: {e}")
