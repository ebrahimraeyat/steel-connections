import pytest
from steel_connections.bfp_connection import BFPConnection
from steel_connections.member.member import SteelSection
from steel_connections.component.bolt import Bolt, BoltGroup2D
from steel_connections.component.plate import Plate


section_dict={
		'sec_type': 'WB',
		'b': 20,
		'd': 42.4,
		't_w': 0.6,
		't_f': 1.2,
		't': 1.2,
		'f_y': 2400,
		'f_yw': 2400,
		'f_u': 3700,

}
PG1 = SteelSection.from_section_dict(section_dict)
bolt = Bolt(d_f=2.4)
web_bolt = Bolt(d_f=2)
plate = Plate(t_i=2.5, b_i=25, f_ui=3700, f_yi=2400)
web_plate = Plate(t_i=1, b_i=15, h_i=32.5, f_ui=3700, f_yi=2400)
bolt_group = BoltGroup2D(n_p=4, n_g=2, bolt=bolt, s_p=8.4, s_g=5)
web_bolt_group = BoltGroup2D(n_p=4, n_g=1, bolt=web_bolt, s_p=6.5, s_g=8.4)
bfp = BFPConnection(beam=PG1,
					column=PG1,
					bolt_group=bolt_group,
					plate=plate,
					s1=7,
					beam_length=580,
					web_plate=web_plate,
					bolt_group_web=web_bolt_group,
					)

def test_cpr():
	assert pytest.approx(bfp.cpr, abs=.001) == 1.2

def test_m_pr():
	assert pytest.approx(bfp.m_pr, abs=1) == 1987200

def test_get_max_bolt_diameter():
	assert pytest.approx(bfp.get_max_bolt_diameter(), abs=0.01) == 2.34

def test_nominal_shear_force_of_bolt_values():
	rn1, rn2, rn3 = bfp.nominal_shear_force_of_bolt_values()
	assert pytest.approx(rn1, abs=1) == 24881
	assert pytest.approx(rn2, abs=1) == 57600
	assert pytest.approx(rn3, abs=1) == 53280

def test_nominal_shear_force_of_bolt():
	rn = bfp.nominal_shear_force_of_bolt()
	assert pytest.approx(rn, abs=1) == 24881

def test_min_no_bolts():
	assert bfp.min_no_bolts() == 4

def test_sh():
	assert pytest.approx(bfp.sh, abs=0.01) == 32.2

def test_s5():
	assert pytest.approx(bfp.s5, abs=0.01) == 5

def test_shear_in_hinge():
	vh = bfp.shear_in_hinge(9847.95)
	assert pytest.approx(vh, abs=1) == 15602

def test_probable_moment_in_column_face():
	mf = bfp.probable_moment_in_column_face(9847.95)
	assert pytest.approx(mf, abs=100) == 2489587

def test_force_of_plate():
	fpr = bfp.force_of_plate(9847.95)
	assert pytest.approx(fpr, abs=10) == 72161

def test_check_no_of_bolts():
	n = bfp.check_no_of_bolts(9847.95)
	assert n == 4

def test_get_minimum_thickness_of_plate():
	t = bfp.get_minimum_thickness_of_plate(9847.95)
	assert pytest.approx(t, abs=.01) == 1.5

def test_get_net_area_of_plate():
	a_nv = bfp.get_net_area_of_plate()
	assert pytest.approx(a_nv, abs=.01) == 36.50

def test_get_net_shear_area_of_plate():
	a_nv = bfp.get_net_shear_area_of_plate()
	assert pytest.approx(a_nv, abs=.01) == 56.875

def test_all_shear_area_of_plate():
	a_nv = bfp.all_shear_area_of_plate()
	assert pytest.approx(a_nv, abs=.01) == 80.50

def test_net_shear_area_in_tensile():
	a_nt = bfp.net_shear_area_in_tensile()
	assert pytest.approx(a_nt, abs=.01) == 9.125




def test_buckling_factor_of_plate():
	kl_r = bfp.buckling_factor_of_plate()
	assert pytest.approx(kl_r, abs=.01) == 6.30

def test_plate_force_compresion_buckling():
	rn_3 = bfp.plate_force_compresion_buckling()
	assert pytest.approx(rn_3, abs=1) == 120000

def test_probable_shear_force_in_column_face():
	vu = bfp.probable_shear_force_in_column_face(v=9847.95, v_gravity=918.344)
	assert pytest.approx(vu, abs=10) == 16520

def test_rnv_1():
	rnv_1 = bfp.rnv_1()
	assert pytest.approx(rnv_1, abs=1) == 12959

def test_anv_web():
	anv_web = bfp.anv_web()
	assert pytest.approx(anv_web, abs=.01) == 19.4



def test_rnv_2():
	rnv_2 = bfp.rnv_2()
	assert pytest.approx(rnv_2, abs=1) == 32301

def test_rnv_3():
	rnv_3 = bfp.rnv_3()
	assert pytest.approx(rnv_3, abs=1) == 37440

def test_get_web_plate_a():
	a = bfp.get_web_plate_a()
	assert pytest.approx(a, abs=0.01) == 6.5

def test_kl():
	assert pytest.approx(bfp.kl, abs=0.01) == 4.55

def test_get_lc():
	lc = bfp.get_lc()
	assert pytest.approx(lc, abs=0.01) == 4.30

def test_rnv_41():
	rnv_41 = bfp.rnv_41()
	assert pytest.approx(rnv_41, abs=1) == 19092

def test_rnv_42():
	rnv_42 = bfp.rnv_42()
	assert pytest.approx(rnv_42, abs=1) == 17760

def test_rnv_4():
	rnv_4 = bfp.rnv_4()
	assert pytest.approx(rnv_4, abs=1) == 13320

def test_rnv_51():
	rnv_51 = bfp.rnv_51()
	assert pytest.approx(rnv_51, abs=1) == 11455

def test_rnv_52():
	rnv_52 = bfp.rnv_52()
	assert pytest.approx(rnv_52, abs=1) == 10656

def test_rnv_5():
	rnv_5 = bfp.rnv_5()
	assert pytest.approx(rnv_5, abs=1) == 7992

def test_get_agv_web_plate():
	agv = bfp.get_agv_web_plate()
	assert pytest.approx(agv, abs=0.01) == 19.5

def test_get_ant_web_plate():
	ant = bfp.get_ant_web_plate()
	assert pytest.approx(ant, abs=0.01) == 6.2

def test_get_anv_web_plate():
	ant = bfp.get_anv_web_plate()
	assert pytest.approx(ant, abs=0.01) == 14.0

def test_rnv_61():
	rnv_61 = bfp.rnv_61()
	assert pytest.approx(rnv_61, abs=1) == 54020

def test_rnv_62():
	rnv_62 = bfp.rnv_62()
	assert pytest.approx(rnv_62, abs=1) == 51020


def test_rnv_6():
	rnv_6 = bfp.rnv_6()
	assert pytest.approx(rnv_6, abs=1) == 38265





if __name__ == '__main__':
	test_rnv_61()