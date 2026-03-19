from dataclasses import dataclass
from functools import lru_cache
import os


@dataclass(frozen=True)
class Settings:
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str = "postgres-db"
    postgres_port: int = 5432
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 30

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


def _get_env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None or value == "":
        raise RuntimeError(f"Environment variable {name} is required")
    return value


@lru_cache
def get_settings() -> Settings:
    return Settings(
        postgres_user=_get_env("POSTGRES_USER"),
        postgres_password=_get_env("POSTGRES_PASSWORD"),
        postgres_db=_get_env("POSTGRES_DB"),
        postgres_host=os.getenv("POSTGRES_HOST", "postgres-db"),
        postgres_port=int(os.getenv("POSTGRES_PORT", "5432")),
        jwt_secret=_get_env("JWT_SECRET"),
        jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
        access_token_ttl_minutes=int(os.getenv("ACCESS_TOKEN_TTL_MINUTES", "15")),
        refresh_token_ttl_days=int(os.getenv("REFRESH_TOKEN_TTL_DAYS", "30")),
    )
