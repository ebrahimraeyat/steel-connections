from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WUFWMaterialDefaults:
    """Default material set for WUF-W designs (internal units: kgf/cm^2)."""

    fy_beam: float = 3515.0
    fu_beam: float = 4921.0
    fy_column: float = 3515.0
    fu_column: float = 4921.0
    fy_plate: float = 2530.0
    fu_plate: float = 4080.0
    fexx_weld: float = 4921.0
    ry: float = 1.1
    rt: float = 1.1


@dataclass(frozen=True)
class WUFWGeometryDefaults:
    """Initial sizing defaults for shear plate and weld detailing."""

    access_hole_offset_cm: float = 1.2
    shear_plate_overlap_cm: float = 0.8
    weld_termination_from_access_hole_min_cm: float = 1.2
    weld_termination_from_access_hole_max_cm: float = 2.5
