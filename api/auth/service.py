from datetime import datetime

from psycopg import Connection
from psycopg.errors import UniqueViolation


def fetch_user_by_login(connection: Connection, login: str):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            select
                id,
                full_name,
                login,
                password_hash,
                warehouse_id,
                is_active,
                created_at
            from app.users
            where login = %s
            """,
            (login,),
        )
        return cursor.fetchone()


def fetch_user_by_id(connection: Connection, user_id: int):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            select
                id,
                full_name,
                login,
                password_hash,
                warehouse_id,
                is_active,
                created_at
            from app.users
            where id = %s
            """,
            (user_id,),
        )
        return cursor.fetchone()


def create_user(
    connection: Connection,
    *,
    full_name: str,
    login: str,
    password_hash: str,
    warehouse_id: int | None,
):
    try:
        with connection.transaction():
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    insert into app.users (
                        full_name,
                        login,
                        password_hash,
                        warehouse_id,
                        is_active
                    )
                    values (%s, %s, %s, %s, true)
                    returning
                        id,
                        full_name,
                        login,
                        password_hash,
                        warehouse_id,
                        is_active,
                        created_at
                    """,
                    (full_name, login, password_hash, warehouse_id),
                )
                return cursor.fetchone()
    except UniqueViolation:
        return None


def create_refresh_token_record(
    connection: Connection,
    user_id: int,
    token_hash: str,
    expires_at: datetime,
) -> None:
    with connection.transaction():
        with connection.cursor() as cursor:
            cursor.execute(
                """
                insert into app.refresh_tokens (user_id, token_hash, expires_at)
                values (%s, %s, %s)
                """,
                (user_id, token_hash, expires_at),
            )


def fetch_refresh_token_record(connection: Connection, token_hash: str):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            select
                id,
                user_id,
                token_hash,
                expires_at,
                created_at,
                revoked_at
            from app.refresh_tokens
            where token_hash = %s
            """,
            (token_hash,),
        )
        return cursor.fetchone()


def revoke_refresh_token_by_id(connection: Connection, token_id: int) -> None:
    with connection.transaction():
        with connection.cursor() as cursor:
            cursor.execute(
                """
                update app.refresh_tokens
                set revoked_at = now()
                where id = %s and revoked_at is null
                """,
                (token_id,),
            )


def revoke_all_refresh_tokens_for_user(connection: Connection, user_id: int) -> None:
    with connection.transaction():
        with connection.cursor() as cursor:
            cursor.execute(
                """
                update app.refresh_tokens
                set revoked_at = now()
                where user_id = %s and revoked_at is null
                """,
                (user_id,),
            )
