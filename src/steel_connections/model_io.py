# -*- coding: utf-8 -*-
"""
model_io.py — JSON serialisation / deserialisation for BFP connection models.

Schema (version 1):
{
  "version": 1,
  "design_code": "AISC 358-16" | "Iranian Code ...",
  "beam":   { "b", "d", "t_f", "t_w", "f_y", "f_u" },
  "column": { "b", "d", "t_f", "t_w", "f_y", "f_u" },
  "plate":  { "b_i", "h_i", "t_i" },
  "bolt_group":  { "d_f", "n_p", "n_g", "s_p", "s_g" },
  "web_plate":   { "h_i", "b_i", "t_i" },            # optional
  "web_bolt":    { "d_f", "n_p", "n_g", "s_p", "s_g" }, # optional
  "s1":          float,
  "beam_length": float
}
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


MODEL_VERSION = 2
FILE_EXT      = ".scj"          # Steel Connection JSON
FILE_FILTER   = "Steel Connection (*.scj);;JSON (*.json);;All files (*)"


# ── save ─────────────────────────────────────────────────────────────────────

def model_to_dict(mw) -> dict[str, Any]:
    """
    Extract every UI input from a MainWindow instance into a plain dict.
    `mw` is the MainWindow object.
    """
    code = mw.design_code_combo.currentData()
    dc_val = code.value if hasattr(code, "value") else str(code)

    data: dict[str, Any] = {
        "version":     MODEL_VERSION,
        "design_code": dc_val,
        "connection_type": (
            mw.connection_type_combo.currentData().value
            if hasattr(mw.connection_type_combo.currentData(), "value")
            else str(mw.connection_type_combo.currentData())
        ),
        "beam": {
            "b":   mw.beam_bf.value(),
            "d":   mw.beam_totaldepth.value(),
            "t_f": float(mw.beam_tf.currentText()),
            "t_w": float(mw.beam_tw.currentText()),
        },
        "column": {
            "b":   mw.column_bf.value(),
            "d":   mw.column_totaldepth.value(),
            "t_f": float(mw.column_tf.currentText()),
            "t_w": float(mw.column_tw.currentText()),
        },
        "plate": {
            "b_i": mw.plate_width.value(),
            "h_i": mw.plate_length.value(),
            "t_i": float(mw.plate_thickness.currentText()),
        },
        "bolt_group": {
            "d_f": float(mw.bolt_diameter.currentText()),
            "n_p": mw.bolt_n.value(),
            "n_g": mw.bolt_m.value(),
        },
        "web_plate": {
            "h_i": mw.web_plate_length.value(),
            "b_i": mw.web_plate_height.value(),
            "t_i": float(mw.web_plate_thickness.currentText()),
        },
        "web_bolt": {
            "d_f": float(mw.web_bolt_diameter.currentText()),
            "n_p": mw.web_bolt_nz.value(),
            "n_g": mw.web_bolt_nx.value(),
        },
        "wufw": {
            "mu": mw.wufw_mu.value(),
            "vu": mw.wufw_vu.value(),
            "pu": mw.wufw_pu.value(),
            "shear_plate_height": mw.wufw_shear_plate_height.value(),
            "shear_plate_width": mw.wufw_shear_plate_width.value(),
            "shear_plate_thickness": mw.wufw_shear_plate_thickness.value(),
            "web_fillet_weld": mw.wufw_web_fillet_weld.value(),
        },
    }
    return data


def save_model(mw, path: str | Path) -> Path:
    """Save current model to *path* (creates parent dirs)."""
    path = Path(path)
    if path.suffix not in (".scj", ".json"):
        path = path.with_suffix(FILE_EXT)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = model_to_dict(mw)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


# ── load ─────────────────────────────────────────────────────────────────────

def load_model(mw, path: str | Path) -> None:
    """
    Read a JSON file and populate every UI input on MainWindow.
    Raises ValueError for unsupported schema versions.
    """
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))

    ver = data.get("version", 1)
    if ver > MODEL_VERSION:
        raise ValueError(
            f"File was saved with schema version {ver}, "
            f"but this version only supports up to {MODEL_VERSION}."
        )

    def _set_combo(combo, value: float | str) -> None:
        """Select the combo item closest to *value* (float comparison)."""
        try:
            target = float(value)
            vals = [float(combo.itemText(i)) for i in range(combo.count())]
            if not vals:
                return
            nearest_idx = min(range(len(vals)), key=lambda i: abs(vals[i] - target))
            combo.setCurrentIndex(nearest_idx)
        except Exception:
            # fallback: plain string match
            idx = combo.findText(str(value))
            if idx >= 0:
                combo.setCurrentIndex(idx)

    # Temporarily block signals to avoid triggering a recalculation for each
    # individual widget update; one recalculation fires at the end.
    all_widgets = [
        mw.beam_bf, mw.beam_totaldepth, mw.beam_tf, mw.beam_tw,
        mw.column_bf, mw.column_totaldepth, mw.column_tf, mw.column_tw,
        mw.plate_width, mw.plate_length, mw.plate_thickness,
        mw.bolt_diameter, mw.bolt_n, mw.bolt_m,
        mw.web_plate_length, mw.web_plate_height, mw.web_plate_thickness,
        mw.web_bolt_diameter, mw.web_bolt_nz, mw.web_bolt_nx,
        mw.wufw_mu, mw.wufw_vu, mw.wufw_pu,
        mw.wufw_shear_plate_height, mw.wufw_shear_plate_width,
        mw.wufw_shear_plate_thickness, mw.wufw_web_fillet_weld,
        mw.design_code_combo,
        mw.connection_type_combo,
    ]
    for w in all_widgets:
        w.blockSignals(True)

    try:
        # Design code
        dc_val = data.get("design_code", "")
        for i in range(mw.design_code_combo.count()):
            item = mw.design_code_combo.itemData(i)
            item_val = item.value if hasattr(item, "value") else str(item)
            if item_val == dc_val:
                mw.design_code_combo.setCurrentIndex(i)
                break

        # Connection type (schema v2+)
        ct_val = data.get("connection_type", "BFP")
        for i in range(mw.connection_type_combo.count()):
            item = mw.connection_type_combo.itemData(i)
            item_val = item.value if hasattr(item, "value") else str(item)
            if item_val == ct_val:
                mw.connection_type_combo.setCurrentIndex(i)
                break

        # Beam
        b = data.get("beam", {})
        mw.beam_bf.setValue(b.get("b", mw.beam_bf.value()))
        mw.beam_totaldepth.setValue(b.get("d", mw.beam_totaldepth.value()))
        _set_combo(mw.beam_tf, b.get("t_f", mw.beam_tf.currentText()))
        _set_combo(mw.beam_tw, b.get("t_w", mw.beam_tw.currentText()))

        # Column
        c = data.get("column", {})
        mw.column_bf.setValue(c.get("b", mw.column_bf.value()))
        mw.column_totaldepth.setValue(c.get("d", mw.column_totaldepth.value()))
        _set_combo(mw.column_tf, c.get("t_f", mw.column_tf.currentText()))
        _set_combo(mw.column_tw, c.get("t_w", mw.column_tw.currentText()))

        # Plate
        p = data.get("plate", {})
        mw.plate_width.setValue(p.get("b_i", mw.plate_width.value()))
        mw.plate_length.setValue(p.get("h_i", mw.plate_length.value()))
        _set_combo(mw.plate_thickness, p.get("t_i", mw.plate_thickness.currentText()))

        # Flange bolts
        bg = data.get("bolt_group", {})
        _set_combo(mw.bolt_diameter, bg.get("d_f", mw.bolt_diameter.currentText()))
        mw.bolt_n.setValue(int(bg.get("n_p", mw.bolt_n.value())))
        mw.bolt_m.setValue(int(bg.get("n_g", mw.bolt_m.value())))

        # Web plate
        wp = data.get("web_plate", {})
        mw.web_plate_length.setValue(wp.get("h_i", mw.web_plate_length.value()))
        mw.web_plate_height.setValue(wp.get("b_i", mw.web_plate_height.value()))
        _set_combo(mw.web_plate_thickness, wp.get("t_i", mw.web_plate_thickness.currentText()))

        # Web bolts
        wb = data.get("web_bolt", {})
        _set_combo(mw.web_bolt_diameter, wb.get("d_f", mw.web_bolt_diameter.currentText()))
        mw.web_bolt_nz.setValue(int(wb.get("n_p", mw.web_bolt_nz.value())))
        mw.web_bolt_nx.setValue(int(wb.get("n_g", mw.web_bolt_nx.value())))

        # WUF-W inputs (schema v2+)
        wufw = data.get("wufw", {})
        mw.wufw_mu.setValue(float(wufw.get("mu", mw.wufw_mu.value())))
        mw.wufw_vu.setValue(float(wufw.get("vu", mw.wufw_vu.value())))
        mw.wufw_pu.setValue(float(wufw.get("pu", mw.wufw_pu.value())))
        mw.wufw_shear_plate_height.setValue(float(wufw.get("shear_plate_height", mw.wufw_shear_plate_height.value())))
        mw.wufw_shear_plate_width.setValue(float(wufw.get("shear_plate_width", mw.wufw_shear_plate_width.value())))
        mw.wufw_shear_plate_thickness.setValue(float(wufw.get("shear_plate_thickness", mw.wufw_shear_plate_thickness.value())))
        mw.wufw_web_fillet_weld.setValue(float(wufw.get("web_fillet_weld", mw.wufw_web_fillet_weld.value())))

    finally:
        for w in all_widgets:
            w.blockSignals(False)
