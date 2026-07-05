from __future__ import annotations

from PySide6.QtWidgets import QWidget


class WUFWInputPanel(QWidget):
    """Input panel skeleton for WUF-W connection parameters."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

    def bind_model(self, connection) -> None:
        """Bind a WUFWConnection instance to UI controls."""

    def read_inputs(self) -> dict:
        """Collect current panel values as a normalized dictionary."""
        return {}

    def set_defaults_from_beam(self, beam_section) -> None:
        """Auto-suggest shear plate defaults from selected beam."""
