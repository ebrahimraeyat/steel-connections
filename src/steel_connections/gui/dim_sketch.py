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
    """3-D beam: I cross-section on right face, extruding left."""
    def __init__(self, p=None): super().__init__(200, 150, p)
    def _paint(self, p, r):
        W, H = r.width(), r.height()
        EX = int(W*0.32); EY = int(H*0.20)
        cx = int(W*0.74); cy = int(H*0.56)
        bfw = int(min(W,H)*0.50); totd = int(H*0.72)
        pts = _isec_pts(cx, cy, bfw, totd)

        # ghost column (faded vertical rect)
        cw = int(bfw*0.55)
        p.setPen(QPen(_C_GHED,1,Qt.DashLine)); p.setBrush(QBrush(_C_GHOST))
        p.drawRect(int(W*0.02), int(cy-totd//2), cw, totd)

        # extrusion top-faces
        _fill(p,_C_TOP,pts[0],pts[1],(pts[1][0]-EX,pts[1][1]-EY),(pts[0][0]-EX,pts[0][1]-EY))
        _stroke(p,_C_EDGE,0.6,pts[0],pts[1],(pts[1][0]-EX,pts[1][1]-EY),(pts[0][0]-EX,pts[0][1]-EY))
        _fill(p,_C_TOP,pts[3],pts[4],(pts[4][0]-EX,pts[4][1]-EY),(pts[3][0]-EX,pts[3][1]-EY))
        _fill(p,_C_TOP,pts[5],pts[6],(pts[6][0]-EX,pts[6][1]-EY),(pts[5][0]-EX,pts[5][1]-EY))
        ext = QColor(90,120,180,80)
        bp = [(x-EX,y-EY) for x,y in pts]
        for i in range(12): _line(p,ext,0.8,bp[i][0],bp[i][1],bp[(i+1)%12][0],bp[(i+1)%12][1])

        # front face
        _fill(p,_C_FACE,*pts); _stroke(p,_C_EDGE,1.4,*pts)

        # dim arrows
        ty0 = cy-totd//2-10
        p.setPen(QPen(_C_DIM,0.8,Qt.DashLine))
        p.drawLine(QPointF(cx-bfw//2,cy-totd//2),QPointF(cx-bfw//2,ty0))
        p.drawLine(QPointF(cx+bfw//2,cy-totd//2),QPointF(cx+bfw//2,ty0))
        _arrow(p,cx-bfw//2,ty0,cx+bfw//2,ty0)
        rx = cx+bfw//2+10
        p.setPen(QPen(_C_DIM,0.8,Qt.DashLine))
        p.drawLine(QPointF(cx+bfw//2,cy-totd//2),QPointF(rx,cy-totd//2))
        p.drawLine(QPointF(cx+bfw//2,cy+totd//2),QPointF(rx,cy+totd//2))
        _arrow(p,rx,cy-totd//2,rx,cy+totd//2)


class ColumnCanvas(_Canvas):
    """3-D column: I cross-section on front face, extruding up-right."""
    def __init__(self, p=None): super().__init__(200, 150, p)
    def _paint(self, p, r):
        W, H = r.width(), r.height()
        EX = int(W*0.22); EY = -int(H*0.28)
        cx = int(W*0.32); cy = int(H*0.60)
        bfw = int(min(W,H)*0.50); totd = int(H*0.72)
        pts = _isec_pts(cx, cy, bfw, totd)

        # ghost beam (faded horizontal rect)
        gh = int(totd*0.25)
        p.setPen(QPen(_C_GHED,1,Qt.DashLine)); p.setBrush(QBrush(_C_GHOST))
        p.drawRect(int(cx-bfw//2), int(cy-gh//2), W-(cx-bfw//2)+5, gh)

        # extrusion
        _fill(p,_C_TOP,pts[0],pts[1],(pts[1][0]+EX,pts[1][1]+EY),(pts[0][0]+EX,pts[0][1]+EY))
        _stroke(p,_C_EDGE,0.6,pts[0],pts[1],(pts[1][0]+EX,pts[1][1]+EY),(pts[0][0]+EX,pts[0][1]+EY))
        _fill(p,_C_DARK,pts[1],(pts[1][0]+EX,pts[1][1]+EY),(pts[6][0]+EX,pts[6][1]+EY),pts[6])
        _fill(p,_C_TOP,pts[3],pts[4],(pts[4][0]+EX,pts[4][1]+EY),(pts[3][0]+EX,pts[3][1]+EY))
        ext = QColor(90,120,180,80)
        bp = [(x+EX,y+EY) for x,y in pts]
        for i in range(12): _line(p,ext,0.8,bp[i][0],bp[i][1],bp[(i+1)%12][0],bp[(i+1)%12][1])

        _fill(p,_C_FACE,*pts); _stroke(p,_C_EDGE,1.4,*pts)

        ty0 = cy-totd//2-10
        p.setPen(QPen(_C_DIM,0.8,Qt.DashLine))
        p.drawLine(QPointF(cx-bfw//2,cy-totd//2),QPointF(cx-bfw//2,ty0))
        p.drawLine(QPointF(cx+bfw//2,cy-totd//2),QPointF(cx+bfw//2,ty0))
        _arrow(p,cx-bfw//2,ty0,cx+bfw//2,ty0)
        rx = cx+bfw//2+10
        p.setPen(QPen(_C_DIM,0.8,Qt.DashLine))
        p.drawLine(QPointF(cx+bfw//2,cy-totd//2),QPointF(rx,cy-totd//2))
        p.drawLine(QPointF(cx+bfw//2,cy+totd//2),QPointF(rx,cy+totd//2))
        _arrow(p,rx,cy-totd//2,rx,cy+totd//2)


class FlangePlateCanvas(_Canvas):
    """Two horizontal flange plates (bold) with faded I-section."""
    def __init__(self, p=None): super().__init__(180, 130, p)
    def _paint(self, p, r):
        W, H = r.width(), r.height()
        EX = int(W*0.18); EY = int(H*0.12)
        bfw = int(W*0.52); totd = int(H*0.68)
        cx = int(W*0.44); cy = int(H*0.54)
        tf = max(totd*0.14,4)

        ghost = _isec_pts(cx,cy,bfw,totd)
        _fill(p,_C_GHOST,*ghost); _stroke(p,_C_GHED,0.8,*ghost)

        pw = int(bfw*1.05); ph = int(totd*0.20)
        px = cx-pw//2

        for py in [cy-totd//2-ph, cy+totd//2]:
            _fill(p,_C_P_TOP,(px,py),(px+pw,py),(px+pw+EX,py-EY),(px+EX,py-EY))
            _fill(p,_C_P_DARK,(px+pw,py),(px+pw+EX,py-EY),(px+pw+EX,py+ph-EY),(px+pw,py+ph))
            _fill(p,_C_P_FACE,(px,py),(px+pw,py),(px+pw,py+ph),(px,py+ph))
            _stroke(p,_C_P_EDGE,1.2,(px,py),(px+pw,py),(px+pw,py+ph),(px,py+ph))

        # dim: width across top plate
        tp = cy-totd//2-ph
        gy = tp-8
        p.setPen(QPen(_C_DIM,0.8,Qt.DashLine))
        p.drawLine(QPointF(px,tp),QPointF(px,gy))
        p.drawLine(QPointF(px+pw,tp),QPointF(px+pw,gy))
        _arrow(p,px,gy,px+pw,gy)
        # dim: height (h) right side
        rx = px+pw+EX+4
        p.setPen(QPen(_C_DIM,0.8,Qt.DashLine))
        p.drawLine(QPointF(px+pw,tp),QPointF(rx,tp))
        p.drawLine(QPointF(px+pw,tp+ph),QPointF(rx,tp+ph))
        _arrow(p,rx,tp,rx,tp+ph)


class WebPlateCanvas(_Canvas):
    """Single vertical web plate (bold) with faded I-section."""
    def __init__(self, p=None): super().__init__(180, 130, p)
    def _paint(self, p, r):
        W, H = r.width(), r.height()
        EX = int(W*0.18); EY = int(H*0.12)
        bfw = int(W*0.52); totd = int(H*0.72)
        cx = int(W*0.44); cy = int(H*0.52)
        tf = max(totd*0.14,4); tw = max(bfw*0.16,4)

        ghost = _isec_pts(cx,cy,bfw,totd)
        _fill(p,_C_GHOST,*ghost); _stroke(p,_C_GHED,0.8,*ghost)

        pw = int(tw*2.8); ph = int((totd-2*tf)*0.85)
        px = cx-pw//2; py = cy-ph//2

        _fill(p,_C_P_TOP,(px,py),(px+pw,py),(px+pw+EX,py-EY),(px+EX,py-EY))
        _fill(p,_C_P_DARK,(px+pw,py),(px+pw+EX,py-EY),(px+pw+EX,py+ph-EY),(px+pw,py+ph))
        _fill(p,_C_P_FACE,(px,py),(px+pw,py),(px+pw,py+ph),(px,py+ph))
        _stroke(p,_C_P_EDGE,1.2,(px,py),(px+pw,py),(px+pw,py+ph),(px,py+ph))

        # dim: b (horizontal = width)
        gy = py-8
        p.setPen(QPen(_C_DIM,0.8,Qt.DashLine))
        p.drawLine(QPointF(px,py),QPointF(px,gy))
        p.drawLine(QPointF(px+pw,py),QPointF(px+pw,gy))
        _arrow(p,px,gy,px+pw,gy)
        # dim: h (vertical = height/length)
        rx = px+pw+EX+4
        p.setPen(QPen(_C_DIM,0.8,Qt.DashLine))
        p.drawLine(QPointF(px+pw,py),QPointF(rx,py))
        p.drawLine(QPointF(px+pw,py+ph),QPointF(rx,py+ph))
        _arrow(p,rx,py,rx,py+ph)


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