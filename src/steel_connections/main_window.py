# -*- coding: utf-8 -*-

import sys
from datetime import datetime
from pathlib import Path
from importlib.resources import files

from PySide6.QtCore import QSettings, QFile, QTextStream, Qt, QTimer, QStandardPaths
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication, QMessageBox, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QFormLayout,
    QSplitter, QScrollArea, QGroupBox,
    QLabel, QPushButton, QTextBrowser,
    QDoubleSpinBox, QSpinBox, QComboBox,
    QSizePolicy, QFrame, QFileDialog, QTabWidget, QDialog, QDialogButtonBox,
)
from PySide6 import QtWidgets

from steel_connections.gui.toggle_button import Switch
from steel_connections.gui.viewer_3d import Viewer3D
from steel_connections.gui.dim_sketch import ISketchWidget, FlangePlateSketchWidget, WebPlateSketchWidget
from steel_connections.cad.bfp_cad import build_bfp_shapes
from steel_connections.model_io import save_model, load_model, FILE_FILTER, FILE_EXT

from steel_connections.connections import DesignCode
from steel_connections.bfp_connection import BFPConnection, BFPCONNECTIONERROR
from steel_connections.bfp_connection_aisc358 import AISC358BFPConnection, AISC358BFPERROR
from steel_connections.member.member import SteelSection
from steel_connections.component.bolt import Bolt, BoltGroup2D
from steel_connections.component.plate import Plate
from steel_connections.bfp_connection_design import (
    design_bfp_connection, BoltType, DesignMethod, ConnectionType
)


# ── helpers ──────────────────────────────────────────────────────────────────

def _section_label(text: str) -> QLabel:
    lbl = QLabel(f"  {text}")
    lbl.setStyleSheet(
        "font-weight: bold; font-size: 11px; "
        "background: #3a3a5c; color: #ccc; padding: 2px 6px; "
        "border-radius: 3px; margin-top: 6px;"
    )
    return lbl


def _hr() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Sunken)
    return line


def _setup_spin(sb: QDoubleSpinBox, mn, mx, val, suffix=""):
    sb.setMinimum(mn); sb.setMaximum(mx)
    sb.setValue(val);  sb.setSuffix(suffix)


# ── result row ────────────────────────────────────────────────────────────────

class ResultRow(QWidget):
    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(4, 1, 4, 1)
        self._lbl = QLabel(label)
        self._lbl.setFixedWidth(145)
        self._lbl.setStyleSheet("color: #999; font-size: 11px;")
        self._val = QLabel("—")
        self._val.setStyleSheet("font-weight: bold; font-size: 11px;")
        lay.addWidget(self._lbl)
        lay.addWidget(self._val)
        lay.addStretch()

    def set_value(self, text: str, ok=None):
        self._val.setText(text)
        if ok is True:
            self._val.setStyleSheet("font-weight:bold;font-size:11px;color:#4caf50;")
        elif ok is False:
            self._val.setStyleSheet("font-weight:bold;font-size:11px;color:#f44336;")
        else:
            self._val.setStyleSheet("font-weight:bold;font-size:11px;")


