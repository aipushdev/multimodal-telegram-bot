"""add_gen_images

Revision ID: 0004
Revises: 0003
Create Date: 2026-03-11

"""
from typing import Sequence, Union
from alembic import op

revision: str = '0004'
down_revision: Union[str, Sequence[str], None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS gen_images (
            id         SERIAL PRIMARY KEY,
            user_id    BIGINT NOT NULL,
            source     VARCHAR(20) NOT NULL,   -- 'card' | 'report'
            prompt     TEXT NOT NULL,
            image_data BYTEA NOT NULL,
            session_id INTEGER REFERENCES sessions(id) ON DELETE SET NULL,
            report_id  INTEGER REFERENCES reports(id) ON DELETE SET NULL,
            created_at TIMESTAMPTZ DEFAULT now()
        )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS gen_images")
