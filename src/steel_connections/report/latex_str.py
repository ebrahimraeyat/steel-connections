# -*- coding: utf-8 -*-
"""
LaTeX formula string templates for BFP (Bolted Flange Plate) connection design.

Two kinds of strings are provided for every design step:
    - Template (no values)  → used in "Formulation" sections
    - Value-substituted     → used in "Calculation" sections

All strings are raw strings compatible with matplotlib.mathtext
(dollar-delimited, no full LaTeX preamble needed).
Fractions use \\frac{}{}, subscripts/superscripts use _ and ^.
"""

from __future__ import annotations

# ═══════════════════════════════════════════════════════════════════════════════
#  Step 1 — Strain-hardening factor and probable moment
# ═══════════════════════════════════════════════════════════════════════════════

cpr_template = r"C_{pr} = \min\!\left(\frac{F_y + F_u}{2\,F_y},\ 1.2\right)"

def cpr_with_values(fy: float, fu: float, cpr: float) -> str:
    return (
        rf"C_{{pr}} = \min\!\left(\frac{{{fy:.0f}+{fu:.0f}}}{{2\times{fy:.0f}}},\ 1.2\right)"
        rf"= {cpr:.3f}"
    )


mp_template = r"M_p = Z_x \cdot F_y"

def mp_with_values(Zx: float, fy: float, mp: float) -> str:
    return rf"M_p = {Zx:.2f}\times{fy:.0f} = {mp:.1f}\ \mathrm{{kg\cdot cm}}"


mpr_template = r"M_{pr} = C_{pr}\cdot R_y\cdot M_p"

