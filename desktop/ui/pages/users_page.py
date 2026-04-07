from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from desktop.auth.service import AuthService
from desktop.models import User
from desktop.ui.role_labels import ROLE_LABELS


# ── Data models ───────────────────────────────────────────────────────────────

@dataclass
class UserRecord:
    id: int
    full_name: str
    login: str
    role: str
    warehouse_id: int | None
    is_active: bool


@dataclass
class WarehouseRecord:
    id: int
    code: str
    name: str
    address: str | None
    inn: str | None
    kpp: str | None
    is_active: bool


_ROLES: list[tuple[str, str]] = [
    ("admin", "Администратор"),
    ("manager", "Менеджер"),
    ("warehouse", "Складской работник"),
]


# ── Shared UI components ──────────────────────────────────────────────────────

class _NotificationBar(QFrame):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("notifBar")
        self.setVisible(False)

        self._icon = QLabel()
        self._icon.setObjectName("notifIcon")
        self._icon.setFixedWidth(20)

        self._msg = QLabel()
        self._msg.setObjectName("notifMsg")
        self._msg.setWordWrap(True)

        close_btn = QPushButton("✕")
        close_btn.setObjectName("notifClose")
        close_btn.setFixedSize(26, 26)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(lambda: self.setVisible(False))

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 10, 10, 10)
        lay.setSpacing(10)
        lay.addWidget(self._icon)
        lay.addWidget(self._msg, 1)
        lay.addWidget(close_btn)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(lambda: self.setVisible(False))

    def error(self, text: str) -> None:
        self._icon.setText("⚠")
        self._style("#fee2e2", "#fca5a5", "#991b1b", "#dc2626")
        self._msg.setText(text)
        self.setVisible(True)
        self._timer.start(6000)

    def success(self, text: str) -> None:
        self._icon.setText("✓")
        self._style("#dcfce7", "#86efac", "#166534", "#16a34a")
        self._msg.setText(text)
        self.setVisible(True)
        self._timer.start(3000)

    def _style(self, bg: str, border: str, msg_fg: str, icon_fg: str) -> None:
        self.setStyleSheet(f"""
            QFrame#notifBar {{
                background:{bg}; border:1px solid {border}; border-radius:12px;
            }}
            QLabel#notifMsg  {{ color:{msg_fg};  font-size:13px; font-weight:500; }}
            QLabel#notifIcon {{ color:{icon_fg}; font-size:16px; font-weight:700; }}
            QPushButton#notifClose {{
                background:transparent; color:{msg_fg}; border:none;
                font-size:13px; font-weight:600; border-radius:6px;
            }}
            QPushButton#notifClose:hover {{ background:rgba(0,0,0,0.06); }}
        """)


class _ConfirmDialog(QDialog):
    def __init__(self, parent: QWidget, title: str, message: str, ok_label: str = "Удалить"):
        super().__init__(parent)
        self.setModal(True)
        self.setMinimumWidth(380)
        self.setWindowTitle(title)

        title_lbl = QLabel(title)
        title_lbl.setObjectName("confirmTitle")
        msg_lbl = QLabel(message)
        msg_lbl.setObjectName("confirmMsg")
        msg_lbl.setWordWrap(True)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.setObjectName("confirmCancel")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)

        ok_btn = QPushButton(ok_label)
        ok_btn.setObjectName("confirmOk")
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.clicked.connect(self.accept)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(ok_btn)

        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("color:#dde7f2;")

        root = QVBoxLayout()
        root.setContentsMargins(28, 28, 28, 24)
        root.setSpacing(16)
        root.addWidget(title_lbl)
        root.addWidget(msg_lbl)
        root.addWidget(div)
        root.addLayout(btn_row)
        self.setLayout(root)

        self.setStyleSheet("""
            QDialog { background:#ffffff; }
            QLabel#confirmTitle { color:#102a4d; font-size:18px; font-weight:700; }
            QLabel#confirmMsg   { color:#475569; font-size:14px; }
            QPushButton#confirmCancel {
                background:#f3f6fb; color:#334155; border:1px solid #d9e2ee;
                border-radius:10px; font-size:14px; font-weight:500;
                padding:0 20px; min-height:42px; min-width:90px;
            }
            QPushButton#confirmCancel:hover { background:#eaf0f8; }
            QPushButton#confirmOk {
                background:#dc2626; color:#ffffff; border:none;
                border-radius:10px; font-size:14px; font-weight:600;
                padding:0 20px; min-height:42px; min-width:90px;
            }
            QPushButton#confirmOk:hover { background:#b91c1c; }
        """)
        for w in self.findChildren(QWidget) + [self]:
            f = w.font(); f.setFamilies(["Roboto", "sans-serif"]); w.setFont(f)


