from dataclasses import dataclass, field
import enum
from math import isnan, sqrt

import numpy as np


from .connections import Connection
# from .member import member
# from .component.bolt import BoltGroup2D
from .component.plate import Plate
# from .bfp_connection import BFPConnection



@dataclass
class ContinuityPlate(Plate):
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
    connection: Connection
    name: str = "Continuity Plate"
    description: str = "Continuity Plate for Steel Connections."
    e: float= np.inf
    

    def __post_init__(self):
        super.__init__(self, )
        self.beam = self.connection.beam
        self.column = self.connection.column


    def check_is_required(self):
        return self.beam.geom.b > 0.15 * self.column.geom.b
    
    def flange_local_bending_force(self, e: float=np.inf):
        '''
        e: distance between non-continues column to above of below beam 
        '''
        rn = 6.25 * self.column.mat.f_y * self.column.geom.t_f ** 2
        if e < 10 * self.column.geom.t_f:
            rn = rn / 2
        return 0.9 * rn
    
    def calculate_tu(self):
        return self.connection.m_p / (self.beam.geom.d - self.beam.geom.t_f)
    
    def get_k(self, ws: float=0.8):
        if hasattr(self.column.geom, 'r_1') and not isnan(self.column.geom.r_1):
            k = self.column.geom.t_f + self.column.geom.r_1
        else:
            k = self.column.geom.t_f + ws
        return k
    
    def web_local_yielding_force(self, e: float=np.inf, ws: float=0.8):
        '''
        ws: Welding size
        '''
        k = self.get_k(ws=ws)
        lb = k
        constant = 5
        if e <= self.beam.geom.d:
            constant = 2.5
        rn = self.column.mat.f_yw * self.column.geom.t_w * (constant * k + lb)
        phi = 1
        return phi * rn
    
    def web_local_crippling_force_1(self, ws: float=0.8):
        t_w = self.column.geom.t_w
        d = self.column.geom.d
        t_f = self.column.geom.t_f
        e = self.column.mat.E
        f_yw = self.column.mat.f_yw
        lb = self.get_k(ws=ws)
        rn_1 = 0.8 * t_w ** 2 * (1 + 3 * (lb / d) * (t_w / t_f) ** 1.5) * sqrt(e * f_yw * t_f / t_w)
        return rn_1
    
    def web_local_crippling_force_3(self, ws: float=0.8):
        t_w = self.column.geom.t_w
        d = self.column.geom.d
        t_f = self.column.geom.t_f
        E = self.column.mat.E
        f_yw = self.column.mat.f_yw
        lb = self.get_k(ws=ws)
        rn_3 = 0.4 * t_w ** 2 * (1 + (4 * lb / d - 0.2) * (t_w / t_f) ** 1.5) * sqrt(E * f_yw * t_f / t_w)
        return rn_3
    
    def get_cr(self, mu: float=np.nan):
        if mu and mu < self.column.my_x:
            return 6.6e6
        return 3.3e6

    def web_sidesway_buckling_force_1(self, constant: float=np.nan, mu: float=np.nan, ws: float=0.8):
        h_c = self.column.h_c(ws)
        if not constant:
            lb = self.beam.geom.d # TODO
            constant = (h_c / self.column.geom.t_w) / (lb / self.column.geom.b)
        cr = self.get_cr(mu)
        rn_1 = cr * self.column.geom.t_w ** 3 * self.column.geom.t_f / h_c ** 2 * (1 + 0.4 * constant ** 3)
        return rn_1
    
    def web_sidesway_buckling_force_2(self, constant: float=np.nan, mu: float=np.nan, ws: float=0.8):
        h_c = self.column.h_c(ws)
        if not constant:
            lb = self.beam.geom.d # TODO
            constant = (h_c / self.column.geom.t_w) / (lb / self.column.geom.b)
        cr = self.get_cr(mu)
        rn_2 = cr * self.column.geom.t_w ** 3 * self.column.geom.t_f / h_c ** 2 * (0.4 * constant ** 3)
        return rn_2
    
    def web_sidesway_buckling_force(self, constant: float=np.nan, mu: float=np.nan, restrained: bool=True, ws: float=0.8):
        lb = self.beam.geom.d # TODO
        constant = (self.column.h_c(ws) / self.column.geom.t_w) / (lb / self.column.geom.b)
        if restrained:
            if constant > 2.3:
                rn = np.inf
            else:
                rn = self.web_sidesway_buckling_force_1(constant=constant, mu=mu)
        else:
            if constant > 1.7:
                rn = np.inf
            else:
                rn = self.web_sidesway_buckling_force_2(constant=constant, mu=mu)
        phi = 0.85
        return phi * rn

    def web_local_crippling_force(self, e: float=np.inf, ws: float=0.8):
        if e >= self.beam.geom.d / 2:
            rn = self.web_local_crippling_force_1(ws=ws)
        else:
            lb = self.get_k(ws=ws)
            if lb / self.beam.geom.d <= 0.2:
                rn = self.web_local_crippling_force_1(ws=ws) / 2
            else:
                rn = self.web_local_crippling_force_3(ws=ws)
        phi = 0.75
        return phi * rn
    
    def web_compression_buckling_force(self, e: float=np.inf, ws: float=0.8):
        rn = 24 * self.column.geom.t_w ** 3 * sqrt(self.column.mat.E * self.column.mat.f_yw) / self.column.h_c(ws)
        if e <= self.beam.geom.d / 2:
            rn /= 2
        phi = 0.9
        return phi * rn
    
    def get_min_force(self, e: float=np.inf, ws: float=0.8):
        rn_1 = self.flange_local_bending_force()
        rn_2 = self.web_local_yielding_force(e, ws)
        rn_3 = self.web_local_crippling_force(e, ws)
        rn_4 = self.web_compression_buckling_force(e, ws)
        return min(rn_1, rn_2, rn_3, rn_4)
    
    def get_continuity_plate_force(self, e: float=np.inf, ws: float=0.8):
        tu = self.calculate_tu()
        rn = self.get_min_force(e, ws)
        return tu - rn

    def check_is_required_continuity_plate(self, e: float=np.inf, ws: float=0.8):
        continuity_plate_force = self.get_continuity_plate_force(e, ws)
        if continuity_plate_force > 0:
            return True
        return False
    
    def get_continuity_plate_width(self):
        return (self.column.geom.b - self.column.geom.t_w) / 2
    
    def min_continuity_plate_thickness(self, e: float=np.inf, ws: float=0.8):
        t1 = self.beam.geom.t_f / 2
        f1 = self.get_continuity_plate_force(e, ws)
        t2 = f1 / (0.9 * self.column.f_y * 2 * self.beam.geom.b)
        return max(t1, t2)
    
    def ag(self):
        return self.b_i * self.h_i
    
    def ip_ap(self):
        tw = self.column.geom.tw
        if self.e <= self.beam.geom.d:
            column_height = 12 * tw
        else:
            column_height = 25 * tw
        ip = tw * (column_height) ** 3 / 12 + 2 * self.b_i * self.h_i ** 3 / 12
        ap = tw * column_height + 2 * self.b_i * self.h_i

        return ip, ap, column_height
    
    def rp(self):
        ip, ap, _ = self.ip_ap()
        return sqrt(ip / ap)
    
    def klr(self):
        '''
        klr < 25
        '''
        kp = 0.75
        rp = self.rp()
        l = self.column.h_c()
        klr = kp * l / rp
        return klr
    
    def tensile_yielding(self):
        phi = 0.9
        klr = self.klr()
        ip, ap = self.ip_ap()
        if klr <= 25:
            rn1 = self.f_yi * ap
        else:
            print("kl/r > 25, please increase the palte thickness")
            return None
        return phi * rn1
    
    def tensile_rupture(self):
        phi = 0.75
        ap = self.ag()
        rn1 = self.f_ui * ap
        return phi * rn1
    
    def get_thickness_of_plate_automatically(self):
        pass

    def check_continuity_plate_is_adequate(self, w: float=0.8):
        f1 = self.get_continuity_plate_force(w=w)
        rn1 = self.tensile_yielding()
        rn2 = self.tensile_rupture()
        rn = min(rn1, rn2)
        if rn > f1:
            return True
        return False

    
    
    
    


        




    
    



    


        

        

        

