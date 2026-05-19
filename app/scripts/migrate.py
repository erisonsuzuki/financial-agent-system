import subprocess
import sys
import os
from pathlib import Path

from sqlalchemy import inspect, text

from app.database import engine


APP_DIR = Path(__file__).resolve().parents[1]
ALEMBIC_INI = APP_DIR / "alembic.ini"
BASELINE_LEGACY_REVISION = "20260518_01"


def _run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def _run_alembic(args: list[str]) -> str:
    command = ["alembic", "-c", str(ALEMBIC_INI), *args]
    result = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        cwd=str(APP_DIR),
    )
    return result.stdout.strip()


def _parse_first_revision(output: str) -> str:
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith("INFO"):
            continue
        return line.split()[0]
    return ""


def _table_exists(table_name: str) -> bool:
    inspector = inspect(engine)
    return inspector.has_table(table_name)


def _has_alembic_version() -> bool:
    if not _table_exists("alembic_version"):
        return False
    with engine.connect() as connection:
        row = connection.execute(text("SELECT version_num FROM alembic_version LIMIT 1")).fetchone()
    return row is not None and bool(row[0])


def _schema_looks_initialized() -> bool:
    required_tables = ["users", "assets", "transactions", "dividends"]
    return all(_table_exists(table_name) for table_name in required_tables)


def _table_has_column(table_name: str, column_name: str) -> bool:
    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns(table_name)}
    return column_name in columns


def _schema_matches_portfolio_model() -> bool:
    if not all(_table_exists(name) for name in ["users", "assets", "transactions", "dividends", "portfolios"]):
        return False
    return (
        _table_has_column("assets", "portfolio_id")
        and _table_has_column("transactions", "portfolio_id")
        and _table_has_column("dividends", "portfolio_id")
    )


def _schema_matches_legacy_model() -> bool:
    if not all(_table_exists(name) for name in ["users", "assets", "transactions", "dividends"]):
        return False
    if _table_exists("portfolios"):
        return False
    return (
        not _table_has_column("assets", "portfolio_id")
        and not _table_has_column("transactions", "portfolio_id")
        and not _table_has_column("dividends", "portfolio_id")
    )


def main() -> int:
    try:
        head = _parse_first_revision(_run_alembic(["heads"]))
        current = _parse_first_revision(_run_alembic(["current"]))

        if not head:
            print("No Alembic head found.")
            return 1

        allow_stamp = os.getenv("ALLOW_ALEMBIC_STAMP", "0") == "1"
        if not current and _schema_looks_initialized() and not _has_alembic_version():
            if not allow_stamp:
                print(
                    "Schema exists without Alembic version tracking. "
                    "Refusing implicit stamp. Run with ALLOW_ALEMBIC_STAMP=1 to stamp head explicitly."
                )
                return 2
            if _schema_matches_legacy_model():
                print(
                    "Legacy schema detected without Alembic version tracking. "
                    f"Stamping baseline revision ({BASELINE_LEGACY_REVISION}) before upgrade."
                )
                _run_alembic(["stamp", BASELINE_LEGACY_REVISION])
                current = BASELINE_LEGACY_REVISION
            elif _schema_matches_portfolio_model():
                print(f"Existing schema detected without Alembic version; stamping head ({head}).")
                _run_alembic(["stamp", head])
                current = head
            else:
                print(
                    "Schema exists but does not match expected legacy or portfolio model. "
                    "Refusing stamp; run migrations on a clean DB or repair schema first."
                )
                return 3

        if current == head:
            print(f"Database already at Alembic head ({head}).")
            return 0

        print("Applying migrations to head...")
        _run_alembic(["upgrade", "head"])
        return 0
    except subprocess.CalledProcessError as exc:
        print(f"Alembic command failed: {' '.join(exc.cmd)}")
        if exc.stderr:
            print(exc.stderr.strip())
        return exc.returncode or 1


if __name__ == "__main__":
    sys.exit(main())
