"""add_reports

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-11

"""
from typing import Sequence, Union
from alembic import op

revision: str = '0003'
down_revision: Union[str, Sequence[str], None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id            SERIAL PRIMARY KEY,
            user_id       BIGINT NOT NULL,
            chat_id       BIGINT NOT NULL,
            period_label  VARCHAR(50) NOT NULL,
            period_start  TIMESTAMPTZ NOT NULL,
            image_data    BYTEA,
            report_text   TEXT,
            system_report JSONB,
            created_at    TIMESTAMPTZ DEFAULT now()
        )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS reports")
