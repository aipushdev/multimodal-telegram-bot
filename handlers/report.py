import json
import logging
from datetime import datetime, timedelta, timezone

import telebot

import db
from prompts.period_report import build_period_report_prompt
from providers import get_llm, get_image_gen
from tg_utils import keep_typing, send_error

logger = logging.getLogger(__name__)

PERIODS = [
    ("1 неделя", 1),
    ("2 недели", 2),
    ("3 недели", 3),
    ("1 месяц", 4),
    ("2 месяца", 8),
    ("3 месяца", 13),
]


def register(bot: telebot.TeleBot) -> None:
    llm = get_llm()
    image_gen = get_image_gen()

    @bot.message_handler(commands=["report"])
    def cmd_report(message):
        chat_id = message.chat.id
        markup = telebot.types.InlineKeyboardMarkup(row_width=3)
        buttons = [
            telebot.types.InlineKeyboardButton(label, callback_data=f"report_{weeks}")
            for label, weeks in PERIODS
        ]
        markup.add(*buttons)
        bot.send_message(chat_id, "За какой период сделать отчёт?", reply_markup=markup)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("report_"))
    def handle_report_period(call):
        user_id = call.from_user.id
        chat_id = call.message.chat.id

        bot.answer_callback_query(call.id)
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)

        weeks = int(call.data.split("_")[1])
        period_label = next(lbl for lbl, w in PERIODS if w == weeks)
        period_start = datetime.now(timezone.utc) - timedelta(weeks=weeks)

        bot.send_message(chat_id, f"Собираю данные за «{period_label}»...")

        sessions = db.get_sessions_for_period(user_id, period_start)
        if not sessions:
            bot.send_message(chat_id, "За этот период нет завершённых сессий.")
            return

        prompt = build_period_report_prompt(sessions, period_label)

        try:
            with keep_typing(bot, chat_id):
                raw = llm.complete(
                    [{"role": "user", "content": prompt}],
                    temperature=0.3,
                )
            raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            report_data = json.loads(raw)
            system_report = report_data.get("system", {})
            report_text = report_data.get("report_text", "")
        except Exception as e:
            logger.error(f"Period report generation failed: {e}")
            send_error(bot, chat_id, user_id, e)
            return

        # Генерируем карту периода
        image_bytes = None
        try:
            themes = ", ".join(system_report.get("recurring_themes", []))
            img_prompt = (
                f"A dreamlike watercolor image reflecting the emotional journey of the past {period_label}. "
                f"Core themes: {themes}. Soft surrealism, no people, symbolic imagery, Dixit card style."
            )
            with keep_typing(bot, chat_id):
                image_bytes = image_gen.generate(img_prompt)
        except Exception as e:
            logger.error(f"Period card generation failed: {e}")

        report_id = db.save_report(
            user_id=user_id,
            chat_id=chat_id,
            period_label=period_label,
            period_start=period_start,
            image_data=image_bytes,
            report_text=report_text,
            system_report=system_report,
        )

        if image_bytes:
            try:
                db.save_gen_image(user_id, "report", img_prompt, image_bytes,
                                  report_id=report_id)
            except Exception as e:
                logger.error(f"save_gen_image report: {e}")
            bot.send_photo(chat_id, image_bytes)

        bot.send_message(chat_id, report_text)
