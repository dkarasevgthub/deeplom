from __future__ import annotations

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from desktop.models import User
from desktop.ui.role_labels import get_role_label


class BaseUserPage(QWidget):
    def __init__(self, user: User, page_title: str, page_subtitle: str):
        super().__init__()
        self.user = user
        self.page_title_text = page_title
        self.page_subtitle_text = page_subtitle

        self._setup_ui()
        self._apply_styles()
        self._apply_fonts()

    def _setup_ui(self) -> None:
        self.setObjectName("pageRoot")

        self.page_title = QLabel(self.page_title_text)
        self.page_title.setObjectName("pageTitle")

        self.page_subtitle = QLabel(self.page_subtitle_text)
        self.page_subtitle.setObjectName("pageSubtitle")
        self.page_subtitle.setWordWrap(True)
        self.page_subtitle.setVisible(bool(self.page_subtitle_text.strip()))

        self.user_name_label = QLabel(self.user.full_name)
        self.user_name_label.setObjectName("userName")

        self.user_id_label = QLabel(f"ID: {self.user.id}")
        self.user_id_label.setObjectName("userMeta")

        self.user_login_label = QLabel(f"Логин: {self.user.login}")
        self.user_login_label.setObjectName("userMeta")

        self.user_role_label = QLabel(f"Роль: {get_role_label(self.user.role)}")
        self.user_role_label.setObjectName("userMeta")

        warehouse_text = str(self.user.warehouse_id) if self.user.warehouse_id is not None else "—"
        self.user_warehouse_label = QLabel(f"Склад: {warehouse_text}")
        self.user_warehouse_label.setObjectName("userMeta")

        status_text = "Активен" if self.user.is_active else "Неактивен"
        self.user_status_label = QLabel(f"Статус: {status_text}")
        self.user_status_label.setObjectName("userMeta")

        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(10)
        card_layout.addWidget(self.user_name_label)
        card_layout.addWidget(self.user_id_label)
        card_layout.addWidget(self.user_login_label)
        card_layout.addWidget(self.user_role_label)
        card_layout.addWidget(self.user_warehouse_label)
        card_layout.addWidget(self.user_status_label)

        self.user_card = QFrame()
        self.user_card.setObjectName("userCard")
        self.user_card.setLayout(card_layout)

        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(18)
        root_layout.addWidget(self.page_title)
        root_layout.addWidget(self.page_subtitle)
        root_layout.addWidget(self.user_card)
        root_layout.addStretch()

        self.setLayout(root_layout)

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QWidget#pageRoot {
                background-color: transparent;
            }

            QLabel#pageTitle {
                color: #102a4d;
                font-size: 28px;
                font-weight: 700;
            }

            QLabel#pageSubtitle {
                color: #63748b;
                font-size: 14px;
            }

            QFrame#userCard {
                background-color: #ffffff;
                border: 1px solid #dfe8f3;
                border-radius: 20px;
            }

            QLabel#userName {
                color: #16345f;
                font-size: 20px;
                font-weight: 700;
            }

            QLabel#userMeta {
                color: #334155;
                font-size: 14px;
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
