from __future__ import annotations

from PySide6.QtWidgets import QWidget


class WUFWValidationBadges(QWidget):
    """Compact validation badges for real-time WUF-W checks."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

    def set_check_results(self, check_results: list) -> None:
        """Render check states and code references in a small badge list."""
