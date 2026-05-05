def build_period_report_prompt(sessions: list[dict], period_label: str) -> str:
    if not sessions:
        return ""

    parts = []
    for s in sessions:
        date = s["started_at"].strftime("%d.%m.%Y")
        stype = {"session": "терапия", "diary": "дневник", "card": "карта"}.get(s["type"], s["type"])
        sr = s.get("system_report") or {}
        themes = ", ".join(sr.get("themes", []))
        emotions = ", ".join(sr.get("emotions", []))
        patterns = ", ".join(sr.get("patterns", []))
        msgs = s.get("user_messages") or []
        excerpt = " / ".join(str(m)[:80] for m in msgs[:3])
        parts.append(
            f"[{date} | {stype}] Темы: {themes}. Эмоции: {emotions}. Паттерны: {patterns}.\n"
            f"Фрагменты: {excerpt}"
        )

    sessions_text = "\n\n".join(parts)

    return f"""На основе сессий за период «{period_label}» составь итоговый отчёт.

Верни JSON строго в формате:
{{
  "system": {{
    "recurring_themes": ["..."],
    "emotional_arc": "...",
    "growth_points": ["..."],
    "attention_areas": ["..."]
  }},
  "report_text": "..."
}}

Где:
- recurring_themes — темы которые повторялись несколько раз
- emotional_arc — как менялось эмоциональное состояние за период
- growth_points — что изменилось или сдвинулось
- attention_areas — что требует внимания в следующем периоде
- report_text — полный текст отчёта для клиента (5–8 предложений, тепло и честно)

Верни только JSON, без markdown.

Данные сессий:
{sessions_text}"""
