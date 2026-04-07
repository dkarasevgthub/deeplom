from fastapi import APIRouter, Depends, HTTPException, Response, status
from psycopg import Connection
from psycopg.errors import ForeignKeyViolation, UniqueViolation

from auth.router import _require_admin, get_current_user
from db import get_db_connection
from warehouses.schemas import (
    CreateWarehouseRequest,
    UpdateWarehouseRequest,
    WarehouseResponse,
)
from warehouses.service import (
    create_warehouse,
    delete_warehouse,
    fetch_all_warehouses,
    fetch_warehouse_by_id,
    update_warehouse,
)

router = APIRouter(prefix="/warehouses", tags=["warehouses"])


def _to_response(w: dict) -> WarehouseResponse:
    return WarehouseResponse(
        id=w["id"],
        code=w["code"],
        name=w["name"],
        address=w["address"],
        inn=w["inn"],
        kpp=w["kpp"],
        is_active=w["is_active"],
    )


@router.get("", response_model=list[WarehouseResponse])
def list_warehouses(
    current_user=Depends(get_current_user),
    connection: Connection = Depends(get_db_connection),
):
    return [_to_response(w) for w in fetch_all_warehouses(connection)]


@router.post("", response_model=WarehouseResponse, status_code=status.HTTP_201_CREATED)
def create(
    payload: CreateWarehouseRequest,
    current_user=Depends(get_current_user),
    connection: Connection = Depends(get_db_connection),
):
    _require_admin(current_user)
    w = create_warehouse(
        connection,
        code=payload.code,
        name=payload.name,
        address=payload.address,
        inn=payload.inn,
        kpp=payload.kpp,
    )
    if w is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Warehouse code already in use",
        )
    return _to_response(w)


@router.patch("/{warehouse_id}", response_model=WarehouseResponse)
def patch(
    warehouse_id: int,
    payload: UpdateWarehouseRequest,
    current_user=Depends(get_current_user),
    connection: Connection = Depends(get_db_connection),
):
    _require_admin(current_user)

    updates = {f: getattr(payload, f) for f in payload.model_fields_set}
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update",
        )

    try:
        w = update_warehouse(connection, warehouse_id, updates)
    except UniqueViolation as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Warehouse code already in use",
        ) from exc

    if w is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warehouse not found",
        )
    return _to_response(w)


@router.delete("/{warehouse_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove(
    warehouse_id: int,
    current_user=Depends(get_current_user),
    connection: Connection = Depends(get_db_connection),
):
    _require_admin(current_user)

    try:
        deleted = delete_warehouse(connection, warehouse_id)
    except ForeignKeyViolation as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Warehouse is referenced by users or other records",
        ) from exc

    if deleted is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warehouse not found",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
