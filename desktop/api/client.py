from __future__ import annotations

import json
from typing import Any
from urllib import error, request

from desktop.models import TokenPair, User


class NetworkError(Exception):
    """Raised when the API is unavailable."""


class ApiError(Exception):
    def __init__(self, message: str, status_code: int | None = None, detail: str | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.detail = detail or message


class ApiClient:
    def __init__(self, base_url: str, timeout_seconds: float):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def login(self, login: str, password: str) -> TokenPair:
        payload = self._request("POST", "/api/auth/login", {"login": login, "password": password})
        return TokenPair(**payload)

    def refresh(self, refresh_token: str) -> TokenPair:
        payload = self._request("POST", "/api/auth/refresh", {"refresh_token": refresh_token})
        return TokenPair(**payload)

    def logout(self, refresh_token: str) -> None:
        self._request("POST", "/api/auth/logout", {"refresh_token": refresh_token}, expected_statuses={204})

    def get_current_user(self, access_token: str) -> User:
        payload = self._request("GET", "/api/auth/me", token=access_token)
        return User(**payload)

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        token: str | None = None,
        expected_statuses: set[int] | None = None,
    ) -> dict[str, Any]:
        request_url = f"{self.base_url}{path}"
        request_data = None
        headers = {"Accept": "application/json"}

        if payload is not None:
            request_data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        if token:
            headers["Authorization"] = f"Bearer {token}"

        api_request = request.Request(request_url, data=request_data, headers=headers, method=method)

        try:
            with request.urlopen(api_request, timeout=self.timeout_seconds) as response:
                if expected_statuses and response.status not in expected_statuses:
                    raise ApiError("Unexpected response from server", status_code=response.status)

                if response.status == 204:
                    return {}

                body = response.read()
                if not body:
                    return {}

                return json.loads(body.decode("utf-8"))
        except error.HTTPError as exc:
            detail = self._extract_error_detail(exc)
            raise ApiError(detail, status_code=exc.code, detail=detail) from exc
        except (error.URLError, TimeoutError, OSError) as exc:
            raise NetworkError("Server is unavailable") from exc

    @staticmethod
    def _extract_error_detail(exc: error.HTTPError) -> str:
        try:
            body = exc.read().decode("utf-8")
        except Exception:
            body = ""

        if body:
            try:
                payload = json.loads(body)
                detail = payload.get("detail")
                if isinstance(detail, str) and detail.strip():
                    return detail
            except json.JSONDecodeError:
                pass

        return exc.reason if isinstance(exc.reason, str) else "Request failed"
