from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


@dataclass(frozen=True)
class User:
    id: int
    full_name: str
    login: str
    role: str
    warehouse_id: int | None
    is_active: bool


@dataclass(frozen=True)
class StoredSession:
    access_token: str
    refresh_token: str
