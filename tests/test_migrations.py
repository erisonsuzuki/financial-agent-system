import os
import subprocess
import tempfile

from sqlalchemy import create_engine, inspect


def test_alembic_upgrade_head_smoke():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "migration_smoke.db")
        env = os.environ.copy()
        env["DATABASE_URL"] = f"sqlite:///{db_path}"

        subprocess.run(
            ["alembic", "-c", "/code/app/alembic.ini", "upgrade", "head"],
            check=True,
            cwd="/code/app",
            env=env,
            capture_output=True,
            text=True,
        )

        engine = create_engine(env["DATABASE_URL"])
        inspector = inspect(engine)
        assert inspector.has_table("users")
        assert inspector.has_table("portfolios")
        assert inspector.has_table("assets")
        assert inspector.has_table("transactions")
        assert inspector.has_table("dividends")