def _make_status_badge(is_active: bool) -> QWidget:
    text = "Активен" if is_active else "Неактивен"
    bg   = "#dcfce7" if is_active else "#fee2e2"
    fg   = "#16a34a" if is_active else "#dc2626"
    label = QLabel(text)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setStyleSheet(
        f"background:{bg}; color:{fg}; border-radius:10px;"
        f"font-size:12px; font-weight:600;"
    )
    wrapper = QWidget()
    wrapper.setStyleSheet("background:transparent;")
    lay = QHBoxLayout(wrapper)
    lay.setContentsMargins(10, 12, 10, 12)
    lay.addWidget(label)
    return wrapper


_TABLE_STYLE = """
    QTableWidget {
        background:#ffffff; border:1px solid #dde7f2;
        border-radius:16px; font-size:14px; color:#334155;
        alternate-background-color:#f8fafc;
    }
    QTableWidget::item { padding:0 12px; border:none; }
    QTableWidget::item:selected { background:#e9f2ff; color:#1d4ed8; }
    QHeaderView::section {
        background:#f1f5fb; color:#8a97aa;
        font-size:12px; font-weight:600;
        padding:10px 12px; border:none;
        border-bottom:1px solid #dde7f2;
    }
    QPushButton#actionEdit {
        background:#e9f2ff; color:#1d4ed8; border:none; border-radius:8px;
        font-size:12px; font-weight:600; min-width:72px; padding:0 10px;
    }
    QPushButton#actionEdit:hover { background:#dbeafe; }
    QPushButton#actionDelete {
        background:#fee2e2; color:#dc2626; border:none; border-radius:8px;
        font-size:12px; font-weight:600; min-width:64px; padding:0 10px;
    }
    QPushButton#actionDelete:hover { background:#fecaca; }
"""

_FILTER_STYLE = """
    QLineEdit#filterInput {
        background:#f8fafc; border:1px solid #dde7f2; border-radius:12px;
        font-size:14px; padding:0 14px; min-height:42px; color:#334155;
    }
    QLineEdit#filterInput:focus { border-color:#1d4ed8; background:#ffffff; }
    QComboBox#filterCombo {
        background:#f8fafc; border:1px solid #dde7f2; border-radius:12px;
        font-size:14px; padding:0 14px; min-height:42px; color:#334155;
    }
    QComboBox#filterCombo:focus { border-color:#1d4ed8; }
    QComboBox#filterCombo::drop-down { border:none; width:24px; }
    QComboBox#filterCombo QAbstractItemView {
        background:#ffffff; border:1px solid #dde7f2; border-radius:8px;
        font-size:14px; outline:none;
        selection-background-color:#e9f2ff; selection-color:#1d4ed8;
    }
    QCheckBox#filterCheck { color:#334155; font-size:14px; spacing:8px; }
"""


# ── Users tab content ─────────────────────────────────────────────────────────

_UC = {0: "ID", 1: "ФИО", 2: "Логин", 3: "Роль", 4: "Склад", 5: "Статус", 6: ""}


