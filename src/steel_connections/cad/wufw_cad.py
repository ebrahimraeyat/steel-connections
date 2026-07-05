# -*- coding: utf-8 -*-
"""
3D CAD geometry builder for Welded Unreinforced Flange-Welded Web (WUF-W)
moment connections (AISC 358-16 Chapter 8).

Coordinate system (same convention as bfp_cad)
----------------------------------------------
  X : beam axis    (beam extends in +X from the column face)
  Z : vertical     (column axis, up = +Z)
  Y : out-of-plane (across flange width, centred at Y=0)

Column : I-section extruded along Z.  Depth d_c along X (flanges at ±d_c/2),
         width b_c along Y.  Column face meeting the beam at X = +d_c/2.
Beam   : I-section extruded along +X starting at the column face.
         Depth d_b along Z (centred at origin), width b_b along Y.

WUF-W specific parts
--------------------
* Beam flanges are joined to the column flange by CJP groove welds.
* The beam web is connected through a single shear plate (shear tab).
* Weld access holes are cut from the beam web adjacent to each flange.
* Continuity plates / web doubler plate are added when required.

The module is intentionally organised as small, single-purpose helpers so it
can later be migrated to the shape/ + component/ class hierarchy (Osdag style)
without touching the calling code.

All dimensions are expected in centimetres (the internal unit of the app).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from OCC.Core.BRepPrimAPI import (
    BRepPrimAPI_MakeBox,
    BRepPrimAPI_MakeCylinder,
)
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse, BRepAlgoAPI_Cut
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCC.Core.gp import gp_Pnt, gp_Ax2, gp_Dir, gp_Trsf
from OCC.Core.TopoDS import TopoDS_Shape
from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCC.Core.AIS import AIS_Shape

if TYPE_CHECKING:
    from steel_connections.wufw_connection import WUFWConnection


# ── colours ───────────────────────────────────────────────────────────────────
COLOUR_BEAM       = Quantity_Color(0.65, 0.72, 0.80, Quantity_TOC_RGB)
COLOUR_COLUMN     = Quantity_Color(0.50, 0.57, 0.63, Quantity_TOC_RGB)
COLOUR_PLATE      = Quantity_Color(0.90, 0.68, 0.15, Quantity_TOC_RGB)
COLOUR_WELD       = Quantity_Color(0.80, 0.35, 0.10, Quantity_TOC_RGB)
COLOUR_BOLT       = Quantity_Color(0.20, 0.20, 0.22, Quantity_TOC_RGB)
COLOUR_CONTINUITY = Quantity_Color(0.35, 0.65, 0.45, Quantity_TOC_RGB)
COLOUR_DOUBLER    = Quantity_Color(0.55, 0.45, 0.70, Quantity_TOC_RGB)


# ── primitives ────────────────────────────────────────────────────────────────

def _translate(shape: TopoDS_Shape, dx: float, dy: float, dz: float) -> TopoDS_Shape:
    t = gp_Trsf()
    t.SetTranslation(gp_Pnt(0, 0, 0), gp_Pnt(dx, dy, dz))
    return BRepBuilderAPI_Transform(shape, t, True).Shape()


def _box(dx: float, dy: float, dz: float) -> TopoDS_Shape:
    return BRepPrimAPI_MakeBox(abs(dx), abs(dy), abs(dz)).Shape()


def _fuse(a: TopoDS_Shape, b: TopoDS_Shape) -> TopoDS_Shape:
    r = BRepAlgoAPI_Fuse(a, b)
    r.Build()
    return r.Shape()


def _cut(a: TopoDS_Shape, b: TopoDS_Shape) -> TopoDS_Shape:
    r = BRepAlgoAPI_Cut(a, b)
    r.Build()
    return r.Shape()


def _cyl_y(r: float, length: float, cx: float, cz: float, y_base: float) -> TopoDS_Shape:
    """Cylinder whose axis is the +Y direction, base centre at (cx, y_base, cz)."""
    ax = gp_Ax2(gp_Pnt(cx, y_base, cz), gp_Dir(0, 1, 0))
    return BRepPrimAPI_MakeCylinder(ax, r, length).Shape()


def _ais(shape: TopoDS_Shape, colour: Quantity_Color) -> AIS_Shape:
    a = AIS_Shape(shape)
    a.SetColor(colour)
    return a


# ── I-sections ────────────────────────────────────────────────────────────────

def _beam_section(d: float, b: float, tf: float, tw: float, length: float) -> TopoDS_Shape:
    """Beam extruded along +X, depth d in Z, width b in Y, centroid at origin."""
    top = _translate(_box(length, b, tf), 0, -b / 2, d / 2 - tf)
    bot = _translate(_box(length, b, tf), 0, -b / 2, -d / 2)
    web = _translate(_box(length, tw, d - 2 * tf), 0, -tw / 2, -d / 2 + tf)
    return _fuse(_fuse(top, bot), web)


def _col_section(d: float, b: float, tf: float, tw: float, length: float) -> TopoDS_Shape:
    """Column extruded along +Z, depth d in X (flanges at ±d/2), width b in Y."""
    fl1 = _translate(_box(tf, b, length), d / 2 - tf, -b / 2, 0)   # right flange (beam side)
    fl2 = _translate(_box(tf, b, length), -d / 2, -b / 2, 0)       # left flange
    web = _translate(_box(d - 2 * tf, tw, length), -d / 2 + tf, -tw / 2, 0)
    return _fuse(_fuse(fl1, fl2), web)


# ── helpers ───────────────────────────────────────────────────────────────────

def _pos(value: float, default: float) -> float:
    """Return a strictly-positive, finite value or the supplied default."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return default
    return v if math.isfinite(v) and v > 0 else default


