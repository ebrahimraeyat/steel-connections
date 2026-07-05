from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, TypeAlias


@dataclass(frozen=True)
class ModuleVariant:
    """A leaf module option shown as one selectable variant in UI."""

    name: str
    image_path: str
    object_name: str


ModuleLeaf: TypeAlias = tuple[list[ModuleVariant], Callable]
ModuleNode: TypeAlias = dict[str, "ModuleTree"] | ModuleLeaf | str
ModuleTree: TypeAlias = ModuleNode

UNDER_DEVELOPMENT = "UNDER DEVELOPMENT"


def build_module_catalog(launchers: dict[str, Callable]) -> dict[str, ModuleTree]:
    """Osdag-style 3-level module tree skeleton for the main launcher UI."""

    return {
        "Connection": {
            "Moment Connection": {
                "Beam-to-Column": (
                    [
                        ModuleVariant(
                            name="Bolted Flange Plate (BFP)",
                            image_path="",
                            object_name="BFP_Moment_Connection",
                        ),
                        ModuleVariant(
                            name="Welded Unreinforced Flange - Welded Web (WUF-W)",
                            image_path="",
                            object_name="WUFW_Moment_Connection",
                        ),
                    ],
                    launchers.get("show_moment_connection_bc", lambda: None),
                )
            },
            "Simple Connection": UNDER_DEVELOPMENT,
            "Base Plate": UNDER_DEVELOPMENT,
        },
        "Member Design": UNDER_DEVELOPMENT,
    }
