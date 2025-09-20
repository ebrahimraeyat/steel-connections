import pytest
from steel_connections.member.member import SteelSection


section_dict={
		'sec_type': 'WB',
		'b': 15,
		'd': 32,
		't_w': 0.6,
		't_f': 1,
		't': 1,
		'f_y': 2400,
		'f_yw': 2400,
		'f_u': 3700,

}
PG1 = SteelSection.from_section_dict(section_dict)

def test_weight_per_length():
    assert PG1.weight_per_length == pytest.approx(37.68, abs=.01)

def test_A_g():
    assert PG1.A_g == pytest.approx(48, abs=.1)


if __name__ == '__main__':
	test_check_minimum_s3()