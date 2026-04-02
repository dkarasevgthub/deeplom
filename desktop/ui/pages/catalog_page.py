from __future__ import annotations

from desktop.models import User
from desktop.ui.pages.base_user_page import BaseUserPage


class CatalogPage(BaseUserPage):
    def __init__(self, user: User):
        super().__init__(
            user=user,
            page_title="Справочник",
            page_subtitle="",
        )
