from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

from steel_connections.design_result import DesignCheckResult
from steel_connections.wufw_rules import WUFWCodeRules, WUFWResistanceFactors


@dataclass
class WUFWDesignCalculator:
    """Design check calculator for AISC 358-16 Chapter 8 WUF-W connections."""

    rules: WUFWCodeRules
    phi: WUFWResistanceFactors

    @staticmethod
    def _check_ratio(numerator: float, denominator: float) -> float | None:
        if denominator == 0:
            return None
        return numerator / denominator

    def check_beam_limits(self, connection) -> DesignCheckResult:
        beam = connection.beam
        d_b = beam.geom.d
        t_f = beam.geom.t_f
        t_w = beam.geom.t_w
        b_f = beam.geom.b
        w_b = beam.weight_per_length
        h = max(d_b - 2.0 * t_f, 0.0)
        e = beam.mat.E
        fy = beam.mat.f_y

        flange_ratio = self._check_ratio(b_f, 2.0 * t_f)
        web_ratio = self._check_ratio(h, t_w)
        web_limit = 2.45 * sqrt(e / fy) if fy > 0 else None

        checks = [
            d_b >= self.rules.beam_depth_min_cm,
            d_b <= self.rules.beam_depth_max_cm,
            w_b <= self.rules.beam_weight_max_kg_per_m,
            t_f <= self.rules.beam_tf_max_cm,
            t_w >= self.rules.beam_tw_min_cm,
            (flange_ratio is not None) and (flange_ratio <= self.rules.beam_b_over_2tf_max),
            (web_ratio is not None) and (web_limit is not None) and (web_ratio <= web_limit),
        ]
        is_pass = all(checks)

        return DesignCheckResult(
            key="beam_limits",
            title="Beam Geometric Limits",
            is_pass=is_pass,
            ratio=max(
                [
                    (d_b / self.rules.beam_depth_max_cm),
                    (w_b / self.rules.beam_weight_max_kg_per_m),
                    (t_f / self.rules.beam_tf_max_cm),
                    (self.rules.beam_tw_min_cm / t_w) if t_w else 999.0,
                    (flange_ratio / self.rules.beam_b_over_2tf_max) if flange_ratio is not None else 999.0,
                    (web_ratio / web_limit) if (web_ratio is not None and web_limit) else 999.0,
                ]
            ),
            code_ref="AISC 358-16 8.3.1",
            message=(
                f"db={d_b:.3f} cm, W={w_b:.3f} kg/m, tf={t_f:.3f} cm, tw={t_w:.3f} cm, "
                f"bf/(2tf)={flange_ratio if flange_ratio is not None else 'n/a'}, "
                f"h/tw={web_ratio if web_ratio is not None else 'n/a'}"
            ),
        )

    def check_column_limits(self, connection) -> DesignCheckResult:
        d_c = connection.column.geom.d
        is_pass = d_c <= self.rules.column_depth_max_cm
        return DesignCheckResult(
            key="column_limits",
            title="Column Geometric Limits",
            is_pass=is_pass,
            ratio=d_c / self.rules.column_depth_max_cm,
            code_ref="AISC 358-16 8.3.2",
            message=f"dc={d_c:.3f} cm",
        )

    def check_access_hole_geometry(self, connection) -> DesignCheckResult:
        length_ok = connection.access_hole_length >= self.rules.access_hole_length_min_cm
        height_ok = connection.access_hole_height >= self.rules.access_hole_height_min_cm
        finish_ok = bool(connection.access_hole_surface_finish_ok)
        is_pass = length_ok and height_ok and finish_ok

        return DesignCheckResult(
            key="access_hole_geometry",
            title="Weld Access Hole Geometry",
            is_pass=is_pass,
            ratio=max(
                self.rules.access_hole_length_min_cm / connection.access_hole_length if connection.access_hole_length else 999.0,
                self.rules.access_hole_height_min_cm / connection.access_hole_height if connection.access_hole_height else 999.0,
                0.0 if finish_ok else 2.0,
            ),
            code_ref="AISC 360-16 J1.6 / AWS D1.8 6.11.1.2",
            message=(
                f"length={connection.access_hole_length:.3f} cm, "
                f"height={connection.access_hole_height:.3f} cm, "
                f"surface_finish_ok={finish_ok}"
            ),
        )

    def check_shear_plate_geometry(self, connection) -> DesignCheckResult:
        db = connection.beam.geom.d
        bf = connection.beam.geom.b
        tw = connection.beam.geom.t_w
        hp = connection.shear_plate_height
        bp = connection.shear_plate_width
        tp = connection.shear_plate_thickness
        overlap = connection.shear_plate_overlap_cm
        access_hole_length = connection.access_hole_length

        height_ok = hp >= self.rules.shear_plate_height_db_ratio_min * db
        width_ok = bp >= self.rules.shear_plate_width_bf_ratio_min * bf
        thickness_ok = tp >= tw
        overlap_ok = self.rules.shear_plate_overlap_min_cm <= overlap <= self.rules.shear_plate_overlap_max_cm
        extra_ok = (bp - access_hole_length) >= self.rules.shear_plate_extra_beyond_hole_min_cm
        is_pass = all([height_ok, width_ok, thickness_ok, overlap_ok, extra_ok])

        return DesignCheckResult(
            key="shear_plate_geometry",
            title="Shear Plate Geometry",
            is_pass=is_pass,
            ratio=max(
                (self.rules.shear_plate_height_db_ratio_min * db / hp) if hp else 999.0,
                (self.rules.shear_plate_width_bf_ratio_min * bf / bp) if bp else 999.0,
                (tw / tp) if tp else 999.0,
                (
                    self.rules.shear_plate_overlap_min_cm / overlap
                    if overlap < self.rules.shear_plate_overlap_min_cm and overlap > 0
                    else (
                        overlap / self.rules.shear_plate_overlap_max_cm
                        if overlap > self.rules.shear_plate_overlap_max_cm
                        else 1.0
                    )
                ),
                (
                    self.rules.shear_plate_extra_beyond_hole_min_cm / (bp - access_hole_length)
                    if (bp - access_hole_length) > 0
                    else 999.0
                ),
            ),
            code_ref="AISC 358-16 8.6 / Fig. 8.2",
            message=(
                f"hp={hp:.3f} cm, bp={bp:.3f} cm, tp={tp:.3f} cm, "
                f"overlap={overlap:.3f} cm, extension={bp - access_hole_length:.3f} cm"
            ),
        )

    def check_beam_design_shear_strength(self, connection) -> DesignCheckResult:
        return DesignCheckResult(
            key="beam_shear_strength",
            title="Beam Shear Strength",
            is_pass=None,
            code_ref="AISC 358-16 8.7",
            message="TODO: implement required beam shear strength check.",
        )

    def check_beam_flexure_compactness(self, connection) -> DesignCheckResult:
        return DesignCheckResult(
            key="beam_flexure_compactness",
            title="Beam Flexural Strength and Compactness",
            is_pass=None,
            code_ref="AISC 360-16 Chapter F",
            message="TODO: compact/non-compact flexural branch.",
        )

    def check_cjp_flange_weld_strength(self, connection) -> DesignCheckResult:
        return DesignCheckResult(
            key="cjp_flange_weld",
            title="Flange CJP Weld Strength",
            is_pass=None,
            code_ref="AISC 358-16 8.5",
            message="TODO: use phi = 0.9 for CJP welds.",
        )

    def check_web_connection_strength(self, connection) -> DesignCheckResult:
        return DesignCheckResult(
            key="web_connection_strength",
            title="Beam Web to Column Connection Strength",
            is_pass=None,
            code_ref="AISC 358-16 8.6 / 8.7",
            message="TODO: shear-plate weld and plate shear chain.",
        )

    def check_moment_at_connection_face(self, connection) -> DesignCheckResult:
        return DesignCheckResult(
            key="moment_at_face",
            title="Moment at Connection Face",
            is_pass=None,
            code_ref="AISC 358-16 8.7",
            message="TODO: Mf = Mp + Vu * (db/2 - tp).",
        )

    def check_protected_zone_restrictions(self, connection) -> DesignCheckResult:
        return DesignCheckResult(
            key="protected_zone",
            title="Protected Zone Detailing",
            is_pass=None,
            code_ref="AISC 358-16 2.3.2a",
            message="TODO: enforce protected-zone weld restrictions.",
        )

    def check_ltb_and_local_buckling(self, connection) -> DesignCheckResult:
        return DesignCheckResult(
            key="ltb_local_buckling",
            title="LTB and Local Buckling",
            is_pass=None,
            code_ref="AISC 360-16 F2/F3 and AISC 341-16 D1.2a",
            message="TODO: implement buckling controls.",
        )
