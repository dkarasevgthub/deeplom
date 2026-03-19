from datetime import UTC, datetime, timedelta
from hashlib import sha256
import secrets
from typing import Any

import bcrypt
import jwt
from fastapi import HTTPException, status

from config import Settings


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def _password_to_bytes(password: str) -> bytes:
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        raise ValueError("Password must be at most 72 bytes in UTF-8")
    return password_bytes


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            _password_to_bytes(password),
            password_hash.encode("utf-8"),
        )
    except ValueError:
        return False


def hash_password(password: str) -> str:
    password_bytes = _password_to_bytes(password)
    password_hash = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return password_hash.decode("utf-8")


def create_access_token(user: dict[str, Any], settings: Settings) -> tuple[str, int]:
    expires_in = settings.access_token_ttl_minutes * 60
    payload = {
        "sub": str(user["id"]),
        "login": user["login"],
        "warehouse_id": user["warehouse_id"],
        "type": "access",
        "exp": datetime.now(UTC) + timedelta(seconds=expires_in),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm), expires_in


def decode_access_token(token: str, settings: Settings) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
        ) from exc

    if payload.get("type") != "access" or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
        )

    return payload
