from __future__ import annotations

from PySide6.QtWidgets import QWidget


class WUFWPreviewWidget(QWidget):
    """2D/3D preview skeleton for WUF-W detailing."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

    def update_geometry(self, connection) -> None:
        """Refresh beam, column, shear plate, welds, and access-hole geometry."""

    def show_check_overlay(self, check_results: list) -> None:
        """Show color-coded pass/fail markers on the preview."""
