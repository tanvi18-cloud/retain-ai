#!/bin/sh
set -eu

# Ensure SQLite volume path exists when using DATABASE_URL=sqlite:////data/retain_ai.db
if [ -n "${DATABASE_URL:-}" ]; then
  case "$DATABASE_URL" in
    sqlite:////data/*)
      mkdir -p /data 2>/dev/null || true
      ;;
  esac
fi

python <<'PY'
"""Initialize schema and seed synthetic demo data when the database is empty."""
from app.core.config import get_settings
from app.core.database import configure_engine, get_engine, init_db
from app.seed.seed_database import is_seed_complete, seed_database
from sqlmodel import Session

settings = get_settings()
configure_engine(settings.database_url)
init_db()
with Session(get_engine()) as session:
    if not is_seed_complete(session):
        summary = seed_database(session, skip_if_complete=False)
        print(
            f"Seed completed: customers={summary.customers_inserted}, "
            f"offers={summary.offers_inserted}"
        )
    else:
        print("Seed skipped: dataset already loaded.")
PY

exec "$@"
