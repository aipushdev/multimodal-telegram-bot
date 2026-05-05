"""
Core session lifecycle logic.
Used by handlers and scheduler.
"""
import json
import logging

import telebot

import db
from config import config
from providers import get_llm

logger = logging.getLogger(__name__)

SESSION_DURATIONS = {
    "session": 60,
    "diary": 30,
    "card": 25,
}


def start_session(user_id: int, chat_id: int, session_type: str,
                  image_prompt: str | None = None) -> dict:
    max_min = SESSION_DURATIONS[session_type]
    return db.create_session(user_id, chat_id, session_type, max_min, image_prompt)


def get_session_context(session_id: int) -> list[dict]:
    return db.get_history(session_id)


def build_past_reports_context(user_id: int, session_type: str) -> str:
    """Формирует текст из system_report прошлых сессий для передачи в LLM."""
    reports = db.get_recent_system_reports(user_id, session_type, limit=5)
    if not reports:
        return ""
    lines = ["Контекст прошлых сессий:"]
    for r in reversed(reports):
        date = r["started_at"].strftime("%d.%m.%Y")
        sr = r["system_report"]
        themes = ", ".join(sr.get("themes", []))
        emotions = ", ".join(sr.get("emotions", []))
        patterns = ", ".join(sr.get("patterns", []))
        lines.append(
            f"[{date}] Темы: {themes}. Эмоции: {emotions}. Паттерны: {patterns}."
        )
    return "\n".join(lines)


def close_session_with_report(session: dict, bot: telebot.TeleBot) -> None:
    session_id = session["id"]
    chat_id = session["chat_id"]
    user_id = session["user_id"]
    session_type = session["type"]

    # Нет сообщений — удаляем сессию без следа
    if db.count_user_messages(session_id) == 0:
        db.delete_session(session_id)
        logger.info(f"Session {session_id} deleted (no messages)")
        return

    # Генерируем репорт
    history = db.get_history(session_id)
    from prompts.session_report import build_report_prompt
    report_prompt = build_report_prompt(history, session_type)

    llm = get_llm()
    try:
        raw = llm.complete(
            [{"role": "user", "content": report_prompt}],
            temperature=0.3,
        )
        # Убираем markdown-блок если есть
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        report = json.loads(raw)
        system_report = report.get("system", {})
        user_report = report.get("user", {})
    except Exception as e:
        logger.error(f"Report generation failed for session {session_id}: {e}")
        system_report = {}
        user_report = {"summary": "Не удалось сгенерировать отчёт."}

    db.close_session(session_id, system_report, user_report)

    # Отправляем пользователю
    summary = user_report.get("summary", "")
    observations = user_report.get("observations", "")
    suggestion = user_report.get("suggestion", "")

    text = "Сессия завершена.\n\n"
    if summary:
        text += f"{summary}\n\n"
    if observations:
        text += f"{observations}\n\n"
    if suggestion:
        text += f"На эту неделю: {suggestion}"

    try:
        bot.send_message(chat_id, text.strip())
    except Exception as e:
        logger.error(f"Failed to send session report to {chat_id}: {e}")

    logger.info(f"Session {session_id} closed with report")
