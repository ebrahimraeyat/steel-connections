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
        vu=30000,
        pu=0,
        shear_plate_height=45,
        shear_plate_width=12,
        shear_plate_thickness=1,
        web_fillet_weld_size=0.8,
        cjp_electrode_fexx=4921,
    )


def test_flange_cjp_weld_strength_uses_phi_0_9():
    conn = _make_connection()
    check = conn.calculator.check_cjp_flange_weld_strength(conn)

    assert check.is_pass is True
    assert check.code_ref == "AISC 358-16 8.5"
    assert "phi = 0.9" in check.message


def test_web_connection_strength_chain():
    conn = _make_connection()
    check = conn.calculator.check_web_connection_strength(conn)

    assert check.capacity is not None
    assert check.demand == conn.vu
    assert check.ratio is not None
