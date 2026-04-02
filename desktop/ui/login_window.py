from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class LoginWindow(QWidget):
    login_requested = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ProЗапас")
        self.setMinimumSize(700, 520)

        self._password_visible = False

        self._setup_ui()
        self._apply_styles()
        self._apply_fonts()

    def _setup_ui(self) -> None:
        self.setObjectName("root")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.title_label = QLabel("Добро пожаловать в ProЗапас")
        self.title_label.setObjectName("titleLabel")
        self.title_label.setWordWrap(True)

        self.subtitle_label = QLabel("Войдите в систему для продолжения работы")
        self.subtitle_label.setObjectName("subtitleLabel")
        self.subtitle_label.setWordWrap(True)

        self.status_label = QLabel("")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setWordWrap(True)
        self.status_label.hide()

        self.login_label = QLabel("Логин")
        self.login_label.setObjectName("fieldLabel")

        self.login_input = QLineEdit()
        self.login_input.setObjectName("input")
        self.login_input.setFixedHeight(52)
        self.login_input.setTextMargins(16, 0, 16, 0)
        self.login_input.setPlaceholderText("Введите логин")
        self.login_input.returnPressed.connect(self._emit_login_requested)

        self.password_label = QLabel("Пароль")
        self.password_label.setObjectName("fieldLabel")

        self.password_input = QLineEdit()
        self.password_input.setObjectName("input")
        self.password_input.setFixedHeight(52)
        self.password_input.setTextMargins(16, 0, 16, 0)
        self.password_input.setPlaceholderText("Введите пароль")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.returnPressed.connect(self._emit_login_requested)

        self.password_toggle_action = QAction(self)
        self.password_toggle_action.setIcon(self._build_eye_icon(False))
        self.password_toggle_action.triggered.connect(self._toggle_password_visibility)
        self.password_input.addAction(
            self.password_toggle_action,
            QLineEdit.ActionPosition.TrailingPosition,
        )

        self.login_button = QPushButton("Войти")
        self.login_button.setObjectName("primaryButton")
        self.login_button.setFixedHeight(52)
        self.login_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_button.clicked.connect(self._emit_login_requested)

        form_layout = QVBoxLayout()
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(10)
        form_layout.addWidget(self.login_label)
        form_layout.addWidget(self.login_input)
        form_layout.addSpacing(6)
        form_layout.addWidget(self.password_label)
        form_layout.addWidget(self.password_input)
        form_layout.addSpacing(12)
        form_layout.addWidget(self.status_label)
        form_layout.addSpacing(6)
        form_layout.addWidget(self.login_button)

        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(44, 40, 44, 40)
        card_layout.setSpacing(14)
        card_layout.addWidget(self.title_label)
        card_layout.addWidget(self.subtitle_label)
        card_layout.addSpacing(18)
        card_layout.addLayout(form_layout)

        self.card = QFrame()
        self.card.setObjectName("card")
        self.card.setLayout(card_layout)

        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(36, 36, 36, 36)
        root_layout.addStretch(1)
        root_layout.addWidget(self.card, alignment=Qt.AlignmentFlag.AlignCenter)
        root_layout.addStretch(1)

        self.setLayout(root_layout)

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QWidget#root {
                background-color: #eef4fb;
                font-family: Roboto, sans-serif;
            }

            QFrame#card {
                background-color: #ffffff;
                border: 1px solid #dde7f2;
                border-radius: 28px;
                min-width: 540px;
                max-width: 540px;
            }

            QLabel#titleLabel {
                color: #102a4d;
                font-size: 26px;
                font-weight: 700;
            }

            QLabel#subtitleLabel {
                color: #63748b;
                font-size: 14px;
            }

            QLabel#fieldLabel {
                color: #16345f;
                font-size: 14px;
                font-weight: 600;
            }

            QLabel#statusLabel {
                background-color: #fff1f2;
                color: #dc2626;
                border: 1px solid #fecdd3;
                border-radius: 14px;
                padding: 12px 14px;
                font-size: 13px;
            }

            QLineEdit#input {
                background-color: #f8fbff;
                border: 1px solid #ccd8e5;
                border-radius: 14px;
                font-size: 15px;
                color: #111827;
            }

            QLineEdit#input:focus {
                border: 1px solid #2563eb;
                background-color: #ffffff;
            }

            QLineEdit#input:disabled {
                background-color: #f3f6fb;
                color: #94a3b8;
            }

            QPushButton#primaryButton {
                background-color: #3164e0;
                color: #ffffff;
                border: none;
                border-radius: 14px;
                font-size: 15px;
                font-weight: 600;
            }

            QPushButton#primaryButton:hover {
                background-color: #2857ca;
            }

            QPushButton#primaryButton:pressed {
                background-color: #2048a8;
            }

            QPushButton#primaryButton:disabled {
                background-color: #9bb7f6;
                color: #eef4ff;
            }
            """
        )

    def _apply_fonts(self) -> None:
        widgets = self.findChildren(QWidget)
        widgets.append(self)

        for widget in widgets:
            font = widget.font()
            font.setFamilies(["Roboto", "sans-serif"])
            widget.setFont(font)

    def set_busy(self, busy: bool) -> None:
        self.login_input.setDisabled(busy)
        self.password_input.setDisabled(busy)
        self.login_button.setDisabled(busy)
        self.password_toggle_action.setEnabled(not busy)
        self.login_button.setText("Входим..." if busy else "Войти")

    def show_error(self, message: str) -> None:
        self.status_label.setText(message)
        self.status_label.show()

    def clear_error(self) -> None:
        self.status_label.clear()
        self.status_label.hide()

    def restore_default_view(self) -> None:
        if self.isFullScreen() or self.isMaximized():
            self.showNormal()

        self.resize(700, 520)
        self.updateGeometry()
        self.update()

    def _build_eye_icon(self, crossed: bool) -> QIcon:
        pixmap = QPixmap(QSize(18, 18))
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pen = QPen(QColor("#64748b"))
        pen.setWidth(2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)

        painter.drawArc(3, 5, 12, 8, 0, 180 * 16)
        painter.drawArc(3, 5, 12, 8, 180 * 16, 180 * 16)
        painter.drawEllipse(7, 7, 4, 4)

        if crossed:
            painter.drawLine(4, 14, 14, 4)

        painter.end()
        return QIcon(pixmap)

    def _toggle_password_visibility(self) -> None:
        self._password_visible = not self._password_visible

        if self._password_visible:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.password_toggle_action.setIcon(self._build_eye_icon(True))
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.password_toggle_action.setIcon(self._build_eye_icon(False))

    def _emit_login_requested(self) -> None:
        self.clear_error()
        self.login_requested.emit(
            self.login_input.text().strip(),
            self.password_input.text(),
        )
