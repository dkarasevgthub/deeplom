from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from psycopg import Connection

from auth.schemas import (
    CurrentUserResponse,
    LoginRequest,
    LogoutRequest,
    RegisterRequest,
    RefreshTokenRequest,
    TokenPair,
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
    create_user,
    create_refresh_token_record,
    fetch_refresh_token_record,
    fetch_user_by_id,
    fetch_user_by_login,
    revoke_all_refresh_tokens_for_user,
    revoke_refresh_token_by_id,
)
from config import Settings, get_settings
from db import get_db_connection


router = APIRouter(prefix="/auth", tags=["auth"])
bearer_scheme = HTTPBearer(auto_error=False)


def _utc_now_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _build_token_pair(user: dict, settings: Settings, connection: Connection) -> TokenPair:
    access_token, expires_in = create_access_token(user, settings)
    refresh_token = generate_refresh_token()
    refresh_token_hash = hash_token(refresh_token)
    refresh_expires_at = _utc_now_naive() + timedelta(days=settings.refresh_token_ttl_days)

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
    user = create_user(
        connection,
        full_name=payload.full_name,
        login=payload.login,
        password_hash=password_hash,
        warehouse_id=payload.warehouse_id,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Login is already in use",
        )

    return CurrentUserResponse(
        id=user["id"],
        full_name=user["full_name"],
        login=user["login"],
        warehouse_id=user["warehouse_id"],
        is_active=user["is_active"],
    )


@router.post("/login", response_model=TokenPair)
def login(
    payload: LoginRequest,
    connection: Connection = Depends(get_db_connection),
    settings: Settings = Depends(get_settings),
):
    user = fetch_user_by_login(connection, payload.login)

    if user is None or not verify_password(payload.password, user["password_hash"]):
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
    return CurrentUserResponse(
        id=current_user["id"],
        full_name=current_user["full_name"],
        login=current_user["login"],
        warehouse_id=current_user["warehouse_id"],
        is_active=current_user["is_active"],
    )


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

    if refresh_token_record["expires_at"] <= _utc_now_naive():
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