# ── result container ──────────────────────────────────────────────────────────

@dataclass
class WUFWShapes:
    beam:              AIS_Shape
    column:            AIS_Shape
    shear_plate:       AIS_Shape
    flange_welds:      list[AIS_Shape] = field(default_factory=list)
    erection_bolts:    list[AIS_Shape] = field(default_factory=list)
    continuity_plates: list[AIS_Shape] = field(default_factory=list)
    doubler_plates:    list[AIS_Shape] = field(default_factory=list)

    def all_shapes(self) -> list[AIS_Shape]:
        return (
            [self.beam, self.column, self.shear_plate]
            + self.flange_welds
            + self.erection_bolts
            + self.continuity_plates
            + self.doubler_plates
        )


# ── main builder ──────────────────────────────────────────────────────────────

def build_wufw_shapes(
    connection: "WUFWConnection",
    show_continuity_plates: bool = False,
    show_doubler_plate: bool = False,
) -> WUFWShapes:
    """Build the 3D CAD assembly for a WUF-W connection.

    Parameters
    ----------
    connection:
        The :class:`WUFWConnection` holding beam/column sections and detailing.
    show_continuity_plates:
        Add transverse continuity plates inside the column (when required).
    show_doubler_plate:
        Add a web doubler plate to the column panel zone (when required).
    """
    beam = connection.beam
    col = connection.column

    d_b = _pos(beam.geom.d, 45.0)
    b_b = _pos(beam.geom.b, 20.0)
    tf_b = _pos(beam.geom.t_f, 1.4)
    tw_b = _pos(beam.geom.t_w, 0.9)

    d_c = _pos(col.geom.d, 40.0)
    b_c = _pos(col.geom.b, 40.0)
    tf_c = _pos(col.geom.t_f, 2.0)
    tw_c = _pos(col.geom.t_w, 1.2)

    col_face = d_c / 2.0
    beam_length = max(2.0 * d_b, 60.0)
    col_height = max(2.5 * d_b, 2.0 * d_c)
    inner_d = max(d_c - 2.0 * tf_c, 1.0)  # clear column depth between flanges

    # ── beam with weld access holes ───────────────────────────────────────────
    beam_shape = _translate(
        _beam_section(d_b, b_b, tf_b, tw_b, beam_length), col_face, 0, 0
    )

    hole_len = _pos(connection.access_hole_length, 3.0)
    hole_h = _pos(connection.access_hole_height, 1.2)
    hole_len = min(hole_len, beam_length * 0.5)
    hole_h = min(hole_h, (d_b - 2.0 * tf_b) * 0.5)

    top_hole = _translate(
        _box(hole_len, tw_b * 2.0, hole_h), col_face, -tw_b, d_b / 2 - tf_b - hole_h
    )
    bot_hole = _translate(
        _box(hole_len, tw_b * 2.0, hole_h), col_face, -tw_b, -d_b / 2 + tf_b
    )
    beam_shape = _cut(_cut(beam_shape, top_hole), bot_hole)

    # ── column ────────────────────────────────────────────────────────────────
    column_shape = _translate(
        _col_section(d_c, b_c, tf_c, tw_c, col_height), 0, 0, -col_height / 2
    )

    # ── shear plate (single plate on +Y face of the beam web) ─────────────────
    tp = _pos(connection.shear_plate_thickness, max(tw_b, 1.0))
    hp = _pos(connection.shear_plate_height, (2.0 / 3.0) * d_b)
    lp = _pos(connection.shear_plate_width, max(b_b / 2.0, 10.0))
    hp = min(hp, d_b - 2.0 * tf_b)
    shear_plate = _translate(_box(lp, tp, hp), col_face, tw_b / 2.0, -hp / 2.0)

    # ── CJP flange welds at the column face ───────────────────────────────────
    w_len = max(tf_b, 0.8)
    top_weld = _translate(
        _box(w_len, b_b, tf_b), col_face - w_len, -b_b / 2, d_b / 2 - tf_b
    )
    bot_weld = _translate(
        _box(w_len, b_b, tf_b), col_face - w_len, -b_b / 2, -d_b / 2
    )
    flange_welds = [_ais(top_weld, COLOUR_WELD), _ais(bot_weld, COLOUR_WELD)]

    # ── erection bolts through the shear plate and beam web ───────────────────
    erection_bolts: list[AIS_Shape] = []
    bolt_r = min(tw_b, 1.0) * 0.9
    bolt_len = tp + tw_b + 1.0
    bolt_x = col_face + lp * 0.55
    for z in (hp * 0.28, -hp * 0.28):
        bolt = _cyl_y(bolt_r, bolt_len, bolt_x, z, -tw_b / 2.0 - 0.5)
        erection_bolts.append(_ais(bolt, COLOUR_BOLT))

    # ── continuity plates (aligned with beam flanges, inside the column) ──────
    continuity_plates: list[AIS_Shape] = []
    if show_continuity_plates:
        cp_th = tf_b
        for z0 in (d_b / 2 - tf_b, -d_b / 2):
            cp = _translate(
                _box(inner_d, b_c, cp_th), -d_c / 2 + tf_c, -b_c / 2, z0
            )
            continuity_plates.append(_ais(cp, COLOUR_CONTINUITY))

    # ── web doubler plate (column panel zone) ─────────────────────────────────
    doubler_plates: list[AIS_Shape] = []
    if show_doubler_plate:
        dp = _translate(
            _box(inner_d, tw_c, d_b), -d_c / 2 + tf_c, tw_c / 2.0, -d_b / 2
        )
        doubler_plates.append(_ais(dp, COLOUR_DOUBLER))

    return WUFWShapes(
        beam=_ais(beam_shape, COLOUR_BEAM),
        column=_ais(column_shape, COLOUR_COLUMN),
        shear_plate=_ais(shear_plate, COLOUR_PLATE),
        flange_welds=flange_welds,
        erection_bolts=erection_bolts,
        continuity_plates=continuity_plates,
        doubler_plates=doubler_plates,
    )
