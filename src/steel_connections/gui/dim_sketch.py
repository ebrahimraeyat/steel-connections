# -*- coding: utf-8 -*-
"""
dim_sketch.py -- 3-D perspective sketches for I-section beam/column and plates.
"""
from __future__ import annotations
import math

from PySide6.QtCore import Qt, QPointF, QSize
from PySide6.QtGui import (
    QPainter, QPen, QColor, QBrush, QPainterPath, QPolygonF,
)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QFrame,
)

_C_FACE  = QColor( 80, 120, 200)
_C_TOP   = QColor(110, 150, 230, 160)
_C_DARK  = QColor( 50,  80, 150, 180)
_C_EDGE  = QColor( 30,  60, 130)
_C_DIM   = QColor(180, 180, 180)
_C_GHOST = QColor(140, 180, 230,  55)
_C_GHED  = QColor(100, 140, 200, 100)

_C_P_FACE = QColor( 50, 160,  90)
_C_P_TOP  = QColor( 80, 190, 110, 160)
_C_P_DARK = QColor( 30, 110,  60, 180)
_C_P_EDGE = QColor( 20,  90,  40)
_C_P_GHOST= QColor(140, 200, 150,  55)
_C_P_GHED = QColor( 80, 160, 100, 110)


def _lbl(t):
    l = QLabel(t); l.setAlignment(Qt.AlignCenter)
    l.setStyleSheet("color:#aaa;font-size:10px;padding:0;"); return l


def _poly(*pts):
    return QPolygonF([QPointF(x, y) for x, y in pts])


def _fill(p, color, *pts):
    p.setBrush(QBrush(color)); p.setPen(Qt.NoPen)
    p.drawPolygon(_poly(*pts))


def _stroke(p, color, w, *pts):
    pen = QPen(color, w); pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen); p.setBrush(Qt.NoBrush); p.drawPolygon(_poly(*pts))


def _line(p, color, w, x1, y1, x2, y2):
    p.setPen(QPen(color, w)); p.setBrush(Qt.NoBrush)
    p.drawLine(QPointF(x1, y1), QPointF(x2, y2))


def _arrow(p, x1, y1, x2, y2, color=_C_DIM):
    dx, dy = x2-x1, y2-y1; L = math.hypot(dx, dy)
    if L < 2: return
    ux, uy = dx/L, dy/L
    p.setPen(QPen(color, 1)); p.setBrush(QBrush(color))
    p.drawLine(QPointF(x1,y1), QPointF(x2,y2))
    hl = 6; hw = 2.5
    for bx, by, sgn in [(x1, y1, 1), (x2, y2, -1)]:
        tx = bx + sgn*ux*hl; ty = by + sgn*uy*hl
        lx = tx - sgn*ux*hl + uy*hw; ly = ty - sgn*uy*hl - ux*hw
        rx = tx - sgn*ux*hl - uy*hw; ry = ty - sgn*uy*hl + ux*hw
        path = QPainterPath()
        path.moveTo(tx,ty); path.lineTo(lx,ly); path.lineTo(rx,ry)
        path.closeSubpath(); p.drawPath(path)


def _isec_pts(cx, cy, bfw, totd):
    hw = bfw/2; hd = totd/2
    tf = max(totd*0.14, 4); tw = max(bfw*0.16, 3); htw = tw/2
    pts = [
        (-hw,-hd),(hw,-hd),(hw,-hd+tf),(htw,-hd+tf),
        (htw,hd-tf),(hw,hd-tf),(hw,hd),(-hw,hd),
        (-hw,hd-tf),(-htw,hd-tf),(-htw,-hd+tf),(-hw,-hd+tf),
    ]
    return [(cx+x, cy+y) for x,y in pts]


class _Canvas(QWidget):
    def __init__(self, w=200, h=150, parent=None):
        super().__init__(parent); self._hint = QSize(w, h)
        self.setMinimumSize(120, 90)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    def sizeHint(self): return self._hint
    def paintEvent(self, ev):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        self._paint(p, self.rect()); p.end()
    def _paint(self, p, r): pass


