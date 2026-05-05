"""
APScheduler cron — проверяет истёкшие сессии каждую минуту.
Запускается из bot.py при старте приложения.
"""
import logging

import telebot
from apscheduler.schedulers.background import BackgroundScheduler

import db
from session_lifecycle import close_session_with_report

logger = logging.getLogger(__name__)
_scheduler = BackgroundScheduler()


def _check_expired(bot: telebot.TeleBot) -> None:
    expired = db.get_expired_sessions()
    for session in expired:
        try:
            close_session_with_report(session, bot)
        except Exception as e:
            logger.error(f"Error closing session {session['id']}: {e}")


def start(bot: telebot.TeleBot) -> None:
    _scheduler.add_job(_check_expired, "interval", minutes=1, args=[bot])
    _scheduler.start()
    logger.info("[SCHEDULER] started")


def stop() -> None:
    _scheduler.shutdown(wait=False)
