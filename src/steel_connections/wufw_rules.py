from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WUFWCodeRules:
    """WUF-W prequalification limits normalized to cm and kgf units."""

    beam_depth_min_cm: float = 30.48
    beam_depth_max_cm: float = 91.44
    beam_weight_max_kg_per_m: float = 223.2
    beam_tf_max_cm: float = 2.54
    beam_tw_min_cm: float = 0.508
    beam_b_over_2tf_max: float = 35.0
    column_depth_max_cm: float = 91.44
    shear_plate_height_db_ratio_min: float = 2.0 / 3.0
    shear_plate_width_bf_ratio_min: float = 0.5
    shear_plate_overlap_min_cm: float = 0.6
    shear_plate_overlap_max_cm: float = 1.2
    shear_plate_extra_beyond_hole_min_cm: float = 5.0
    continuity_plate_trigger_factor: float = 0.4
    access_hole_length_min_cm: float = 3.0
    access_hole_height_min_cm: float = 1.2


@dataclass(frozen=True)
class WUFWResistanceFactors:
    """LRFD resistance factors used by WUF-W checks."""

    phi_ductile: float = 0.9
    phi_non_ductile: float = 0.75
    phi_cjp: float = 0.9
