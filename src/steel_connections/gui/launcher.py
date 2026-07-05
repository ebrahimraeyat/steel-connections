"""Osdag-style module launcher window.

Presents the available design modules in a left navigation panel with a
stacked page area on the right. Each leaf module offers one or more module
variants (radio buttons) and a Start button that opens the corresponding
module window. Modules that are not yet implemented are shown as
``UNDER DEVELOPMENT`` placeholders.
"""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from steel_connections.connection_types import ConnectionType

UNDER_DEVELOPMENT = "UNDER DEVELOPMENT"


class _VariantWidget(QWidget):
    """A single selectable module variant: image placeholder + radio + label."""

    def __init__(self, name: str, image_path: str, object_name: str, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(6)
        lay.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        preview = QLabel()
        preview.setFixedSize(160, 120)
        preview.setAlignment(Qt.AlignCenter)
        preview.setStyleSheet(
            "border:1px solid #888; border-radius:4px; color:#888;"
        )
        if image_path:
            from PySide6.QtGui import QPixmap

            pix = QPixmap(image_path)
            if not pix.isNull():
                preview.setPixmap(
                    pix.scaled(
                        preview.size(),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation,
                    )
                )
            else:
                preview.setText("[No preview]")
        else:
            preview.setText("[No preview]")
        lay.addWidget(preview)

        self.radio = QRadioButton(name)
        self.radio.setObjectName(object_name)
        lay.addWidget(self.radio, alignment=Qt.AlignHCenter)


class LauncherWindow(QMainWindow):
    """Main entry-point window listing all design modules."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Steel Connections \u2014 Module Launcher")
        self.resize(900, 600)
        self._module_window = None  # keep a reference so it is not GC'd

        # Module tree: 1st level -> left-panel buttons; nested dicts -> tabs;
        # tuple(*variants, launcher) -> selectable module page.
        self._modules: dict[str, object] = {
            "Connection": {
                "Moment Connection": {
                    "Beam-to-Column": (
                        ("Bolted Flange Plate (BFP)", "", ConnectionType.BFP.value),
                        (
                            "Welded Unreinforced Flange \u2013 Welded Web (WUF-W)",
                            "",
                            ConnectionType.WUFW.value,
                        ),
                        self._launch_moment_beam_to_column,
                    ),
                    "Beam-to-Beam Splice": UNDER_DEVELOPMENT,
                    "Column-to-Column Splice": UNDER_DEVELOPMENT,
                },
                "Shear Connection": UNDER_DEVELOPMENT,
                "Base Plate": UNDER_DEVELOPMENT,
            },
            "Tension Member": UNDER_DEVELOPMENT,
            "Compression Member": UNDER_DEVELOPMENT,
            "Flexural Member": UNDER_DEVELOPMENT,
        }

        self._build_ui()

    # ── UI construction ────────────────────────────────────────────────────
    def _build_ui(self) -> None:
        central = QWidget()
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Left navigation panel
        nav = QWidget()
        nav.setFixedWidth(220)
        nav_lay = QVBoxLayout(nav)
        nav_lay.setContentsMargins(8, 12, 8, 12)
        nav_lay.setSpacing(6)

        title = QLabel("Modules")
        title.setStyleSheet("font-weight:bold; font-size:14px;")
        nav_lay.addWidget(title)

        self._stack = QStackedWidget()
        self._nav_buttons: list[QPushButton] = []

        for index, (name, value) in enumerate(self._modules.items()):
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setFixedHeight(34)
            btn.clicked.connect(lambda _=False, i=index: self._select_page(i))
            nav_lay.addWidget(btn)
            self._nav_buttons.append(btn)
            self._stack.addWidget(self._render_node(value))

        nav_lay.addStretch()
        root.addWidget(nav)
        root.addWidget(self._stack, stretch=1)

        self.setCentralWidget(central)

        if self._nav_buttons:
            self._select_page(0)

    def _select_page(self, index: int) -> None:
        self._stack.setCurrentIndex(index)
        for i, btn in enumerate(self._nav_buttons):
            btn.setChecked(i == index)

    def _render_node(self, value: object) -> QWidget:
        """Recursively render a module tree node into a widget."""
        if value == UNDER_DEVELOPMENT:
            return self._under_development_page()

        if isinstance(value, dict):
            tabs = QTabWidget()
            tabs.setDocumentMode(True)
            for key, sub in value.items():
                tabs.addTab(self._render_node(sub), key)
            return tabs

        if isinstance(value, (list, tuple)) and callable(value[-1]):
            *variants, launcher = value
            return self._variant_page(variants, launcher)

        return self._under_development_page()

    def _variant_page(
        self, variants: list, launcher: Callable[[QWidget], None]
    ) -> QWidget:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(12)

        grid_host = QWidget()
        grid = QGridLayout(grid_host)
        grid.setSpacing(12)
        group = QButtonGroup(page)
        group.setExclusive(True)

        cols = 2
        first_radio: QRadioButton | None = None
        for i, (name, image_path, object_name) in enumerate(variants):
            w = _VariantWidget(name, image_path, object_name, page)
            group.addButton(w.radio)
            grid.addWidget(w, i // cols, i % cols)
            if first_radio is None:
                first_radio = w.radio

        if first_radio is not None:
            first_radio.setChecked(True)

        outer.addWidget(grid_host)

        start_bar = QHBoxLayout()
        start_bar.addStretch()
        start_btn = QPushButton("Start")
        start_btn.setFixedWidth(120)
        start_btn.setFixedHeight(32)
        start_btn.setStyleSheet("font-weight:bold;")
        start_btn.clicked.connect(lambda: launcher(page))
        start_bar.addWidget(start_btn)
        outer.addLayout(start_bar)
        outer.addStretch()
        return page

    def _under_development_page(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setAlignment(Qt.AlignCenter)
        label = QLabel(UNDER_DEVELOPMENT)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color:#999; font-size:16px; font-weight:bold;")
        lay.addWidget(label)
        return page

    # ── launchers ──────────────────────────────────────────────────────────
    def _launch_moment_beam_to_column(self, page: QWidget) -> None:
        selected = self._selected_object_name(page)
        if selected is None:
            QMessageBox.information(
                self, "Select a variant", "Please select a connection variant."
            )
            return
        try:
            ctype = ConnectionType(selected)
        except ValueError:
            QMessageBox.warning(self, "Unknown module", f"Unknown variant: {selected}")
            return
        self._open_module(ctype)

    @staticmethod
    def _selected_object_name(page: QWidget) -> str | None:
        for radio in page.findChildren(QRadioButton):
            if radio.isChecked():
                return radio.objectName()
        return None

    def _open_module(self, connection_type: ConnectionType) -> None:
        from steel_connections.main_window import MainWindow

        self._module_window = MainWindow(connection_type=connection_type)
        self._module_window.closed.connect(self._on_module_closed)
        self.hide()
        self._module_window.show()

    def _on_module_closed(self) -> None:
        self._module_window = None
        self.show()
