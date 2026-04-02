from __future__ import annotations

from desktop.api.client import ApiClient, ApiError, NetworkError
from desktop.auth.storage import TokenStorage
from desktop.models import StoredSession, TokenPair, User


class AuthServiceError(Exception):
    """Base auth service error."""


class InvalidCredentialsError(AuthServiceError):
    """Raised when login/password pair is incorrect."""


class SessionExpiredError(AuthServiceError):
    """Raised when the saved session can no longer be restored."""


class AuthService:
    def __init__(self, api_client: ApiClient, token_storage: TokenStorage):
        self.api_client = api_client
        self.token_storage = token_storage
        self._session: StoredSession | None = self.token_storage.load()

    def login(self, login: str, password: str) -> User:
        try:
            token_pair = self.api_client.login(login, password)
        except ApiError as exc:
            if exc.status_code == 401:
                raise InvalidCredentialsError("Неверный логин или пароль.") from exc
            raise

        return self._store_tokens_and_fetch_user(token_pair)

    def restore_session(self) -> User | None:
        if self._session is None:
            return None

        try:
            return self.api_client.get_current_user(self._session.access_token)
        except ApiError as exc:
            if exc.status_code == 401:
                return self._refresh_and_fetch_user()
            self.clear_session()
            raise SessionExpiredError("Сохранённая сессия больше недействительна.") from exc

    def logout(self) -> None:
        if self._session is None:
            return

        try:
            self.api_client.logout(self._session.refresh_token)
        finally:
            self.clear_session()

    def clear_session(self) -> None:
        self._session = None
        self.token_storage.clear()

    def _refresh_and_fetch_user(self) -> User:
        if self._session is None:
            raise SessionExpiredError("Сохранённая сессия отсутствует.")

        try:
            token_pair = self.api_client.refresh(self._session.refresh_token)
            return self._store_tokens_and_fetch_user(token_pair)
        except NetworkError:
            raise
        except ApiError as exc:
            self.clear_session()
            raise SessionExpiredError("Сессия истекла. Войдите снова.") from exc

    def _store_tokens_and_fetch_user(self, token_pair: TokenPair) -> User:
        self.token_storage.save(token_pair.access_token, token_pair.refresh_token)
        self._session = StoredSession(
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token,
        )

        try:
            return self.api_client.get_current_user(token_pair.access_token)
        except NetworkError:
            raise
        except Exception:
            self.clear_session()
            raise
