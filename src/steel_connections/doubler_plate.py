from dataclasses import dataclass, field
import enum
from math import isnan, sqrt

import numpy as np


from .connections import Connection
from .member import member
# from .component.bolt import BoltGroup2D
from .component.plate import Plate
# from .bfp_connection import BFPConnection



@dataclass
class DoublerPlate(Plate):
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
    left_beam: member=None
    below_column: member=None
    right_beam: member= None
    above_column: member = None
    name: str = "Continuity Plate"
    description: str = "Continuity Plate for Steel Connections."
    

    # def __post_init__(self):
    #     super.__init__(self, )

    def capacity_of_web(self):
        phi = 0.9
        rn = 0.6 * self.below_column.mat.f_y * self.below_column.geom.d * self.below_column.geom.t_w
        return phi * rn
    
    def vu_p(self, mu1: float, vr: float, mu2: float=0):
        vu_p = mu1 / self.left_beam.geom.d - vr
        if self.right_beam:
            vu_p += mu2 / self.right_beam.geom.d
        return vu_p

    def is_required(self, vup: float):
        rn = self.capacity_of_web()
        return vup > rn
    
    def required_calculated_thickness(self, vup):
        t_calc = vup / (0.6 * self.below_column.mat.f_y * self.below_column.geom.d)
        t_required = t_calc - self.below_column.geom.t_w
        return t_calc, t_required
    
    def required_applicable_thickness(self, vup, double: bool=True):
        _, t_required = self.required_calculated_thickness(vup)
        if double:
            t_required /= 2
        for t in Plate.standard_thickness:
            if t > t_required:
                return t
            

    
            



    
    

    
    
    
    


        




    
    



    


        

        

        

