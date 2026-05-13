from dataclasses import dataclass, field
import enum

import numpy as np

from .connections import Connection
from .member import member
from .component.bolt import BoltGroup2D
from .component.plate import Plate


@enum.unique
class BFPCONNECTIONERROR(enum.IntEnum):
    beam_weight = (1, "Beam weight constraint violation")
    beam_depth = (2, "Beam depth constraint violation")
    max_beam_flange_thickness = (3, "Maximum beam flange thickness exceeded")
    minimum_ln_over_beam_depth_intermediate = (4, "Minimum Ln/beam depth ratio for intermediate moment frames not satisfied")
    minimum_ln_over_beam_depth_special = (5, "Minimum Ln/beam depth ratio for special moment frames not satisfied")
    max_depth_of_H_and_salibi_column_in_moment_frame_with_slab = (6, "Maximum depth of H/Salibi column in moment frame with slab exceeded")
    max_depth_of_H_and_salibi_column_in_moment_frame_without_slab = (7, "Maximum depth of H/Salibi column in moment frame without slab exceeded")
    max_depth_width_of_box_and_HBox_column = (8, "Maximum depth/width of box/HBox column exceeded")
    minimum_grade_of_bolt = (9, "Minimum bolt grade requirement not met")
    max_bolt_diameter = (10, "Maximum bolt diameter exceeded")
    max_web_bolt_diameter = (11, "Maximum web bolt diameter exceeded")
    max_sh = (12, "Maximum sh value exceeded")
    minimum_s3 = (13, "Minimum s3 value not satisfied")
    minimum_s5 = (14, "Minimum s5 value not satisfied")
    check_max_buckling_factor_of_plate = (15, "Maximum buckling factor of plate constraint violation")
    
    def __new__(cls, value: int, description: str):
        obj = int.__new__(cls, value)
        obj._value_ = value
        obj.description = description
        return obj
    
    def __str__(self):
        return f"{self.name}: {self.description}"
    
    @classmethod
    def get_description(cls, value: int) -> str:
        """Get description by value"""
        return cls(value).description



