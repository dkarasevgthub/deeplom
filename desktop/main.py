from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMessageBox

from desktop.api.client import ApiClient, ApiError, NetworkError
from desktop.auth.service import AuthService, InvalidCredentialsError, SessionExpiredError
from desktop.auth.storage import TokenStorage
from desktop.config import get_config
from desktop.models import User
from desktop.ui.login_window import LoginWindow
from desktop.ui.main_window import MainWindow


class DesktopApplication:
    def __init__(self):
        self.qt_app = QApplication(sys.argv)
        self.config = get_config()
        self.auth_service = AuthService(
            api_client=ApiClient(
                base_url=self.config.api_base_url,
                timeout_seconds=self.config.request_timeout_seconds,
            ),
            token_storage=TokenStorage(self.config.session_file),
        )
        self.login_window = LoginWindow()
        self.main_window: MainWindow | None = None

        self.login_window.login_requested.connect(self.handle_login)

    def run(self) -> int:
        try:
            user = self.auth_service.restore_session()
        except NetworkError:
            self.login_window.show_error("Сервер недоступен. Проверьте, что API запущено.")
            user = None
        except SessionExpiredError as exc:
            self.login_window.show_error(str(exc))
            user = None
        except ApiError as exc:
            self.login_window.show_error(self._map_api_error(exc))
            user = None

        if user is not None:
            self.open_main_window(user)
        else:
            self.login_window.show()

        return self.qt_app.exec()

    def handle_login(self, login: str, password: str) -> None:
        if not login or not password:
            self.login_window.show_error("Введите логин и пароль.")
            return

        self.login_window.set_busy(True)
        try:
            user = self.auth_service.login(login, password)
        except InvalidCredentialsError as exc:
            self.login_window.show_error(str(exc))
        except NetworkError:
            self.login_window.show_error("Сервер недоступен. Проверьте подключение и повторите попытку.")
        except ApiError as exc:
            self.login_window.show_error(self._map_api_error(exc))
        finally:
            self.login_window.set_busy(False)

        if "user" in locals():
            self.login_window.password_input.clear()
            self.open_main_window(user)

    def handle_logout(self) -> None:
        try:
            self.auth_service.logout()
        except ApiError as exc:
            QMessageBox.warning(None, "Ошибка выхода", self._map_api_error(exc))
        except NetworkError:
            QMessageBox.warning(
                None,
                "Ошибка выхода",
                "Не удалось связаться с сервером, локальная сессия очищена.",
            )

        if self.main_window is not None:
            self.main_window.close()
            self.main_window = None

        self.login_window.password_input.clear()
        self.login_window.clear_error()
        self.login_window.restore_default_view()
        self.login_window.show()
        self.login_window.raise_()
        self.login_window.activateWindow()

    def open_main_window(self, user: User) -> None:
        if self.main_window is not None:
            self.main_window.close()

        self.main_window = MainWindow(user, self.auth_service)
        self.main_window.logout_requested.connect(self.handle_logout)
        self.main_window.showMaximized()
        self.login_window.hide()

    @staticmethod
    def _map_api_error(exc: ApiError) -> str:
        if exc.status_code == 401:
            return "Сессия недействительна. Войдите снова."
        if exc.status_code == 403:
            return "Пользователь неактивен или доступ запрещён."
        if exc.status_code and exc.status_code >= 500:
            return "Сервер вернул ошибку. Попробуйте позже."
        return exc.detail


def main() -> int:
    app = DesktopApplication()
    return app.run()


if __name__ == "__main__":
    raise SystemExit(main())
