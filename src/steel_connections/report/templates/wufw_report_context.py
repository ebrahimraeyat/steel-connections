from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class WUFWReportContext:
    """Context object consumed by report templates for WUF-W outputs."""

    project_name: str = ""
    engineer: str = ""
    checker: str = ""
    design_code: str = "AISC 358-16 Chapter 8"
    units: str = "cm, kgf"
    summary_rows: list[dict[str, str]] = field(default_factory=list)
    check_rows: list[dict[str, str]] = field(default_factory=list)
