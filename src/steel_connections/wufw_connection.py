from __future__ import annotations

from dataclasses import dataclass, field

from steel_connections.connection_types import ConnectionType, FrameSystem
from steel_connections.design_result import ConnectionDesignResult, DesignCheckResult
from steel_connections.member.member import SteelSection
from steel_connections.steel_moment_connection import SteelMomentConnection
from steel_connections.wufw_defaults import WUFWGeometryDefaults, WUFWMaterialDefaults
from steel_connections.wufw_design_calculator import WUFWDesignCalculator
from steel_connections.wufw_rules import WUFWCodeRules, WUFWResistanceFactors


@dataclass
class WUFWConnection(SteelMomentConnection):
    """WUF-W seismic moment connection skeleton (AISC 358-16 Chapter 8)."""

    beam: SteelSection
    column: SteelSection
    frame_system: FrameSystem = FrameSystem.SMF

    mu: float = 0.0
    vu: float = 0.0
    pu: float = 0.0

    shear_plate_height: float = 0.0
    shear_plate_width: float = 0.0
    shear_plate_thickness: float = 0.0

    web_fillet_weld_size: float = 0.0
    cjp_electrode_fexx: float = 4921.0

    material_defaults: WUFWMaterialDefaults = field(default_factory=WUFWMaterialDefaults)
    geometry_defaults: WUFWGeometryDefaults = field(default_factory=WUFWGeometryDefaults)
    rules: WUFWCodeRules = field(default_factory=WUFWCodeRules)
    phi: WUFWResistanceFactors = field(default_factory=WUFWResistanceFactors)

    connection_type: ConnectionType = ConnectionType.WUFW
    name: str = "WUF-W Moment Connection"

    def __post_init__(self) -> None:
        self.calculator = WUFWDesignCalculator(rules=self.rules, phi=self.phi)

    def validate_geometry(self) -> list[DesignCheckResult]:
        geometry_checks = [
            self.calculator.check_beam_limits(self),
            self.calculator.check_column_limits(self),
            self.calculator.check_access_hole_geometry(self),
            self.calculator.check_shear_plate_geometry(self),
        ]
        self.checks.extend(geometry_checks)
        return geometry_checks

    def run_all_checks(self) -> ConnectionDesignResult:
        self.checks = []

        self.validate_geometry()
        self.check_strong_column_weak_beam(pu_column=self.pu)
        self.check_continuity_plates()
        self.check_panel_zone(vu_panel=self.vu)

        self.checks.extend(
            [
                self.calculator.check_beam_design_shear_strength(self),
                self.calculator.check_beam_flexure_compactness(self),
                self.calculator.check_cjp_flange_weld_strength(self),
                self.calculator.check_web_connection_strength(self),
                self.calculator.check_moment_at_connection_face(self),
                self.calculator.check_protected_zone_restrictions(self),
                self.calculator.check_ltb_and_local_buckling(self),
            ]
        )

        is_ok = all(chk.is_pass is not False for chk in self.checks)
        return ConnectionDesignResult(
            connection_type=self.connection_type.value,
            units=self.units,
            checks=self.checks,
            is_ok=is_ok,
        )

    def generate_report(self, output_path: str | None = None) -> str | None:
        from steel_connections.report.wufw_report import generate_wufw_report

        return str(generate_wufw_report(self, output_path=output_path))
