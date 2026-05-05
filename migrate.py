"""
Runs all pending Alembic migrations.
Safe to run multiple times (idempotent).
"""
from alembic.config import Config
from alembic import command


def run_migrations() -> None:
    cfg = Config("alembic.ini")
    command.upgrade(cfg, "head")
    print("Migrations complete.")


if __name__ == "__main__":
    run_migrations()
