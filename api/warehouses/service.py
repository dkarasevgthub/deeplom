from psycopg import Connection
from psycopg.errors import UniqueViolation

_SELECT = """
    select id, code, name, address, inn, kpp, is_active, created_at
    from app.warehouses
"""


def fetch_all_warehouses(connection: Connection):
    with connection.cursor() as cursor:
        cursor.execute(_SELECT + " order by id")
        return cursor.fetchall()


def fetch_warehouse_by_id(connection: Connection, warehouse_id: int):
    with connection.cursor() as cursor:
        cursor.execute(_SELECT + " where id = %s", (warehouse_id,))
        return cursor.fetchone()


def create_warehouse(
    connection: Connection,
    *,
    code: str,
    name: str,
    address: str | None,
    inn: str | None,
    kpp: str | None,
):
    try:
        with connection.transaction():
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    insert into app.warehouses (code, name, address, inn, kpp)
                    values (%s, %s, %s, %s, %s)
                    returning id, code, name, address, inn, kpp, is_active, created_at
                    """,
                    (code, name, address, inn, kpp),
                )
                return cursor.fetchone()
    except UniqueViolation:
        return None


def update_warehouse(connection: Connection, warehouse_id: int, updates: dict):
    if not updates:
        return fetch_warehouse_by_id(connection, warehouse_id)

    set_clauses = [f"{field} = %s" for field in updates]
    params = [*updates.values(), warehouse_id]

    with connection.transaction():
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                update app.warehouses
                set {', '.join(set_clauses)}
                where id = %s
                returning id, code, name, address, inn, kpp, is_active, created_at
                """,
                params,
            )
            return cursor.fetchone()


def delete_warehouse(connection: Connection, warehouse_id: int):
    with connection.transaction():
        with connection.cursor() as cursor:
            cursor.execute(
                "delete from app.warehouses where id = %s returning id",
                (warehouse_id,),
            )
            return cursor.fetchone()
