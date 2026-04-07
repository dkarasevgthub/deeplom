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

    # ── User management (admin only) ──────────────────────────────────────────

    def list_users(self, access_token: str) -> list[dict[str, Any]]:
        result = self._request("GET", "/api/auth/users", token=access_token)
        assert isinstance(result, list)
        return result

    def register_user(
        self,
        full_name: str,
        login: str,
        password: str,
        role: str,
        warehouse_id: int | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "full_name": full_name,
            "login": login,
            "password": password,
            "role": role,
        }
        if warehouse_id is not None:
            payload["warehouse_id"] = warehouse_id
        result = self._request("POST", "/api/auth/register", payload)
        assert isinstance(result, dict)
        return result

    def update_user(self, access_token: str, user_id: int, **fields: Any) -> dict[str, Any]:
        result = self._request("PATCH", f"/api/auth/users/{user_id}", fields, token=access_token)
        assert isinstance(result, dict)
        return result

    def delete_user(self, access_token: str, user_id: int) -> None:
        self._request(
            "DELETE",
            f"/api/auth/users/{user_id}",
            token=access_token,
            expected_statuses={204},
        )

    # ── Warehouse management ──────────────────────────────────────────────────

    def list_warehouses(self, access_token: str) -> list[dict[str, Any]]:
        result = self._request("GET", "/api/warehouses", token=access_token)
        assert isinstance(result, list)
        return result

    def create_warehouse(
        self,
        access_token: str,
        code: str,
        name: str,
        address: str | None = None,
        inn: str | None = None,
        kpp: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"code": code, "name": name}
        if address is not None:
            payload["address"] = address
        if inn is not None:
            payload["inn"] = inn
        if kpp is not None:
            payload["kpp"] = kpp
        result = self._request("POST", "/api/warehouses", payload, token=access_token)
        assert isinstance(result, dict)
        return result

    def update_warehouse(self, access_token: str, warehouse_id: int, **fields: Any) -> dict[str, Any]:
        result = self._request("PATCH", f"/api/warehouses/{warehouse_id}", fields, token=access_token)
        assert isinstance(result, dict)
        return result

    def delete_warehouse(self, access_token: str, warehouse_id: int) -> None:
        self._request(
            "DELETE",
            f"/api/warehouses/{warehouse_id}",
            token=access_token,
            expected_statuses={204},
        )

    # ── Internal ──────────────────────────────────────────────────────────────

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        token: str | None = None,
        expected_statuses: set[int] | None = None,
    ) -> Any:
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
