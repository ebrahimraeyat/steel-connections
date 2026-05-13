"""
AISC 358-16 Chapter 7 – Bolted Flange Plate (BFP) Moment Connection
====================================================================
All internal geometry units follow the same cm / kgf·cm convention used
by the rest of this package so that the two design-code classes are
interchangeable.

Key limit conversions from imperial to cm / kgf / kgf·cm:
  1 in  = 2.54  cm
  1 ft  = 30.48 cm
  1 kip = 453.6 kgf
  1 ksi = 70.31 kgf/cm²
  3/4 in bolt-hole offset from Eq. 7.6-2 → 1.905 cm
  Beam weight 175 lb/ft → 260.4 kg/m (use 260)
  Beam depth W36  → d ≤ 91.44 cm (use 91)
  Beam flange tf  ≤ 1-1/8 in → 2.857 cm
  Column depth W36 → 91 cm (no slab distinction in AISC 358-16)
  Box column ≤ 16 in → 40.6 cm
  A325 Fu = 120 ksi = 8437 kgf/cm² (minimum bolt grade for AISC 358-16)
"""

from __future__ import annotations

import enum

from .bfp_connection import BFPConnection, BFPCONNECTIONERROR


# ── AISC-specific prequalification error catalogue ──────────────────────────

@enum.unique
class AISC358BFPERROR(enum.IntEnum):
    """
    Prequalification errors defined in AISC 358-16 §7.3 (BFP connection).
    Integer values that do *not* overlap with BFPCONNECTIONERROR so both
    error sets can be combined in a single list without ambiguity.
    """
    beam_weight               = (101, "Beam weight > 175 lb/ft (AISC 358-16 §7.3.1)")
    beam_depth                = (102, "Beam depth > W36 / 36 in  (AISC 358-16 §7.3.1)")
    max_beam_flange_thickness = (103, "Beam flange tf > 1-1/8 in  (AISC 358-16 §7.3.1)")
    min_ln_over_d_smf         = (104, "Ln/d < 7 [SMF]  (AISC 358-16 §7.3.1)")
    min_ln_over_d_imf         = (105, "Ln/d < 7 [IMF]  (AISC 358-16 §7.3.1)")
    max_column_depth          = (106, "Column depth > W36 / 36 in  (AISC 358-16 §7.3.2)")
    max_box_column_dim        = (107, "Box column b or d > 16 in   (AISC 358-16 §7.3.2)")
    minimum_bolt_grade        = (108, "Bolt grade below ASTM A325 minimum  (AISC 358-16 §7.3.5)")
    max_bolt_diameter         = (109, "Bolt diameter exceeds Eq. 7.6-2 limit  (AISC 358-16 §7.6)")
    max_web_bolt_diameter     = (110, "Web bolt diameter > 1 in   (AISC 358-16 §7.3.5)")
    max_sh                    = (111, "sh > beam depth  (AISC 358-16 §7.6)")
    minimum_s3                = (112, "s3 too small  (AISC 358-16 §7.6)")
    minimum_s5                = (113, "s5 too small  (AISC 358-16 §7.6)")
    plate_buckling            = (114, "Plate kL/r > 25  (AISC 358-16 Eq. 7.6-12)")

    def __new__(cls, value: int, description: str):
        obj = int.__new__(cls, value)
        obj._value_ = value
        obj.description = description
        return obj

    def __str__(self) -> str:
        return f"{self.name}: {self.description}"

    @classmethod
    def get_description(cls, value: int) -> str:
        return cls(value).description


# ── conversion constants ─────────────────────────────────────────────────────

_IN_TO_CM   = 2.54          # 1 in  → cm
_LB_FT_TO_KG_M = 1.48816   # 1 lb/ft → kg/m

# AISC 358-16 §7.3 prequalification limits in cm / kg/m
_AISC_MAX_BEAM_WEIGHT_KG_M  = 175  * _LB_FT_TO_KG_M   # ≈ 260.4 kg/m
_AISC_MAX_BEAM_DEPTH_CM     = 36   * _IN_TO_CM          # ≈ 91.44 cm  (W36)
_AISC_MAX_BEAM_TF_CM        = 1.125 * _IN_TO_CM         # ≈ 2.857 cm  (1⅛ in)
_AISC_MIN_LN_OVER_D         = 7                         # both SMF & IMF
_AISC_MAX_COL_DEPTH_CM      = 36   * _IN_TO_CM          # ≈ 91.44 cm  (W36)
_AISC_MAX_BOX_COL_DIM_CM    = 16   * _IN_TO_CM          # ≈ 40.64 cm

