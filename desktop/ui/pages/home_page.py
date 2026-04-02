from __future__ import annotations

from desktop.models import User
from desktop.ui.pages.base_user_page import BaseUserPage


class HomePage(BaseUserPage):
    def __init__(self, user: User):
        super().__init__(
            user=user,
            page_title="Главная",
            page_subtitle="",
        )
