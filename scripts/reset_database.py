#!/usr/bin/env python3
"""Reset or seed the RetainAI SQLite database with synthetic demo data."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import get_settings  # noqa: E402
from app.core.database import configure_engine, get_engine, init_db  # noqa: E402
from app.core.exceptions import DomainError  # noqa: E402
from app.seed.seed_database import print_seed_summary, reset_database, seed_database  # noqa: E402
from sqlmodel import Session  # noqa: E402


def main() -> int:
    """Run seed or reset operations."""
    parser = argparse.ArgumentParser(description="Seed or reset RetainAI synthetic demo data.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete the SQLite database file, recreate schema, and reload seed data.",
    )
    args = parser.parse_args()

    try:
        if args.reset:
            summary = reset_database()
        else:
            settings = get_settings()
            configure_engine(settings.database_url)
            init_db()
            with Session(get_engine()) as session:
                summary = seed_database(session)
        print_seed_summary(summary)
        return 0
    except DomainError as exc:
        print(f"Seed failed: {exc.message}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 - script entrypoint must report failures
        print(f"Seed failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