class _UsersTab(QWidget):
    def __init__(self, current_user: User, auth_service: AuthService):
        super().__init__()
        self.current_user = current_user
        self.auth_service = auth_service
        self._all: list[UserRecord] = []
        self._setup_ui()
        self.setStyleSheet(_FILTER_STYLE + _TABLE_STYLE)

    def _setup_ui(self) -> None:
        # Filters
        self.search = QLineEdit()
        self.search.setPlaceholderText("Поиск по ID, имени или логину…")
        self.search.setObjectName("filterInput")
        self.search.textChanged.connect(self._filter)

        self.role_cb = QComboBox()
        self.role_cb.setObjectName("filterCombo")
        self.role_cb.addItem("Все роли", userData=None)
        for v, l in _ROLES:
            self.role_cb.addItem(l, userData=v)
        self.role_cb.currentIndexChanged.connect(self._filter)

        self.status_cb = QComboBox()
        self.status_cb.setObjectName("filterCombo")
        self.status_cb.addItem("Все статусы", userData=None)
        self.status_cb.addItem("Активен",     userData=True)
        self.status_cb.addItem("Неактивен",   userData=False)
        self.status_cb.currentIndexChanged.connect(self._filter)

        self.wh_input = QLineEdit()
        self.wh_input.setPlaceholderText("ID склада…")
        self.wh_input.setObjectName("filterInput")
        self.wh_input.textChanged.connect(self._on_wh_input)

        self.no_wh_check = QCheckBox("Без склада")
        self.no_wh_check.setObjectName("filterCheck")
        self.no_wh_check.stateChanged.connect(self._on_no_wh)

        filter_row = QHBoxLayout()
        filter_row.setContentsMargins(0, 0, 0, 0)
        filter_row.setSpacing(10)
        filter_row.addWidget(self.search, 3)
        filter_row.addWidget(self.role_cb, 2)
        filter_row.addWidget(self.status_cb, 2)
        filter_row.addWidget(self.wh_input, 1)
        filter_row.addWidget(self.no_wh_check)

        # Notification
        self.notif = _NotificationBar()

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(list(_UC.values()))
        hh = self.table.horizontalHeader()
        for col, mode in [
            (0, QHeaderView.ResizeMode.Fixed),
            (1, QHeaderView.ResizeMode.Stretch),
            (2, QHeaderView.ResizeMode.Stretch),
            (3, QHeaderView.ResizeMode.Fixed),
            (4, QHeaderView.ResizeMode.Fixed),
            (5, QHeaderView.ResizeMode.Fixed),
            (6, QHeaderView.ResizeMode.Fixed),
        ]:
            hh.setSectionResizeMode(col, mode)
        self.table.setColumnWidth(0, 52)
        self.table.setColumnWidth(3, 160)
        self.table.setColumnWidth(4, 80)
        self.table.setColumnWidth(5, 130)
        self.table.setColumnWidth(6, 170)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)
        root.addLayout(filter_row)
        root.addWidget(self.notif)
        root.addWidget(self.table, 1)

    def load(self) -> None:
        token = self.auth_service.access_token
        if not token:
            self.notif.error("Нет активной сессии.")
            return
        try:
            self._all = [UserRecord(**u) for u in self.auth_service.api_client.list_users(token)]
        except Exception as exc:
            self.notif.error(f"Ошибка загрузки: {exc}")
            return
        self._filter()

    def _filter(self) -> None:
        text   = self.search.text().lower().strip()
        role   = self.role_cb.currentData()
        status = self.status_cb.currentData()
        wh_txt = self.wh_input.text().strip()
        no_wh  = self.no_wh_check.isChecked()

        res = self._all
        if text:
            res = [u for u in res if
                   text in u.full_name.lower() or text in u.login.lower() or text == str(u.id)]
        if role is not None:
            res = [u for u in res if u.role == role]
        if status is not None:
            res = [u for u in res if u.is_active == status]
        if no_wh:
            res = [u for u in res if u.warehouse_id is None]
        elif wh_txt:
            try:
                wid = int(wh_txt)
                res = [u for u in res if u.warehouse_id == wid]
            except ValueError:
                pass
        self._render(res)

    def _on_wh_input(self, text: str) -> None:
        if text.strip():
            self.no_wh_check.blockSignals(True)
            self.no_wh_check.setChecked(False)
            self.no_wh_check.blockSignals(False)
        self._filter()

    def _on_no_wh(self) -> None:
        if self.no_wh_check.isChecked():
            self.wh_input.blockSignals(True)
            self.wh_input.clear()
            self.wh_input.blockSignals(False)
        self._filter()

    def _render(self, users: list[UserRecord]) -> None:
        self.table.setRowCount(0)
        for u in users:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setRowHeight(r, 54)
            self._cell(r, 0, str(u.id), Qt.AlignmentFlag.AlignCenter)
            self._cell(r, 1, u.full_name)
            self._cell(r, 2, u.login)
            self._cell(r, 3, ROLE_LABELS.get(u.role, u.role))
            self._cell(r, 4, str(u.warehouse_id) if u.warehouse_id else "—", Qt.AlignmentFlag.AlignCenter)
            self.table.setCellWidget(r, 5, _make_status_badge(u.is_active))
            self.table.setCellWidget(r, 6, self._actions(u))

    def _cell(self, r: int, c: int, text: str,
              align: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft) -> None:
        item = QTableWidgetItem(text)
        item.setTextAlignment(align)
        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        self.table.setItem(r, c, item)

    def _actions(self, u: UserRecord) -> QWidget:
        edit = QPushButton("Изменить")
        edit.setObjectName("actionEdit")
        edit.setFixedHeight(30)
        edit.setCursor(Qt.CursorShape.PointingHandCursor)
        edit.clicked.connect(lambda: self._on_edit(u))

        delete = QPushButton("Удалить")
        delete.setObjectName("actionDelete")
        delete.setFixedHeight(30)
        delete.setCursor(Qt.CursorShape.PointingHandCursor)
        delete.clicked.connect(lambda: self._on_delete(u))

        w = QWidget()
        w.setStyleSheet("background:transparent;")
        lay = QHBoxLayout(w)
        lay.setContentsMargins(6, 0, 6, 0)
        lay.setSpacing(6)
        lay.addWidget(edit)
        lay.addWidget(delete)
        lay.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        return w

    def on_add(self) -> None:
        dlg = _UserDialog(parent=self, mode="create")
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        data = dlg.get_data()
        try:
            self.auth_service.api_client.register_user(
                full_name=data["full_name"], login=data["login"],
                password=data["password"], role=data["role"],
                warehouse_id=data["warehouse_id"],
            )
            self.load()
            self.notif.success(f"Пользователь «{data['full_name']}» создан.")
        except Exception as exc:
            self.notif.error(f"Ошибка создания: {exc}")

    def _on_edit(self, u: UserRecord) -> None:
        dlg = _UserDialog(parent=self, mode="edit", user=u)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        token = self.auth_service.access_token
        if not token:
            return
        data = dlg.get_data()
        patch = {k: v for k, v in data.items()
                 if (k != "password" and v is not None) or (k == "password" and v)}
        try:
            self.auth_service.api_client.update_user(access_token=token, user_id=u.id, **patch)
            self.load()
            self.notif.success(f"Данные «{data['full_name']}» обновлены.")
        except Exception as exc:
            self.notif.error(f"Ошибка сохранения: {exc}")

    def _on_delete(self, u: UserRecord) -> None:
        if u.id == self.current_user.id:
            self.notif.error("Нельзя удалить собственную учётную запись.")
            return
        dlg = _ConfirmDialog(self, "Удаление пользователя",
                             f"Удалить «{u.full_name}»?\nДействие необратимо.")
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        token = self.auth_service.access_token
        if not token:
            return
        try:
            self.auth_service.api_client.delete_user(access_token=token, user_id=u.id)
            self.load()
            self.notif.success(f"Пользователь «{u.full_name}» удалён.")
        except Exception as exc:
            self.notif.error(f"Ошибка удаления: {exc}")


