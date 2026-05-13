# -*- coding: utf-8 -*-
"""
Embedded OCC 3D viewer widget for PyQt5.

Init strategy
-------------
* qtViewer3d is created in __init__ and added to the layout immediately so
  Qt accounts for it when computing the window geometry.
* InitDriver() is called inside the first resizeEvent that reports a real
  size (> 50 px). At that moment the native window handle is valid and OCC
  receives the correct viewport dimensions.
* Every subsequent resizeEvent calls View.MustBeResized() to keep OCC in sync.
* The very first display_shapes call ends with FitAll(); all later calls
  preserve the camera so the user's zoom/pan is not reset.
"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PySide6.QtCore import QTimer

from OCC.Display import backend as _occ_backend
_occ_backend.load_backend("pyside6")

from OCC.Display.qtDisplay import qtViewer3d
from OCC.Core.AIS import AIS_Shape
from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCC.Core.V3d import V3d_TypeOfOrientation
from OCC.Core.Aspect import Aspect_GFM_VER


class Viewer3D(QWidget):

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(200, 200)

        self._ready    = False
        self._need_fit = True
        self._queued: list[AIS_Shape] | None = None

        self._occ = qtViewer3d(self)
        self._occ.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._occ)

    # ── resize: init on first real size, then keep OCC in sync ───────────────

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w, h = event.size().width(), event.size().height()
        if not self._ready:
            if w > 50 and h > 50:
                self._init_occ()
        else:
            try:
                self._occ._display.View.MustBeResized()
            except Exception:
                pass

    # ── one-time OCC initialisation ───────────────────────────────────────────

    def _init_occ(self) -> None:
        if self._ready:
            return
        self._occ.InitDriver()
        self._ready = True

        disp = self._occ._display
        top    = Quantity_Color(0.13, 0.16, 0.22, Quantity_TOC_RGB)   # dark navy
        bottom = Quantity_Color(0.05, 0.06, 0.10, Quantity_TOC_RGB)   # near-black
        disp.View.SetBgGradientColors(top, bottom, Aspect_GFM_VER, True)
        disp.View.SetProj(V3d_TypeOfOrientation.V3d_XposYnegZpos)  # isometric default
        disp.View.MustBeResized()
        try:
            disp.DisableAntiAliasing()   # faster redraws (Osdag pattern)
        except Exception:
            pass
        try:
            disp.display_triedron()   # show X/Y/Z axis indicator in corner
        except Exception:
            pass

        if self._queued is not None:
            shapes, self._queued = self._queued, None
            QTimer.singleShot(50, lambda: self._do_display(shapes, fit=True))

    # ── public API ────────────────────────────────────────────────────────────

    def display_shapes(self, shapes: list[AIS_Shape]) -> None:
        if not self._ready:
            self._queued = shapes
            return
        fit = self._need_fit
        self._need_fit = False
        self._do_display(shapes, fit=fit)

    def _do_display(self, shapes: list[AIS_Shape], fit: bool = False) -> None:
        if not self._ready:
            return
        disp = self._occ._display
        ctx  = disp.Context
        ctx.RemoveAll(False)
        for ais in shapes:
            ais.SetDisplayMode(1)
            ctx.Display(ais, False)
        ctx.UpdateCurrentViewer()
        if fit:
            disp.View.MustBeResized()
            disp.FitAll()

    # ── camera controls ───────────────────────────────────────────────────────

    def fit_all(self) -> None:
        if self._ready:
            self._occ._display.FitAll()

    def set_view_iso(self) -> None:
        if self._ready:
            self._occ._display.View.SetProj(V3d_TypeOfOrientation.V3d_XposYnegZpos)
            self.fit_all()

    def set_view_front(self) -> None:
        """Look from +X toward -X → sees beam end cross-section (روبرو)."""
        if self._ready:
            self._occ._display.View.SetProj(V3d_TypeOfOrientation.V3d_Xpos)
            self.fit_all()

    def set_view_side(self) -> None:
        """Look from -Y → XZ plane → beam web visible (بغل)."""
        if self._ready:
            self._occ._display.View.SetProj(V3d_TypeOfOrientation.V3d_Yneg)
            self.fit_all()

    def set_view_top(self) -> None:
        """Look from +Z → XY plane → top flange visible (بالا)."""
        if self._ready:
            self._occ._display.View.SetProj(V3d_TypeOfOrientation.V3d_Zpos)
            self.fit_all()

    def set_display_mode(self, mode: int = 1) -> None:
        if self._ready:
            self._occ._display.Context.SetDisplayMode(mode, True)

    # ── image capture for reports ─────────────────────────────────────────────

    def capture_views(self, folder: str) -> dict[str, str]:
        """
        Capture 4 views (isometric, front, side, top) as PNG images into *folder*.
        Uses a temporary white background for readability in reports.
        Returns dict mapping view-name → absolute image path.
        """
        import os
        from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
        from OCC.Core.Aspect import Aspect_GFM_VER

        if not self._ready:
            return {}

        os.makedirs(folder, exist_ok=True)
        disp = self._occ._display
        view = disp.View

        # switch to white background for report images
        white = Quantity_Color(1.0, 1.0, 1.0, Quantity_TOC_RGB)
        view.SetBgGradientColors(white, white, Aspect_GFM_VER, True)
        view.MustBeResized()

        view_defs = [
            ("iso",   V3d_TypeOfOrientation.V3d_XposYnegZpos),
            ("front", V3d_TypeOfOrientation.V3d_Xpos),
            ("side",  V3d_TypeOfOrientation.V3d_Yneg),
            ("top",   V3d_TypeOfOrientation.V3d_Zpos),
        ]

        captured: dict[str, str] = {}
        for name, proj in view_defs:
            view.SetProj(proj)
            disp.FitAll()
            disp.Context.UpdateCurrentViewer()
            path = os.path.join(folder, f"view_{name}.png")
            try:
                view.Dump(path)
                if os.path.isfile(path) and os.path.getsize(path) > 0:
                    captured[name] = path
            except Exception:
                pass

        # restore dark gradient background
        top    = Quantity_Color(0.13, 0.16, 0.22, Quantity_TOC_RGB)
        bottom = Quantity_Color(0.05, 0.06, 0.10, Quantity_TOC_RGB)
        view.SetBgGradientColors(top, bottom, Aspect_GFM_VER, True)
        # restore to iso view
        view.SetProj(V3d_TypeOfOrientation.V3d_XposYnegZpos)
        disp.FitAll()

        return captured

