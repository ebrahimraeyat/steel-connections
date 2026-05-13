from dataclasses import dataclass, field
import enum


class DesignCode(enum.StrEnum):
    """Supported design code standards for BFP connection checks."""
    IRAN = "Iranian Code (PN-S 2800 / Instruction 360)"
    AISC = "AISC 358-16 (USA)"


@dataclass
class Connection:
    pass
    

    