def mpr_with_values(cpr: float, Ry: float, mp: float, mpr: float) -> str:
    return (
        rf"M_{{pr}} = {cpr:.3f}\times{Ry:.2f}\times{mp:.1f}"
        rf"= {mpr:.1f}\ \mathrm{{kg\cdot cm}}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  Step 2 — Maximum bolt diameter
# ═══════════════════════════════════════════════════════════════════════════════

db_max_template = (
    r"d_{b,\max} = \frac{b_f}{2}\left(1 - \frac{R_y F_y}{R_t F_u}\right) - 0.3"
)

def db_max_with_values(bf: float, Ry: float, fy: float, Rt: float, fu: float,
                        db_max: float) -> str:
    return (
        rf"d_{{b,\max}} = \frac{{{bf:.2f}}}{{2}}"
        rf"\!\left(1-\frac{{{Ry:.2f}\times{fy:.0f}}}{{{Rt:.2f}\times{fu:.0f}}}\right)-0.3"
        rf"= {db_max:.3f}\ \mathrm{{cm}}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  Step 3 — Nominal shear force per bolt
# ═══════════════════════════════════════════════════════════════════════════════

rn1_template = r"R_{n,1} = 0.55\,F_{uf}\,A_o"

def rn1_with_values(fuf: float, Ao: float, rn1: float) -> str:
    return rf"R_{{n,1}} = 0.55\times{fuf:.0f}\times{Ao:.3f} = {rn1:.2f}\ \mathrm{{kg}}"


rn2_template = r"R_{n,2} = 2.4\,F_{uf}\,d_f\,t_f\quad\text{(beam flange bearing)}"

def rn2_with_values(fuf: float, df: float, tf: float, rn2: float) -> str:
    return (
        rf"R_{{n,2}} = 2.4\times{fuf:.0f}\times{df:.2f}\times{tf:.2f}"
        rf" = {rn2:.2f}\ \mathrm{{kg}}"
    )


rn3_template = r"R_{n,3} = 2.4\,F_{up}\,d_f\,t_p\quad\text{(plate bearing)}"

def rn3_with_values(fup: float, df: float, tp: float, rn3: float) -> str:
    return (
        rf"R_{{n,3}} = 2.4\times{fup:.0f}\times{df:.2f}\times{tp:.2f}"
        rf" = {rn3:.2f}\ \mathrm{{kg}}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  Step 4 — Minimum number of bolts
# ═══════════════════════════════════════════════════════════════════════════════

n_min_template = (
    r"n_{min} = \frac{1.25\,M_{pr}}{\phi\,R_n\,(d_b + t_p)}"
)

def n_min_with_values(mpr: float, phi: float, rn: float,
                       d: float, tp: float, n_min: int) -> str:
    return (
        rf"n_{{min}} = \frac{{1.25\times{mpr:.1f}}}{{{phi:.1f}\times{rn:.2f}"
        rf"\times({d:.2f}+{tp:.2f})}} = {n_min}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  Step 5 — Connection geometry
# ═══════════════════════════════════════════════════════════════════════════════

sh_template = r"s_h = s_1 + s_p\,(n_p - 1)"

def sh_with_values(s1: float, sp: float, np_: int, sh: float) -> str:
    return rf"s_h = {s1:.2f} + {sp:.2f}\times({np_}-1) = {sh:.2f}\ \mathrm{{cm}}"


lh_template = r"L_h = L - 2\,s_h"

def lh_with_values(L: float, sh: float, lh: float) -> str:
    return rf"L_h = {L:.2f} - 2\times{sh:.2f} = {lh:.2f}\ \mathrm{{cm}}"


kl_template = r"KL = 0.65\,s_1"

def kl_with_values(s1: float, kl: float) -> str:
    return rf"KL = 0.65\times{s1:.2f} = {kl:.2f}\ \mathrm{{cm}}"


# ═══════════════════════════════════════════════════════════════════════════════
#  Step 6 — Shear at plastic hinge
# ═══════════════════════════════════════════════════════════════════════════════

vh_template = r"V_h = \frac{2\,M_{pr}}{L_h} + V_{gravity}"

def vh_with_values(mpr: float, lh: float, v: float, vh: float) -> str:
    return (
        rf"V_h = \frac{{2\times{mpr:.1f}}}{{{lh:.2f}}} + {v:.1f}"
        rf" = {vh:.2f}\ \mathrm{{kg}}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  Step 7 — Probable moment at column face
# ═══════════════════════════════════════════════════════════════════════════════

mf_template = r"M_f = M_{pr} + V_h\,s_h"

def mf_with_values(mpr: float, vh: float, sh: float, mf: float) -> str:
    return (
        rf"M_f = {mpr:.1f} + {vh:.2f}\times{sh:.2f}"
        rf" = {mf:.1f}\ \mathrm{{kg\cdot cm}}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  Step 8 — Required plate force
# ═══════════════════════════════════════════════════════════════════════════════

fpr_template = r"F_{pr} = \frac{M_f}{d_b + t_p}"

def fpr_with_values(mf: float, d: float, tp: float, fpr: float) -> str:
    return (
        rf"F_{{pr}} = \frac{{{mf:.1f}}}{{{d:.2f}+{tp:.2f}}}"
        rf" = {fpr:.1f}\ \mathrm{{kg}}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  Step 9 — Required bolt count under F_pr
# ═══════════════════════════════════════════════════════════════════════════════

n_req_template = r"n_{req} = \frac{F_{pr}}{\phi\,R_n}"

def n_req_with_values(fpr: float, phi: float, rn: float, n_req: int) -> str:
    return (
        rf"n_{{req}} = \frac{{{fpr:.1f}}}{{{phi:.1f}\times{rn:.2f}}}"
        rf" = {n_req}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  Step 10 — Minimum plate thickness
# ═══════════════════════════════════════════════════════════════════════════════

tmin_template = r"t_{min} = \frac{F_{pr}}{\phi_d\,F_{yp}\,b_p}"

def tmin_with_values(fpr: float, phi_d: float, fyp: float,
                      bp: float, tmin: float) -> str:
    return (
        rf"t_{{min}} = \frac{{{fpr:.1f}}}{{{phi_d:.1f}\times{fyp:.0f}\times{bp:.2f}}}"
        rf" = {tmin:.3f}\ \mathrm{{cm}}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  Step 11 — Tensile rupture of plate
# ═══════════════════════════════════════════════════════════════════════════════

rup_template = r"\phi R_{n,rup} = \phi\,F_{up}\,A_{np}"

def rup_with_values(phi: float, fup: float, anp: float, rn_rup: float) -> str:
    return (
        rf"\phi R_{{n,rup}} = {phi:.1f}\times{fup:.0f}\times{anp:.3f}"
        rf" = {rn_rup:.1f}\ \mathrm{{kg}}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  Step 12 — Block shear
# ═══════════════════════════════════════════════════════════════════════════════

bs_template = (
    r"\phi R_{n,bs} = \phi\,\min\!\left("
    r"0.6\,F_{up}\,A_{nv}+F_{up}\,A_{nt},\;"
    r"0.6\,F_{yp}\,A_{gv}+F_{up}\,A_{nt}\right)"
)

def bs_with_values(phi: float, fup: float, anv: float, ant: float,
                    fyp: float, agv: float, rn_bs: float) -> str:
    v1 = 0.6 * fup * anv + fup * ant
    v2 = 0.6 * fyp * agv + fup * ant
    return (
        rf"\phi R_{{n,bs}} = {phi:.1f}\times\min({v1:.1f},\ {v2:.1f})"
        rf" = {phi*rn_bs:.1f}\ \mathrm{{kg}}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  Step 13 — Plate compression buckling
# ═══════════════════════════════════════════════════════════════════════════════

kl_r_template = r"\frac{KL}{r} = \frac{0.65\,s_1}{r_p} \leq 25"

def kl_r_with_values(kl: float, rp: float, kl_r: float) -> str:
    return (
        rf"\frac{{KL}}{{r}} = \frac{{{kl:.2f}}}{{{rp:.3f}}}"
        rf" = {kl_r:.2f}"
        + (r"\ \leq 25\ \checkmark" if kl_r <= 25 else r"\ > 25\ \times")
    )


buck_template = r"\phi R_{n,buck} = F_{yp}\,A_p\quad (KL/r\leq 25)"

def buck_with_values(fyp: float, Ap: float, rn_buck: float) -> str:
    return (
        rf"\phi R_{{n,buck}} = {fyp:.0f}\times{Ap:.3f}"
        rf" = {rn_buck:.1f}\ \mathrm{{kg}}"
    )
