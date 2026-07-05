from __future__ import annotations

from dataclasses import dataclass

from steel_connections.design_result import DesignCheckResult
from steel_connections.wufw_rules import WUFWCodeRules, WUFWResistanceFactors


@dataclass
class WUFWDesignCalculator:
    """Design check calculator for AISC 358-16 Chapter 8 WUF-W connections."""

    rules: WUFWCodeRules
    phi: WUFWResistanceFactors

    def check_beam_limits(self, connection) -> DesignCheckResult:
        return DesignCheckResult(
            key="beam_limits",
            title="Beam Geometric Limits",
            is_pass=None,
            code_ref="AISC 358-16 8.3.1",
            message="TODO: implement beam limit checks.",
        )

    def check_column_limits(self, connection) -> DesignCheckResult:
        return DesignCheckResult(
            key="column_limits",
            title="Column Geometric Limits",
            is_pass=None,
            code_ref="AISC 358-16 8.3.2",
            message="TODO: implement column limit checks.",
        )

    def check_access_hole_geometry(self, connection) -> DesignCheckResult:
        return DesignCheckResult(
            key="access_hole_geometry",
            title="Weld Access Hole Geometry",
            is_pass=None,
            code_ref="AISC 360-16 J1.6 / AWS D1.8 6.11.1.2",
            message="TODO: implement access-hole geometry checks.",
        )

    def check_shear_plate_geometry(self, connection) -> DesignCheckResult:
        return DesignCheckResult(
            key="shear_plate_geometry",
            title="Shear Plate Geometry",
            is_pass=None,
            code_ref="AISC 358-16 8.6 / Fig. 8.2",
            message="TODO: implement shear plate geometry checks.",
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