# ── Warehouses tab content ────────────────────────────────────────────────────

_WC = {0: "ID", 1: "Код", 2: "Название", 3: "Адрес", 4: "ИНН", 5: "КПП", 6: "Статус", 7: ""}


class _WarehousesTab(QWidget):
    def __init__(self, auth_service: AuthService):
        super().__init__()
        self.auth_service = auth_service
        self._all: list[WarehouseRecord] = []
        self._setup_ui()
        self.setStyleSheet(_FILTER_STYLE + _TABLE_STYLE)

    def _setup_ui(self) -> None:
        # Filters
        self.search = QLineEdit()
        self.search.setPlaceholderText("Поиск по коду, названию или ИНН…")
        self.search.setObjectName("filterInput")
        self.search.textChanged.connect(self._filter)

        self.status_cb = QComboBox()
        self.status_cb.setObjectName("filterCombo")
        self.status_cb.addItem("Все статусы", userData=None)
        self.status_cb.addItem("Активен",     userData=True)
        self.status_cb.addItem("Неактивен",   userData=False)
        self.status_cb.currentIndexChanged.connect(self._filter)

        filter_row = QHBoxLayout()
        filter_row.setContentsMargins(0, 0, 0, 0)
        filter_row.setSpacing(10)
        filter_row.addWidget(self.search, 3)
        filter_row.addWidget(self.status_cb, 1)
        filter_row.addStretch(3)

        # Notification
        self.notif = _NotificationBar()

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(list(_WC.values()))
        hh = self.table.horizontalHeader()
        for col, mode in [
            (0, QHeaderView.ResizeMode.Fixed),
            (1, QHeaderView.ResizeMode.Fixed),
            (2, QHeaderView.ResizeMode.Stretch),
            (3, QHeaderView.ResizeMode.Stretch),
            (4, QHeaderView.ResizeMode.Fixed),
            (5, QHeaderView.ResizeMode.Fixed),
            (6, QHeaderView.ResizeMode.Fixed),
            (7, QHeaderView.ResizeMode.Fixed),
        ]:
            hh.setSectionResizeMode(col, mode)
        self.table.setColumnWidth(0, 52)
        self.table.setColumnWidth(1, 90)
        self.table.setColumnWidth(4, 150)
        self.table.setColumnWidth(5, 130)
        self.table.setColumnWidth(6, 130)
        self.table.setColumnWidth(7, 170)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)
        root.addLayout(filter_row)
        root.addWidget(self.notif)
        root.addWidget(self.table, 1)

    def load(self) -> None:
        token = self.auth_service.access_token
        if not token:
            self.notif.error("Нет активной сессии.")
            return
        try:
            self._all = [WarehouseRecord(**w) for w in self.auth_service.api_client.list_warehouses(token)]
        except Exception as exc:
            self.notif.error(f"Ошибка загрузки: {exc}")
            return
        self._filter()

    def _filter(self) -> None:
        text   = self.search.text().lower().strip()
        status = self.status_cb.currentData()

        res = self._all
        if text:
            res = [w for w in res if
                   text in w.code.lower() or text in w.name.lower()
                   or (w.inn and text in w.inn)]
        if status is not None:
            res = [w for w in res if w.is_active == status]
        self._render(res)

    def _render(self, warehouses: list[WarehouseRecord]) -> None:
        self.table.setRowCount(0)
        for w in warehouses:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setRowHeight(r, 54)
            self._cell(r, 0, str(w.id),  Qt.AlignmentFlag.AlignCenter)
            self._cell(r, 1, w.code,     Qt.AlignmentFlag.AlignCenter)
            self._cell(r, 2, w.name)
            self._cell(r, 3, w.address or "—")
            self._cell(r, 4, w.inn or "—", Qt.AlignmentFlag.AlignCenter)
            self._cell(r, 5, w.kpp or "—", Qt.AlignmentFlag.AlignCenter)
            self.table.setCellWidget(r, 6, _make_status_badge(w.is_active))
            self.table.setCellWidget(r, 7, self._actions(w))

    def _cell(self, r: int, c: int, text: str,
              align: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft) -> None:
        item = QTableWidgetItem(text)
        item.setTextAlignment(align)
        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        self.table.setItem(r, c, item)

    def _actions(self, w: WarehouseRecord) -> QWidget:
        edit = QPushButton("Изменить")
        edit.setObjectName("actionEdit")
        edit.setFixedHeight(30)
        edit.setCursor(Qt.CursorShape.PointingHandCursor)
        edit.clicked.connect(lambda: self._on_edit(w))

        delete = QPushButton("Удалить")
        delete.setObjectName("actionDelete")
        delete.setFixedHeight(30)
        delete.setCursor(Qt.CursorShape.PointingHandCursor)
        delete.clicked.connect(lambda: self._on_delete(w))

        wrapper = QWidget()
        wrapper.setStyleSheet("background:transparent;")
        lay = QHBoxLayout(wrapper)
        lay.setContentsMargins(6, 0, 6, 0)
        lay.setSpacing(6)
        lay.addWidget(edit)
        lay.addWidget(delete)
        lay.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        return wrapper

    def on_add(self) -> None:
        dlg = _WarehouseDialog(parent=self, mode="create")
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        data = dlg.get_data()
        token = self.auth_service.access_token
        if not token:
            return
        try:
            self.auth_service.api_client.create_warehouse(
                access_token=token,
                code=data["code"], name=data["name"],
                address=data["address"], inn=data["inn"], kpp=data["kpp"],
            )
            self.load()
            self.notif.success(f"Склад «{data['name']}» создан.")
        except Exception as exc:
            self.notif.error(f"Ошибка создания: {exc}")

    def _on_edit(self, w: WarehouseRecord) -> None:
        dlg = _WarehouseDialog(parent=self, mode="edit", warehouse=w)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        token = self.auth_service.access_token
        if not token:
            return
        data = dlg.get_data()
        patch = {k: v for k, v in data.items() if v is not None}
        try:
            self.auth_service.api_client.update_warehouse(
                access_token=token, warehouse_id=w.id, **patch
            )
            self.load()
            self.notif.success(f"Склад «{data['name']}» обновлён.")
        except Exception as exc:
            self.notif.error(f"Ошибка сохранения: {exc}")

    def _on_delete(self, w: WarehouseRecord) -> None:
        dlg = _ConfirmDialog(self, "Удаление склада",
                             f"Удалить склад «{w.name}» (код: {w.code})?\n"
                             f"Это невозможно, если к складу привязаны пользователи.")
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        token = self.auth_service.access_token
        if not token:
            return
        try:
            self.auth_service.api_client.delete_warehouse(access_token=token, warehouse_id=w.id)
            self.load()
            self.notif.success(f"Склад «{w.name}» удалён.")
        except Exception as exc:
            self.notif.error(f"Ошибка удаления: {exc}")