# ASTM A325 minimum Fu = 120 ksi → 120 × 70.307 kg/cm²
_AISC_MIN_BOLT_FUF_KG_CM2   = 120  * 70.307             # ≈ 8437 kgf/cm²

# Maximum web bolt diameter: 1 in (AISC 358-16 §7.3.5)
_AISC_MAX_WEB_BOLT_DIAM_CM  = 1.0 * _IN_TO_CM           # 2.54 cm

# Bolt-hole offset for Eq. 7.6-2: 3/4 in
_AISC_EQ762_OFFSET_CM       = 0.75 * _IN_TO_CM          # 1.905 cm


# ── AISC 358-16 BFP connection class ────────────────────────────────────────

class AISC358BFPConnection(BFPConnection):
    """
    BFP connection designed to AISC 358-16 Chapter 7.

    Inherits all calculation methods (M_pr, V_h, M_f, F_pr, plate checks,
    web-plate checks, etc.) from :class:`BFPConnection`. Only the
    prequalification limit-check methods and the bolt-diameter formula
    constant (Eq. 7.6-2) are overridden to reflect AISC 358-16 §7.3
    instead of the Iranian code.

    Units convention (same as base class)
    --------------------------------------
    Lengths : cm
    Forces  : kgf
    Moments : kgf·cm
    Stress  : kgf/cm²
    Weight  : kg/m
    """

    # ── §7.3.1 Beam limitations ──────────────────────────────────────────────

    def check_beam_weight(self) -> bool:
        """AISC 358-16 §7.3.1: Beam weight ≤ 175 lb/ft (≈ 260.4 kg/m)."""
        return self.beam.weight_per_length <= _AISC_MAX_BEAM_WEIGHT_KG_M

    def check_beam_depth(self) -> bool:
        """AISC 358-16 §7.3.1: Beam depth ≤ W36 (d ≤ 36 in ≈ 91.4 cm)."""
        return self.beam.geom.d <= _AISC_MAX_BEAM_DEPTH_CM

    def check_max_beam_flange_thickness(self) -> bool:
        """AISC 358-16 §7.3.1: Beam flange tf ≤ 1-1/8 in (≈ 2.86 cm)."""
        return self.beam.geom.t_f <= _AISC_MAX_BEAM_TF_CM

    def check_minimum_ln_over_beam_depth_intermediate_mf(self) -> bool:
        """AISC 358-16 §7.3.1: Clear span Ln/d ≥ 7 (IMF)."""
        return self.beam_length / self.beam.geom.d >= _AISC_MIN_LN_OVER_D

    def check_minimum_ln_over_beam_depth_special_mf(self) -> bool:
        """AISC 358-16 §7.3.1: Clear span Ln/d ≥ 7 (SMF) — same threshold as IMF."""
        return self.beam_length / self.beam.geom.d >= _AISC_MIN_LN_OVER_D

    # ── §7.3.2 Column limitations ────────────────────────────────────────────

    def check_max_depth_of_H_and_salibi_column_in_moment_frame_with_slab(self) -> bool:
        """AISC 358-16 §7.3.2: W-shape column depth ≤ W36 (≈ 91.4 cm)."""
        return self.column.geom.d <= _AISC_MAX_COL_DEPTH_CM

    def check_max_depth_of_H_and_salibi_column_in_moment_frame_without_slab(self) -> bool:
        """AISC 358-16 §7.3.2: W-shape column depth ≤ W36 — no slab distinction."""
        return self.column.geom.d <= _AISC_MAX_COL_DEPTH_CM

    def check_max_depth_width_of_box_and_HBox_column(self) -> bool:
        """AISC 358-16 §7.3.2: Box column b or d ≤ 16 in (≈ 40.6 cm)."""
        return min(self.column.geom.d, self.column.geom.b) <= _AISC_MAX_BOX_COL_DIM_CM

    # ── §7.3.5 Bolt grade ────────────────────────────────────────────────────

    def check_minimum_grade_of_bolt(self) -> bool:
        """AISC 358-16 §7.3.5: Bolts ≥ ASTM A325 (Fu ≥ 120 ksi ≈ 8 437 kgf/cm²)."""
        return self.bolt.f_uf >= _AISC_MIN_BOLT_FUF_KG_CM2

    # ── §7.3.5 / §7.6 Bolt diameter limits ──────────────────────────────────

    def check_max_web_bolt_diameter(self) -> bool:
        """AISC 358-16 §7.3.5: Web bolt diameter ≤ 1 in (2.54 cm)."""
        if self.bolt_group_web is None:
            return True
        return self.bolt_group_web.bolt.d_f <= _AISC_MAX_WEB_BOLT_DIAM_CM

    def get_max_bolt_diameter(self) -> float:
        """
        AISC 358-16 Eq. 7.6-2.

        db ≤ (bf / 2) × (1 − Ry·Fy / (Rt·Fu)) − 3/4 in
        """
        bf = self.beam.geom.b
        db = bf / 2 * (1 - (self.Ry * self.fy) / (self.Rt * self.fu)) - _AISC_EQ762_OFFSET_CM
        return db

    # ── check_connection – uses AISC error enum ──────────────────────────────

    def check_connection(self) -> list[AISC358BFPERROR]:
        """
        Run all AISC 358-16 §7.3 prequalification checks.

        Returns a (possibly empty) list of :class:`AISC358BFPERROR` members
        for every violated limit.  An empty list means the connection
        passes all checks.
        """
        errors: list[AISC358BFPERROR] = []
        e = AISC358BFPERROR

        if not self.check_beam_weight():
            errors.append(e.beam_weight)
        if not self.check_beam_depth():
            errors.append(e.beam_depth)
        if not self.check_max_beam_flange_thickness():
            errors.append(e.max_beam_flange_thickness)
        if not self.check_minimum_ln_over_beam_depth_intermediate_mf():
            errors.append(e.min_ln_over_d_imf)
        if not self.check_minimum_ln_over_beam_depth_special_mf():
            errors.append(e.min_ln_over_d_smf)
        if not self.check_max_depth_of_H_and_salibi_column_in_moment_frame_with_slab():
            errors.append(e.max_column_depth)
        if not self.check_max_depth_width_of_box_and_HBox_column():
            errors.append(e.max_box_column_dim)
        if not self.check_minimum_grade_of_bolt():
            errors.append(e.minimum_bolt_grade)
        if not self.check_max_bolt_diameter():
            errors.append(e.max_bolt_diameter)
        if not self.check_max_web_bolt_diameter():
            errors.append(e.max_web_bolt_diameter)
        if not self.check_max_sh():
            errors.append(e.max_sh)
        if not self.check_minimum_s3():
            errors.append(e.minimum_s3)
        if not self.check_minimum_s5():
            errors.append(e.minimum_s5)
        if not self.check_max_buckling_factor_of_plate():
            errors.append(e.plate_buckling)

        return errors

    # ── Eq. 7.6-3 wrapper (documented override) ──────────────────────────────

    def min_no_bolts(self) -> int:
        """
        AISC 358-16 §7.6 Step 4.

        n ≥ M_pr / (φ · rn · (d_beam + t_plate))
        φ = 0.9  (non-ductile limit state, bearing on bolt)
        """
        phi_n = 0.9
        rn = self.nominal_shear_force_of_bolt()
        n = 1.25 * self.m_pr / (phi_n * rn * (self.beam.geom.d + self.plate.t_i))
        return int(n) + 1

    # ── Property: design code label ──────────────────────────────────────────

    @property
    def design_code(self) -> str:
        return "AISC 358-16"

    @property
    def code_refs(self) -> dict[str, str]:
        """AISC 358-16 clause references for each design step."""
        return {
            "cpr":          "AISC 358-16 §2.4.3, Eq. 2.4-1",
            "mp":           "AISC 360-16 §F2",
            "mpr":          "AISC 358-16 §2.4.3, Eq. 2.4-2",
            "bolt_diam":    "AISC 358-16 §7.6, Eq. 7.6-2",
            "bolt_shear":   "AISC 358-16 §7.6, Eq. 7.6-3",
            "n_bolts":      "AISC 358-16 §7.6, Step 4",
            "sh_lh":        "AISC 358-16 §7.6, Eq. 7.6-5",
            "vh":           "AISC 358-16 §7.6, Step 6",
            "mf":           "AISC 358-16 §7.6, Eq. 7.6-6",
            "fpr":          "AISC 358-16 §7.6, Eq. 7.6-7",
            "t_min":        "AISC 358-16 §7.6, Eq. 7.6-9",
            "rupture":      "AISC 358-16 §7.6, Eq. 7.6-10",
            "block_shear":  "AISC 358-16 §7.6, Eq. 7.6-11",
            "buckling":     "AISC 358-16 §7.6, Eq. 7.6-12 (KL/r ≤ 25)",
            "preq_beam":    "AISC 358-16 §7.3.1",
            "preq_column":  "AISC 358-16 §7.3.2",
            "preq_bolt":    "AISC 358-16 §7.3.5",
        }