@dataclass
class BFPConnection(Connection):
    """Bolted Flange Plate Connection

    Attributes:
        name (str): Name of the connection.
        description (str): Description of the connection.
        bolt_diameter (float): Diameter of the bolts in mm.
        bolt_grade (str): Grade of the bolts.
        plate_thickness (float): Thickness of the flange plate in mm.
        weld_size (float): Size of the welds in mm.
        num_bolts (int): Number of bolts in the connection.
        bolt_spacing (float): Spacing between bolts in mm.
        edge_distance (float): Edge distance for bolts in mm.
    """

    beam: member.SteelSection
    column: member.SteelSection
    bolt_group: BoltGroup2D | None = None
    plate: Plate | None = None
    bolt_group_web: BoltGroup2D | None = None
    web_plate: Plate | None = None
    s1: float = 7
    beam_length: float = 0
    name: str = "Bolted Flange Plate Connection"
    description: str = "A bolted flange plate connection for steel structures."

    def __post_init__(self):
        self.fy = self.beam.mat.f_y
        self.fu = self.beam.mat.f_u
        self.Ry = self.beam.Ry
        self.Rt = self.beam.Rt
        if self.bolt_group is not None:
            self.bolt = self.bolt_group.bolt
            self.sh = self._sh()
            self.lh = self._lh()
            self.kl = self._kl()
            self.s3 = self._s3()
            self.s5 = self._s5()
        else:
            self.bolt = None
            self.sh = np.nan
            self.lh = np.nan
            self.kl = np.nan
            self.s3 = np.nan
            self.s5 = np.nan
        self.m_p = self._m_p()


    def check_beam_weight(self):
        return self.beam.weight_per_length <= 250
    
    def check_beam_depth(self):
        return self.beam.geom.d <= 100
    
    def check_max_beam_flange_thickness(self):
        return self.beam.geom.t_f <= 3

    def check_minimum_ln_over_beam_depth_intermediate_mf(self):
        return self.beam_length / self.beam.geom.d >= 7
    
    def check_minimum_ln_over_beam_depth_special_mf(self):
        return self.beam_length / self.beam.geom.d >= 9
    
    def check_max_depth_of_H_and_salibi_column_in_moment_frame_with_slab(self):
        return self.column.geom.d <= 100

    def check_max_depth_of_H_and_salibi_column_in_moment_frame_without_slab(self):
        return self.column.geom.d <= 40

    def check_max_depth_width_of_box_and_HBox_column(self):
        return min(self.column.geom.d, self.column.geom.b) <= 75

    def check_minimum_grade_of_bolt(self):
        return self.bolt.f_uf >= 10000

    def check_max_bolt_diameter(self):
        return self.bolt.d_f <= 2.7

    def check_max_web_bolt_diameter(self):
        if self.bolt_group_web is None:
            return True
        return self.bolt_group_web.bolt.d_f <= 2.7

    def check_max_buckling_factor_of_plate(self):
        return self.buckling_factor_of_plate() <= 25

    @property
    def design_code(self) -> str:
        return "Iranian Code (PN-S 2800 / Instruction 360)"

    @property
    def code_refs(self) -> dict[str, str]:
        """بند آیین‌نامه متناظر با هر مرحله محاسبه."""
        return {
            "cpr":          "دستورالعمل ۳۶۰، بند ۱۰-۲-۱",
            "mp":           "دستورالعمل ۳۶۰، بند ۱۰-۲-۱",
            "mpr":          "دستورالعمل ۳۶۰، رابطه ۱۰-۲-۱",
            "bolt_diam":    "دستورالعمل ۳۶۰، رابطه ۱۰-۲-۲",
            "bolt_shear":   "دستورالعمل ۳۶۰، بند ۱۰-۲-۳",
            "n_bolts":      "دستورالعمل ۳۶۰، بند ۱۰-۲-۴",
            "sh_lh":        "دستورالعمل ۳۶۰، بند ۱۰-۲-۵",
            "vh":           "دستورالعمل ۳۶۰، بند ۱۰-۲-۶",
            "mf":           "دستورالعمل ۳۶۰، رابطه ۱۰-۲-۷",
            "fpr":          "دستورالعمل ۳۶۰، رابطه ۱۰-۲-۸",
            "t_min":        "دستورالعمل ۳۶۰، رابطه ۱۰-۲-۹",
            "rupture":      "دستورالعمل ۳۶۰، رابطه ۱۰-۲-۱۰",
            "block_shear":  "دستورالعمل ۳۶۰، رابطه ۱۰-۲-۱۱",
            "buckling":     "دستورالعمل ۳۶۰، رابطه ۱۰-۲-۱۲",
            "preq_beam":    "دستورالعمل ۳۶۰، جدول ۱۰-۲-۱",
            "preq_column":  "دستورالعمل ۳۶۰، جدول ۱۰-۲-۱",
            "preq_bolt":    "دستورالعمل ۳۶۰، بند ۱۰-۲-۲",
        }

    def check_max_sh(self, tolerance=.5):
        return self.sh - tolerance <= self.beam.geom.d
    
    def check_minimum_s3(self):
        if self.plate.t_i <= 1.5:
            return self.s3 >= 2 * self.bolt.d_f
        return self.s3 >= 1.5 * self.bolt.d_f
    
    def check_minimum_s5(self):
        if self.beam.geom.t_f <= 1.5:
            return self.s5 >= 2 * self.bolt.d_f
        return self.s5 >= 1.5 * self.bolt.d_f
    

    @property
    def cpr(self):
        return min((self.fy + self.fu) / (2 * self.fy), 1.2)

    def _m_p(self):
        '''
        step 1
        '''
        m_p = self.beam.geom.Z_x * self.fy
        return m_p
    
    @property
    def m_pr(self):
        '''
        step 1
        '''
        cpr = self.cpr
        m_pr = cpr * self.Ry * self.m_p
        return m_pr
    
    def get_max_bolt_diameter(self):
        '''
        step 2
        '''
        
        bf = self.beam.geom.b
        db = bf / 2 * (1 - (self.Ry * self.fy) / (self.Rt * self.fu)) - 0.3
        return db
    
    def check_distance_between_hole_and_flange_edge_y_direction(self):
        pass
    
    def check_distance_between_hole_and_flange_edge_x_direction(self):
        pass

    def nominal_shear_force_of_bolt_values(self):
        '''
        step 3
        '''
        rn1 = self.bolt.nominal_shear_force
        rn2 = 2.4 * self.bolt.f_uf * self.bolt.d_f * self.beam.geom.t_f
        rn3 = 2.4 * self.plate.f_ui * self.bolt.d_f * self.plate.t_i
        return rn1, rn2, rn3
    
    def nominal_shear_force_of_bolt(self):
        return min(self.nominal_shear_force_of_bolt_values())
    
    def min_no_bolts(self):
        '''
        step 4
        '''
        phi_n = 0.9
        rn = self.nominal_shear_force_of_bolt()
        n = 1.25 * self.m_pr / (phi_n * rn * (self.beam.geom.d + self.plate.t_i))
        return int(n) + 1
    
    def _sh(self):
        '''
        step 5
        distance between column face to center of last hole
        '''
        sh = self.s1 + self.bolt_group.s_p * (self.bolt_group.n_p - 1)
        return sh
    
    def _lh(self) -> float:
        lh = self.beam_length - 2 * self.sh
        return lh
    
    def shear_in_hinge(self, v):
        '''
        step 6
        '''
        vh = 2 * self.m_pr / self.lh + v
        return vh
    
    def probable_moment_in_column_face(self, v):
        '''
        step 7
        '''
        vh = self.shear_in_hinge(v)
        mf = self.m_pr + vh * self.sh
        return mf
    
    def force_of_plate(self, v):
        '''
        step 8
        '''
        mf = self.probable_moment_in_column_face(v)
        fpr = mf / (self.plate.t_i + self.beam.geom.d)
        return fpr
    
    def check_no_of_bolts(self, v):
        '''
        step 9
        '''
        fpr = self.force_of_plate(v)
        rn = self.nominal_shear_force_of_bolt()
        n = int(fpr / (0.9 * rn)) + 1
        return n
    
    def get_minimum_thickness_of_plate(self, v):
        '''
        step 10
        '''
        phi_d = 1.0 # TODO
        fpr = self.force_of_plate(v)
        tmin = fpr / (phi_d * self.plate.f_yi * self.plate.b_i)
        return tmin
    
    def get_net_area_of_plate(self):
        a_nv = (self.plate.b_i - self.bolt_group.n_g * (self.bolt.standard_hole_diameter)) * self.plate.t_i
        return a_nv
    
    def get_net_shear_area_of_plate(self):
        a_nv = (self.sh - (self.bolt_group.n_p - 0.5) * (self.bolt.standard_hole_diameter)) * self.plate.t_i
        return a_nv
    
    def all_shear_area_of_plate(self):
        a_gv = self.sh * self.plate.t_i
        return a_gv
    
    def _s3(self):
        return (self.plate.b_i - self.bolt_group.s_g ) / 2
    
    def _s5(self):
        return (self.beam.geom.b - self.bolt_group.s_g ) / 2
    
    def net_shear_area_in_tensile(self):
        a_nt = (self.s5 - self.bolt.standard_hole_diameter / 2) * self.plate.t_i
        return a_nt

    
    def max_flange_plate_force_according_to_the_limit_state_of_tensile_rupture(self):
        '''
        step 11
        '''
        rn_1 = self.plate.f_ui * self.get_net_area_of_plate()
        return rn_1
    
    def flange_plate_force_block_shear_according_to_fu(self):
        '''
        step 12
        '''
        a_nv = self.get_net_area_of_plate()
        a_nt = self.net_shear_area_in_tensile()
        u_bs = 1
        rn_21 = 0.6 * self.plate.f_ui * a_nv + u_bs * self.plate.f_ui * a_nt
        return rn_21

    def max_flange_plate_force_according_to_the_limit_state_of_block_shear(self):
        u_bs = 1
        a_nt = self.net_shear_area_in_tensile()
        a_gv = self.all_shear_area_of_plate()
        rn_22 = 0.6 * self.plate.f_yi * a_gv + u_bs * self.plate.f_ui * a_nt
        return rn_22
    
    def flange_plate_force_block_shear(self):
        rn_21 = self.flange_plate_force_block_shear_according_to_fu()
        rn_22 = self.max_flange_plate_force_according_to_the_limit_state_of_block_shear()
        rn_2 = min(rn_21, rn_22)
        return rn_2
    
    def check_flange_plate_block_shear(self, v):
        f_pr = self.force_of_plate(v)
        rn_2 = self.flange_plate_force_block_shear()
        phi_n = 0.9
        return (f_pr / 2) < phi_n * rn_2
    
    def _kl(self):
        return 0.65 * self.s1
    
    def buckling_factor_of_plate(self):
        return self.kl / self.plate.r_p
    
    def plate_force_compresion_buckling(self):
        '''
        step 13
        '''
        kl_r = self.buckling_factor_of_plate()
        if kl_r <= 25:
            rn_3 = self.plate.f_yi * self.plate.A_p
        else:
            rn_3 = None # chapter E
        return rn_3
    
    def probable_shear_force_in_column_face(self, v, v_gravity):
        '''
        step 14
        '''
        vh = self.shear_in_hinge(v)
        vu = vh + v_gravity
        return vu
    
    def shear_plate_connection(self):
        dv = self.web_plate.b_i

    #  starting step 15
    def rnv_1(self):
        rnv_1 = 0.55 * self.bolt_group_web.bolt.f_uf * self.bolt_group_web.bolt.A_o
        return 0.75 * rnv_1

    def anv_web(self):
        anv = self.web_plate.t_i * (self.web_plate.h_i - (self.bolt_group_web.n_p * self.bolt_group_web.bolt.standard_hole_diameter))
        return anv
    
    def rnv_2(self):
        anv = self.anv_web()
        rnv_2 = 0.6 * self.web_plate.f_ui * anv
        return 0.75 * rnv_2
    
    def rnv_3(self):
        rnv_3 = 0.6 * self.web_plate.f_yi * self.web_plate.A_g
        return rnv_3
    
    def get_web_plate_a(self):
        a = (self.web_plate.h_i - (self.bolt_group_web.n_p - 1) * self.bolt_group_web.s_p) / 2
        return a
    
    def get_lc(self):
        lc1 = self.bolt_group_web.s_p - self.bolt_group_web.bolt.standard_hole_diameter
        lc2 = self.get_web_plate_a() - self.bolt_group_web.bolt.standard_hole_diameter / 2
        return min(lc1, lc2)
    
    def rnv_41(self):
        lc = self.get_lc()
        rnv_41 = 1.2 * lc * self.web_plate.t_i * self.web_plate.f_ui
        return rnv_41
    
    def rnv_42(self):
        rnv_42 = 2.4 * self.bolt_group_web.bolt.d_f * self.web_plate.t_i * self.web_plate.f_ui
        return rnv_42
    
    def rnv_4(self):
        rnv_41 = self.rnv_41()
        rnv_42 = self.rnv_42()
        rnv_4 = min(rnv_41, rnv_42)
        return 0.75 * rnv_4
    
    def rnv_51(self):
        lc = self.get_lc()
        rnv_51 = 1.2 * lc * self.beam.geom.t_w * self.fu
        return rnv_51
    
    def rnv_52(self):
        rnv_52 = 2.4 * self.bolt_group_web.bolt.d_f * self.beam.geom.t_w * self.fu
        return rnv_52

    def rnv_5(self):
        rnv_51 = self.rnv_51()
        rnv_52 = self.rnv_52()
        rnv_5 = min(rnv_51, rnv_52)
        return 0.75 * rnv_5
    
    def get_agv_web_plate(self):
        return self.web_plate.t_i * (self.web_plate.h_i - self.get_web_plate_a())

    def get_ant_web_plate(self):
        return self.web_plate.t_i * (self.web_plate.b_i - (self.bolt_group_web.bolt.standard_hole_diameter_short_lobiaee)) / 2

    def get_anv_web_plate(self):
        a = self.get_web_plate_a()
        anv = self.web_plate.t_i * ((self.web_plate.h_i - a) - (self.bolt_group_web.n_p - 0.5) * self.bolt_group_web.bolt.standard_hole_diameter)
        return anv
    
    def rnv_61(self):
        '''
        step 15
        '''
        u_bs = 1
        anv_6 = self.get_anv_web_plate()
        ant_6 = self.get_ant_web_plate()
        rnv_61 = self.web_plate.f_ui * (0.6 * anv_6 + u_bs * ant_6)
        return rnv_61
    
    def rnv_62(self):
        '''
        step 15
        '''
        u_bs = 1
        ant_6 = self.get_ant_web_plate()
        agv_6 = self.get_agv_web_plate()
        rnv_62 = 0.6 * self.web_plate.f_yi * agv_6 + u_bs * self.web_plate.f_ui * ant_6
        return rnv_62
    
    def rnv_6(self):
        '''
        step 15
        '''
        rnv_61 = self.rnv_61()
        rnv_62 = self.rnv_62()
        return 0.75 * min(rnv_61, rnv_62)
    
    def get_rnv(self):
        rnv_1 = self.rnv_1() * self.bolt_group.n_b
        rnv_2 = self.rnv_2()
        rnv_3 = self.rnv_3()
        rnv_4 = self.rnv_4() * self.bolt_group.n_b
        rnv_5 = self.rnv_5() * self.bolt_group.n_b
        rnv_6 = self.rnv_6()
        return min(rnv_1, rnv_2, rnv_3, rnv_4, rnv_5, rnv_6)
    
    def check_web_plate_connection(self, lh, v_gravity):
        rnv = self.get_rnv()
        vu = self.probable_shear_force_in_column_face(lh, v_gravity)
        return vu <= rnv

    def check_connection(self):
        errors = []
        if not self.check_beam_weight():
            errors.append(BFPCONNECTIONERROR.beam_weight)
        if not self.check_max_bolt_diameter():
            errors.append(BFPCONNECTIONERROR.max_bolt_diameter)
        if not self.check_beam_depth():
            errors.append(BFPCONNECTIONERROR.beam_depth)
        if not self.check_max_beam_flange_thickness():
            errors.append(BFPCONNECTIONERROR.max_beam_flange_thickness)
        if not self.check_minimum_ln_over_beam_depth_intermediate_mf():
            errors.append(BFPCONNECTIONERROR.minimum_ln_over_beam_depth_intermediate)
        if not self.check_minimum_ln_over_beam_depth_special_mf():
            errors.append(BFPCONNECTIONERROR.minimum_ln_over_beam_depth_special)
        if not self.check_max_depth_of_H_and_salibi_column_in_moment_frame_with_slab():
            errors.append(BFPCONNECTIONERROR.max_depth_of_H_and_salibi_column_in_moment_frame_with_slab)
        if not self.check_max_depth_of_H_and_salibi_column_in_moment_frame_without_slab():
            errors.append(BFPCONNECTIONERROR.max_depth_of_H_and_salibi_column_in_moment_frame_without_slab)
        if not self.check_max_depth_width_of_box_and_HBox_column():
            errors.append(BFPCONNECTIONERROR.max_depth_width_of_box_and_HBox_column)
        if not self.check_minimum_grade_of_bolt():
            errors.append(BFPCONNECTIONERROR.minimum_grade_of_bolt)
        if not self.check_max_web_bolt_diameter():
            errors.append(BFPCONNECTIONERROR.max_web_bolt_diameter)
        if not self.check_max_sh():
            errors.append(BFPCONNECTIONERROR.max_sh)
        if not self.check_minimum_s3():
            errors.append(BFPCONNECTIONERROR.minimum_s3)
        if not self.check_minimum_s5():
            errors.append(BFPCONNECTIONERROR.minimum_s5)
        if not self.check_max_buckling_factor_of_plate():
            errors.append(BFPCONNECTIONERROR.check_max_buckling_factor_of_plate)
        return errors




    


        

        

        

