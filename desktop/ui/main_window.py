from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from desktop.models import User
from desktop.ui.pages.catalog_page import CatalogPage
from desktop.ui.pages.home_page import HomePage
from desktop.ui.pages.orders_page import OrdersPage
from desktop.ui.pages.receiving_page import ReceivingPage
from desktop.ui.pages.shipping_page import ShippingPage
from desktop.ui.role_labels import get_role_label


class MainWindow(QWidget):
    logout_requested = Signal()

    def __init__(self, user: User):
        super().__init__()
        self.user = user
        self._nav_buttons: dict[str, QPushButton] = {}

        self.setWindowTitle("ProЗапас")
        self.setMinimumSize(1100, 720)

        self._setup_ui()
        self._apply_styles()
        self._apply_fonts()
        self._switch_tab("home")

    def _setup_ui(self) -> None:
        self.setObjectName("root")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.brand_label = QLabel("ProЗапас")
        self.brand_label.setObjectName("brandLabel")

        self.nav_title = QLabel("Меню")
        self.nav_title.setObjectName("navTitle")

        self.home_button = self._build_nav_button("Главная", "home")
        self.receiving_button = self._build_nav_button("Приемка", "receiving")
        self.shipping_button = self._build_nav_button("Отгрузка", "shipping")
        self.orders_button = self._build_nav_button("Заказы", "orders")
        self.catalog_button = self._build_nav_button("Справочник", "catalog")

        self.user_meta_label = QLabel(f"{self.user.full_name}\n{get_role_label(self.user.role)}")
        self.user_meta_label.setObjectName("userMeta")

        self.logout_button = QPushButton("Выйти")
        self.logout_button.setObjectName("logoutButton")
        self.logout_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.logout_button.clicked.connect(self.logout_requested.emit)

        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(20, 22, 20, 20)
        sidebar_layout.setSpacing(10)
        sidebar_layout.addWidget(self.brand_label)
        sidebar_layout.addSpacing(12)
        sidebar_layout.addWidget(self.nav_title)
        sidebar_layout.addWidget(self.home_button)
        sidebar_layout.addWidget(self.receiving_button)
        sidebar_layout.addWidget(self.shipping_button)
        sidebar_layout.addWidget(self.orders_button)
        sidebar_layout.addWidget(self.catalog_button)
        sidebar_layout.addStretch()
        sidebar_layout.addWidget(self.user_meta_label)
        sidebar_layout.addSpacing(8)
        sidebar_layout.addWidget(self.logout_button)

        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setLayout(sidebar_layout)
        self.sidebar.setFixedWidth(248)

        self.stack = QStackedWidget()
        self.stack.setObjectName("contentStack")
        self.stack.addWidget(HomePage(self.user))
        self.stack.addWidget(ReceivingPage(self.user))
        self.stack.addWidget(ShippingPage(self.user))
        self.stack.addWidget(OrdersPage(self.user))
        self.stack.addWidget(CatalogPage(self.user))

        self.page_lookup = {
            "home": 0,
            "receiving": 1,
            "shipping": 2,
            "orders": 3,
            "catalog": 4,
        }

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(28, 28, 28, 28)
        content_layout.addWidget(self.stack)

        self.content = QFrame()
        self.content.setObjectName("content")
        self.content.setLayout(content_layout)

        root_layout = QHBoxLayout()
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(16)
        root_layout.addWidget(self.sidebar)
        root_layout.addWidget(self.content, 1)

        self.setLayout(root_layout)

    def _build_nav_button(self, text: str, key: str) -> QPushButton:
        button = QPushButton(text)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setObjectName("navButton")
        button.setProperty("active", False)
        button.setMinimumHeight(44)
        button.clicked.connect(lambda: self._switch_tab(key))
        self._nav_buttons[key] = button
        return button

    def _switch_tab(self, key: str) -> None:
        self.stack.setCurrentIndex(self.page_lookup[key])

        for nav_key, button in self._nav_buttons.items():
            button.setProperty("active", nav_key == key)
            button.style().unpolish(button)
            button.style().polish(button)
            button.update()

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QWidget#root {
                background-color: #eef4fb;
                font-family: Roboto, sans-serif;
            }

            QFrame#sidebar {
                background-color: #ffffff;
                border: 1px solid #dde7f2;
                border-radius: 24px;
            }

            QFrame#content {
                background-color: #ffffff;
                border: 1px solid #dde7f2;
                border-radius: 24px;
            }

            QStackedWidget#contentStack {
                background-color: transparent;
            }

            QLabel#brandLabel {
                color: #16345f;
                font-size: 24px;
                font-weight: 700;
            }

            QLabel#navTitle {
                color: #8a97aa;
                font-size: 12px;
                font-weight: 600;
                padding-top: 4px;
                padding-bottom: 4px;
            }

            QPushButton#navButton {
                background-color: transparent;
                color: #334155;
                border: none;
                border-radius: 14px;
                font-size: 14px;
                font-weight: 500;
                padding: 0 14px;
                text-align: left;
            }

            QPushButton#navButton:hover {
                background-color: #f3f8ff;
                color: #1d4ed8;
            }

            QPushButton#navButton[active="true"] {
                background-color: #e9f2ff;
                color: #1d4ed8;
                font-weight: 600;
            }

            QLabel#userMeta {
                color: #5b6b80;
                font-size: 13px;
                line-height: 1.4;
            }

            QPushButton#logoutButton {
                background-color: #f3f6fb;
                color: #334155;
                border: 1px solid #d9e2ee;
                border-radius: 14px;
                min-height: 44px;
                font-size: 14px;
                font-weight: 600;
            }

            QPushButton#logoutButton:hover {
                background-color: #eaf0f8;
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