# ── Main page with tabs ───────────────────────────────────────────────────────

class UsersPage(QWidget):
    def __init__(self, current_user: User, auth_service: AuthService):
        super().__init__()
        self.current_user = current_user
        self.auth_service = auth_service

        self._users_tab = _UsersTab(current_user, auth_service)
        self._wh_tab    = _WarehousesTab(auth_service)
        self._active    = "users"

        self._setup_ui()
        self._apply_styles()
        self._apply_fonts()
        self._switch("users")
        self._users_tab.load()

    def _setup_ui(self) -> None:
        self.setObjectName("pageRoot")

        # Tab buttons
        self._tab_users = self._tab_btn("Пользователи", "users")
        self._tab_wh    = self._tab_btn("Склады", "warehouses")

        tab_row = QHBoxLayout()
        tab_row.setContentsMargins(0, 0, 0, 0)
        tab_row.setSpacing(4)
        tab_row.addWidget(self._tab_users)
        tab_row.addWidget(self._tab_wh)
        tab_row.addStretch()

        self.add_btn = QPushButton("+ Добавить")
        self.add_btn.setObjectName("primaryButton")
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.clicked.connect(self._on_add)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.addLayout(tab_row)
        header.addWidget(self.add_btn)

        # Stacked content
        self.stack = QStackedWidget()
        self.stack.addWidget(self._users_tab)   # index 0
        self.stack.addWidget(self._wh_tab)       # index 1

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)
        root.addLayout(header)
        root.addWidget(self.stack, 1)

    def _tab_btn(self, text: str, key: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setObjectName("tabBtn")
        btn.setProperty("active", False)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumHeight(40)
        btn.clicked.connect(lambda: self._switch(key))
        return btn

    def _switch(self, key: str) -> None:
        self._active = key
        is_users = key == "users"

        self.stack.setCurrentIndex(0 if is_users else 1)
        self.add_btn.setText("+ Добавить пользователя" if is_users else "+ Добавить склад")

        for btn, active in [(self._tab_users, is_users), (self._tab_wh, not is_users)]:
            btn.setProperty("active", active)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        if key == "warehouses" and not self._wh_tab._all:
            self._wh_tab.load()

    def _on_add(self) -> None:
        if self._active == "users":
            self._users_tab.on_add()
        else:
            self._wh_tab.on_add()

    def _apply_styles(self) -> None:
        self.setStyleSheet("""
            QWidget#pageRoot { background:transparent; }

            QPushButton#tabBtn {
                background:transparent; color:#64748b;
                border:none; border-radius:12px;
                font-size:16px; font-weight:600;
                padding:0 18px;
            }
            QPushButton#tabBtn:hover { background:#f1f5fb; color:#334155; }
            QPushButton#tabBtn[active="true"] {
                background:#e9f2ff; color:#1d4ed8;
            }

            QPushButton#primaryButton {
                background:#1d4ed8; color:#ffffff;
                border:none; border-radius:12px;
                font-size:14px; font-weight:600;
                padding:0 22px; min-height:42px;
            }
            QPushButton#primaryButton:hover { background:#1e40af; }
        """)

    def _apply_fonts(self) -> None:
        for w in self.findChildren(QWidget) + [self]:
            f = w.font(); f.setFamilies(["Roboto", "sans-serif"]); w.setFont(f)


# ── Dialogs ───────────────────────────────────────────────────────────────────

_DIALOG_STYLE = """
    QDialog { background:#ffffff; }
    QLabel#dialogTitle { color:#102a4d; font-size:20px; font-weight:700; }
    QLineEdit#formField, QComboBox#formField {
        background:#f8fafc; border:1px solid #dde7f2; border-radius:10px;
        font-size:14px; padding:0 12px; min-height:44px; color:#334155;
    }
    QLineEdit#formField:focus { border-color:#1d4ed8; background:#ffffff; }
    QComboBox#formField { padding-left:12px; }
    QComboBox#formField::drop-down { border:none; width:28px; }
    QComboBox#formField QAbstractItemView {
        background:#ffffff; border:1px solid #dde7f2; border-radius:8px;
        font-size:14px; outline:none;
        selection-background-color:#e9f2ff; selection-color:#1d4ed8;
    }
    QCheckBox#formCheck { color:#334155; font-size:14px; spacing:8px; }
    QPushButton#cancelBtn {
        background:#f3f6fb; color:#334155; border:1px solid #d9e2ee;
        border-radius:10px; font-size:14px; font-weight:500;
        padding:0 22px; min-height:44px; min-width:100px;
    }
    QPushButton#cancelBtn:hover { background:#eaf0f8; }
    QPushButton#saveBtn {
        background:#1d4ed8; color:#ffffff; border:none;
        border-radius:10px; font-size:14px; font-weight:600;
        padding:0 22px; min-height:44px; min-width:100px;
    }
    QPushButton#saveBtn:hover { background:#1e40af; }
"""


def _build_dialog_buttons(dialog: QDialog) -> tuple[QHBoxLayout, _NotificationBar]:
    notif = _NotificationBar()

    cancel = QPushButton("Отмена")
    cancel.setObjectName("cancelBtn")
    cancel.setCursor(Qt.CursorShape.PointingHandCursor)
    cancel.clicked.connect(dialog.reject)

    save = QPushButton("Сохранить")
    save.setObjectName("saveBtn")
    save.setCursor(Qt.CursorShape.PointingHandCursor)
    save.clicked.connect(dialog._on_save)  # type: ignore[attr-defined]

    div = QFrame()
    div.setFrameShape(QFrame.Shape.HLine)
    div.setStyleSheet("color:#dde7f2;")

    btn_row = QHBoxLayout()
    btn_row.setSpacing(10)
    btn_row.addStretch()
    btn_row.addWidget(cancel)
    btn_row.addWidget(save)

    return btn_row, notif, div  # type: ignore[return-value]


class _UserDialog(QDialog):
    def __init__(self, parent: QWidget, mode: str = "create", user: UserRecord | None = None):
        super().__init__(parent)
        self.mode = mode
        self.user = user
        self._data: dict = {}
        self.setModal(True)
        self.setMinimumWidth(460)
        self.setWindowTitle("Добавить пользователя" if mode == "create" else "Редактировать пользователя")
        self._setup_ui()
        self.setStyleSheet(_DIALOG_STYLE)
        for w in self.findChildren(QWidget) + [self]:
            f = w.font(); f.setFamilies(["Roboto", "sans-serif"]); w.setFont(f)
        if mode == "edit" and user:
            self._fill(user)

    def _setup_ui(self) -> None:
        title = QLabel(self.windowTitle())
        title.setObjectName("dialogTitle")

        self.f_name  = self._field("Иванов Иван Иванович")
        self.f_login = self._field("ivanov")
        self.f_pass  = self._field(
            "Минимум 8 символов" if self.mode == "create" else "Оставьте пустым, чтобы не менять",
            password=True,
        )
        self.f_role = QComboBox(); self.f_role.setObjectName("formField")
        for v, l in _ROLES:
            self.f_role.addItem(l, userData=v)
        self.f_wh     = self._field("ID склада (необязательно)")
        self.f_active = QCheckBox("Активен"); self.f_active.setObjectName("formCheck")
        self.f_active.setChecked(True)

        form = QFormLayout()
        form.setSpacing(12); form.setHorizontalSpacing(20)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form.addRow("ФИО",        self.f_name)
        form.addRow("Логин",      self.f_login)
        form.addRow("Пароль",     self.f_pass)
        form.addRow("Роль",       self.f_role)
        form.addRow("Склад (ID)", self.f_wh)
        form.addRow("",           self.f_active)

        self.notif = _NotificationBar()
        div = QFrame(); div.setFrameShape(QFrame.Shape.HLine); div.setStyleSheet("color:#dde7f2;")

        cancel = QPushButton("Отмена"); cancel.setObjectName("cancelBtn")
        cancel.setCursor(Qt.CursorShape.PointingHandCursor); cancel.clicked.connect(self.reject)
        save = QPushButton("Сохранить"); save.setObjectName("saveBtn")
        save.setCursor(Qt.CursorShape.PointingHandCursor); save.clicked.connect(self._on_save)

        btn_row = QHBoxLayout(); btn_row.setSpacing(10); btn_row.addStretch()
        btn_row.addWidget(cancel); btn_row.addWidget(save)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 24); root.setSpacing(16)
        root.addWidget(title); root.addLayout(form)
        root.addWidget(self.notif); root.addWidget(div); root.addLayout(btn_row)

    def _field(self, placeholder: str, password: bool = False) -> QLineEdit:
        f = QLineEdit(); f.setObjectName("formField"); f.setPlaceholderText(placeholder)
        if password:
            f.setEchoMode(QLineEdit.EchoMode.Password)
        return f

    def _fill(self, u: UserRecord) -> None:
        self.f_name.setText(u.full_name); self.f_login.setText(u.login)
        for i in range(self.f_role.count()):
            if self.f_role.itemData(i) == u.role:
                self.f_role.setCurrentIndex(i); break
        if u.warehouse_id:
            self.f_wh.setText(str(u.warehouse_id))
        self.f_active.setChecked(u.is_active)

    def _on_save(self) -> None:
        name  = self.f_name.text().strip()
        login = self.f_login.text().strip()
        pwd   = self.f_pass.text()
        wh    = self.f_wh.text().strip()

        if not name:  self.notif.error("Введите ФИО."); return
        if not login: self.notif.error("Введите логин."); return
        if self.mode == "create" and not pwd:
            self.notif.error("Введите пароль."); return

        wh_id: int | None = None
        if wh:
            try:    wh_id = int(wh)
            except: self.notif.error("ID склада должен быть числом."); return

        self._data = {
            "full_name": name, "login": login,
            "password": pwd or None, "role": self.f_role.currentData(),
            "warehouse_id": wh_id, "is_active": self.f_active.isChecked(),
        }
        self.accept()

    def get_data(self) -> dict:
        return self._data


