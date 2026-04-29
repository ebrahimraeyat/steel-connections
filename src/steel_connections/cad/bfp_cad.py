# -*- coding: utf-8 -*-
"""
3D CAD geometry builder for Bolted Flange Plate (BFP) connections.

Coordinate system
-----------------
  X : beam axis  (beam extends in +X from the column face)
  Z : vertical   (up = +Z)  — column axis
  Y : out-of-plane / across flange width

Column  : I-section extruded along Z.
          Depth d_c along X  →  flanges at X = ±d_c/2
          Width b_c along Y  (centred Y=0)
          Column face meeting the beam  →  X = +d_c/2

Beam    : I-section extruded along X from X = +d_c/2.
          Depth d_b along Z  →  top flange top = Z=+d_b/2, bot = Z=-d_b/2
          Width b_b along Y  (centred Y=0)

Flange plates
          Top plate   : Z ∈ [+d_b/2, +d_b/2+p_t], X ∈ [col_face, col_face+p_h]
          Bottom plate: Z ∈ [-d_b/2-p_t, -d_b/2]
          Both centred in Y.

Bolts   : Vertical (Z-direction).
          n_g gauge lines along X (beam axis), first at col_face + s1.
          n_p rows across Y (flange width), centred at Y=0.
          Head OUTSIDE, nut INSIDE.

View buttons
          Front  (روبرو) : look from -X  →  beam cross-section visible
          Side   (بغل)   : look from -Y  →  web + connection in XZ plane
          Top    (بالا)  : look from +Z  →  top flange in XY plane
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse
from OCC.Core.BRepBuilderAPI import (
    BRepBuilderAPI_MakeEdge,
    BRepBuilderAPI_MakeWire,
    BRepBuilderAPI_MakeFace,
    BRepBuilderAPI_Transform,
)
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCC.Core.gp import gp_Pnt, gp_Ax2, gp_Dir, gp_Vec, gp_Trsf
from OCC.Core.TopoDS import TopoDS_Shape
from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCC.Core.AIS import AIS_Shape

if TYPE_CHECKING:
    from steel_connections.bfp_connection import BFPConnection


# ── colours ───────────────────────────────────────────────────────────────────
COLOUR_BEAM   = Quantity_Color(0.65, 0.72, 0.80, Quantity_TOC_RGB)
COLOUR_COLUMN = Quantity_Color(0.50, 0.57, 0.63, Quantity_TOC_RGB)
COLOUR_PLATE  = Quantity_Color(0.90, 0.68, 0.15, Quantity_TOC_RGB)
COLOUR_BOLT   = Quantity_Color(0.20, 0.20, 0.22, Quantity_TOC_RGB)


# ── primitives ────────────────────────────────────────────────────────────────

def _translate(shape: TopoDS_Shape, dx: float, dy: float, dz: float) -> TopoDS_Shape:
    t = gp_Trsf()
    t.SetTranslation(gp_Vec(dx, dy, dz))
    return BRepBuilderAPI_Transform(shape, t, True).Shape()


def _fuse(a: TopoDS_Shape, b: TopoDS_Shape) -> TopoDS_Shape:
    r = BRepAlgoAPI_Fuse(a, b); r.Build(); return r.Shape()


def _box(dx: float, dy: float, dz: float) -> TopoDS_Shape:
    return BRepPrimAPI_MakeBox(abs(dx), abs(dy), abs(dz)).Shape()


def _cyl_z(r: float, h: float, cx: float, cy: float, z_bot: float) -> TopoDS_Shape:
    """Cylinder along +Z."""
    return BRepPrimAPI_MakeCylinder(
        gp_Ax2(gp_Pnt(cx, cy, z_bot), gp_Dir(0, 0, 1)), r, abs(h)
    ).Shape()


def _ais(shape: TopoDS_Shape, colour: Quantity_Color) -> AIS_Shape:
    a = AIS_Shape(shape); a.SetColor(colour); return a


def _cyl_y(r: float, h: float, cx: float, z_cen: float, y_start: float) -> TopoDS_Shape:
    """Cylinder along +Y."""
    return BRepPrimAPI_MakeCylinder(
        gp_Ax2(gp_Pnt(cx, y_start, z_cen), gp_Dir(0, 1, 0)), r, abs(h)
    ).Shape()


def _hex_y(cx: float, z_cen: float, y_base: float,
           across_flats: float, thick: float) -> TopoDS_Shape:
    """Hexagonal prism in XZ plane extruded in +Y by thick. Centre at (cx, z_cen)."""
    R = across_flats / math.sqrt(3)
    pts = [gp_Pnt(cx + R*math.cos(math.radians(30+i*60)),
                  y_base,
                  z_cen + R*math.sin(math.radians(30+i*60))) for i in range(6)]
    wire = BRepBuilderAPI_MakeWire()
    for i in range(6):
        wire.Add(BRepBuilderAPI_MakeEdge(pts[i], pts[(i+1)%6]).Edge())
    face = BRepBuilderAPI_MakeFace(wire.Wire()).Face()
    return BRepPrimAPI_MakePrism(face, gp_Vec(0, thick, 0)).Shape()


def _make_bolt_y(cx: float, z_cen: float,
                y_out: float, y_in: float,
                pl_t: float, web_t: float, d_f: float,
                from_pos_y: bool) -> TopoDS_Shape:
    """
    Web bolt along Y axis.
    from_pos_y=True : head at +Y (outer face), nut at -Y side
    from_pos_y=False: head at -Y (outer face), nut at +Y side
    """
    r      = d_f / 2
    af     = d_f * 1.6
    head_t = d_f * 0.7
    nut_t  = d_f * 0.6
    proto  = d_f * 0.5

    if from_pos_y:
        head_y  = y_out                         # head outer face
        nut_y   = y_in - web_t - nut_t          # nut past web inner
        shaft_y = nut_y - proto
        shaft_h = (head_y + head_t) - shaft_y
        head  = _hex_y(cx, z_cen, head_y, af, head_t)
        shaft = _cyl_y(r, shaft_h, cx, z_cen, shaft_y)
        nut   = _hex_y(cx, z_cen, nut_y, af, nut_t)
    else:
        head_y  = y_out - head_t
        nut_y   = y_in + web_t
        shaft_h = (nut_y + nut_t + proto) - head_y
        head  = _hex_y(cx, z_cen, head_y, af, head_t)
        shaft = _cyl_y(r, shaft_h, cx, z_cen, head_y)
        nut   = _hex_y(cx, z_cen, nut_y, af, nut_t)

    return _fuse(_fuse(head, shaft), nut)


def _beam_section(d: float, b: float, tf: float, tw: float, length: float) -> TopoDS_Shape:
    """Beam: extruded along +X, depth d in Z, width b in Y, centroid at origin."""
    top = _translate(_box(length, b,  tf),       0, -b/2,   d/2 - tf)
    bot = _translate(_box(length, b,  tf),       0, -b/2,  -d/2)
    web = _translate(_box(length, tw, d - 2*tf), 0, -tw/2, -d/2 + tf)
    return _fuse(_fuse(top, bot), web)


def _col_section(d: float, b: float, tf: float, tw: float, length: float) -> TopoDS_Shape:
    """Column: extruded along +Z, depth d in X (flanges at ±d/2), width b in Y."""
    fl1 = _translate(_box(tf,        b,  length),  d/2 - tf, -b/2, 0)  # right flange
    fl2 = _translate(_box(tf,        b,  length), -d/2,      -b/2, 0)  # left flange
    web = _translate(_box(d - 2*tf, tw,  length), -d/2 + tf, -tw/2, 0)
    return _fuse(_fuse(fl1, fl2), web)


# ── hex bolt (XY hexagon extruded in Z) ──────────────────────────────────────

def _hex_z(cx: float, cy: float, z_base: float,
           across_flats: float, thick: float) -> TopoDS_Shape:
    """Hexagonal prism in XY plane, base at z_base, height thick in +Z."""
    R = across_flats / math.sqrt(3)
    pts = [gp_Pnt(cx + R*math.cos(math.radians(30+i*60)),
                  cy + R*math.sin(math.radians(30+i*60)),
                  z_base) for i in range(6)]
    wire = BRepBuilderAPI_MakeWire()
    for i in range(6):
        wire.Add(BRepBuilderAPI_MakeEdge(pts[i], pts[(i+1)%6]).Edge())
    face = BRepBuilderAPI_MakeFace(wire.Wire()).Face()
    return BRepPrimAPI_MakePrism(face, gp_Vec(0, 0, thick)).Shape()


def _make_bolt(cx: float, cy: float,
               z_out: float, z_in: float,
               p_t: float, tf_b: float, d_f: float,
               top: bool) -> TopoDS_Shape:
    """
    Full bolt assembly (hex head + shaft + nut) along Z.
    top=True  → head above top plate (z_out = +d_b/2+p_t), nut below top flange
    top=False → head below bot plate (z_out = -d_b/2-p_t), nut above bot flange
    """
    r      = d_f / 2
    af     = d_f * 1.6
    head_t = d_f * 0.7
    nut_t  = d_f * 0.6
    proto  = d_f * 0.5

    if top:
        # head above plate, nut below flange
        head_base = z_out                      # starts at outer plate surface
        nut_base  = z_in - tf_b - nut_t        # nut just below inner flange face
        shaft_bot = nut_base - proto
        shaft_h   = (head_base + head_t) - shaft_bot
        head  = _hex_z(cx, cy, head_base, af, head_t)
        shaft = _cyl_z(r, shaft_h, cx, cy, shaft_bot)
        nut   = _hex_z(cx, cy, nut_base, af, nut_t)
    else:
        # head below plate, nut above flange
        head_base = z_out - head_t             # head top = plate outer surface
        nut_base  = z_in + tf_b               # nut just above inner flange face
        shaft_top = nut_base + nut_t + proto
        shaft_h   = shaft_top - head_base
        head  = _hex_z(cx, cy, head_base, af, head_t)
        shaft = _cyl_z(r, shaft_h, cx, cy, head_base)
        nut   = _hex_z(cx, cy, nut_base, af, nut_t)

    return _fuse(_fuse(head, shaft), nut)


# ── result container ──────────────────────────────────────────────────────────

@dataclass
class BFPShapes:
    beam:      AIS_Shape
    column:    AIS_Shape
    top_plate: AIS_Shape
    bot_plate: AIS_Shape
    web_plate: AIS_Shape
    bolts:     list[AIS_Shape]   # flange bolts
    web_bolts: list[AIS_Shape]   # web plate bolts

    def all_shapes(self) -> list[AIS_Shape]:
        return ([self.beam, self.column, self.top_plate, self.bot_plate, self.web_plate]
                + self.bolts + self.web_bolts)


# ── main builder ──────────────────────────────────────────────────────────────

def build_bfp_shapes(connection: "BFPConnection",
                     wp_width: float | None = None,
                     wp_length: float | None = None,
                     wp_height: float | None = None,
                     wp_thickness: float | None = None,
                     wb_diam: float | None = None,
                     wb_nz: int | None = None,
                     wb_nx: int | None = None) -> tuple["BFPShapes", list[str]]:
    bg   = connection.bolt_group
    bolt = bg.bolt

    d_b  = connection.beam.geom.d;  b_b  = connection.beam.geom.b
    tf_b = connection.beam.geom.t_f; tw_b = connection.beam.geom.t_w
    d_c  = connection.column.geom.d; b_c  = connection.column.geom.b
    tf_c = connection.column.geom.t_f; tw_c = connection.column.geom.t_w

    p_w = connection.plate.b_i
    p_h = connection.plate.h_i
    p_t = connection.plate.t_i

    n_rows = bg.n_p
    n_gau  = bg.n_g
    s_p    = bg.s_p
    s_g    = bg.s_g
    d_f    = bolt.d_f
    s1     = connection.s1

    # web plate params (fall back to sensible defaults)
    web_clear  = d_b - 2 * tf_b          # max usable height inside flanges
    wp_l  = wp_length    if wp_length    is not None else p_h
    wp_h  = wp_height    if wp_height    is not None else web_clear
    wp_t  = wp_thickness if wp_thickness is not None else max(tw_b, p_t * 0.8)
    wb_df = wb_diam      if wb_diam      is not None else d_f * 0.8
    wb_nz_val = int(wb_nz) if wb_nz is not None else max(2, n_rows)
    wb_nx_val = int(wb_nx) if wb_nx is not None else max(1, n_gau)

    warnings: list[str] = []

    # ── validity / auto-adjust ────────────────────────────────────────────────

    # 1. Web plate height capped to clear height between flanges
    if wp_h > web_clear:
        wp_h = web_clear
        warnings.append(f"Web plate height reduced to {web_clear:.2f} cm "
                        f"(clear height between flanges).")

    # 2. Flange plate ↔ gauge count: if p_h is too short for n_gau, reduce n_gau;
    #    if n_gau is too many for p_h, shrink n_gau to fit (don't grow the plate).
    flange_edge   = s1
    max_n_gau_fit = max(1, int((p_h - 2 * flange_edge) / s_g) + 1) if s_g > 0 else n_gau
    if n_gau > max_n_gau_fit:
        n_gau = max_n_gau_fit
        p_h   = flange_edge * 2 + max(0, n_gau - 1) * s_g
        warnings.append(f"Flange bolt gauge lines reduced to {n_gau} to fit "
                        f"plate length {p_h:.1f} cm (edge dist {flange_edge:.1f} cm).")
    else:
        flange_min_ph = flange_edge * 2 + max(0, n_gau - 1) * s_g
        if p_h < flange_min_ph:
            p_h = flange_min_ph
            warnings.append(f"Flange plate length increased to {p_h:.1f} cm "
                            f"to satisfy bolt edge distance ({flange_edge:.1f} cm each end).")

    # 3. Web plate ↔ bolt column count: if wp_l is too short, reduce wb_nx_val;
    #    if wb_nx_val demands more length, grow the web plate.
    wb_edge = max(wb_df * 2.0, 3.0)              # min edge dist each end
    wb_spacing = wb_edge * 2                      # bolt spacing = 2× edge dist
    max_wb_nx_fit = max(1, int((wp_l - 2 * wb_edge) / wb_spacing) + 1) if wb_spacing > 0 else wb_nx_val
    if wb_nx_val > max_wb_nx_fit:
        wb_nx_val = max_wb_nx_fit
        wp_l = wb_edge * 2 + max(0, wb_nx_val - 1) * wb_spacing
        warnings.append(f"Web bolt columns reduced to {wb_nx_val} to fit "
                        f"web plate length {wp_l:.1f} cm (edge dist {wb_edge:.1f} cm).")
    else:
        wp_min_l = wb_edge * 2 + max(0, wb_nx_val - 1) * wb_spacing
        if wp_l < wp_min_l:
            wp_l = wp_min_l
            warnings.append(f"Web plate length increased to {wp_l:.1f} cm "
                            f"to satisfy web bolt edge distance ({wb_edge:.1f} cm each end).")

    col_face_x = d_c / 2
    gap        = 0.0                     # beam end flush with column face (visual)

    # 4. Beam display length must clear the longest plate with 20% margin
    longest_pl = max(p_h, wp_l)
    beam_len   = max(longest_pl * 1.2, d_b * 1.3)
    if longest_pl * 1.2 > d_b * 1.3:
        warnings.append(f"Beam display length set to {beam_len:.1f} cm "
                        f"to accommodate plate length ({longest_pl:.1f} cm).")

    # ── record all effective (possibly adjusted) values for UI sync ───────────
    adjustments = {
        "plate_length":     p_h,
        "bolt_m":           n_gau,
        "web_plate_length": wp_l,
        "web_bolt_nx":      wb_nx_val,
        "web_plate_height": wp_h,
    }
    col_h      = max(d_c * 2.5, d_b * 2.0)

    # ── column (Z-axis, centred at origin) ──────────────────────────────────────
    col_s = _col_section(d_c, b_c, tf_c, tw_c, col_h)
    col_s = _translate(col_s, -d_c/2, -b_c/2, -col_h/2)
    col_ais = _ais(col_s, COLOUR_COLUMN)

    # ── beam (X-axis, centroid at Z=0 = column mid-height) ────────────────────
    # _beam_section centres the section at origin (top flange top = +d_b/2, bot = -d_b/2)
    # No Z shift needed → beam centroid stays at Z=0
    beam_s = _beam_section(d_b, b_b, tf_b, tw_b, beam_len)
    beam_s = _translate(beam_s, col_face_x + gap, -b_b/2, 0)
    beam_ais = _ais(beam_s, COLOUR_BEAM)

    # ── flange plates ─────────────────────────────────────────────────────────
    # Top flange top  = Z = +d_b/2
    # Bot flange bot  = Z = -d_b/2
    pl_y = -b_b/2 - p_w/2
    top_pl = _translate(_box(p_h, p_w, p_t), col_face_x, pl_y,  d_b/2)
    bot_pl = _translate(_box(p_h, p_w, p_t), col_face_x, pl_y, -d_b/2 - p_t)
    top_pl_ais = _ais(top_pl, COLOUR_PLATE)
    bot_pl_ais = _ais(bot_pl, COLOUR_PLATE)

    # ── web plate (on +Y face of beam web, between inner flange faces) ────────
    web_y_face = -b_b/2 + tw_b/2      # +Y outer face of the beam web
    wp_z_bot   = -wp_h / 2            # centre web plate on beam centroid in Z
    wp = _translate(_box(wp_l, wp_t, wp_h),
                    col_face_x,
                    web_y_face,                  # plate starts at web +Y face
                    wp_z_bot)                    # centred on beam centroid
    web_pl_ais = _ais(wp, COLOUR_PLATE)

    # shared X start for all bolt grids
    x0 = col_face_x + s1
    y0 = -b_b/2 - (n_rows - 1) * s_p / 2

    # ── web plate bolts (Y-direction) ────────────────────────────────────────
    # independent X spacing: spread wb_nx_val bolts along the plate length
    s_wb_x  = wp_l / (wb_nx_val + 1)          # X spacing between web bolts
    s_wb_z  = wp_h / (wb_nz_val + 1)          # Z spacing between web bolts
    y_wp_outer = web_y_face + wp_t             # +Y outer face of web plate
    # y_in passed to _make_bolt_y = plate-to-web interface (+Y face of beam web)
    # _make_bolt_y then subtracts web_t to place nut past -Y web face

    web_bolts: list[AIS_Shape] = []
    for xi in range(wb_nx_val):
        bx = col_face_x + s_wb_x * (xi + 1)
        for zi in range(wb_nz_val):
            bz = wp_z_bot + s_wb_z * (zi + 1)
            wb = _make_bolt_y(
                cx=bx, z_cen=bz,
                y_out=y_wp_outer,
                y_in=web_y_face,               # ← plate/web interface (fixed)
                pl_t=wp_t, web_t=tw_b, d_f=wb_df,
                from_pos_y=True,
            )
            web_bolts.append(_ais(wb, COLOUR_BOLT))

    # ── flange bolt grid ──────────────────────────────────────────────────────

    bolts: list[AIS_Shape] = []
    for gi in range(n_gau):
        bx = x0 + gi * s_g
        for ri in range(n_rows):
            by = y0 + ri * s_p

            tb = _make_bolt(bx, by,
                            z_out=d_b/2 + p_t,   # top of top plate
                            z_in=d_b/2,           # top flange top face
                            p_t=p_t, tf_b=tf_b, d_f=d_f, top=True)
            bolts.append(_ais(tb, COLOUR_BOLT))

            bb_s = _make_bolt(bx, by,
                              z_out=-d_b/2 - p_t,  # bottom of bottom plate
                              z_in=-d_b/2,          # bottom flange bottom face
                              p_t=p_t, tf_b=tf_b, d_f=d_f, top=False)
            bolts.append(_ais(bb_s, COLOUR_BOLT))

    return BFPShapes(beam_ais, col_ais, top_pl_ais, bot_pl_ais, web_pl_ais, bolts, web_bolts), warnings, adjustments

