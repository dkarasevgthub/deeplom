from __future__ import annotations


ROLE_LABELS = {
    "admin": "Администратор",
    "manager": "Менеджер",
    "warehouse": "Складской работник",
}


def get_role_label(role: str) -> str:
    return ROLE_LABELS.get(role, role)
