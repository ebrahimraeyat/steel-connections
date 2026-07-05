import pytest

from steel_connections.member.member import SteelSection
from steel_connections.wufw_connection import WUFWConnection


def _make_connection() -> WUFWConnection:
    beam = SteelSection.from_section_dict(
        {
            "sec_type": "WB",
            "b": 20,
            "d": 60,
            "t_w": 0.9,
            "t_f": 1.0,
            "t": 1.0,
            "f_y": 2400,
            "f_yw": 2400,
            "f_u": 3700,
        }
    )
    column = SteelSection.from_section_dict(
        {
            "sec_type": "WC",
            "b": 30,
            "d": 70,
            "t_w": 1.2,
            "t_f": 2.0,
            "t": 2.0,
            "f_y": 2400,
            "f_yw": 2400,
            "f_u": 3700,
        }
    )
    return WUFWConnection(
        beam=beam,
        column=column,
        mu=100000,
        vu=30000,
        pu=0,
        shear_plate_height=45,
        shear_plate_width=12,
        shear_plate_thickness=1,
        web_fillet_weld_size=0.8,
    )


def test_scwb_ratio_requirement():
    conn = _make_connection()
    check = conn.check_strong_column_weak_beam()

    assert check.ratio is not None
    assert check.code_ref == "AISC 341-16 E3.4a"


def test_moment_at_connection_face_expression():
    conn = _make_connection()
    check = conn.calculator.check_moment_at_connection_face(conn)

    expected_mf = conn.beam.mat.f_y * conn.beam.geom.Z_x + conn.vu * (
        conn.beam.geom.d / 2.0 - conn.shear_plate_thickness
    )
    assert check.capacity == pytest.approx(expected_mf, rel=1e-9)
