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

section_dict_IPE600={
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

PG1 = SteelSection.from_section_dict(section_dict)
IPE600 = SteelSection.from_section_dict(section_dict_IPE600)

def test_h_c():
     assert IPE600.geom.h_c == pytest.approx(51.4, abs=.01)




if __name__ == '__main__':
	test_s_x_ipe600()