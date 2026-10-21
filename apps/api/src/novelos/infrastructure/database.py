from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from novelos.infrastructure.config import Settings


def create_database_engine(settings: Settings) -> Engine:
    timeout = settings.database_timeout_seconds
    return create_engine(
        settings.database_url.get_secret_value(),
        pool_pre_ping=True,
        pool_size=2,
        max_overflow=0,
        pool_timeout=timeout,
        connect_args={
            "connect_timeout": timeout,
            "options": f"-c statement_timeout={timeout * 1000}",
        },
        hide_parameters=True,
    )


def database_is_ready(engine: Engine) -> bool:
    try:
        with engine.connect() as connection:
            return bool(connection.execute(text("SELECT 1")).scalar_one() == 1)
    except SQLAlchemyError:
        # Do not expose connection strings, credentials or driver exceptions.
        return False
