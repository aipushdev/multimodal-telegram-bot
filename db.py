import json
from datetime import datetime

import psycopg2
import psycopg2.extras

from config import config


def _conn():
    return psycopg2.connect(config.database_url)


# ─── Messages ────────────────────────────────────────────────────────────────

def save_message(user_id: int, chat_id: int, role: str, content: str, ts: str,
                 session_id: int | None = None) -> None:
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO messages (user_id, chat_id, role, content, ts, session_id) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (user_id, chat_id, role, content, ts, session_id),
        )


def get_history(session_id: int, limit: int | None = None) -> list[dict]:
    with _conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        if limit is None:
            cur.execute(
                "SELECT role, content FROM messages "
                "WHERE session_id = %s ORDER BY created_at ASC",
                (session_id,),
            )
        else:
            cur.execute(
                "SELECT role, content FROM messages "
                "WHERE session_id = %s ORDER BY created_at ASC LIMIT %s",
                (session_id, limit),
            )
        return [dict(r) for r in cur.fetchall()]


def count_user_messages(session_id: int) -> int:
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM messages WHERE session_id = %s AND role = 'user'",
            (session_id,),
        )
        return cur.fetchone()[0]


# ─── Sessions ────────────────────────────────────────────────────────────────

def create_session(user_id: int, chat_id: int, session_type: str,
                   max_duration_minutes: int,
                   image_prompt: str | None = None) -> dict:
    with _conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            INSERT INTO sessions
                (user_id, chat_id, type, max_duration_minutes, ends_at, image_prompt)
            VALUES (%s, %s, %s, %s,
                    now() + (%s || ' minutes')::interval,
                    %s)
            RETURNING *
            """,
            (user_id, chat_id, session_type, max_duration_minutes,
             max_duration_minutes, image_prompt),
        )
        return dict(cur.fetchone())


def get_active_session(user_id: int) -> dict | None:
    with _conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "SELECT * FROM sessions WHERE user_id = %s AND status = 'active' "
            "ORDER BY started_at DESC LIMIT 1",
            (user_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def get_expired_sessions() -> list[dict]:
    with _conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "SELECT * FROM sessions WHERE status = 'active' AND ends_at <= now()"
        )
        return [dict(r) for r in cur.fetchall()]


def close_session(session_id: int, system_report: dict, user_report: dict) -> None:
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE sessions
            SET status = 'closed',
                closed_at = now(),
                system_report = %s,
                user_report = %s
            WHERE id = %s
            """,
            (json.dumps(system_report, ensure_ascii=False),
             json.dumps(user_report, ensure_ascii=False),
             session_id),
        )


def delete_session(session_id: int) -> None:
    with _conn() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM messages WHERE session_id = %s", (session_id,))
        cur.execute("DELETE FROM sessions WHERE id = %s", (session_id,))


def get_recent_system_reports(user_id: int, session_type: str,
                               limit: int = 5) -> list[dict]:
    with _conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT system_report, started_at FROM sessions
            WHERE user_id = %s AND type = %s AND status = 'closed'
                  AND system_report IS NOT NULL
            ORDER BY started_at DESC LIMIT %s
            """,
            (user_id, session_type, limit),
        )
        return [dict(r) for r in cur.fetchall()]


def get_recent_closed_sessions(user_id: int, types: list[str],
                                limit: int, weeks: int = 2) -> list[dict]:
    with _conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT id, type, system_report, started_at FROM sessions
            WHERE user_id = %s AND type = ANY(%s) AND status = 'closed'
                  AND started_at >= now() - (%s || ' weeks')::interval
            ORDER BY started_at DESC LIMIT %s
            """,
            (user_id, types, weeks, limit),
        )
        return [dict(r) for r in cur.fetchall()]


# ─── Reports ─────────────────────────────────────────────────────────────────

def save_report(user_id: int, chat_id: int, period_label: str,
                period_start: datetime, image_data: bytes | None,
                report_text: str, system_report: dict) -> int:
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO reports
                (user_id, chat_id, period_label, period_start,
                 image_data, report_text, system_report)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (user_id, chat_id, period_label, period_start,
             psycopg2.Binary(image_data) if image_data else None,
             report_text,
             json.dumps(system_report, ensure_ascii=False)),
        )
        return cur.fetchone()[0]


# ─── Generated images ────────────────────────────────────────────────────────

def save_gen_image(user_id: int, source: str, prompt: str, image_data: bytes,
                   session_id: int | None = None, report_id: int | None = None) -> None:
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO gen_images (user_id, source, prompt, image_data, session_id, report_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (user_id, source, prompt, psycopg2.Binary(image_data), session_id, report_id),
        )


def get_sessions_for_period(user_id: int, period_start: datetime) -> list[dict]:
    with _conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT s.id, s.type, s.started_at, s.system_report,
                   array_agg(m.content ORDER BY m.created_at)
                       FILTER (WHERE m.role = 'user') AS user_messages
            FROM sessions s
            LEFT JOIN messages m ON m.session_id = s.id
            WHERE s.user_id = %s AND s.status = 'closed'
                  AND s.started_at >= %s
            GROUP BY s.id
            ORDER BY s.started_at ASC
            """,
            (user_id, period_start),
        )
        return [dict(r) for r in cur.fetchall()]
