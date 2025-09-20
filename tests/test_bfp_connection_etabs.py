import pytest
from steel_connections.bfp_connection import BFPConnection
from steel_connections.member.member import SteelSection

# Mocks for dependencies
class MockMat:
	f_y = 300
	f_u = 450

class MockGeom:
	b = 200
	t_f = 20

class MockSlenderness:
	Z_ex = 5000

class MockSteelSection:
	mat = MockMat()
	geom = MockGeom()
	Z_ex = 5000
	Ry = 1.1
	Rt = 1.2

class MockBolt:
	nominal_shear_force = 100
	f_uf = 400
	d_f = 20

class MockPlate:
	f_ui = 410
	t_i = 10

class MockBoltGroup:
	bolt = MockBolt()
	s_p = 50
	n_b = 4

def make_bfp():
	beam = MockSteelSection()
	column = MockSteelSection()
	bolt_group = MockBoltGroup()
	plate = MockPlate()
	bfp = BFPConnection(beam=beam, column=column, bolt_group=bolt_group, plate=plate)
	bfp.s1 = 30
	return bfp

def test_cpr():
	bfp = make_bfp()
	assert pytest.approx(bfp.cpr, 0.01) == min((bfp.fy + bfp.fu) / (2 * bfp.fy), 1.2)

def test_m_pr():
	bfp = make_bfp()
	expected = bfp.cpr * bfp.Ry * bfp.beam.Z_ex * bfp.beam.mat.f_y
	assert pytest.approx(bfp.m_pr, 0.01) == expected

def test_get_max_bolt_diameter():
	bfp = make_bfp()
	bf = bfp.beam.geom.b
	db = bf / 2 * (1 - (bfp.Ry * bfp.fy) / (bfp.Rt * bfp.fu)) - 3
	assert pytest.approx(bfp.get_max_bolt_diameter(), 0.01) == db

def test_nominal_shear_force_of_bolt():
	bfp = make_bfp()
	rn1 = bfp.bolt.nominal_shear_force
	rn2 = 2.4 * bfp.bolt.f_uf * bfp.bolt.d_f * bfp.beam.geom.t_f
	rn3 = 2.4 * bfp.plate.f_ui * bfp.bolt.d_f * bfp.plate.t_i
	expected = min(rn1, rn2, rn3)
	assert pytest.approx(bfp.nominal_shear_force_of_bolt(), 0.01) == expected

def test_min_no_bolts():
	bfp = make_bfp()
	phi_n = 0.9
	rn = bfp.nominal_shear_force_of_bolt()
	n = 1.25 * bfp.m_pr / (phi_n * rn * (bfp.beam.geom.b + bfp.plate.t_i))
	assert bfp.min_no_bolts() == int(n) + 1

def test_sh():
	bfp = make_bfp()
	expected = bfp.s1 + bfp.bolt_group.s_p * (bfp.bolt_group.n_b / 2 - 1)
	assert pytest.approx(bfp.sh, 0.01) == expected