class BeamCanvas(_Canvas):
    """2-D beam I cross-section (front view)."""
    def __init__(self, p=None): super().__init__(200, 150, p)
    def _paint(self, p, r):
        W, H = r.width(), r.height()
        cx = int(W*0.50); cy = int(H*0.50)
        bfw = int(min(W,H)*0.45); totd = int(H*0.65)
        pts = _isec_pts(cx, cy, bfw, totd)

        # Draw I-beam cross-section (2D only, no extrusion)
        _fill(p, _C_FACE, *pts)
        _stroke(p, _C_EDGE, 1.5, *pts)

        # Dimension arrows
        ty0 = cy - totd//2 - 12
        p.setPen(QPen(_C_DIM, 0.8, Qt.DashLine))
        p.drawLine(QPointF(cx - bfw//2, cy - totd//2), QPointF(cx - bfw//2, ty0))
        p.drawLine(QPointF(cx + bfw//2, cy - totd//2), QPointF(cx + bfw//2, ty0))
        _arrow(p, cx - bfw//2, ty0, cx + bfw//2, ty0)
        
        rx = cx + bfw//2 + 12
        p.setPen(QPen(_C_DIM, 0.8, Qt.DashLine))
        p.drawLine(QPointF(cx + bfw//2, cy - totd//2), QPointF(rx, cy - totd//2))
        p.drawLine(QPointF(cx + bfw//2, cy + totd//2), QPointF(rx, cy + totd//2))
        _arrow(p, rx, cy - totd//2, rx, cy + totd//2)


class ColumnCanvas(_Canvas):
    """2-D column I cross-section (front view)."""
    def __init__(self, p=None): super().__init__(200, 150, p)
    def _paint(self, p, r):
        W, H = r.width(), r.height()
        cx = int(W*0.50); cy = int(H*0.50)
        bfw = int(min(W,H)*0.45); totd = int(H*0.65)
        pts = _isec_pts(cx, cy, bfw, totd)

        # Draw I-column cross-section (2D only, no extrusion)
        _fill(p, _C_FACE, *pts)
        _stroke(p, _C_EDGE, 1.5, *pts)

        # Dimension arrows
        ty0 = cy - totd//2 - 12
        p.setPen(QPen(_C_DIM, 0.8, Qt.DashLine))
        p.drawLine(QPointF(cx - bfw//2, cy - totd//2), QPointF(cx - bfw//2, ty0))
        p.drawLine(QPointF(cx + bfw//2, cy - totd//2), QPointF(cx + bfw//2, ty0))
        _arrow(p, cx - bfw//2, ty0, cx + bfw//2, ty0)
        
        rx = cx + bfw//2 + 12
        p.setPen(QPen(_C_DIM, 0.8, Qt.DashLine))
        p.drawLine(QPointF(cx + bfw//2, cy - totd//2), QPointF(rx, cy - totd//2))
        p.drawLine(QPointF(cx + bfw//2, cy + totd//2), QPointF(rx, cy + totd//2))
        _arrow(p, rx, cy - totd//2, rx, cy + totd//2)


class FlangePlateCanvas(_Canvas):
    """2-D flange plates (top view) - only plates, no I-section background."""
    def __init__(self, p=None): super().__init__(180, 130, p)
    def _paint(self, p, r):
        W, H = r.width(), r.height()
        bfw = int(W*0.52); totd = int(H*0.68)
        cx = int(W*0.50); cy = int(H*0.50)
        
        pw = int(bfw*1.05); ph = int(totd*0.20)
        px = cx - pw//2

        # Draw top and bottom flange plates (2D view from above)
        for py in [cy - totd//2, cy + totd//2]:
            _fill(p, _C_P_FACE, (px, py), (px + pw, py), (px + pw, py + ph), (px, py + ph))
            _stroke(p, _C_P_EDGE, 1.2, (px, py), (px + pw, py), (px + pw, py + ph), (px, py + ph))

        # Dimension: width
        tp = cy - totd//2 - 8
        p.setPen(QPen(_C_DIM, 0.8, Qt.DashLine))
        p.drawLine(QPointF(px, py), QPointF(px, tp))
        p.drawLine(QPointF(px + pw, py), QPointF(px + pw, tp))
        _arrow(p, px, tp, px + pw, tp)
        
        # Dimension: plate length (height between plates)
        rx = px + pw + 8
        p.setPen(QPen(_C_DIM, 0.8, Qt.DashLine))
        p.drawLine(QPointF(px + pw, cy - totd//2), QPointF(rx, cy - totd//2))
        p.drawLine(QPointF(px + pw, cy + totd//2 + ph), QPointF(rx, cy + totd//2 + ph))
        _arrow(p, rx, cy - totd//2, rx, cy + totd//2 + ph)


class WebPlateCanvas(_Canvas):
    """2-D web plate (side view) with faded I-section schematic."""
    def __init__(self, p=None): super().__init__(180, 130, p)
    def _paint(self, p, r):
        W, H = r.width(), r.height()
        bfw = int(W*0.52); totd = int(H*0.72)
        cx = int(W*0.50); cy = int(H*0.52)
        tf = max(totd*0.14, 4); tw = max(bfw*0.16, 4)

        # Draw faded I-section schematic (beam outline - very light)
        ghost = _isec_pts(cx, cy, bfw, totd)
        p.setPen(QPen(_C_GHED, 0.5, Qt.DashLine))
        p.setBrush(QBrush(_C_GHOST))
        p.drawPolygon(_poly(*ghost))

        # Draw web plate (2D view from side)
        pw = int(tw*2.8); ph = int((totd - 2*tf)*0.90)
        px = cx - pw//2; py = cy - ph//2

        _fill(p, _C_P_FACE, (px, py), (px + pw, py), (px + pw, py + ph), (px, py + ph))
        _stroke(p, _C_P_EDGE, 1.2, (px, py), (px + pw, py), (px + pw, py + ph), (px, py + ph))

        # Dimension: width
        gy = py - 8
        p.setPen(QPen(_C_DIM, 0.8, Qt.DashLine))
        p.drawLine(QPointF(px, py), QPointF(px, gy))
        p.drawLine(QPointF(px + pw, py), QPointF(px + pw, gy))
        _arrow(p, px, gy, px + pw, gy)
        
        # Dimension: height
        rx = px + pw + 8
        p.setPen(QPen(_C_DIM, 0.8, Qt.DashLine))
        p.drawLine(QPointF(px + pw, py), QPointF(rx, py))
        p.drawLine(QPointF(px + pw, py + ph), QPointF(rx, py + ph))
        _arrow(p, rx, py, rx, py + ph)


def _sketchlayout(top_w, top_lbl, left_w, left_lbl, canvas, right_rows, bot_rows=None):
    """Generic 3-zone layout: top-arrow, left-arrow, canvas+right, bottom."""
    main = QVBoxLayout(); main.setSpacing(2); main.setContentsMargins(4,2,4,2)
    top = QHBoxLayout(); top.setSpacing(2)
    top.addWidget(_lbl("←"),0); top.addWidget(top_w,1); top.addWidget(_lbl(top_lbl),0)
    main.addLayout(top)
    mid = QHBoxLayout(); mid.setSpacing(4)
    lc = QVBoxLayout(); lc.setSpacing(1)
    lc.addWidget(_lbl("↑"),0); lc.addWidget(left_w,1); lc.addWidget(_lbl(left_lbl),0)
    mid.addLayout(lc,0); mid.addWidget(canvas,1)
    if right_rows:
        rc = QVBoxLayout(); rc.setSpacing(4)
        for label, widget in right_rows:
            row = QHBoxLayout(); row.setSpacing(2)
            row.addWidget(_lbl(label)); row.addWidget(widget)
            rc.addLayout(row)
            rc.addStretch()
        mid.addLayout(rc,0)
    main.addLayout(mid,1)
    if bot_rows:
        for label, widget in bot_rows:
            row = QHBoxLayout(); row.setSpacing(3)
            row.addWidget(_lbl(label)); row.addWidget(widget)
            main.addLayout(row)
    return main


class ISketchWidget(QFrame):
    def __init__(self, bf_w, d_w, tf_w, tw_w, is_column=False, parent=None):
        super().__init__(parent); self.setFrameShape(QFrame.NoFrame)
        cnv = ColumnCanvas() if is_column else BeamCanvas()
        lay = _sketchlayout(bf_w, "Bf →", d_w, "D ↓", cnv,
                             [("tf", tf_w), ("tw", tw_w)])
        self.setLayout(lay)


class FlangePlateSketchWidget(QFrame):
    def __init__(self, width_w, height_w, thickness_w, parent=None):
        super().__init__(parent); self.setFrameShape(QFrame.NoFrame)
        lay = _sketchlayout(width_w, "b →", height_w, "h ↓",
                             FlangePlateCanvas(), None,
                             [("t =", thickness_w)])
        self.setLayout(lay)


class WebPlateSketchWidget(QFrame):
    def __init__(self, width_w, height_w, thickness_w, parent=None):
        super().__init__(parent); self.setFrameShape(QFrame.NoFrame)
        lay = _sketchlayout(width_w, "b →", height_w, "h ↓",
                             WebPlateCanvas(), None,
                             [("t =", thickness_w)])
        self.setLayout(lay)


PlateSketchWidget = FlangePlateSketchWidget