class _WarehouseDialog(QDialog):
    def __init__(self, parent: QWidget, mode: str = "create", warehouse: WarehouseRecord | None = None):
        super().__init__(parent)
        self.mode = mode
        self.warehouse = warehouse
        self._data: dict = {}
        self.setModal(True)
        self.setMinimumWidth(460)
        self.setWindowTitle("Добавить склад" if mode == "create" else "Редактировать склад")
        self._setup_ui()
        self.setStyleSheet(_DIALOG_STYLE)
        for w in self.findChildren(QWidget) + [self]:
            f = w.font(); f.setFamilies(["Roboto", "sans-serif"]); w.setFont(f)
        if mode == "edit" and warehouse:
            self._fill(warehouse)

    def _setup_ui(self) -> None:
        title = QLabel(self.windowTitle())
        title.setObjectName("dialogTitle")

        self.f_code    = self._field("МСК-01")
        self.f_name    = self._field("Московский склад №1")
        self.f_address = self._field("г. Москва, ул. Примерная, д. 1")
        self.f_inn     = self._field("7700000000")
        self.f_kpp     = self._field("770000000")
        self.f_active  = QCheckBox("Активен"); self.f_active.setObjectName("formCheck")
        self.f_active.setChecked(True)

        form = QFormLayout()
        form.setSpacing(12); form.setHorizontalSpacing(20)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form.addRow("Код",     self.f_code)
        form.addRow("Название", self.f_name)
        form.addRow("Адрес",   self.f_address)
        form.addRow("ИНН",     self.f_inn)
        form.addRow("КПП",     self.f_kpp)
        if self.mode == "edit":
            form.addRow("", self.f_active)

        self.notif = _NotificationBar()
        div = QFrame(); div.setFrameShape(QFrame.Shape.HLine); div.setStyleSheet("color:#dde7f2;")

        cancel = QPushButton("Отмена"); cancel.setObjectName("cancelBtn")
        cancel.setCursor(Qt.CursorShape.PointingHandCursor); cancel.clicked.connect(self.reject)
        save = QPushButton("Сохранить"); save.setObjectName("saveBtn")
        save.setCursor(Qt.CursorShape.PointingHandCursor); save.clicked.connect(self._on_save)

        btn_row = QHBoxLayout(); btn_row.setSpacing(10); btn_row.addStretch()
        btn_row.addWidget(cancel); btn_row.addWidget(save)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 24); root.setSpacing(16)
        root.addWidget(title); root.addLayout(form)
        root.addWidget(self.notif); root.addWidget(div); root.addLayout(btn_row)

    def _field(self, placeholder: str) -> QLineEdit:
        f = QLineEdit(); f.setObjectName("formField"); f.setPlaceholderText(placeholder)
        return f

    def _fill(self, w: WarehouseRecord) -> None:
        self.f_code.setText(w.code)
        self.f_name.setText(w.name)
        self.f_address.setText(w.address or "")
        self.f_inn.setText(w.inn or "")
        self.f_kpp.setText(w.kpp or "")
        self.f_active.setChecked(w.is_active)

    def _on_save(self) -> None:
        code = self.f_code.text().strip()
        name = self.f_name.text().strip()
        if not code: self.notif.error("Введите код склада."); return
        if not name: self.notif.error("Введите название склада."); return

        self._data = {
            "code":    code,
            "name":    name,
            "address": self.f_address.text().strip() or None,
            "inn":     self.f_inn.text().strip() or None,
            "kpp":     self.f_kpp.text().strip() or None,
            "is_active": self.f_active.isChecked() if self.mode == "edit" else None,
        }
        self.accept()

    def get_data(self) -> dict:
        return self._data
