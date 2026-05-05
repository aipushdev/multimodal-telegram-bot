"""add_sessions

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-11

"""
from typing import Sequence, Union
from alembic import op

revision: str = '0002'
down_revision: Union[str, Sequence[str], None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id                   SERIAL PRIMARY KEY,
            user_id              BIGINT NOT NULL,
            chat_id              BIGINT NOT NULL,
            type                 VARCHAR(20) NOT NULL,
            status               VARCHAR(20) NOT NULL DEFAULT 'active',
            started_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
            ends_at              TIMESTAMPTZ NOT NULL,
            closed_at            TIMESTAMPTZ,
            max_duration_minutes INTEGER NOT NULL,
            image_prompt         TEXT,
            system_report        JSONB,
            user_report          JSONB
        )
    """)
    op.execute("""
        ALTER TABLE messages
        ADD CONSTRAINT fk_messages_session
        FOREIGN KEY (session_id) REFERENCES sessions(id)
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE messages DROP CONSTRAINT IF EXISTS fk_messages_session")
    op.execute("DROP TABLE IF EXISTS sessions")
