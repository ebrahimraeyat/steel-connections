from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DesignCheckResult:
    """Single check result in a code-referenced design workflow."""

    key: str
    title: str
    is_pass: bool | None
    demand: float | None = None
    capacity: float | None = None
    ratio: float | None = None
    code_ref: str = ""
    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConnectionDesignResult:
    """Aggregated result package used by UI and report generators."""

    connection_type: str
    units: str
    checks: list[DesignCheckResult] = field(default_factory=list)
    governing_check_key: str | None = None
    is_ok: bool = False
    notes: list[str] = field(default_factory=list)

    def add_check(self, check: DesignCheckResult) -> None:
        self.checks.append(check)
