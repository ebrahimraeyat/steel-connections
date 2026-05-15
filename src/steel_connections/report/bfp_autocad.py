# -*- coding: utf-8 -*-
"""
DXF drawing generator for BFP (Bolted Flange Plate) connections.

The exporter creates three views in one DXF file:
1) Side view
2) Front view
3) 3D isometric projected view

Key design goals
----------------
- Use real dimensions in millimetres.
- Use DXF DIMENSION entities where practical.
- Follow the actual geometry used by the 3D BFP model.
- Use a DXF template if available for dimension style / text style defaults.
- Keep all notes in English.
- Do not append unit strings to each dimension value; instead a note is added:
  "ALL DIMENSIONS ARE IN MILLIMETRES."
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math

import ezdxf
from ezdxf.layouts import Modelspace


LAYER_SIDE = "Side_View"
LAYER_FRONT = "Front_View"
LAYER_3D = "3D_View"
LAYER_DIM = "Dimensions"
LAYER_TEXT = "Text"
LAYER_WELD = "Welds"
LAYER_BOLT = "Bolts"


@dataclass
class BFPDrawingData:
    beam_d: float
    beam_bf: float
    beam_tf: float
    beam_tw: float
    col_d: float
    col_bf: float
    col_tf: float
    col_tw: float
    plate_w: float
    plate_l: float
    plate_t: float
    bolt_df: float
    bolt_np: int
    bolt_ng: int
    bolt_sp: float
    bolt_sg: float
    web_plate_l: float | None
    web_plate_h: float | None
    web_plate_t: float | None
    web_bolt_df: float | None
    web_bolt_np: int
    web_bolt_ng: int
    sh: float
    s1: float
    s3: float
    s5: float
    lh: float
    gap: float
    continuity_t: float | None


@dataclass
class BFPLayoutData:
    col_h: float
    col_face_x: float
    beam_start_x: float
    beam_len: float
    taper_len: float
    flange_edge: float
    flange_spacing: float
    web_plate_x: float
    web_plate_z_bot: float
    web_weld_size: float


def _to_mm(value) -> float:
    return 0.0 if value is None else float(value) * 10.0


def _get_attr_chain(obj, *names, default=None):
    cur = obj
    for name in names:
        if cur is None or not hasattr(cur, name):
            return default
        cur = getattr(cur, name)
    return cur


def _extract_continuity_thickness_mm(connection) -> float | None:
    for path in [
        ("continuity_plate", "t_i"),
        ("continuity_plate", "t"),
        ("continuity_plate", "thickness"),
        ("continuity_plate_top", "t_i"),
        ("continuity_plate_bottom", "t_i"),
    ]:
        value = _get_attr_chain(connection, *path, default=None)
        if value is not None:
            return _to_mm(value)
    return None


def _extract_data(connection) -> BFPDrawingData:
    beam_geom = connection.beam.geom
    col_geom = connection.column.geom
    plate = connection.plate
    bolt_group = connection.bolt_group
    bolt = getattr(connection, "bolt", None) or bolt_group.bolt
    web_plate = getattr(connection, "web_plate", None)
    web_group = getattr(connection, "bolt_group_web", None)
    web_bolt = getattr(web_group, "bolt", None) if web_group else None

    return BFPDrawingData(
        beam_d=_to_mm(beam_geom.d),
        beam_bf=_to_mm(beam_geom.b),
        beam_tf=_to_mm(beam_geom.t_f),
        beam_tw=_to_mm(beam_geom.t_w),
        col_d=_to_mm(col_geom.d),
        col_bf=_to_mm(col_geom.b),
        col_tf=_to_mm(col_geom.t_f),
        col_tw=_to_mm(col_geom.t_w),
        plate_w=_to_mm(plate.b_i),
        plate_l=_to_mm(plate.h_i),
        plate_t=_to_mm(plate.t_i),
        bolt_df=_to_mm(bolt.d_f),
        bolt_np=int(bolt_group.n_p),
        bolt_ng=int(bolt_group.n_g),
        bolt_sp=_to_mm(bolt_group.s_p),
        bolt_sg=_to_mm(bolt_group.s_g),
        web_plate_l=_to_mm(web_plate.h_i) if web_plate else None,
        web_plate_h=_to_mm(web_plate.b_i) if web_plate else None,
        web_plate_t=_to_mm(web_plate.t_i) if web_plate else None,
        web_bolt_df=_to_mm(web_bolt.d_f) if web_bolt else None,
        web_bolt_np=int(web_group.n_p) if web_group else 0,
        web_bolt_ng=int(web_group.n_g) if web_group else 0,
        sh=_to_mm(getattr(connection, "sh", 0.0)),
        s1=_to_mm(getattr(connection, "s1", 0.0)),
        s3=_to_mm(getattr(connection, "s3", 0.0)),
        s5=_to_mm(getattr(connection, "s5", 0.0)),
        lh=_to_mm(getattr(connection, "lh", 0.0)),
        gap=_to_mm(getattr(connection, "gap", 0.0)),
        continuity_t=_extract_continuity_thickness_mm(connection),
    )


def _compute_layout(data: BFPDrawingData) -> BFPLayoutData:
    longest_plate = max(data.plate_l, data.web_plate_l or 0.0)
    taper_len = data.plate_t
    gap = data.gap if data.gap > 0 else taper_len
    col_face_x = data.col_d / 2.0
    beam_start_x = col_face_x + gap
    beam_len = max(longest_plate * 1.2, data.beam_d * 1.3)
    col_h = max(data.col_d * 2.5, data.beam_d * 2.0)
    flange_edge = max(data.s1, 1.5 * data.bolt_df)
    flange_spacing = 0.0
    if data.bolt_ng > 1:
        flange_spacing = max(data.plate_l - 2.0 * flange_edge, 0.0) / (data.bolt_ng - 1)
    web_plate_h = data.web_plate_h or max(data.beam_d - 2.0 * data.beam_tf, 0.0)
    web_plate_x = col_face_x
    web_plate_z_bot = -web_plate_h / 2.0
    web_weld_size = min(data.web_plate_t or data.beam_tw, max(4.0, data.beam_tw * 0.5))
    return BFPLayoutData(
        col_h=col_h,
        col_face_x=col_face_x,
        beam_start_x=beam_start_x,
        beam_len=beam_len,
        taper_len=taper_len,
        flange_edge=flange_edge,
        flange_spacing=flange_spacing,
        web_plate_x=web_plate_x,
        web_plate_z_bot=web_plate_z_bot,
        web_weld_size=web_weld_size,
    )


def _template_path() -> Path:
    return Path(__file__).resolve().parents[1] / "templates" / "bfp.dxf"


def _new_document() -> ezdxf.EzDxfDocument:
    template = _template_path()
    if template.exists():
        try:
            doc = ezdxf.readfile(template)
            msp = doc.modelspace()
            for entity in list(msp):
                try:
                    msp.delete_entity(entity)
                except Exception:
                    pass
            return doc
        except Exception:
            pass
    return ezdxf.new("R2010")


def _setup_layers(doc: ezdxf.EzDxfDocument) -> None:
    for name, color in [
        (LAYER_SIDE, 2),
        (LAYER_FRONT, 3),
        (LAYER_3D, 5),
        (LAYER_DIM, 1),
        (LAYER_TEXT, 7),
        (LAYER_WELD, 30),
        (LAYER_BOLT, 250),
    ]:
        if name not in doc.layers:
            doc.layers.new(name, dxfattribs={"color": color})


def _dimstyle_name(doc: ezdxf.EzDxfDocument) -> str:
    for name in ("ISO-25", "Annotative", "Standard"):
        if name in doc.dimstyles:
            return name
    return "Standard"


def _rgb(r: int, g: int, b: int) -> int:
    return (r << 16) + (g << 8) + b


def _add_text(msp: Modelspace, text: str, x: float, y: float, height: float = 18.0,
              layer: str = LAYER_TEXT, rotation: float = 0.0) -> None:
    msp.add_text(
        text,
        dxfattribs={"height": height, "layer": layer, "rotation": rotation},
    ).set_placement((x, y))


def _line(msp: Modelspace, p1, p2, layer: str, color: int | None = None) -> None:
    attrs = {"layer": layer}
    if color is not None:
        attrs["true_color"] = color
    msp.add_line(p1, p2, dxfattribs=attrs)


def _poly(msp: Modelspace, points, layer: str, closed: bool = True,
          color: int | None = None) -> None:
    attrs = {"layer": layer}
    if color is not None:
        attrs["true_color"] = color
    pts = list(points)
    if closed and pts and pts[0] != pts[-1]:
        pts.append(pts[0])
    msp.add_lwpolyline(pts, dxfattribs=attrs)


def _rect(msp: Modelspace, x: float, y: float, w: float, h: float, layer: str,
          color: int | None = None) -> None:
    _poly(msp, [(x, y), (x + w, y), (x + w, y + h), (x, y + h)], layer, closed=True, color=color)


def _circle(msp: Modelspace, x: float, y: float, r: float, layer: str,
            color: int | None = None) -> None:
    attrs = {"layer": layer}
    if color is not None:
        attrs["true_color"] = color
    msp.add_circle((x, y), r, dxfattribs=attrs)


def _solid(msp: Modelspace, points, layer: str, color: int | None = None) -> None:
    attrs = {"layer": layer}
    if color is not None:
        attrs["true_color"] = color
    pts = list(points)
    if len(pts) == 3:
        pts.append(pts[-1])
    msp.add_solid(pts, dxfattribs=attrs)


def _add_linear_dim(msp: Modelspace, p1, p2, base, angle: float, doc: ezdxf.EzDxfDocument) -> None:
    dim = msp.add_linear_dim(
        base=base,
        p1=p1,
        p2=p2,
        angle=angle,
        dimstyle=_dimstyle_name(doc),
        override={
            "dimtxt": 18.0,
            "dimasz": 18.0,
            "dimexo": 6.0,
            "dimexe": 6.0,
            "dimtad": 1,
            "dimclrd": 1,
            "dimclre": 1,
            "dimclrt": 1,
        },
        dxfattribs={"layer": LAYER_DIM},
    )
    dim.render()


def _flange_bolt_x_positions(data: BFPDrawingData, layout: BFPLayoutData) -> list[float]:
    if data.bolt_ng <= 0:
        return []
    if data.bolt_ng == 1:
        return [layout.beam_start_x + data.plate_l / 2.0]
    return [layout.beam_start_x + layout.flange_edge + i * layout.flange_spacing for i in range(data.bolt_ng)]


def _flange_bolt_y_positions(data: BFPDrawingData) -> list[float]:
    if data.bolt_np <= 0:
        return []
    if data.bolt_np == 1:
        return [0.0]
    start = -(data.bolt_np - 1) * data.bolt_sp / 2.0
    return [start + i * data.bolt_sp for i in range(data.bolt_np)]


def _front_flange_bolt_y_positions(data: BFPDrawingData) -> list[float]:
    if data.bolt_np <= 0:
        return []
    if data.bolt_np == 1:
        return [data.plate_w / 2.0]
    total = (data.bolt_np - 1) * data.bolt_sp
    edge = max((data.plate_w - total) / 2.0, 1.5 * data.bolt_df)
    return [edge + i * data.bolt_sp for i in range(data.bolt_np)]


def _web_bolt_positions(data: BFPDrawingData) -> list[tuple[float, float]]:
    if not data.web_plate_l or not data.web_plate_h or not data.web_bolt_df:
        return []
    nx = max(data.web_bolt_ng, 1)
    nz = max(data.web_bolt_np, 1)
    edge_x = max(1.5 * data.web_bolt_df, 30.0)
    edge_z = max(1.5 * data.web_bolt_df, 30.0)
    xs = [data.web_plate_l / 2.0] if nx == 1 else [
        edge_x + i * (max(data.web_plate_l - 2 * edge_x, 0.0) / (nx - 1)) for i in range(nx)
    ]
    zs = [data.web_plate_h / 2.0] if nz == 1 else [
        edge_z + i * (max(data.web_plate_h - 2 * edge_z, 0.0) / (nz - 1)) for i in range(nz)
    ]
    return [(x, z) for x in xs for z in zs]


def add_general_note(msp: Modelspace, x: float, y: float) -> None:
    _add_text(msp, "ALL DIMENSIONS ARE IN MILLIMETRES.", x, y, height=14.0, layer=LAYER_TEXT)


def _hex_bolt_side(msp: Modelspace, cx: float, z_base: float, df: float, upward: bool) -> None:
    head_w = df * 1.6
    head_t = df * 0.7
    x0 = cx - head_w / 2.0
    if upward:
        _rect(msp, x0, z_base, head_w, head_t, LAYER_BOLT)
    else:
        _rect(msp, x0, z_base - head_t, head_w, head_t, LAYER_BOLT)


def draw_side_view(msp: Modelspace, connection, doc: ezdxf.EzDxfDocument, origin=(0.0, 0.0)) -> tuple[float, float]:
    data = _extract_data(connection)
    layout = _compute_layout(data)
    ox, oy = origin
    x_min = -data.col_d / 2.0
    y_shift = oy + layout.col_h / 2.0 + 120.0

    def pt(x: float, z: float) -> tuple[float, float]:
        return ox + (x - x_min), y_shift + z

    _rect(msp, *pt(-data.col_d / 2.0, -layout.col_h / 2.0), data.col_d, layout.col_h, LAYER_SIDE)
    _rect(msp, *pt(layout.beam_start_x, data.beam_d / 2.0 - data.beam_tf), layout.beam_len, data.beam_tf, LAYER_SIDE)
    _rect(msp, *pt(layout.beam_start_x, -data.beam_d / 2.0), layout.beam_len, data.beam_tf, LAYER_SIDE)
    _rect(msp, *pt(layout.beam_start_x, -data.beam_d / 2.0 + data.beam_tf), layout.beam_len, data.beam_d - 2.0 * data.beam_tf, LAYER_SIDE)

    if data.continuity_t and data.continuity_t > 0:
        cp_t = data.continuity_t
        cp_x0 = -data.col_d / 2.0 + data.col_tf
        cp_w = data.col_d - 2.0 * data.col_tf
        _rect(msp, *pt(cp_x0, data.beam_d / 2.0 - cp_t), cp_w, cp_t, LAYER_SIDE)
        _rect(msp, *pt(cp_x0, -data.beam_d / 2.0), cp_w, cp_t, LAYER_SIDE)

    top_plate = [
        pt(layout.col_face_x, data.beam_d / 2.0),
        pt(layout.beam_start_x + data.plate_l, data.beam_d / 2.0),
        pt(layout.beam_start_x + data.plate_l, data.beam_d / 2.0 + data.plate_t),
        pt(layout.beam_start_x, data.beam_d / 2.0 + data.plate_t),
    ]
    bot_plate = [
        pt(layout.col_face_x, -data.beam_d / 2.0),
        pt(layout.beam_start_x + data.plate_l, -data.beam_d / 2.0),
        pt(layout.beam_start_x + data.plate_l, -data.beam_d / 2.0 - data.plate_t),
        pt(layout.beam_start_x, -data.beam_d / 2.0 - data.plate_t),
    ]
    _poly(msp, top_plate, LAYER_SIDE)
    _poly(msp, bot_plate, LAYER_SIDE)

    _solid(msp, [
        pt(layout.col_face_x, data.beam_d / 2.0),
        pt(layout.col_face_x, data.beam_d / 2.0 + data.plate_t),
        pt(layout.beam_start_x, data.beam_d / 2.0 + data.plate_t),
    ], LAYER_WELD)
    _solid(msp, [
        pt(layout.col_face_x, -data.beam_d / 2.0),
        pt(layout.col_face_x, -data.beam_d / 2.0 - data.plate_t),
        pt(layout.beam_start_x, -data.beam_d / 2.0 - data.plate_t),
    ], LAYER_WELD)

    if data.web_plate_l and data.web_plate_h and data.web_plate_t:
        _rect(msp, *pt(layout.web_plate_x, layout.web_plate_z_bot), data.web_plate_l, data.web_plate_h, LAYER_SIDE)
        _poly(msp, [
            pt(layout.web_plate_x, layout.web_plate_z_bot),
            pt(layout.web_plate_x + layout.web_weld_size, layout.web_plate_z_bot),
            pt(layout.web_plate_x + layout.web_weld_size, layout.web_plate_z_bot + data.web_plate_h),
            pt(layout.web_plate_x, layout.web_plate_z_bot + data.web_plate_h),
        ], LAYER_WELD)
        for bx, bz in _web_bolt_positions(data):
            _circle(msp, *pt(layout.web_plate_x + bx, layout.web_plate_z_bot + bz), (data.web_bolt_df or 16.0) / 2.0, LAYER_BOLT)

    for bx in _flange_bolt_x_positions(data, layout):
        x2d = pt(bx, 0.0)[0]
        _hex_bolt_side(msp, x2d, pt(0.0, data.beam_d / 2.0 + data.plate_t)[1], data.bolt_df, upward=True)
        _hex_bolt_side(msp, x2d, pt(0.0, data.beam_d / 2.0)[1], data.bolt_df, upward=False)
        _hex_bolt_side(msp, x2d, pt(0.0, -data.beam_d / 2.0 - data.plate_t)[1], data.bolt_df, upward=False)
        _hex_bolt_side(msp, x2d, pt(0.0, -data.beam_d / 2.0)[1], data.bolt_df, upward=True)

    _add_linear_dim(msp, pt(layout.col_face_x, data.beam_d / 2.0 + data.plate_t), pt(layout.beam_start_x + data.plate_l, data.beam_d / 2.0 + data.plate_t), pt(layout.col_face_x, data.beam_d / 2.0 + data.plate_t + 65.0), 0, doc)
    _add_linear_dim(msp, pt(layout.col_face_x, -data.beam_d / 2.0 - data.plate_t), pt(layout.beam_start_x, -data.beam_d / 2.0 - data.plate_t), pt(layout.col_face_x, -data.beam_d / 2.0 - data.plate_t - 55.0), 0, doc)
    _add_linear_dim(msp, pt(layout.beam_start_x + layout.beam_len, -data.beam_d / 2.0), pt(layout.beam_start_x + layout.beam_len, data.beam_d / 2.0), pt(layout.beam_start_x + layout.beam_len + 90.0, -data.beam_d / 2.0), 90, doc)
    if data.web_plate_l and data.web_plate_h:
        _add_linear_dim(msp, pt(layout.web_plate_x, layout.web_plate_z_bot + data.web_plate_h), pt(layout.web_plate_x + data.web_plate_l, layout.web_plate_z_bot + data.web_plate_h), pt(layout.web_plate_x, layout.web_plate_z_bot + data.web_plate_h + 60.0), 0, doc)
        _add_linear_dim(msp, pt(layout.web_plate_x + data.web_plate_l, layout.web_plate_z_bot), pt(layout.web_plate_x + data.web_plate_l, layout.web_plate_z_bot + data.web_plate_h), pt(layout.web_plate_x + data.web_plate_l + 70.0, layout.web_plate_z_bot), 90, doc)
    bolt_xs = _flange_bolt_x_positions(data, layout)
    if len(bolt_xs) >= 2:
        _add_linear_dim(msp, pt(bolt_xs[0], data.beam_d / 2.0 + data.plate_t), pt(bolt_xs[1], data.beam_d / 2.0 + data.plate_t), pt(bolt_xs[0], data.beam_d / 2.0 + data.plate_t + 110.0), 0, doc)
    if bolt_xs:
        _add_linear_dim(msp, pt(layout.col_face_x, data.beam_d / 2.0 + data.plate_t), pt(bolt_xs[-1], data.beam_d / 2.0 + data.plate_t), pt(layout.col_face_x, data.beam_d / 2.0 + data.plate_t + 155.0), 0, doc)

    _add_text(msp, "SIDE VIEW", ox, y_shift + data.beam_d / 2.0 + 210.0, height=22.0)
    add_general_note(msp, ox, y_shift - layout.col_h / 2.0 - 60.0)
    return (layout.beam_start_x + layout.beam_len - x_min + 300.0), (layout.col_h + 360.0)


def draw_front_view(msp: Modelspace, connection, doc: ezdxf.EzDxfDocument, origin=(0.0, 0.0)) -> tuple[float, float]:
    data = _extract_data(connection)
    layout = _compute_layout(data)
    ox, oy = origin
    gap_y = 120.0
    top_y0 = oy + data.plate_w + gap_y + 140.0
    bot_y0 = oy + 140.0

    _rect(msp, ox, top_y0, data.plate_l, data.plate_w, LAYER_FRONT)
    _rect(msp, ox, bot_y0, data.plate_l, data.plate_w, LAYER_FRONT)
    _line(msp, (ox, top_y0 + data.plate_w / 2.0), (ox + data.plate_l + 100.0, top_y0 + data.plate_w / 2.0), LAYER_FRONT)
    _line(msp, (ox, bot_y0 + data.plate_w / 2.0), (ox + data.plate_l + 100.0, bot_y0 + data.plate_w / 2.0), LAYER_FRONT)

    r_std = data.bolt_df / 2.0
    r_ovr = r_std * 1.15
    bolt_xs = [x - layout.beam_start_x for x in _flange_bolt_x_positions(data, layout)]
    bolt_ys = _front_flange_bolt_y_positions(data)
    for base_y in (top_y0, bot_y0):
        for x in bolt_xs:
            for y in bolt_ys:
                _circle(msp, ox + x, base_y + y, r_ovr, LAYER_BOLT)
                _circle(msp, ox + x, base_y + y, r_std, LAYER_FRONT)

    if data.web_plate_h and data.web_plate_t:
        wp_x = ox - 220.0
        wp_y = oy + 210.0
        _rect(msp, wp_x, wp_y, data.web_plate_t, data.web_plate_h, LAYER_FRONT)
        for _, bz in _web_bolt_positions(data):
            _circle(msp, wp_x + data.web_plate_t / 2.0, wp_y + bz, (data.web_bolt_df or 16.0) / 2.0, LAYER_BOLT)

    _add_linear_dim(msp, (ox, top_y0 + data.plate_w), (ox + data.plate_l, top_y0 + data.plate_w), (ox, top_y0 + data.plate_w + 60.0), 0, doc)
    _add_linear_dim(msp, (ox, top_y0), (ox, top_y0 + data.plate_w), (ox - 70.0, top_y0), 90, doc)
    _add_linear_dim(msp, (ox, bot_y0), (ox, bot_y0 + data.plate_w), (ox - 70.0, bot_y0), 90, doc)
    if bolt_xs:
        _add_linear_dim(msp, (ox, top_y0 + data.plate_w), (ox + bolt_xs[0], top_y0 + data.plate_w), (ox, top_y0 + data.plate_w + 100.0), 0, doc)
    if len(bolt_xs) >= 2:
        _add_linear_dim(msp, (ox + bolt_xs[0], top_y0 + data.plate_w), (ox + bolt_xs[1], top_y0 + data.plate_w), (ox + bolt_xs[0], top_y0 + data.plate_w + 145.0), 0, doc)
    if len(bolt_ys) >= 2:
        _add_linear_dim(msp, (ox + data.plate_l, top_y0 + bolt_ys[0]), (ox + data.plate_l, top_y0 + bolt_ys[1]), (ox + data.plate_l + 70.0, top_y0 + bolt_ys[0]), 90, doc)

    _add_text(msp, "FRONT VIEW", ox, top_y0 + data.plate_w + 175.0, height=22.0)
    _add_text(msp, "N1 BOLTS – OVERSIZE HOLES ON CONNECTION PLATE", ox, top_y0 + data.plate_w + 150.0, height=12.0)
    _add_text(msp, "STANDARD HOLES ON GIRDER FLANGE", ox, top_y0 + data.plate_w + 132.0, height=12.0)
    add_general_note(msp, ox, oy + 45.0)
    return data.plate_l + 360.0, top_y0 + data.plate_w - oy + 240.0


def _iso_project(x: float, y: float, z: float) -> tuple[float, float]:
    az = math.radians(45.0)
    el = math.radians(35.26438968)
    u = math.cos(az) * x - math.sin(az) * y
    v = math.sin(el) * math.sin(az) * x + math.sin(el) * math.cos(az) * y + math.cos(el) * z
    return u, v


def _box_vertices(origin, size):
    x, y, z = origin
    dx, dy, dz = size
    return [
        (x, y, z),
        (x + dx, y, z),
        (x + dx, y + dy, z),
        (x, y + dy, z),
        (x, y, z + dz),
        (x + dx, y, z + dz),
        (x + dx, y + dy, z + dz),
        (x, y + dy, z + dz),
    ]


def _visible_box_edges():
    return {
        (0, 1), (1, 5), (5, 4), (4, 0),
        (1, 2), (2, 6), (6, 5),
        (4, 5), (5, 6), (6, 7), (7, 4),
    }


def _draw_box_iso(msp: Modelspace, origin, size, offset, color: int) -> None:
    ox, oy = offset
    pts = _box_vertices(origin, size)
    for a, b in _visible_box_edges():
        u1, v1 = _iso_project(*pts[a])
        u2, v2 = _iso_project(*pts[b])
        _line(msp, (ox + u1, oy + v1), (ox + u2, oy + v2), LAYER_3D, color=color)


def _draw_tri_prism_iso(msp: Modelspace, tri_a, tri_b, offset, color: int) -> None:
    ox, oy = offset
    points = tri_a + tri_b
    for a, b in [(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3), (0, 3), (1, 4), (2, 5)]:
        u1, v1 = _iso_project(*points[a])
        u2, v2 = _iso_project(*points[b])
        _line(msp, (ox + u1, oy + v1), (ox + u2, oy + v2), LAYER_3D, color=color)


def draw_3d_isometric(msp: Modelspace, connection, origin=(0.0, 0.0)) -> tuple[float, float]:
    data = _extract_data(connection)
    layout = _compute_layout(data)
    ox, oy = origin
    c_beam = _rgb(72, 149, 239)
    c_col = _rgb(38, 70, 83)
    c_plate = _rgb(244, 162, 97)
    c_bolt = _rgb(43, 45, 66)
    c_weld = _rgb(231, 111, 81)

    _draw_box_iso(msp, (-data.col_d / 2.0, -data.col_bf / 2.0, -layout.col_h / 2.0), (data.col_tf, data.col_bf, layout.col_h), (ox, oy), c_col)
    _draw_box_iso(msp, (data.col_d / 2.0 - data.col_tf, -data.col_bf / 2.0, -layout.col_h / 2.0), (data.col_tf, data.col_bf, layout.col_h), (ox, oy), c_col)
    _draw_box_iso(msp, (-data.col_d / 2.0 + data.col_tf, -data.col_tw / 2.0, -layout.col_h / 2.0), (data.col_d - 2.0 * data.col_tf, data.col_tw, layout.col_h), (ox, oy), c_col)

    _draw_box_iso(msp, (layout.beam_start_x, -data.beam_bf / 2.0, data.beam_d / 2.0 - data.beam_tf), (layout.beam_len, data.beam_bf, data.beam_tf), (ox, oy), c_beam)
    _draw_box_iso(msp, (layout.beam_start_x, -data.beam_bf / 2.0, -data.beam_d / 2.0), (layout.beam_len, data.beam_bf, data.beam_tf), (ox, oy), c_beam)
    _draw_box_iso(msp, (layout.beam_start_x, -data.beam_tw / 2.0, -data.beam_d / 2.0 + data.beam_tf), (layout.beam_len, data.beam_tw, data.beam_d - 2.0 * data.beam_tf), (ox, oy), c_beam)

    _draw_box_iso(msp, (layout.beam_start_x, -data.plate_w / 2.0, data.beam_d / 2.0), (data.plate_l, data.plate_w, data.plate_t), (ox, oy), c_plate)
    _draw_box_iso(msp, (layout.beam_start_x, -data.plate_w / 2.0, -data.beam_d / 2.0 - data.plate_t), (data.plate_l, data.plate_w, data.plate_t), (ox, oy), c_plate)

    top_tri_a = [
        (layout.col_face_x, -data.plate_w / 2.0, data.beam_d / 2.0),
        (layout.beam_start_x, -data.plate_w / 2.0, data.beam_d / 2.0),
        (layout.beam_start_x, -data.plate_w / 2.0, data.beam_d / 2.0 + data.plate_t),
    ]
    top_tri_b = [(x, data.plate_w / 2.0, z) for x, _, z in top_tri_a]
    _draw_tri_prism_iso(msp, top_tri_a, top_tri_b, (ox, oy), c_plate)

    bot_tri_a = [
        (layout.col_face_x, -data.plate_w / 2.0, -data.beam_d / 2.0),
        (layout.beam_start_x, -data.plate_w / 2.0, -data.beam_d / 2.0),
        (layout.beam_start_x, -data.plate_w / 2.0, -data.beam_d / 2.0 - data.plate_t),
    ]
    bot_tri_b = [(x, data.plate_w / 2.0, z) for x, _, z in bot_tri_a]
    _draw_tri_prism_iso(msp, bot_tri_a, bot_tri_b, (ox, oy), c_plate)

    _draw_tri_prism_iso(msp, [
        (layout.col_face_x, -data.plate_w / 2.0, data.beam_d / 2.0),
        (layout.col_face_x, -data.plate_w / 2.0, data.beam_d / 2.0 + data.plate_t),
        (layout.beam_start_x, -data.plate_w / 2.0, data.beam_d / 2.0 + data.plate_t),
    ], [(x, data.plate_w / 2.0, z) for x, _, z in [
        (layout.col_face_x, -data.plate_w / 2.0, data.beam_d / 2.0),
        (layout.col_face_x, -data.plate_w / 2.0, data.beam_d / 2.0 + data.plate_t),
        (layout.beam_start_x, -data.plate_w / 2.0, data.beam_d / 2.0 + data.plate_t),
    ]], (ox, oy), c_weld)
    _draw_tri_prism_iso(msp, [
        (layout.col_face_x, -data.plate_w / 2.0, -data.beam_d / 2.0),
        (layout.col_face_x, -data.plate_w / 2.0, -data.beam_d / 2.0 - data.plate_t),
        (layout.beam_start_x, -data.plate_w / 2.0, -data.beam_d / 2.0 - data.plate_t),
    ], [(x, data.plate_w / 2.0, z) for x, _, z in [
        (layout.col_face_x, -data.plate_w / 2.0, -data.beam_d / 2.0),
        (layout.col_face_x, -data.plate_w / 2.0, -data.beam_d / 2.0 - data.plate_t),
        (layout.beam_start_x, -data.plate_w / 2.0, -data.beam_d / 2.0 - data.plate_t),
    ]], (ox, oy), c_weld)

    if data.web_plate_l and data.web_plate_h and data.web_plate_t:
        _draw_box_iso(msp, (layout.web_plate_x, data.beam_tw / 2.0, -data.web_plate_h / 2.0), (data.web_plate_l, data.web_plate_t, data.web_plate_h), (ox, oy), c_plate)

    for bx in _flange_bolt_x_positions(data, layout):
        for by in _flange_bolt_y_positions(data):
            for bz in (data.beam_d / 2.0 + data.plate_t / 2.0, -data.beam_d / 2.0 - data.plate_t / 2.0):
                u, v = _iso_project(bx, by, bz)
                _circle(msp, ox + u, oy + v, max(data.bolt_df * 0.22, 2.5), LAYER_BOLT, color=c_bolt)

    if data.web_plate_l and data.web_plate_h and data.web_bolt_df:
        for bx, bz in _web_bolt_positions(data):
            u, v = _iso_project(layout.web_plate_x + bx, data.beam_tw / 2.0 + (data.web_plate_t or 0.0) / 2.0, -data.web_plate_h / 2.0 + bz)
            _circle(msp, ox + u, oy + v, max(data.web_bolt_df * 0.22, 2.5), LAYER_BOLT, color=c_bolt)

    _add_text(msp, "3D ISOMETRIC VIEW", ox, oy + layout.col_h * 0.95, height=22.0)
    add_general_note(msp, ox, oy - 50.0)
    return layout.beam_start_x + layout.beam_len + data.col_d + 280.0, layout.col_h + 260.0


def flange_spacing_warning(connection) -> str | None:
    data = _extract_data(connection)
    layout = _compute_layout(data)
    if data.bolt_ng <= 1:
        return None
    min_spacing = 2.5 * data.bolt_df
    if layout.flange_spacing < min_spacing:
        return (
            f"FLANGE BOLT SPACING {layout.flange_spacing:.1f} IS LESS THAN "
            f"RECOMMENDED MINIMUM {min_spacing:.1f}."
        )
    return None


def generate_autocad_drawing(connection, output_path: str | Path = "bfp_connection.dxf") -> Path:
    """
    Generate AutoCAD DXF file with side view, front view, and 3D isometric view.

    Parameters
    ----------
    connection : BFPConnection object
    output_path : str or Path
    """
    output_path = Path(output_path)
    doc = _new_document()
    _setup_layers(doc)
    msp = doc.modelspace()

    side_w, side_h = draw_side_view(msp, connection, doc, origin=(0.0, 0.0))
    front_w, front_h = draw_front_view(msp, connection, doc, origin=(side_w + 250.0, 0.0))
    draw_3d_isometric(msp, connection, origin=(0.0, max(side_h, front_h) + 280.0))

    warning = flange_spacing_warning(connection)
    if warning:
        _add_text(msp, f"WARNING: {warning}", 0.0, max(side_h, front_h) + 210.0, height=16.0, layer=LAYER_TEXT)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(output_path)
    return output_path
