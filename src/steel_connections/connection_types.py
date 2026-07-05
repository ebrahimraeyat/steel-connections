from __future__ import annotations

from enum import Enum


class FrameSystem(str, Enum):
    """Moment frame category for seismic design logic."""

    SMF = "SMF"
    IMF = "IMF"
    OMF = "OMF"


class ConnectionType(str, Enum):
    """Connection families currently supported by the application."""

    BFP = "BFP"
    WUFW = "WUFW"
