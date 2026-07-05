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
        beam = connection.beam
        aw = beam.geom.d * beam.geom.t_w
        vn = 0.6 * beam.mat.f_y * aw
        capacity = self.phi.phi_non_ductile * vn
        demand = connection.vu
        ratio = (demand / capacity) if capacity else None
        return DesignCheckResult(
            key="beam_shear_strength",
            title="Beam Shear Strength",
            is_pass=(capacity >= demand),
            demand=demand,
            capacity=capacity,
            ratio=ratio,
            code_ref="AISC 358-16 8.7",
            message=f"Aw={aw:.3f} cm2, phiVn={capacity:.3f} kgf",
        )

    def check_beam_flexure_compactness(self, connection) -> DesignCheckResult:
        beam = connection.beam
        e = beam.mat.E
        fy = beam.mat.f_y
        bf = beam.geom.b
        tf = beam.geom.t_f
        tw = beam.geom.t_w
        d = beam.geom.d
        h = max(d - 2.0 * tf, 0.0)

        lam_f = self._check_ratio(bf, 2.0 * tf)
        lam_w = self._check_ratio(h, tw)
        lam_pf = 0.38 * sqrt(e / fy) if fy > 0 else None
        lam_pw = 3.76 * sqrt(e / fy) if fy > 0 else None
        compact = (
            (lam_f is not None and lam_pf is not None and lam_f <= lam_pf)
            and (lam_w is not None and lam_pw is not None and lam_w <= lam_pw)
        )

        z_x = beam.geom.Z_x
        mn = fy * z_x if compact else 0.9 * fy * z_x
        capacity = self.phi.phi_ductile * mn
        demand = connection.mu
        ratio = (demand / capacity) if capacity else None

        return DesignCheckResult(
            key="beam_flexure_compactness",
            title="Beam Flexural Strength and Compactness",
            is_pass=(capacity >= demand),
            demand=demand,
            capacity=capacity,
            ratio=ratio,
            code_ref="AISC 360-16 Chapter F",
            message=(
                "compact="
                f"{compact}, lambda_f={f'{lam_f:.3f}' if lam_f is not None else 'n/a'}, "
                f"lambda_w={f'{lam_w:.3f}' if lam_w is not None else 'n/a'}"
            ),
        )

    def check_cjp_flange_weld_strength(self, connection) -> DesignCheckResult:
        beam = connection.beam
        af = beam.geom.b * beam.geom.t_f
        demand = beam.mat.f_u * af
        capacity = self.phi.phi_cjp * connection.cjp_electrode_fexx * af
        ratio = (demand / capacity) if capacity else None
        return DesignCheckResult(
            key="cjp_flange_weld",
            title="Flange CJP Weld Strength",
            is_pass=(capacity >= demand),
            demand=demand,
            capacity=capacity,
            ratio=ratio,
            code_ref="AISC 358-16 8.5",
            message="CJP weld check uses phi = 0.9.",
        )

    def check_web_connection_strength(self, connection) -> DesignCheckResult:
        hp = connection.shear_plate_height
        bp = connection.shear_plate_width
        tp = connection.shear_plate_thickness
        weld_size = connection.web_fillet_weld_size

        weld_length = max(2.0 * hp + bp, 0.0)
        throat = 0.707 * weld_size
        weld_capacity = self.phi.phi_non_ductile * 0.6 * connection.cjp_electrode_fexx * throat * weld_length

        fy_plate = connection.material_defaults.fy_plate
        plate_shear_capacity = self.phi.phi_non_ductile * 0.6 * fy_plate * hp * tp

        capacity = min(weld_capacity, plate_shear_capacity)
        demand = connection.vu
        ratio = (demand / capacity) if capacity else None

        return DesignCheckResult(
            key="web_connection_strength",
            title="Beam Web to Column Connection Strength",
            is_pass=(capacity >= demand),
            demand=demand,
            capacity=capacity,
            ratio=ratio,
            code_ref="AISC 358-16 8.6 / 8.7",
            message=(
                f"weld_capacity={weld_capacity:.3f} kgf, "
                f"plate_capacity={plate_shear_capacity:.3f} kgf"
            ),
        )

    def check_moment_at_connection_face(self, connection) -> DesignCheckResult:
        mp = connection.beam.mat.f_y * connection.beam.geom.Z_x
        arm = (connection.beam.geom.d / 2.0) - connection.shear_plate_thickness
        mf = mp + connection.vu * arm
        demand = connection.mu
        ratio = (demand / mf) if mf else None
        return DesignCheckResult(
            key="moment_at_face",
            title="Moment at Connection Face",
            is_pass=(mf >= demand),
            demand=demand,
            capacity=mf,
            ratio=ratio,
            code_ref="AISC 358-16 8.7",
            message=f"Mf=Mp+Vu*(db/2-tp), arm={arm:.3f} cm",
        )

    def check_protected_zone_restrictions(self, connection) -> DesignCheckResult:
        sec_type = str(connection.beam.geom.sec_type).upper()
        rolled_w = sec_type.startswith("W")
        if rolled_w:
            is_pass = True
            note = "Rolled W-shape treated as standard mill-practice compliant."
        else:
            is_pass = connection.web_fillet_weld_size >= 0.8
            note = "Built-up section requires >= 0.8 cm reinforcing fillet weld in protected zone."

        return DesignCheckResult(
            key="protected_zone",
            title="Protected Zone Detailing",
            is_pass=is_pass,
            code_ref="AISC 358-16 2.3.2a",
            message=note,
        )

    def check_ltb_and_local_buckling(self, connection) -> DesignCheckResult:
        beam = connection.beam
        e = beam.mat.E
        fy = beam.mat.f_y
        bf = beam.geom.b
        tf = beam.geom.t_f
        tw = beam.geom.t_w
        d = beam.geom.d
        h = max(d - 2.0 * tf, 0.0)

        lam_f = self._check_ratio(bf, 2.0 * tf)
        lam_w = self._check_ratio(h, tw)
        lam_pf = 0.38 * sqrt(e / fy) if fy > 0 else None
        lam_pw = 3.76 * sqrt(e / fy) if fy > 0 else None
        local_ok = (
            (lam_f is not None and lam_pf is not None and lam_f <= lam_pf)
            and (lam_w is not None and lam_pw is not None and lam_w <= lam_pw)
        )

        # Placeholder LTB adequacy, pending explicit unbraced-length input.
        ltb_ok = True

        return DesignCheckResult(
            key="ltb_local_buckling",
            title="LTB and Local Buckling",
            is_pass=(local_ok and ltb_ok),
            code_ref="AISC 360-16 F2/F3 and AISC 341-16 D1.2a",
            message="Local buckling limits checked. LTB placeholder assumes bracing adequacy.",
        )
