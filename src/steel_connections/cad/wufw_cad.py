from __future__ import annotations


def build_wufw_shapes(connection) -> dict:
    """Return placeholder CAD primitives for a WUF-W connection preview."""

    return {
        "beam": None,
        "column": None,
        "shear_plate": None,
        "access_holes": [],
        "continuity_plates": [],
        "doubler_plates": [],
    }
