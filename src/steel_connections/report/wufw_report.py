from __future__ import annotations

from pathlib import Path


def generate_wufw_report(connection, output_path: str | None = None) -> Path:
    """WUF-W report entry point (English-only skeleton)."""

    if output_path is None:
        return Path("wufw_report.docx")
    return Path(output_path)
