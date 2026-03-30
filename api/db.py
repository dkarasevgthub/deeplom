from collections.abc import Generator

from fastapi import Request
from psycopg import Connection
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from config import Settings


_db_pool: ConnectionPool | None = None


def initialize_db_pool(settings: Settings) -> None:
    global _db_pool

    if _db_pool is not None:
        return

    _db_pool = ConnectionPool(
        conninfo=settings.database_url,
        min_size=1,
        max_size=5,
        kwargs={"autocommit": True, "row_factory": dict_row},
        open=True,
    )


def close_db_pool() -> None:
    global _db_pool

    if _db_pool is None:
        return

    _db_pool.close()
    _db_pool = None


def get_db_pool() -> ConnectionPool:
    if _db_pool is None:
        raise RuntimeError("Database pool is not initialized")
    return _db_pool


def get_db_connection(request: Request) -> Generator[Connection, None, None]:
    pool = get_db_pool()

    with pool.connection() as connection:
        request.state.db = connection
        yield connection
