import os

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import text

from novelos.api.main import create_app
from novelos.infrastructure.config import Settings
from novelos.infrastructure.database import create_database_engine

pytestmark = pytest.mark.integration


def test_migration_roundtrip_and_database_health(monkeypatch: pytest.MonkeyPatch) -> None:
    url = os.environ.get("NOVELOS_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set NOVELOS_TEST_DATABASE_URL to a disposable PostgreSQL database")

    monkeypatch.setenv("NOVELOS_DATABASE_URL", url)
    config = Config("alembic.ini")
    settings = Settings(environment="test", database_url=SecretStr(url))
    engine = create_database_engine(settings)
    try:
        # Require an empty disposable database. Never downgrade an existing schema.
        with engine.connect() as connection:
            tables = (
                connection.execute(
                    text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
                )
                .scalars()
                .all()
            )
            assert tables == [], "Integration database must start empty"

        command.upgrade(config, "head")
        command.upgrade(config, "head")
        with engine.connect() as connection:
            assert connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one() == ("0001_baseline")
        with TestClient(create_app(settings)) as client:
            assert client.get("/health/live").status_code == 200
            ready = client.get("/health/ready")
            assert ready.status_code == 200
            assert ready.json() == {"status": "ready"}

        command.downgrade(config, "base")
        with engine.connect() as connection:
            assert (
                connection.execute(text("SELECT count(*) FROM alembic_version")).scalar_one() == 0
            )
        command.upgrade(config, "head")
        command.check(config)
    finally:
        engine.dispose()
