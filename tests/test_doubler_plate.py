import pytest
from steel_connections.bfp_connection import BFPConnection
from steel_connections.doubler_plate import DoublerPlate
from steel_connections.member.member import SteelSection


section_dict_beam={
		'sec_type': 'WB',
		'b': 20,
		'd': 39.9,
		't_w': 0.8,
		't_f': 1.2,
		't': 1.2,
		# 'r_1': 2.4,
		'f_y': 2400,
		'f_yw': 2400,
		'f_u': 3700,
}
section_dict_column={
		'sec_type': 'WC',
		'b': 25,
		'd': 37,
		't_w': 1.2,
		't_f': 2,
		't': 2,
		# 'r_1': 2.7,
		'f_y': 2400,
		'f_yw': 2400,
		'f_u': 3700,
}
beam = SteelSection.from_section_dict(section_dict_beam)
col = SteelSection.from_section_dict(section_dict_column)

doubler_plate = DoublerPlate(right_beam=beam, below_column=col, left_beam=beam, above_column=col)

vup = 204443


def test_capacity_of_web():
	assert pytest.approx(doubler_plate.capacity_of_web(), abs=1) == 57542

def test_vu_p():
	mu1 = 4675633.2
	mu2 = mu1
	vr = 29924.05
	assert pytest.approx(doubler_plate.vu_p(mu1=mu1, mu2=mu2, vr=vr), abs=1) == vup
	mu2 = 0
	vr = 14962
	assert pytest.approx(doubler_plate.vu_p(mu1=mu1, mu2=mu2, vr=vr), abs=1) == 102222

def test_is_required():
	assert doubler_plate.is_required(vup=vup)
	assert doubler_plate.is_required(vup=102222)
	
def test_required_calculated_thickness():
	t_calc, t_required = doubler_plate.required_calculated_thickness(vup)
	assert pytest.approx(t_calc, abs=.01) == 3.837
	assert pytest.approx(t_required, abs=.01) == 2.637

def test_required_applicable_thickness():
	t = doubler_plate.required_applicable_thickness(vup)
	assert pytest.approx(t, abs=.01) == 1.5
	t = doubler_plate.required_applicable_thickness(vup, double=False)
	assert pytest.approx(t, abs=.01) == 3



if __name__ == '__main__':
	test_required_applicable_thickness()