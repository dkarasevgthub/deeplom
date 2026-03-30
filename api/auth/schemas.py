from pydantic import BaseModel, field_validator


VALID_ROLES = {"admin", "manager", "warehouse"}


def _validate_password_length(password: str) -> str:
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Password must be at most 72 bytes in UTF-8")
    return password


def _validate_role(value: str | None) -> str | None:
    if value is not None and value not in VALID_ROLES:
        raise ValueError("Role must be one of: admin, manager, warehouse")
    return value


class RegisterRequest(BaseModel):
    full_name: str
    login: str
    password: str
    role: str
    warehouse_id: int | None = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return _validate_password_length(value)

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        validated = _validate_role(value)
        assert validated is not None
        return validated


class UpdateUserRequest(BaseModel):
    full_name: str | None = None
    login: str | None = None
    password: str | None = None
    role: str | None = None
    warehouse_id: int | None = None
    is_active: bool | None = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return _validate_password_length(value)

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str | None) -> str | None:
        return _validate_role(value)


class LoginRequest(BaseModel):
    login: str
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return _validate_password_length(value)


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class CurrentUserResponse(BaseModel):
    id: int
    full_name: str
    login: str
    role: str
    warehouse_id: int | None
    is_active: bool
