from dataclasses import dataclass, field
import enum


class DesignCode(enum.StrEnum):
    """Supported design code standards for BFP connection checks."""
    MABHAS10 = "مبحث دهم مقررات ملی ایران (ویرایش ۱۴۰۱) / AISC 360"
    AISC = "AISC 358-16 (USA)"


@dataclass
class Connection:
    pass
    

    