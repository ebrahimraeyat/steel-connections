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
            "d": 60,
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
        vu=50000,
        pu=0,
        shear_plate_height=45,
        shear_plate_width=12,
        shear_plate_thickness=1,
        shear_plate_overlap_cm=0.8,
        access_hole_length=3,
        access_hole_height=1.2,
        access_hole_surface_finish_ok=True,
        web_fillet_weld_size=0.8,
    )


def test_aisc358_ch8_beam_and_column_limits():
    conn = _make_connection()
    results = {c.key: c for c in conn.validate_geometry()}

    assert results["beam_limits"].is_pass is True
    assert results["column_limits"].is_pass is True


def test_access_hole_geometry_requirements():
    conn = _make_connection()
    conn.access_hole_length = 2.0

    results = {c.key: c for c in conn.validate_geometry()}
    assert results["access_hole_geometry"].is_pass is False
