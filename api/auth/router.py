from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from psycopg import Connection
from psycopg.errors import ForeignKeyViolation, UniqueViolation

from auth.schemas import (
    CurrentUserResponse,
    LoginRequest,
    LogoutRequest,
    RegisterRequest,
    RefreshTokenRequest,
    TokenPair,
    UpdateUserRequest,
)
from auth.security import (
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from auth.service import (
    create_refresh_token_record,
    create_user,
    delete_user,
    fetch_all_users,
    fetch_refresh_token_record,
    fetch_user_by_id,
    fetch_user_by_login,
    revoke_all_refresh_tokens_for_user,
    revoke_refresh_token_by_id,
    update_user,
)
from config import Settings, get_settings
from db import get_db_connection


router = APIRouter(prefix="/auth", tags=["auth"])
bearer_scheme = HTTPBearer(auto_error=False)


def _build_token_pair(user: dict, settings: Settings, connection: Connection) -> TokenPair:
    access_token, expires_in = create_access_token(user, settings)
    refresh_token = generate_refresh_token()
    refresh_token_hash = hash_token(refresh_token)
    refresh_expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_ttl_days)

    create_refresh_token_record(
        connection=connection,
        user_id=user["id"],
        token_hash=refresh_token_hash,
        expires_at=refresh_expires_at,
    )

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
    )


def _to_user_response(user: dict) -> CurrentUserResponse:
    return CurrentUserResponse(
        id=user["id"],
        full_name=user["full_name"],
        login=user["login"],
        role=user["role"],
        warehouse_id=user["warehouse_id"],
        is_active=user["is_active"],
    )


def _require_admin(user: dict[str, Any]) -> None:
    if user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can manage users",
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    connection: Connection = Depends(get_db_connection),
    settings: Settings = Depends(get_settings),
):
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing access token",
        )

    payload = decode_access_token(credentials.credentials, settings)
    user = fetch_user_by_id(connection, int(payload["sub"]))

    if user is None or not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is not authorized",
        )

    return user


@router.post(
    "/register",
    response_model=CurrentUserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: RegisterRequest,
    connection: Connection = Depends(get_db_connection),
):
    password_hash = hash_password(payload.password)
    try:
        user = create_user(
            connection,
            full_name=payload.full_name,
            login=payload.login,
            password_hash=password_hash,
            role=payload.role,
            warehouse_id=payload.warehouse_id,
        )
    except ForeignKeyViolation as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Warehouse does not exist",
        ) from exc

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Login is already in use",
        )

    return _to_user_response(user)


@router.get("/users", response_model=list[CurrentUserResponse])
def list_users(
    current_user=Depends(get_current_user),
    connection: Connection = Depends(get_db_connection),
):
    _require_admin(current_user)
    users = fetch_all_users(connection)
    return [_to_user_response(user) for user in users]


@router.patch("/users/{user_id}", response_model=CurrentUserResponse)
def patch_user(
    user_id: int,
    payload: UpdateUserRequest,
    current_user=Depends(get_current_user),
    connection: Connection = Depends(get_db_connection),
):
    _require_admin(current_user)

    updates: dict[str, object] = {}

    if "full_name" in payload.model_fields_set:
        updates["full_name"] = payload.full_name
    if "login" in payload.model_fields_set:
        updates["login"] = payload.login
    if "password" in payload.model_fields_set:
        updates["password_hash"] = None if payload.password is None else hash_password(payload.password)
    if "role" in payload.model_fields_set:
        updates["role"] = payload.role
    if "warehouse_id" in payload.model_fields_set:
        updates["warehouse_id"] = payload.warehouse_id
    if "is_active" in payload.model_fields_set:
        updates["is_active"] = payload.is_active

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update",
        )

    try:
        user = update_user(connection, user_id, updates)
    except UniqueViolation as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Login is already in use",
        ) from exc
    except ForeignKeyViolation as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Warehouse does not exist",
        ) from exc

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return _to_user_response(user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_user(
    user_id: int,
    current_user=Depends(get_current_user),
    connection: Connection = Depends(get_db_connection),
):
    _require_admin(current_user)

    if current_user["id"] == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete yourself",
        )

    try:
        deleted = delete_user(connection, user_id)
    except ForeignKeyViolation as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User cannot be deleted because it is referenced by other records",
        ) from exc

    if deleted is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/login", response_model=TokenPair)
def login(
    payload: LoginRequest,
    connection: Connection = Depends(get_db_connection),
    settings: Settings = Depends(get_settings),
):
    user = fetch_user_by_login(connection, payload.login)

    if (
        user is None
        or user["password_hash"] is None
        or not verify_password(payload.password, user["password_hash"])
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid login or password",
        )

    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )

    return _build_token_pair(user, settings, connection)


@router.get("/me", response_model=CurrentUserResponse)
def me(current_user=Depends(get_current_user)):
    return _to_user_response(current_user)


@router.post("/refresh", response_model=TokenPair)
def refresh(
    payload: RefreshTokenRequest,
    connection: Connection = Depends(get_db_connection),
    settings: Settings = Depends(get_settings),
):
    token_hash = hash_token(payload.refresh_token)
    refresh_token_record = fetch_refresh_token_record(connection, token_hash)

    if refresh_token_record is None or refresh_token_record["revoked_at"] is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    if refresh_token_record["expires_at"] <= datetime.now(UTC):
        revoke_refresh_token_by_id(connection, refresh_token_record["id"])
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )

    user = fetch_user_by_id(connection, refresh_token_record["user_id"])
    if user is None or not user["is_active"]:
        revoke_refresh_token_by_id(connection, refresh_token_record["id"])
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is not authorized",
        )

    revoke_refresh_token_by_id(connection, refresh_token_record["id"])
    return _build_token_pair(user, settings, connection)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    payload: LogoutRequest,
    connection: Connection = Depends(get_db_connection),
):
    token_hash = hash_token(payload.refresh_token)
    refresh_token_record = fetch_refresh_token_record(connection, token_hash)

    if refresh_token_record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    revoke_refresh_token_by_id(connection, refresh_token_record["id"])
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
def logout_all(
    current_user=Depends(get_current_user),
    connection: Connection = Depends(get_db_connection),
):
    revoke_all_refresh_tokens_for_user(connection, current_user["id"])
    return Response(status_code=status.HTTP_204_NO_CONTENT)
