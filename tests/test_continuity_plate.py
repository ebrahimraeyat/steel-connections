import pytest
from steel_connections.bfp_connection import BFPConnection
from steel_connections.continuity_plate import ContinuityPlate
from steel_connections.member.member import SteelSection


section_dict_beam={
		'sec_type': 'WB',
		'b': 22,
		'd': 60,
		't_w': 1.2,
		't_f': 1.9,
		't': 1.9,
		'r_1': 2.4,
		'f_y': 2400,
		'f_yw': 2400,
		'f_u': 3700,
}
section_dict_column={
		'sec_type': 'WC',
		'b': 30,
		'd': 49,
		't_w': 1.2,
		't_f': 2.3,
		't': 2.3,
		'r_1': 2.7,
		'f_y': 2400,
		'f_yw': 2400,
		'f_u': 3700,
}
beam = SteelSection.from_section_dict(section_dict_beam)
col = SteelSection.from_section_dict(section_dict_column)
bfp = BFPConnection(beam=beam,
					column=col,
					)
cont_plate = ContinuityPlate(bfp)



def test_check_is_required():
	assert cont_plate.check_is_required()

def test_flange_local_bending_force():
	assert pytest.approx(cont_plate.flange_local_bending_force(), abs=1) == 71415

def test_calculate_tu():
	assert pytest.approx(cont_plate.calculate_tu(), abs=1) == 145074

def test_web_local_yielding_force():
	assert pytest.approx(cont_plate.web_local_yielding_force(), abs=1) == 86400

def test_web_local_crippling_force_1():
	assert pytest.approx(cont_plate.web_local_crippling_force_1(), abs=1) == 123243

def test_web_local_crippling_force_3():
	assert pytest.approx(cont_plate.web_local_crippling_force_3(), abs=1) == 59582

def test_web_local_crippling_force():
	assert pytest.approx(cont_plate.web_local_crippling_force(), abs=1) == 123243 * .75
	assert pytest.approx(cont_plate.web_local_crippling_force(e=20), abs=1) == 123243 * .5 * .75
	cont_plate.column.geom.r_1 = 10
	assert pytest.approx(cont_plate.web_local_crippling_force(e=20), abs=1) == 53992
	cont_plate.column.geom.r_1 = 2.7

def test_web_compression_buckling_force():
	assert pytest.approx(cont_plate.web_compression_buckling_force(), abs=1) == 66306
	assert pytest.approx(cont_plate.web_compression_buckling_force(e=20), abs=1) == 66306 * .5

def test_get_k():
	assert pytest.approx(cont_plate.get_k(), abs=.01) == 5

def test_get_cr():
	assert pytest.approx(cont_plate.get_cr(), abs=1) == 3.3e6

def test_check_is_required_continuity_plate():
	assert cont_plate.check_is_required_continuity_plate()

def test_get_continuity_plate_force():
	assert pytest.approx(cont_plate.get_continuity_plate_force(), abs=1) == 78768


if __name__ == '__main__':
	test_calculate_tu()