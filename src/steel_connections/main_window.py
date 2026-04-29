# -*- coding: utf-8 -*-

import sys
from datetime import datetime
from pathlib import Path
from importlib.resources import files

from PyQt5.QtCore import QSettings, QFile, QTextStream, Qt, QTimer
from PyQt5.QtWidgets import (
    QApplication, QMessageBox, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QFormLayout,
    QSplitter, QScrollArea, QGroupBox,
    QLabel, QPushButton, QTextBrowser,
    QDoubleSpinBox, QSpinBox, QComboBox,
    QSizePolicy, QFrame,
)
from PyQt5 import QtWidgets

from steel_connections.gui.toggle_button import Switch
from steel_connections.gui.viewer_3d import Viewer3D
from steel_connections.cad.bfp_cad import build_bfp_shapes

from steel_connections.bfp_connection import BFPConnection
from steel_connections.member.member import SteelSection
from steel_connections.component.bolt import Bolt, BoltGroup2D
from steel_connections.component.plate import Plate


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
        self._build_ui()
        self._fill_thickness()
        self._wire_signals()
        self._load_settings()
        # populate 3D view on startup (shapes will be queued until OCC is ready)
        QTimer.singleShot(0, self.calculate_connection)

    # ── layout ───────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QSplitter(Qt.Horizontal, self)
        root.setHandleWidth(5)
        self.setCentralWidget(root)
        root.addWidget(self._build_left_panel())
        root.addWidget(self._build_centre_panel())
        root.addWidget(self._build_right_panel())
        root.setSizes([270, 880, 290])
        root.setStretchFactor(0, 0)
        root.setStretchFactor(1, 1)
        root.setStretchFactor(2, 0)

    # ── left: inputs ─────────────────────────────────────────────────────────

    def _build_left_panel(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setMinimumWidth(230); scroll.setMaximumWidth(310)

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

        # Beam
        lay.addWidget(_section_label("Beam"))
        bb = QGroupBox(); bf = QFormLayout(bb); bf.setContentsMargins(6,4,6,4)
        self.beam_bf          = QDoubleSpinBox(); _setup_spin(self.beam_bf, 5, 100, 20, " cm")
        self.beam_totaldepth  = QDoubleSpinBox(); _setup_spin(self.beam_totaldepth, 5, 150, 30, " cm")
        self.beam_tf = QComboBox(); self.beam_tw = QComboBox()
        bf.addRow("Bf:", self.beam_bf); bf.addRow("D:", self.beam_totaldepth)
        bf.addRow("Tf:", self.beam_tf); bf.addRow("Tw:", self.beam_tw)
        lay.addWidget(bb)

        # Column
        lay.addWidget(_section_label("Column"))
        cb = QGroupBox(); cf = QFormLayout(cb); cf.setContentsMargins(6,4,6,4)
        self.column_bf         = QDoubleSpinBox(); _setup_spin(self.column_bf, 5, 100, 20, " cm")
        self.column_totaldepth = QDoubleSpinBox(); _setup_spin(self.column_totaldepth, 5, 150, 30, " cm")
        self.column_tf = QComboBox(); self.column_tw = QComboBox()
        cf.addRow("Bf:", self.column_bf); cf.addRow("D:", self.column_totaldepth)
        cf.addRow("Tf:", self.column_tf); cf.addRow("Tw:", self.column_tw)
        lay.addWidget(cb)

        # Plate
        lay.addWidget(_section_label("Flange Plate"))
        pb = QGroupBox(); pf = QFormLayout(pb); pf.setContentsMargins(6,4,6,4)
        self.plate_width     = QDoubleSpinBox(); _setup_spin(self.plate_width, 5, 60, 15, " cm")
        self.plate_length    = QDoubleSpinBox(); _setup_spin(self.plate_length, 5, 100, 30, " cm")
        self.plate_thickness = QComboBox()
        pf.addRow("Width:", self.plate_width); pf.addRow("Length:", self.plate_length)
        pf.addRow("Thickness:", self.plate_thickness)
        lay.addWidget(pb)

        # Web Plate
        lay.addWidget(_section_label("Web Plate"))
        wpb = QGroupBox(); wpf = QFormLayout(wpb); wpf.setContentsMargins(6,4,6,4)
        self.web_plate_length    = QDoubleSpinBox(); _setup_spin(self.web_plate_length, 1, 100, 25, " cm")
        self.web_plate_height    = QDoubleSpinBox(); _setup_spin(self.web_plate_height, 1, 100, 20, " cm")
        self.web_plate_thickness = QComboBox()
        wpf.addRow("Length:",    self.web_plate_length)
        wpf.addRow("Height:",    self.web_plate_height)
        wpf.addRow("Thickness:", self.web_plate_thickness)
        lay.addWidget(wpb)

        # Flange Bolts
        lay.addWidget(_section_label("Flange Bolts"))
        ltb = QGroupBox(); lf = QFormLayout(ltb); lf.setContentsMargins(6,4,6,4)
        self.bolt_diameter = QComboBox(); self.bolt_diameter.addItems(["2.4", "2.7", "3.0"])
        self.bolt_n = QSpinBox(); self.bolt_n.setMinimum(1); self.bolt_n.setSingleStep(2); self.bolt_n.setValue(2)
        self.bolt_m = QSpinBox(); self.bolt_m.setMinimum(1); self.bolt_m.setValue(5)
        lf.addRow("Diameter:",      self.bolt_diameter)
        lf.addRow("N (rows/Z):",    self.bolt_n)
        lf.addRow("M (gauge/X):",   self.bolt_m)
        lay.addWidget(ltb)

        # Web Bolts
        lay.addWidget(_section_label("Web Bolts"))
        wltb = QGroupBox(); wlf = QFormLayout(wltb); wlf.setContentsMargins(6,4,6,4)
        self.web_bolt_diameter = QComboBox(); self.web_bolt_diameter.addItems(["2.0", "2.4", "2.7"])
        self.web_bolt_nz = QSpinBox(); self.web_bolt_nz.setMinimum(1); self.web_bolt_nz.setValue(3)
        self.web_bolt_nx = QSpinBox(); self.web_bolt_nx.setMinimum(1); self.web_bolt_nx.setValue(2)
        wlf.addRow("Diameter:",   self.web_bolt_diameter)
        wlf.addRow("Rows (Z):",   self.web_bolt_nz)
        wlf.addRow("Cols (X):",   self.web_bolt_nx)
        lay.addWidget(wltb)

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
        for lbl, slot in [
            ("Shaded",    lambda: self._viewer.set_display_mode(1)),
            ("Wireframe", lambda: self._viewer.set_display_mode(0)),
        ]:
            btn = QPushButton(lbl); btn.setFixedHeight(22)
            btn.clicked.connect(slot); bar.addWidget(btn)
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
        lay = QVBoxLayout(inner); lay.setContentsMargins(8,8,8,8); lay.setSpacing(2)

        self._rr: dict[str, ResultRow] = {}

        lay.addWidget(_section_label("Connection Values"))
        for k, lbl in [
            ("m_pr", "M_pr  (t·cm)"),
            ("sh",   "sh  (cm)"),
            ("lh",   "lh  (cm)"),
            ("kl",   "kl  (cm)"),
            ("s3",   "s3  (cm)"),
            ("s5",   "s5  (cm)"),
        ]:
            rr = ResultRow(lbl); lay.addWidget(rr); self._rr[k] = rr

        lay.addWidget(_hr())
        lay.addWidget(_section_label("Bolt Group"))
        for k, lbl in [
            ("bolt_name", "Bolt"),
            ("n_bolts",   "Total bolts"),
            ("rn_min",    "φRn  (t)"),
        ]:
            rr = ResultRow(lbl); lay.addWidget(rr); self._rr[k] = rr

        lay.addWidget(_hr())
        lay.addWidget(_section_label("Design Checks"))
        self._check_rows: dict[str, ResultRow] = {}
        for k, lbl in [
            ("beam_weight",  "Beam weight"),
            ("beam_depth",   "Beam depth"),
            ("bolt_grade",   "Bolt grade"),
            ("bolt_diam",    "Max bolt diam"),
            ("plate_buckle", "Plate buckling"),
            ("sh_check",     "sh ≤ d (beam)"),
            ("s3_check",     "Min s3"),
            ("s5_check",     "Min s5"),
        ]:
            rr = ResultRow(lbl); lay.addWidget(rr); self._check_rows[k] = rr

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

        for w in [self.beam_bf, self.beam_totaldepth,
                  self.column_bf, self.column_totaldepth,
                  self.plate_width, self.plate_length,
                  self.web_plate_length, self.web_plate_height]:
            w.valueChanged.connect(self._debounce.start)
        for w in [self.bolt_n, self.bolt_m, self.web_bolt_nz, self.web_bolt_nx]:
            w.valueChanged.connect(self._debounce.start)
        for w in [self.beam_tf, self.beam_tw, self.column_tf, self.column_tw,
                  self.plate_thickness, self.web_plate_thickness,
                  self.bolt_diameter, self.web_bolt_diameter]:
            w.currentIndexChanged.connect(self._debounce.start)
        self.switch.toggled.connect(self.change_theme)

    def calculate_connection(self):
        """Public entry point — starts debounce timer (or fires immediately)."""
        self._debounce.start()

    # ── settings ──────────────────────────────────────────────────────────────

    def closeEvent(self, event):
        qs = QSettings("steel_connection", "main_window_v2")
        qs.setValue("geometry", self.saveGeometry())
        qs.setValue("state", self.saveState())
        super().closeEvent(event)

    def _load_settings(self):
        qs = QSettings("steel_connection", "main_window_v2")
        geom = qs.value("geometry")
        if geom: self.restoreGeometry(geom)
        state = qs.value("state")
        if state: self.restoreState(state)

    # ── calculation ───────────────────────────────────────────────────────────

    def _do_calculate(self):
        try:
            beam = SteelSection.from_section_dict({
                'sec_type': 'WB',
                'b': self.beam_bf.value(), 'd': self.beam_totaldepth.value(),
                't_w': float(self.beam_tw.currentText()),
                't_f': float(self.beam_tf.currentText()),
                't':   float(self.beam_tf.currentText()),
                'f_y': 2400, 'f_yw': 2400, 'f_u': 3700,
            })
            col = SteelSection.from_section_dict({
                'sec_type': 'WC',
                'b': self.column_bf.value(), 'd': self.column_totaldepth.value(),
                't_w': float(self.column_tw.currentText()),
                't_f': float(self.column_tf.currentText()),
                't':   float(self.column_tf.currentText()),
                'f_y': 2400, 'f_yw': 2400, 'f_u': 3700,
            })
            bolt       = Bolt(d_f=float(self.bolt_diameter.currentText()))
            bolt_group = BoltGroup2D(n_p=int(self.bolt_n.value()),
                                     n_g=int(self.bolt_m.value()),
                                     bolt=bolt, s_p=8.4, s_g=5)
            plate = Plate(b_i=self.plate_width.value(),
                          h_i=self.plate_length.value(),
                          t_i=float(self.plate_thickness.currentText()))
            connection = BFPConnection(beam=beam, column=col,
                                       plate=plate, bolt_group=bolt_group,
                                       s1=7, beam_length=755)

            errors = connection.check_connection()
            self.results.clear()
            if not errors:
                self.log_success("Connection is adequate.")
            else:
                for err in errors:
                    self.log_warning(f"- {err.description}")

            self._update_right_panel(connection, errors)

            try:
                shapes, cad_warnings, adjustments = build_bfp_shapes(
                    connection,
                    wp_length    = self.web_plate_length.value(),
                    wp_height    = self.web_plate_height.value(),
                    wp_thickness = float(self.web_plate_thickness.currentText()),
                    wb_diam      = float(self.web_bolt_diameter.currentText()),
                    wb_nz        = int(self.web_bolt_nz.value()),
                    wb_nx        = int(self.web_bolt_nx.value()),
                )
                for w in cad_warnings:
                    self.log_info(f"⚠ {w}", color="orange")
                # Sync adjusted values back to left-panel inputs without re-triggering
                self._sync_inputs(adjustments)
                self._viewer.display_shapes(shapes.all_shapes())
            except Exception as e3d:
                self.log_info(f"3D error: {e3d}", color="red")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Calculation error:\n{e}")

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

        from steel_connections.bfp_connection import BFPCONNECTIONERROR as ERR
        check_map = {
            "beam_weight":  ERR.beam_weight.value,
            "beam_depth":   ERR.beam_depth.value,
            "bolt_grade":   ERR.minimum_grade_of_bolt.value,
            "bolt_diam":    ERR.max_bolt_diameter.value,
            "plate_buckle": ERR.check_max_buckling_factor_of_plate.value,
            "sh_check":     ERR.max_sh.value,
            "s3_check":     ERR.minimum_s3.value,
            "s5_check":     ERR.minimum_s5.value,
        }
        for row_key, ev in check_map.items():
            failed = ev in err_keys
            self._check_rows[row_key].set_value(
                "✗  FAIL" if failed else "✓  OK", ok=not failed)

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
    window = MainWindow()
    window.show()
    app.exec_()


if __name__ == "__main__":
    main()

