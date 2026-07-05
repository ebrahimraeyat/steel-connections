from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from steel_connections.connection_types import FrameSystem
from steel_connections.connections import Connection
from steel_connections.design_result import ConnectionDesignResult, DesignCheckResult
from steel_connections.member.member import SteelSection


@dataclass
class SteelMomentConnection(Connection, ABC):
    """Abstract base for steel moment connection design modules."""

    beam: SteelSection
    column: SteelSection
    frame_system: FrameSystem = FrameSystem.SMF
    name: str = "Steel Moment Connection"
    units: str = "cm-kgf"
    checks: list[DesignCheckResult] = field(default_factory=list)

    @property
    def m_p(self) -> float:
        """Plastic moment proxy used by continuity plate checks."""
        return self.beam.geom.Z_x * self.beam.mat.f_y

    @abstractmethod
    def validate_geometry(self) -> list[DesignCheckResult]:
        """Validate prequalification limits and geometry constraints."""

    @abstractmethod
    def generate_report(self, output_path: str | None = None) -> str | None:
        """Generate a connection report and return a path if available."""

    def check_strong_column_weak_beam(self, pu_column: float = 0.0) -> DesignCheckResult:
        """AISC 341 SCWB check skeleton: sum(Mpc*) / sum(Mpb*) >= 1.0."""
        zc = self.column.geom.Z_x
        zb = self.beam.geom.Z_x
        fyc = self.column.mat.f_y
        fyb = self.beam.mat.f_y
        agc = self.column.geom.A_g

        mpc = zc * (fyc - (pu_column / agc if agc else 0.0))
        mpb = zb * fyb
        ratio = (mpc / mpb) if mpb else None
        is_pass = (ratio is not None) and (ratio >= 1.0)
        result = DesignCheckResult(
            key="scwb",
            title="Strong Column - Weak Beam",
            is_pass=is_pass,
            demand=mpb,
            capacity=mpc,
            ratio=ratio,
            code_ref="AISC 341-16 E3.4a",
        )
        self.checks.append(result)
        return result

    def check_continuity_plates(self) -> DesignCheckResult:
        """Route continuity plate requirement through existing project class."""
        from steel_connections.continuity_plate import ContinuityPlate

        continuity = ContinuityPlate(connection=self)
        required = continuity.check_is_required_continuity_plate()
        result = DesignCheckResult(
            key="continuity_plate",
            title="Continuity Plate Requirement",
            is_pass=not required,
            code_ref="AISC 341-16 E3.6f",
            message="Continuity plates are required." if required else "No continuity plates required.",
        )
        self.checks.append(result)
        return result

    def check_panel_zone(self, vu_panel: float) -> DesignCheckResult:
        """Route panel zone demand through existing doubler plate class."""
        from steel_connections.doubler_plate import DoublerPlate

        doubler = DoublerPlate(
            left_beam=self.beam,
            right_beam=self.beam,
            below_column=self.column,
            above_column=self.column,
        )
        required = doubler.is_required(vup=vu_panel)
        result = DesignCheckResult(
            key="panel_zone",
            title="Panel Zone Shear Check",
            is_pass=not required,
            demand=vu_panel,
            capacity=doubler.capacity_of_web(),
            ratio=(vu_panel / doubler.capacity_of_web()) if doubler.capacity_of_web() else None,
            code_ref="AISC 341-16 E3.6e",
            message="Doubler plate is required." if required else "Column web is adequate.",
        )
        self.checks.append(result)
        return result

    def run_all_checks(self) -> ConnectionDesignResult:
        """Base aggregation skeleton for connection-level checks."""
        self.checks = []
        self.validate_geometry()
        self.check_strong_column_weak_beam()
        return ConnectionDesignResult(
            connection_type=self.name,
            units=self.units,
            checks=self.checks,
            is_ok=all(chk.is_pass is not False for chk in self.checks),
        )