# ── main window ───────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Steel Connection Designer — BFP")
        self.resize(1440, 840)
        self._current_path: str | None = None   # path of the open .scj file
        self._is_dirty: bool = False             # unsaved changes flag
        self._last_m10_result = None             # last Mabhas10 design result
        self._last_dir = self._documents_dir()
        self._startup_last_file: str | None = None
        self._saved_design_code = DesignCode.MABHAS10.value
        self._saved_projection_perspective = False
        self._saved_display_style = "shaded"
        self._saved_shadows_enabled = False
        self._saved_dark_theme = False
        self._build_ui()
        self._build_menu()
        self._fill_thickness()
        self._wire_signals()
        self._load_settings()
        self._on_code_changed()   # apply panel visibility for saved code
        QTimer.singleShot(0, self._finish_startup)

    def _settings(self) -> QSettings:
        cfg_dir = QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation)
        cfg_root = Path(cfg_dir) if cfg_dir else (Path.home() / ".steel_connection")
        cfg_root.mkdir(parents=True, exist_ok=True)
        return QSettings(str(cfg_root / "main_window_v2.ini"), QSettings.IniFormat)

    def _documents_dir(self) -> str:
        docs = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
        return docs or str(Path.home())

    def _default_dialog_dir(self) -> str:
        return self._last_dir or self._documents_dir()

    def _projection_is_perspective(self) -> bool:
        return self.view_perspective_switch.isChecked()

    def _display_style(self) -> str:
        return self.view_style_combo.currentData() or "shaded"

    def _shadows_enabled(self) -> bool:
        return self.view_shadows_switch.isChecked()

    def _theme_is_dark(self) -> bool:
        return self.switch.isChecked()

    def _apply_projection_toggle(self, perspective: bool) -> None:
        self.view_perspective_switch.blockSignals(True)
        self.view_perspective_switch.setChecked(perspective)
        self.view_perspective_switch.blockSignals(False)
        if perspective:
            self._viewer.set_projection_perspective()
        else:
            self._viewer.set_projection_isometric()

    def _apply_display_style(self, style: str) -> None:
        target = style or "shaded"
        idx = self.view_style_combo.findData(target)
        if idx < 0:
            idx = self.view_style_combo.findData("shaded")
        self.view_style_combo.blockSignals(True)
        if idx >= 0:
            self.view_style_combo.setCurrentIndex(idx)
        self.view_style_combo.blockSignals(False)
        self._viewer.set_visual_style(self.view_style_combo.currentData() or "shaded")

    def _apply_shadows_toggle(self, enabled: bool) -> None:
        self.view_shadows_switch.blockSignals(True)
        self.view_shadows_switch.setChecked(enabled)
        self.view_shadows_switch.blockSignals(False)
        self._viewer.set_shadows_enabled(enabled)

    def _apply_theme_toggle(self, dark: bool) -> None:
        self.switch.blockSignals(True)
        self.switch.setChecked(dark)
        self.switch.blockSignals(False)
        toggle_stylesheet(dark)

    def _set_design_code_by_value(self, saved_code: str) -> None:
        for i in range(self.design_code_combo.count()):
            item = self.design_code_combo.itemData(i)
            item_value = item.value if isinstance(item, DesignCode) else item
            if item_value == saved_code:
                self.design_code_combo.setCurrentIndex(i)
                break

    def _apply_saved_preferences_to_ui(self) -> None:
        self._set_design_code_by_value(self._saved_design_code)
        self._on_code_changed()
        self._apply_theme_toggle(self._saved_dark_theme)
        self._apply_projection_toggle(self._saved_projection_perspective)
        self._apply_display_style(self._saved_display_style)
        self._apply_shadows_toggle(self._saved_shadows_enabled)
        self.design_code_combo.update()
        self.view_perspective_switch.update()
        self.view_style_combo.update()
        self.view_shadows_switch.update()
        self.switch.update()

    def _save_app_settings(self) -> None:
        qs = self._settings()
        qs.setValue("geometry", self.saveGeometry())
        qs.setValue("state", self.saveState())
        dc = self.design_code_combo.currentData()
        self._saved_design_code = dc.value if hasattr(dc, "value") else str(dc)
        self._saved_projection_perspective = self._projection_is_perspective()
        self._saved_display_style = self._display_style()
        self._saved_shadows_enabled = self._shadows_enabled()
        self._saved_dark_theme = self._theme_is_dark()
        qs.setValue("design_code", self._saved_design_code)
        qs.setValue("projection_perspective", self._saved_projection_perspective)
        qs.setValue("display_style", self._saved_display_style)
        qs.setValue("shadows_enabled", self._saved_shadows_enabled)
        qs.setValue("dark_theme", self._saved_dark_theme)
        qs.setValue("last_dir", self._last_dir or self._documents_dir())
        qs.setValue("last_file", self._current_path or "")
        qs.sync()

    def _restore_last_file(self) -> None:
        path = self._startup_last_file
        self._startup_last_file = None
        if not path or not Path(path).is_file():
            self.calculate_connection()
            return
        try:
            self._open_model_path(path, mark_log=False)
            self._apply_saved_preferences_to_ui()
            self.calculate_connection()
        except Exception:
            self.calculate_connection()

    def _finish_startup(self) -> None:
        # Apply saved preferences two times to ensure they take effect
        # First application sets the UI state
        self._apply_saved_preferences_to_ui()
        
        # Load last file or calculate default connection
        if self._startup_last_file:
            self._restore_last_file()
        else:
            self.calculate_connection()
        
        # Second application (delayed) ensures settings are fully applied after UI is ready
        QTimer.singleShot(100, lambda: self._apply_saved_preferences_to_ui())

    # ── menu bar ──────────────────────────────────────────────────
    def _build_menu(self):
        mb = self.menuBar()
        fm = mb.addMenu("&File")

        act_new = QAction("&New", self)
        act_new.setShortcut(QKeySequence.New)
        act_new.triggered.connect(self._new_model)
        fm.addAction(act_new)

        act_open = QAction("&Open…", self)
        act_open.setShortcut(QKeySequence.Open)
        act_open.triggered.connect(self._open_model)
        fm.addAction(act_open)

        fm.addSeparator()

        act_save = QAction("&Save", self)
        act_save.setShortcut(QKeySequence.Save)
        act_save.triggered.connect(self._save_model)
        fm.addAction(act_save)

        act_saveas = QAction("Save &As…", self)
        act_saveas.setShortcut(QKeySequence.SaveAs)
        act_saveas.triggered.connect(self._save_model_as)
        fm.addAction(act_saveas)

        fm.addSeparator()

        act_quit = QAction("&Quit", self)
        act_quit.setShortcut(QKeySequence.Quit)
        act_quit.triggered.connect(self.close)
        fm.addAction(act_quit)

        sm = mb.addMenu("&Settings")
        act_settings = QAction("&Preferences…", self)
        act_settings.triggered.connect(self._open_settings_dialog)
        sm.addAction(act_settings)

    # ── layout ───────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QSplitter(Qt.Horizontal, self)
        root.setHandleWidth(5)
        self.setCentralWidget(root)
        root.addWidget(self._build_left_panel())
        root.addWidget(self._build_centre_panel())
        root.addWidget(self._build_right_panel())
        root.setSizes([320, 840, 280])
        root.setStretchFactor(0, 0)
        root.setStretchFactor(1, 1)
        root.setStretchFactor(2, 0)
        # Allow left and right panels to be resizable but not collapsible
        root.setCollapsible(0, False)
        root.setCollapsible(1, False)
        root.setCollapsible(2, False)

    # ── left: inputs ─────────────────────────────────────────────────────────

    def _build_left_panel(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setMinimumWidth(230); scroll.setMaximumWidth(420)

        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(4)

        # dark‑mode toggle
        sw_row = QHBoxLayout()
        sw_row.addWidget(QLabel("Dark mode"))
        self.switch = Switch(thumb_radius=8, track_radius=6)
        sw_row.addWidget(self.switch)
        sw_row.addStretch()
        lay.addLayout(sw_row)
        lay.addWidget(_hr())

        # Design code selector
        lay.addWidget(_section_label("Design Code"))
        dc_box = QGroupBox(); dc_form = QFormLayout(dc_box); dc_form.setContentsMargins(6, 4, 6, 4)
        self.design_code_combo = QComboBox()
        for code in DesignCode:
            self.design_code_combo.addItem(code.value, userData=code)
        dc_form.addRow("Standard:", self.design_code_combo)
        lay.addWidget(dc_box)
        lay.addWidget(_hr())

        input_tabs = QTabWidget()
        input_tabs.setDocumentMode(True)

        member_tab = QWidget()
        member_lay = QVBoxLayout(member_tab)
        member_lay.setContentsMargins(4, 4, 4, 4)
        member_lay.setSpacing(4)

        connection_tab = QWidget()
        connection_lay = QVBoxLayout(connection_tab)
        connection_lay.setContentsMargins(4, 4, 4, 4)
        connection_lay.setSpacing(4)

        design_tab = QWidget()
        design_lay = QVBoxLayout(design_tab)
        design_lay.setContentsMargins(4, 4, 4, 4)
        design_lay.setSpacing(4)

        # Beam
        member_lay.addWidget(_section_label("Beam"))
        self.beam_bf          = QDoubleSpinBox(); _setup_spin(self.beam_bf, 5, 100, 20, " cm")
        self.beam_totaldepth  = QDoubleSpinBox(); _setup_spin(self.beam_totaldepth, 5, 150, 30, " cm")
        self.beam_tf = QComboBox(); self.beam_tw = QComboBox()
        member_lay.addWidget(ISketchWidget(self.beam_bf, self.beam_totaldepth,
                           self.beam_tf, self.beam_tw, is_column=False))

        # Column
        member_lay.addWidget(_section_label("Column"))
        self.column_bf         = QDoubleSpinBox(); _setup_spin(self.column_bf, 5, 100, 20, " cm")
        self.column_totaldepth = QDoubleSpinBox(); _setup_spin(self.column_totaldepth, 5, 150, 30, " cm")
        self.column_tf = QComboBox(); self.column_tw = QComboBox()
        member_lay.addWidget(ISketchWidget(self.column_bf, self.column_totaldepth,
                           self.column_tf, self.column_tw, is_column=True))
        member_lay.addStretch()

        # Plate
        connection_lay.addWidget(_section_label("Flange Plate"))
        self.plate_width     = QDoubleSpinBox(); _setup_spin(self.plate_width, 5, 60, 15, " cm")
        self.plate_length    = QDoubleSpinBox(); _setup_spin(self.plate_length, 5, 100, 30, " cm")
        self.plate_thickness = QComboBox()
        connection_lay.addWidget(FlangePlateSketchWidget(self.plate_length, self.plate_width,
                                 self.plate_thickness))

        # Web Plate
        connection_lay.addWidget(_section_label("Web Plate"))
        self.web_plate_length    = QDoubleSpinBox(); _setup_spin(self.web_plate_length, 1, 100, 25, " cm")
        self.web_plate_height    = QDoubleSpinBox(); _setup_spin(self.web_plate_height, 1, 100, 20, " cm")
        self.web_plate_thickness = QComboBox()
        connection_lay.addWidget(WebPlateSketchWidget(self.web_plate_height, self.web_plate_length,
                                  self.web_plate_thickness))

        # Flange Bolts
        connection_lay.addWidget(_section_label("Flange Bolts"))
        ltb = QGroupBox(); lf = QFormLayout(ltb); lf.setContentsMargins(6,4,6,4)
        self.bolt_diameter = QComboBox(); self.bolt_diameter.addItems(["2.4", "2.7", "3.0"])
        self.bolt_n = QSpinBox(); self.bolt_n.setMinimum(1); self.bolt_n.setSingleStep(2); self.bolt_n.setValue(2)
        self.bolt_m = QSpinBox(); self.bolt_m.setMinimum(1); self.bolt_m.setValue(5)
        lf.addRow("Diameter:",      self.bolt_diameter)
        lf.addRow("N (rows/Z):",    self.bolt_n)
        lf.addRow("M (gauge/X):",   self.bolt_m)
        connection_lay.addWidget(ltb)

        # Web Bolts
        connection_lay.addWidget(_section_label("Web Bolts"))
        wltb = QGroupBox(); wlf = QFormLayout(wltb); wlf.setContentsMargins(6,4,6,4)
        self.web_bolt_diameter = QComboBox(); self.web_bolt_diameter.addItems(["2.0", "2.4", "2.7"])
        self.web_bolt_nz = QSpinBox(); self.web_bolt_nz.setMinimum(1); self.web_bolt_nz.setValue(3)
        self.web_bolt_nx = QSpinBox(); self.web_bolt_nx.setMinimum(1); self.web_bolt_nx.setValue(2)
        wlf.addRow("Diameter:",   self.web_bolt_diameter)
        wlf.addRow("Rows (Z):",   self.web_bolt_nz)
        wlf.addRow("Cols (X):",   self.web_bolt_nx)
        connection_lay.addWidget(wltb)
        connection_lay.addStretch()

        # ── Shared design inputs for both design codes ─────────────────────
        self._mabhas10_group = QGroupBox()
        m10_lay = QVBoxLayout(self._mabhas10_group)
        m10_lay.setContentsMargins(0, 0, 0, 0)
        m10_lay.setSpacing(4)

        m10_lay.addWidget(_section_label("Material & Beam Strength"))
        m10_steel_box = QGroupBox(); m10_steel_form = QFormLayout(m10_steel_box)
        m10_steel_form.setContentsMargins(6, 4, 6, 4)
        self.m10_fy_beam = QDoubleSpinBox(); _setup_spin(self.m10_fy_beam, 100, 600, 345, " MPa")
        self.m10_fu_beam = QDoubleSpinBox(); _setup_spin(self.m10_fu_beam, 200, 800, 450, " MPa")
        self.m10_zx_beam = QDoubleSpinBox(); _setup_spin(self.m10_zx_beam, 100, 100000, 1020, " cm³")
        m10_steel_form.addRow("Beam F_y (MPa):", self.m10_fy_beam)
        m10_steel_form.addRow("Beam F_u (MPa):", self.m10_fu_beam)
        m10_steel_form.addRow("Beam Z_x (cm³):", self.m10_zx_beam)
        m10_lay.addWidget(m10_steel_box)

        m10_lay.addWidget(_section_label("Bolt Design"))
        m10_bolt_box = QGroupBox(); m10_bolt_form = QFormLayout(m10_bolt_box)
        m10_bolt_form.setContentsMargins(6, 4, 6, 4)
        self.m10_bolt_type = QComboBox()
        self.m10_bolt_type.addItems(["A325", "A490"])
        self.m10_bolt_diam = QComboBox()
        self.m10_bolt_diam.addItems(["16", "20", "22", "24", "27", "30", "36"])
        self.m10_bolt_diam.setCurrentText("20")
        self.m10_design_method = QComboBox()
        self.m10_design_method.addItems(["LRFD", "ASD"])
        self.m10_bolt_ry = QDoubleSpinBox(); _setup_spin(self.m10_bolt_ry, 1.0, 1.5, 1.1)
        m10_bolt_form.addRow("Bolt type:", self.m10_bolt_type)
        m10_bolt_form.addRow("Bolt diameter (mm):", self.m10_bolt_diam)
        m10_bolt_form.addRow("Design method:", self.m10_design_method)
        m10_bolt_form.addRow("R_y:", self.m10_bolt_ry)
        m10_lay.addWidget(m10_bolt_box)

        m10_lay.addWidget(_section_label("Plate & Detailing"))
        m10_plate_box = QGroupBox(); m10_plate_form = QFormLayout(m10_plate_box)
        m10_plate_form.setContentsMargins(6, 4, 6, 4)
        self.m10_plate_fy = QDoubleSpinBox(); _setup_spin(self.m10_plate_fy, 100, 600, 345, " MPa")
        self.m10_plate_fu = QDoubleSpinBox(); _setup_spin(self.m10_plate_fu, 200, 800, 450, " MPa")
        self.m10_edge_dist = QDoubleSpinBox(); _setup_spin(self.m10_edge_dist, 20, 200, 40, " mm")
        self.m10_bolt_spacing = QDoubleSpinBox(); _setup_spin(self.m10_bolt_spacing, 40, 300, 80, " mm")
        m10_plate_form.addRow("Plate F_y (MPa):", self.m10_plate_fy)
        m10_plate_form.addRow("Plate F_u (MPa):", self.m10_plate_fu)
        m10_plate_form.addRow("Edge distance (mm):", self.m10_edge_dist)
        m10_plate_form.addRow("Bolt spacing (mm):", self.m10_bolt_spacing)
        m10_lay.addWidget(m10_plate_box)

        design_lay.addWidget(self._mabhas10_group)
        design_lay.addStretch()

        input_tabs.addTab(member_tab, "Members")
        input_tabs.addTab(connection_tab, "Connection")
        input_tabs.addTab(design_tab, "Design")
        lay.addWidget(input_tabs)

        lay.addStretch()
        scroll.setWidget(inner)
        return scroll

    # ── centre: 3D + log ─────────────────────────────────────────────────────

    def _build_centre_panel(self) -> QWidget:
        vsplit = QSplitter(Qt.Vertical)
        vsplit.setHandleWidth(5)

        # viewer + toolbar
        vc = QWidget()
        vl = QVBoxLayout(vc); vl.setContentsMargins(0,0,0,0); vl.setSpacing(2)

        bar = QHBoxLayout(); bar.setContentsMargins(4,2,4,0); bar.setSpacing(4)
        for lbl, slot in [
            ("Isometric",  lambda: self._viewer.set_view_iso()),
            ("Front",      lambda: self._viewer.set_view_front()),
            ("Side",       lambda: self._viewer.set_view_side()),
            ("Top",        lambda: self._viewer.set_view_top()),
            ("Fit All",    lambda: self._viewer.fit_all()),
        ]:
            btn = QPushButton(lbl); btn.setFixedHeight(22)
            btn.clicked.connect(slot); bar.addWidget(btn)
        bar.addStretch()

        bar.addWidget(QLabel("Perspective"))
        self.view_perspective_switch = Switch(thumb_radius=8, track_radius=6)
        self.view_perspective_switch.toggled.connect(
            lambda checked: self._viewer.set_projection_perspective() if checked else self._viewer.set_projection_isometric()
        )
        bar.addWidget(self.view_perspective_switch)
        bar.addStretch()

        bar.addWidget(QLabel("Display"))
        self.view_style_combo = QComboBox()
        self.view_style_combo.setFixedHeight(22)
        self.view_style_combo.addItem("Shaded", "shaded")
        self.view_style_combo.addItem("Shaded + Edges", "shaded_edges")
        self.view_style_combo.addItem("Wireframe", "wireframe")
        self.view_style_combo.addItem("X-Ray", "xray")
        self.view_style_combo.addItem("X-Ray + Edges", "xray_edges")
        self.view_style_combo.addItem("Hidden Line", "hidden_line")
        self.view_style_combo.currentIndexChanged.connect(
            lambda _=None: self._viewer.set_visual_style(self.view_style_combo.currentData())
        )
        bar.addWidget(self.view_style_combo)
        bar.addStretch()

        bar.addWidget(QLabel("Shadows"))
        self.view_shadows_switch = Switch(thumb_radius=8, track_radius=6)
        self.view_shadows_switch.toggled.connect(
            lambda checked: self._viewer.set_shadows_enabled(checked)
        )
        bar.addWidget(self.view_shadows_switch)
        bar.addStretch()

        self.report_lang = QComboBox()
        self.report_lang.addItems(["English", "فارسی"])
        self.report_lang.setFixedHeight(22)
        bar.addWidget(QLabel("Lang:"))
        bar.addWidget(self.report_lang)

        rpt_btn = QPushButton("📄  Export Report")
        rpt_btn.setFixedHeight(22)
        rpt_btn.setStyleSheet("font-weight:bold; color:#1F497D;")
        rpt_btn.clicked.connect(self._export_report)
        bar.addWidget(rpt_btn)

        dxf_btn = QPushButton("📐  Export DXF")
        dxf_btn.setFixedHeight(22)
        dxf_btn.setStyleSheet("font-weight:bold; color:#1F497D;")
        dxf_btn.clicked.connect(self._export_dxf)
        bar.addWidget(dxf_btn)
        vl.addLayout(bar)

        self._viewer = Viewer3D(vc)
        vl.addWidget(self._viewer)

        # log
        log_box = QGroupBox("Design Log")
        ll = QVBoxLayout(log_box); ll.setContentsMargins(4,4,4,4)
        self.results = QTextBrowser()
        self.results.setMinimumHeight(100)
        ll.addWidget(self.results)

        vsplit.addWidget(vc)
        vsplit.addWidget(log_box)
        vsplit.setSizes([640, 160])
        vsplit.setStretchFactor(0, 1)
        vsplit.setStretchFactor(1, 0)
        return vsplit

    # ── right: design results ─────────────────────────────────────────────────

    def _build_right_panel(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setMinimumWidth(240); scroll.setMaximumWidth(320)

        inner = QWidget()
        lay = QVBoxLayout(inner); lay.setContentsMargins(8,8,8,8); lay.setSpacing(4)

        self._rr: dict[str, ResultRow] = {}
        self._check_rows: dict[str, ResultRow] = {}

        result_tabs = QTabWidget()
        result_tabs.setDocumentMode(True)

        summary_tab = QWidget()
        summary_lay = QVBoxLayout(summary_tab)
        summary_lay.setContentsMargins(4, 4, 4, 4)
        summary_lay.setSpacing(2)

        bolts_tab = QWidget()
        bolts_lay = QVBoxLayout(bolts_tab)
        bolts_lay.setContentsMargins(4, 4, 4, 4)
        bolts_lay.setSpacing(2)

        weld_tab = QWidget()
        weld_lay = QVBoxLayout(weld_tab)
        weld_lay.setContentsMargins(4, 4, 4, 4)
        weld_lay.setSpacing(2)

        self._m10_results_widget = QWidget()
        m10r_lay = QVBoxLayout(self._m10_results_widget)
        m10r_lay.setContentsMargins(0, 0, 0, 0)
        m10r_lay.setSpacing(2)

        summary_lay.addWidget(_section_label("Design Summary"))
        self._m10_rr: dict[str, ResultRow] = {}
        for k, lbl in [
            ("m10_mpr",        "M_pr  (kN·m)"),
            ("m10_flange_f",   "Flange force  (kN)"),
            ("m10_overstr",    "Overstrength ratio"),
            ("m10_seismic",    "Seismic check"),
            ("m10_validity",   "Design status"),
        ]:
            rr = ResultRow(lbl); summary_lay.addWidget(rr); self._m10_rr[k] = rr

        bolts_lay.addWidget(_section_label("Bolts"))
        for k, lbl in [
            ("m10_n_bolts",    "Number of bolts"),
            ("m10_bolt_force", "Bolt force  (kN)"),
            ("m10_bolt_cap",   "Bolt capacity  (kN)"),
            ("m10_bolt_util",  "Bolt utilization"),
        ]:
            rr = ResultRow(lbl); bolts_lay.addWidget(rr); self._m10_rr[k] = rr

        bolts_lay.addWidget(_section_label("Flange Plate"))
        for k, lbl in [
            ("m10_pl_t",       "Plate thickness  (mm)"),
            ("m10_pl_w",       "Plate width  (mm)"),
            ("m10_pl_l",       "Plate length  (mm)"),
            ("m10_pl_yield",   "Yielding check"),
            ("m10_pl_rupt",    "Rupture check"),
            ("m10_pl_blk",     "Block shear"),
        ]:
            rr = ResultRow(lbl); bolts_lay.addWidget(rr); self._m10_rr[k] = rr

        weld_lay.addWidget(_section_label("Weld"))
        for k, lbl in [
            ("m10_weld_sz",    "Weld size  (mm)"),
            ("m10_weld_cap",   "Weld capacity  (kN)"),
            ("m10_weld_util",  "Weld utilization"),
        ]:
            rr = ResultRow(lbl); weld_lay.addWidget(rr); self._m10_rr[k] = rr

        summary_lay.addStretch()
        bolts_lay.addStretch()
        weld_lay.addStretch()

        result_tabs.addTab(summary_tab, "Summary")
        result_tabs.addTab(bolts_tab, "Bolts & Plate")
        result_tabs.addTab(weld_tab, "Weld")
        m10r_lay.addWidget(result_tabs)
        lay.addWidget(self._m10_results_widget)

        lay.addStretch()
        scroll.setWidget(inner)
        return scroll

    # ── init helpers ──────────────────────────────────────────────────────────

    def _fill_thickness(self):
        thicknesses = [str(t) for t in Plate.standard_thickness]
        for cb in [self.plate_thickness, self.web_plate_thickness,
                   self.beam_tf, self.beam_tw, self.column_tf, self.column_tw]:
            cb.addItems(thicknesses)

    def _wire_signals(self):
        # debounce: wait 250 ms after last change before rebuilding geometry
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(250)
        self._debounce.timeout.connect(self._do_calculate)

        def _mark_dirty():
            self._is_dirty = True
            self._update_title()

        for w in [self.beam_bf, self.beam_totaldepth,
                  self.column_bf, self.column_totaldepth,
                  self.plate_width, self.plate_length,
                  self.web_plate_length, self.web_plate_height]:
            w.valueChanged.connect(self._debounce.start)
            w.valueChanged.connect(lambda _=None: _mark_dirty())
        for w in [self.bolt_n, self.bolt_m, self.web_bolt_nz, self.web_bolt_nx]:
            w.valueChanged.connect(self._debounce.start)
            w.valueChanged.connect(lambda _=None: _mark_dirty())
        for w in [self.beam_tf, self.beam_tw, self.column_tf, self.column_tw,
                  self.plate_thickness, self.web_plate_thickness,
                  self.bolt_diameter, self.web_bolt_diameter]:
            w.currentIndexChanged.connect(self._debounce.start)
            w.currentIndexChanged.connect(lambda _=None: _mark_dirty())

        # Mabhas10 inputs
        for w in [self.m10_fy_beam, self.m10_fu_beam, self.m10_zx_beam,
                  self.m10_plate_fy, self.m10_plate_fu,
                  self.m10_edge_dist, self.m10_bolt_spacing, self.m10_bolt_ry]:
            w.valueChanged.connect(self._debounce.start)
            w.valueChanged.connect(lambda _=None: _mark_dirty())
        for w in [self.m10_bolt_type, self.m10_bolt_diam, self.m10_design_method]:
            w.currentIndexChanged.connect(self._debounce.start)
            w.currentIndexChanged.connect(lambda _=None: _mark_dirty())

        self.design_code_combo.currentIndexChanged.connect(self._debounce.start)
        self.design_code_combo.currentIndexChanged.connect(lambda _=None: _mark_dirty())
        self.design_code_combo.currentIndexChanged.connect(self._on_code_changed)
        self.design_code_combo.currentIndexChanged.connect(lambda _=None: self._save_app_settings())
        self.view_perspective_switch.toggled.connect(lambda _=None: self._save_app_settings())
        self.view_style_combo.currentIndexChanged.connect(lambda _=None: self._save_app_settings())
        self.view_shadows_switch.toggled.connect(lambda _=None: self._save_app_settings())
        self.switch.toggled.connect(lambda _=None: self._save_app_settings())
        self.switch.toggled.connect(self.change_theme)

    def calculate_connection(self):
        """Public entry point — starts debounce timer (or fires immediately)."""
        self._debounce.start()

    def _on_code_changed(self):
        """Keep the unified UI visible for both supported design codes."""
        self._mabhas10_group.setVisible(True)
        self._m10_results_widget.setVisible(True)

    # ── settings ──────────────────────────────────────────────────────────────

    def closeEvent(self, event):
        if self._is_dirty:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes.\nSave before closing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            )
            if reply == QMessageBox.Save:
                if not self._save_model():     # returns False if user cancelled
                    event.ignore()
                    return
            elif reply == QMessageBox.Cancel:
                event.ignore()
                return
        self._save_app_settings()
        super().closeEvent(event)

    def _load_settings(self):
        qs = self._settings()
        geom = qs.value("geometry")
        if geom: self.restoreGeometry(geom)
        state = qs.value("state")
        if state: self.restoreState(state)
        self._last_dir = qs.value("last_dir", self._documents_dir(), type=str) or self._documents_dir()
        self._saved_design_code = qs.value("design_code", DesignCode.MABHAS10.value, type=str) or DesignCode.MABHAS10.value
        self._saved_projection_perspective = qs.value("projection_perspective", False, type=bool)
        self._saved_display_style = qs.value("display_style", "shaded", type=str) or "shaded"
        self._saved_shadows_enabled = qs.value("shadows_enabled", False, type=bool)
        self._saved_dark_theme = qs.value("dark_theme", False, type=bool)
        # NOTE: Preferences are applied later in _finish_startup() after all widgets are ready
        last_file = qs.value("last_file", "", type=str) or ""
        if last_file and Path(last_file).is_file():
            self._startup_last_file = last_file

    def _open_settings_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Settings")
        lay = QVBoxLayout(dlg)

        tabs = QTabWidget(dlg)

        design_tab = QWidget(dlg)
        design_form = QFormLayout(design_tab)
        code_combo = QComboBox(dlg)
        for i in range(self.design_code_combo.count()):
            code_combo.addItem(self.design_code_combo.itemText(i), self.design_code_combo.itemData(i))
        code_combo.setCurrentIndex(self.design_code_combo.currentIndex())

        design_form.addRow("Design code:", code_combo)

        display_tab = QWidget(dlg)
        display_form = QFormLayout(display_tab)

        perspective_switch = Switch(thumb_radius=8, track_radius=6)
        perspective_switch.setChecked(self._projection_is_perspective())

        style_combo = QComboBox(dlg)
        for i in range(self.view_style_combo.count()):
            style_combo.addItem(self.view_style_combo.itemText(i), self.view_style_combo.itemData(i))
        style_combo.setCurrentIndex(self.view_style_combo.currentIndex())

        shadows_switch = Switch(thumb_radius=8, track_radius=6)
        shadows_switch.setChecked(self._shadows_enabled())

        theme_switch = Switch(thumb_radius=8, track_radius=6)
        theme_switch.setChecked(self._theme_is_dark())

        display_form.addRow("Perspective:", perspective_switch)
        display_form.addRow("Display mode:", style_combo)
        display_form.addRow("Shadows:", shadows_switch)
        display_form.addRow("Dark theme:", theme_switch)

        tabs.addTab(design_tab, "Design Code")
        tabs.addTab(display_tab, "Display")

        lay.addWidget(tabs)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=dlg)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        lay.addWidget(buttons)

        if dlg.exec() != QDialog.Accepted:
            return

        self.design_code_combo.setCurrentIndex(code_combo.currentIndex())
        self._apply_theme_toggle(theme_switch.isChecked())
        self._apply_projection_toggle(perspective_switch.isChecked())
        self._apply_display_style(style_combo.currentData() or "shaded")
        self._apply_shadows_toggle(shadows_switch.isChecked())
        self._save_app_settings()
        self.calculate_connection()

    # ── file model actions ────────────────────────────────────────────
    def _update_title(self):
        name = Path(self._current_path).name if self._current_path else "Untitled"
        dirty = " ●" if self._is_dirty else ""
        lc = getattr(self, "_last_connection", None)
        if isinstance(lc, str) and lc in ("MABHAS10", "BFP_DESIGN"):
            code = self.design_code_combo.currentText()
        else:
            code = getattr(lc, "design_code", "") if lc else ""
        code_str = f"  [{code}]" if code else ""
        self.setWindowTitle(f"Steel Connection Designer — {name}{dirty}{code_str}")

    def _ask_save_if_dirty(self) -> bool:
        """Return True if it's safe to proceed (saved or discarded)."""
        if not self._is_dirty:
            return True
        reply = QMessageBox.question(
            self, "Unsaved Changes",
            "You have unsaved changes. Save now?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
        )
        if reply == QMessageBox.Save:
            return self._save_model()
        return reply == QMessageBox.Discard

    def _new_model(self):
        if not self._ask_save_if_dirty():
            return
        self._current_path = None
        self._is_dirty = False
        self._save_app_settings()
        self._update_title()

    def _open_model_path(self, path: str, mark_log: bool = True) -> None:
        load_model(self, path)
        self._current_path = path
        self._last_dir = str(Path(path).parent)
        self._is_dirty = False
        self._update_title()
        self.calculate_connection()
        self._save_app_settings()
        if mark_log:
            self.log_info(f"Opened: {path}")

    def _open_model(self):
        if not self._ask_save_if_dirty():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Model", self._default_dialog_dir(), FILE_FILTER)
        if not path:
            return
        try:
            self._open_model_path(path)
        except Exception as e:
            QMessageBox.critical(self, "Open Error", str(e))

    def _save_model(self) -> bool:
        """Save to current path; if none, fall through to Save As. Returns True on success."""
        if self._current_path:
            try:
                save_model(self, self._current_path)
                self._last_dir = str(Path(self._current_path).parent)
                self._is_dirty = False
                self._update_title()
                self._save_app_settings()
                self.log_info(f"Saved: {self._current_path}")
                return True
            except Exception as e:
                QMessageBox.critical(self, "Save Error", str(e))
                return False
        return self._save_model_as()

    def _save_model_as(self) -> bool:
        default = (Path(self._current_path).stem if self._current_path else "connection") + FILE_EXT
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Model As", str(Path(self._default_dialog_dir()) / default), FILE_FILTER)
        if not path:
            return False
        try:
            out = save_model(self, path)
            self._current_path = str(out)
            self._last_dir = str(Path(out).parent)
            self._is_dirty = False
            self._update_title()
            self._save_app_settings()
            self.log_info(f"Saved: {out}")
            return True
        except Exception as e:
            QMessageBox.critical(self, "Save Error", str(e))
            return False

    # ── calculation ───────────────────────────────────────────────────────────

    def _do_calculate(self):
        self._last_connection = None  # reset before each run
        self._do_calculate_mabhas10()

    def _do_calculate_mabhas10(self):
        """Run Mabhas10 BFP connection design and update UI."""
        try:
            selected_code: DesignCode = self.design_code_combo.currentData()
            # Read beam geometry from shared inputs
            fy = self.m10_fy_beam.value()
            fu = self.m10_fu_beam.value()
            zx_cm3 = self.m10_zx_beam.value()
            zx_mm3 = zx_cm3 * 1000.0  # cm³ → mm³
            beam_depth_mm = self.beam_totaldepth.value() * 10.0   # cm → mm
            flange_w_mm = self.beam_bf.value() * 10.0             # cm → mm
            flange_t_mm = float(self.beam_tf.currentText()) * 10.0  # cm → mm

            bolt_type = BoltType(self.m10_bolt_type.currentText())
            bolt_diam = float(self.m10_bolt_diam.currentText())
            dm = DesignMethod(self.m10_design_method.currentText())
            ry = self.m10_bolt_ry.value()
            plate_fy = self.m10_plate_fy.value()
            plate_fu = self.m10_plate_fu.value()
            edge_d = self.m10_edge_dist.value()
            bolt_sp = self.m10_bolt_spacing.value()

            result = design_bfp_connection(
                fy_beam_mpa=fy,
                fu_beam_mpa=fu,
                zx_beam_mm3=zx_mm3,
                beam_depth_mm=beam_depth_mm,
                beam_flange_width_mm=flange_w_mm,
                beam_flange_thickness_mm=flange_t_mm,
                bolt_type=bolt_type,
                bolt_diameter_mm=bolt_diam,
                bolt_grade_ry=ry,
                plate_fy_mpa=plate_fy,
                plate_fu_mpa=plate_fu,
                edge_distance_mm=edge_d,
                bolt_spacing_mm=bolt_sp,
                design_method=dm,
                connection_type=ConnectionType.BOTH_FLANGES,
            )

            self.results.clear()
            selected_code_name = self.design_code_combo.currentText()
            self.log_info(f"Design code: <b>{selected_code_name}</b>", color="#aaa")

            if result.is_valid:
                self.log_success(f"BFP design passed for {selected_code_name}.")
            else:
                self.log_warning(f"BFP design for {selected_code_name} needs review.")

            for chk in result.seismic_checks:
                color = "#4caf50" if "✓" in chk else ("orange" if "⚠" in chk else "#aaa")
                self.log_info(chk, color=color)

            self._last_m10_result = result
            self._last_connection = None
            self._update_m10_right_panel(result)
            self._update_title()

            # Build 3D shapes using standard BFP connection for geometry
            try:
                beam = SteelSection.from_section_dict({
                    'sec_type': 'WB',
                    'b': self.beam_bf.value(), 'd': self.beam_totaldepth.value(),
                    't_w': float(self.beam_tw.currentText()),
                    't_f': float(self.beam_tf.currentText()),
                    't':   float(self.beam_tf.currentText()),
                    'f_y': fy * 0.102,  # MPa → kgf/cm² approx
                    'f_yw': fy * 0.102,
                    'f_u': fu * 0.102,
                })
                col = SteelSection.from_section_dict({
                    'sec_type': 'WC',
                    'b': self.column_bf.value(), 'd': self.column_totaldepth.value(),
                    't_w': float(self.column_tw.currentText()),
                    't_f': float(self.column_tf.currentText()),
                    't':   float(self.column_tf.currentText()),
                    'f_y': fy * 0.102, 'f_yw': fy * 0.102, 'f_u': fu * 0.102,
                })
                bolt_3d = Bolt(d_f=float(self.bolt_diameter.currentText()))
                bolt_group_3d = BoltGroup2D(
                    n_p=int(self.bolt_n.value()), n_g=int(self.bolt_m.value()),
                    bolt=bolt_3d, s_p=8.4, s_g=5)
                plate_3d = Plate(b_i=self.plate_width.value(),
                                 h_i=self.plate_length.value(),
                                 t_i=float(self.plate_thickness.currentText()))
                web_bolt_3d = Bolt(d_f=float(self.web_bolt_diameter.currentText()))
                web_bolt_group_3d = BoltGroup2D(
                    n_p=int(self.web_bolt_nz.value()), n_g=int(self.web_bolt_nx.value()),
                    bolt=web_bolt_3d, s_p=8.4, s_g=5)
                web_plate_3d = Plate(
                    b_i=self.web_plate_height.value(),
                    h_i=self.web_plate_length.value(),
                    t_i=float(self.web_plate_thickness.currentText())
                )
                connection_cls = AISC358BFPConnection if selected_code == DesignCode.AISC else BFPConnection
                conn_3d = connection_cls(
                    beam=beam,
                    column=col,
                    plate=plate_3d,
                    bolt_group=bolt_group_3d,
                    bolt_group_web=web_bolt_group_3d,
                    web_plate=web_plate_3d,
                    s1=7,
                    beam_length=755,
                )
                self._last_connection = conn_3d
                self._update_title()
                shapes, cad_warnings, adjustments = build_bfp_shapes(
                    conn_3d,
                    wp_length    = self.web_plate_length.value(),
                    wp_height    = self.web_plate_height.value(),
                    wp_thickness = float(self.web_plate_thickness.currentText()),
                    wb_diam      = float(self.web_bolt_diameter.currentText()),
                    wb_nz        = int(self.web_bolt_nz.value()),
                    wb_nx        = int(self.web_bolt_nx.value()),
                )
                for w in cad_warnings:
                    self.log_info(f"⚠ {w}", color="orange")
                self._sync_inputs(adjustments)
                self._viewer.display_shapes(shapes.all_shapes())
            except Exception as e3d:
                self.log_info(f"3D: {e3d}", color="orange")

        except Exception as e:
            import traceback
            QMessageBox.critical(self, "خطا در محاسبات مبحث دهم",
                                 f"{e}\n\n{traceback.format_exc()}")

    def _update_m10_right_panel(self, result) -> None:
        """Fill Mabhas10 result rows from BFPConnectionDesign dataclass."""
        def _f(v): return f"{v:.2f}"

        self._m10_rr["m10_mpr"].set_value(_f(result.m_pr_nmm / 1e6))
        self._m10_rr["m10_flange_f"].set_value(_f(result.flange_force_n / 1000.0))
        self._m10_rr["m10_overstr"].set_value(_f(result.overstrength_ratio),
                                               ok=result.overstrength_ratio >= 1.0)
        b = result.top_bolts
        if b:
            self._m10_rr["m10_n_bolts"].set_value(str(b.num_bolts))
            self._m10_rr["m10_bolt_force"].set_value(_f(b.bolt_force_n / 1000.0))
            self._m10_rr["m10_bolt_cap"].set_value(_f(b.bolt_capacity_n / 1000.0))
            self._m10_rr["m10_bolt_util"].set_value(_f(b.utilization_ratio),
                                                     ok=b.is_adequate)
        p = result.top_plate
        if p:
            self._m10_rr["m10_pl_t"].set_value(_f(p.plate_thickness_mm))
            self._m10_rr["m10_pl_w"].set_value(_f(p.plate_width_mm))
            self._m10_rr["m10_pl_l"].set_value(_f(p.plate_length_mm))
            self._m10_rr["m10_pl_yield"].set_value(_f(p.yield_check_ratio),
                                                    ok=p.yield_check_ratio <= 1.0)
            self._m10_rr["m10_pl_rupt"].set_value(_f(p.rupture_check_ratio),
                                                   ok=p.rupture_check_ratio <= 1.0)
            self._m10_rr["m10_pl_blk"].set_value(_f(p.block_shear_ratio),
                                                  ok=p.block_shear_ratio <= 1.0)
        w = result.top_weld
        if w:
            self._m10_rr["m10_weld_sz"].set_value(_f(w.weld_size_mm))
            self._m10_rr["m10_weld_cap"].set_value(_f(w.capacity_n / 1000.0))
            self._m10_rr["m10_weld_util"].set_value(_f(w.utilization_ratio),
                                                     ok=w.is_adequate)
        self._m10_rr["m10_seismic"].set_value(
            "✓  OK" if result.seismic_check_passed else "✗  FAIL",
            ok=result.seismic_check_passed)
        self._m10_rr["m10_validity"].set_value(
            "✓  معتبر" if result.is_valid else "✗  نیاز به بازنگری",
            ok=result.is_valid)

    def _update_right_panel(self, conn, errors):
        import math
        err_keys = {e.value for e in errors}

        def _fmt(v):
            try: return f"{v:.2f}" if not math.isnan(v) else "—"
            except: return str(v)

        self._rr["m_pr"].set_value(_fmt(conn.m_pr))
        self._rr["sh"].set_value(_fmt(conn.sh))
        self._rr["lh"].set_value(_fmt(conn.lh))
        self._rr["kl"].set_value(_fmt(conn.kl))
        self._rr["s3"].set_value(_fmt(conn.s3))
        self._rr["s5"].set_value(_fmt(conn.s5))
        self._rr["bolt_name"].set_value(conn.bolt.name if conn.bolt else "—")
        self._rr["n_bolts"].set_value(str(conn.bolt_group.n_b) if conn.bolt_group else "—")
        try:
            self._rr["rn_min"].set_value(_fmt(conn.nominal_shear_force_of_bolt()))
        except: self._rr["rn_min"].set_value("—")

        # Build error-value lookup depending on which code was used
        if isinstance(conn, AISC358BFPConnection):
            E = AISC358BFPERROR
            check_map = {
                "beam_weight":  E.beam_weight.value,
                "beam_depth":   E.beam_depth.value,
                "bolt_grade":   E.minimum_bolt_grade.value,
                "bolt_diam":    E.max_bolt_diameter.value,
                "plate_buckle": E.plate_buckling.value,
                "sh_check":     E.max_sh.value,
                "s3_check":     E.minimum_s3.value,
                "s5_check":     E.minimum_s5.value,
            }
        else:
            E = BFPCONNECTIONERROR
            check_map = {
                "beam_weight":  E.beam_weight.value,
                "beam_depth":   E.beam_depth.value,
                "bolt_grade":   E.minimum_grade_of_bolt.value,
                "bolt_diam":    E.max_bolt_diameter.value,
                "plate_buckle": E.check_max_buckling_factor_of_plate.value,
                "sh_check":     E.max_sh.value,
                "s3_check":     E.minimum_s3.value,
                "s5_check":     E.minimum_s5.value,
            }
        for row_key, ev in check_map.items():
            failed = ev in err_keys
            self._check_rows[row_key].set_value(
                "✗  FAIL" if failed else "✓  OK", ok=not failed)

    def _export_report(self):
        if not getattr(self, '_last_connection', None):
            QMessageBox.warning(self, "No Connection",
                                "Run the calculation first before exporting a report.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Report", "BFP_Connection_Report.docx",
            "Word Document (*.docx)")
        if not path:
            return
        try:
            import os

            lang = "fa" if self.report_lang.currentText() == "فارسی" else "en"

            import tempfile
            from steel_connections.report.bfp_report import generate_report

            tmp_dir = tempfile.mkdtemp(prefix="bfp_report_views_")
            view_images: dict = {}
            try:
                view_images = self._viewer.capture_views(tmp_dir)
            except Exception:
                pass

            out = generate_report(
                self._last_connection,
                project_info={
                    "date": str(__import__('datetime').date.today()),
                    "standard": self.design_code_combo.currentText(),
                },
                output_path=path,
                view_images=view_images,
            )
            reply = QMessageBox.question(
                self, "Report Saved",
                f"Report saved to:\n{out}\n\nOpen the file now?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                os.startfile(str(out))
        except Exception as e:
            import traceback
            QMessageBox.critical(self, "Report Error",
                                 f"{e}\n\n{traceback.format_exc()}")

    def _export_dxf(self):
        if not getattr(self, '_last_connection', None):
            QMessageBox.warning(self, "No Connection",
                                "Run the calculation first before exporting a DXF drawing.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save DXF Drawing", "BFP_Connection_Drawing.dxf",
            "DXF Drawing (*.dxf)")
        if not path:
            return
        try:
            import os
            from steel_connections.report.bfp_autocad import generate_autocad_drawing

            out = generate_autocad_drawing(self._last_connection, output_path=path)
            reply = QMessageBox.question(
                self, "DXF Saved",
                f"DXF drawing saved to:\n{out}\n\nOpen the file now?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                os.startfile(str(out))
        except Exception as e:
            import traceback
            QMessageBox.critical(self, "DXF Export Error",
                                 f"{e}\n\n{traceback.format_exc()}")

    def _sync_inputs(self, adjustments: dict) -> None:
        """Silently update left-panel inputs to match any geometry auto-adjustments.
        Signals are blocked to prevent a re-calculation loop."""
        mapping = {
            "plate_length":     (self.plate_length,       "setValue"),
            "bolt_m":           (self.bolt_m,             "setValue"),
            "web_plate_length": (self.web_plate_length,   "setValue"),
            "web_bolt_nx":      (self.web_bolt_nx,        "setValue"),
            "web_plate_height": (self.web_plate_height,   "setValue"),
        }
        for key, (widget, method) in mapping.items():
            if key in adjustments:
                widget.blockSignals(True)
                getattr(widget, method)(adjustments[key])
                widget.blockSignals(False)

    # ── logging ───────────────────────────────────────────────────────────────

    def log_success(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.results.append(f"[{ts}] <span style='color:green;font-weight:bold;'>✓ OK:</span> {msg}")

    def log_error(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.results.append(f"[{ts}] <span style='color:red;font-weight:bold;'>✗ ERROR:</span> {msg}")

    def log_warning(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.results.append(f"[{ts}] <span style='color:orange;font-weight:bold;'>⚠ WARNING:</span> {msg}")

    def log_info(self, msg, color="#aaa"):
        ts = datetime.now().strftime("%H:%M:%S")
        self.results.append(f"[{ts}] <span style='color:{color};font-weight:bold;'>ℹ INFO:</span> {msg}")

    def change_theme(self):
        toggle_stylesheet(self.switch.isChecked())


# ── module-level helpers ──────────────────────────────────────────────────────

def toggle_stylesheet(dark: bool):
    app = QApplication.instance()
    if app is None: return
    path = 'darkstyle.qss' if dark else 'light.qss'
    theme_path = str(files("steel_connections.data.themes").joinpath(path))
    f = QFile(theme_path)
    f.open(QFile.ReadOnly | QFile.Text)
    app.setStyleSheet(QTextStream(f).readAll())


def main():
    app = QApplication(sys.argv)
    toggle_stylesheet(False)
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()

