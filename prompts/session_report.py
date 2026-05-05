def build_report_prompt(history: list[dict], session_type: str) -> str:
    session_label = {
        "session": "терапевтическая сессия",
        "diary": "дневниковая сессия",
        "card": "сессия с метафорической картой",
    }.get(session_type, "сессия")

    dialogue = "\n".join(
        f"{'Клиент' if m['role'] == 'user' else 'Терапевт'}: {m['content']}"
        for m in history
    )

    return f"""Проанализируй завершённую {session_label} и верни JSON строго в формате:

{{
  "system": {{
    "themes": ["..."],
    "emotions": ["..."],
    "patterns": ["..."],
    "key_moments": ["..."]
  }},
  "user": {{
    "summary": "...",
    "observations": "...",
    "suggestion": "..."
  }}
}}

Где:
- themes — главные темы которые поднимал клиент
- emotions — эмоции которые звучали
- patterns — повторяющиеся паттерны поведения или реакции
- key_moments — важные моменты сессии (цитаты или наблюдения)
- summary — краткое резюме сессии для клиента (2–3 предложения, тепло)
- observations — что терапевт заметил (от первого лица, без оценок)
- suggestion — одно мягкое предложение на ближайшее время (не совет, а приглашение)

Верни только JSON, без markdown и пояснений.

Диалог сессии:
{dialogue}"""
