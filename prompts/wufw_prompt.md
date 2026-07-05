# پرامپت حرفه‌ای: پیاده‌سازی اتصال WUF-W در نرم‌افزار طراحی اتصالات فولادی

---

## Context

You are a senior structural software engineer specializing in steel connection design software. I have an existing open-source steel connection design application written in Python (Qt-based GUI) available at `https://github.com/ebrahimraeyat/steel-connections`. The application currently implements the **Bolted Flange Plate (BFP)** moment connection per **AISC 358-16 Chapter 7**. I need to add full support for the **Welded Unreinforced Flange-Welded Web (WUF-W)** prequalified seismic moment connection per **AISC 358-16 Chapter 8** and **AISC 341-16**.

---

## Objective

Implement a complete, production-ready WUF-W connection design module that integrates seamlessly with the existing codebase architecture, UI patterns, and report generation system.

---

## 1. Technical Requirements & Scope

**Connection Type:** WUF-W (Welded Unreinforced Flange-Welded Web) Moment Connection  
**Governing Codes:** ANSI/AISC 358-16 Chapter 8, AISC 341-16, AWS D1.8/D1.8M:2024  
**Frame Systems:** SMF, IMF, OMF (Special, Intermediate, Ordinary Moment Frames)

### Key Components to Model
- Beam-to-column direct weld connection (no flange plates)
- Complete Joint Penetration (CJP) groove welds for beam flanges to column flange
- Beam web to column flange connection via shear tab (shear plate)
- Weld access holes per **AWS D1.8/D1.8M:2024 Section 6.11.1.2** / **AISC 360-16 J1.6**
- Continuity plates (transverse stiffeners) per **AISC 341-16 E3.6f**
- Panel zone (web doubler plates if required) per **AISC 341-16 E3.6e**
- Protected zone (plastic hinge region) detailing

---

## 2. Geometric & Material Limitations (AISC 358-16 Sec. 8.3)

### Beam Limitations (Table 8.1)
| Parameter | Limit |
|-----------|-------|
| Depth | $d_b \geq 12$ in and $d_b \leq 36$ in (W-shape) |
| Weight | $W_b \leq 150$ lb/ft |
| Flange thickness | $t_{bf} \leq 1$ in |
| Web thickness | $t_{wb} \geq 0.2$ in |
| Flange width-to-thickness ratio | $b_{bf}/(2t_{bf}) \leq 35$ (local buckling prevention) |
| Web depth-to-thickness ratio | $h/t_w \leq 2.45\sqrt{E/F_y}$ per **AISC 341-16 Table D1.1** |
| Material | ASTM A992 ($F_y = 50$ ksi typical) |

### Column Limitations
| Parameter | Limit |
|-----------|-------|
| Depth | $d_c \leq 36$ in (W-shape) |
| Material | ASTM A992 |

### Weld Requirements
- **Flange welds:** CJP groove weld, E70XX, E80XX, or E90XX electrodes
- **Backing bars:** Remove if used (per **AISC 358-16 Sec. 3.4**), or use weld tabs with $45°$ max angle
- **Web weld:** Shear plate to column flange fillet weld + shear plate to beam web fillet weld
- **Weld access hole geometry:** comply with **AWS D1.8/D1.8M:2024 Section 6.11.1.2** and **AISC 360-16 J1.6, J1.7**

---

## 3. Design Checks & Limit States to Implement

Implement the following calculation checks with full formula references and $\phi$ factors per **AISC 358-16 Table A3.1**.

### A. Geometric Verification Checks
1. **Beam geometric limitations** (AISC 358-16 Sec. 8.3.1) — all parameters from Table 8.1
2. **Column geometric limitations** (AISC 358-16 Sec. 8.3.2)
3. **Weld access hole geometry** (AISC 360-16 J1.6, J1.7 & AWS D1.8/D1.8M:2024 Sec. 6.11.1.2)
   - Minimum length, height, and surface finish requirements
4. **Shear plate geometry requirements** (AISC 358-16 Sec. 8.6 / Fig. 8.2):
   - Plate height: $h_p \geq \frac{2}{3} d_b$ and must overlap weld access holes by $6–12$ mm
   - Plate width: $b_p \geq \frac{b_{fb}}{2}$ and must extend $\geq 50$ mm beyond access hole
   - Plate thickness: $t_p \geq t_{wb}$ (beam web thickness)

### B. Strength & Capacity Checks
5. **Beam design shear strength** (AISC 358-16 Sec. 8.7)
6. **Beam flexural strength:** $\phi M_n \geq M_u$ where $M_n = M_p = F_y Z_x$ **(AISC 360-16 Eq. F2-1)**
   - **CRITICAL:** Verify $\lambda \leq \lambda_p$ for the section to be **Compact** before using $M_p$. If $\lambda > \lambda_p$, use $M_n \leq M_p$ per local buckling provisions (AISC 360-16 Chapter F).
7. **Column-beam strength relationship / Strong Column-Weak Beam check** (AISC 358-16 Sec. 8.4, AISC 341-16 E3.4a):
   $$\frac{\sum M^*_{pc}}{\sum M^*_{pb}} \geq 1.0$$
   Where:
   - $M_{pc} = Z_c \left(F_{yc} - \frac{P_{uc}}{A_g}\right)$
   - $M_{pb} = Z_b F_{yb}$
   - If ratio $< 1.0$, apply amplification factor per AISC 341-16.
8. **Beam flange-to-column flange CJP weld strength** (AISC 358-16 Sec. 8.5):
   - Weld strength must equal the tensile strength of the connected member.
   - **CRITICAL:** Use $\phi = 0.9$ for CJP groove welds (NOT 0.75). The factor 0.75 applies to shear and fillet welds only.
9. **Beam web-to-column connection strength:**
   - Shear plate to column flange weld capacity
   - Shear plate to beam web weld capacity (must extend on sloped and vertical sides, terminating $12–25$ mm from access holes)
   - Shear plate shear capacity
   - Bolt capacity (if applicable for erection bolts)
10. **Continuity plate requirements** (AISC 341-16 E3.6f.2)
    - Check if $t_{cf} < 0.4\sqrt{b_{bf} t_{bf}}$ (approximate trigger); if true, require continuity plates.
11. **Panel zone shear strength** (AISC 341-16 E3.6e, Eq. E3-6a)
    - Check required thickness; if insufficient, require doubler plates.
12. **Protected zone welding restrictions** (AISC 358-16 Sec. 2.3.2a):
    - For built-up beams: CJP + min $5/16$" ($8$ mm) fillet reinforcement extending from beam end to at least $d_b$ beyond plastic hinge.
    - For rolled W-shapes: standard mill practice acceptable within protected zone limits.

### C. Seismic-Specific Checks
13. **Moment at connection face** (AISC 358-16 Sec. 8.7):
    $$M_f = M_p + V_u \left(\frac{d_b}{2} - t_p\right)$$
    Where $V_u$ = required shear strength and $t_p$ = shear plate thickness.
14. **Plastic hinge location:** Assumed at face of column (AISC 358-16 Sec. 8.7). Note: FEMA 350 suggests $d_b/2$ from column face, but code uses face of column.
15. **Local flange buckling control** (AISC 341-16 Sec. D1.2a)
16. **Lateral-torsional buckling control** (AISC 360-16 Chapter F2/F3)
17. **Cyclic loading resistance** for SMF (deformation capacity verification)

---

## 4. Software Architecture Requirements

### Base Class Design (CRITICAL for Maintainability)
Create an abstract base class **`SteelMomentConnection`** that both BFP and WUF-W inherit from. Implement shared methods such as:
- `check_strong_column_weak_beam()`
- `check_panel_zone()`
- `check_continuity_plates()`
- `generate_report()`
- `validate_geometry()`

### Integration Pattern
- Create a new **`WUFWConnection`** class inheriting from `SteelMomentConnection`
- Add `ConnectionType.WUFW` to the enum/type system
- Implement **`WUFWDesignCalculator`** with methods mapping to each check above
- Reuse existing utilities: section properties database, material constants, weld strength calculators, report generators
- Add WUF-W specific UI panel in the connection configuration dialog (Qt widgets)

### Input Parameters
- Beam section (W-shape, e.g., W14x38)
- Column section (W-shape, e.g., W14x120)
- Material grades ($F_y$, $F_u$ for beam, column, plate, weld electrode)
- Shear plate dimensions ($h_p, b_p, t_p$) — auto-suggest defaults based on beam section
- Weld sizes (fillet weld leg size for web connections)
- Continuity plate option (auto-calculate required vs. user-defined)
- Doubler plate option (auto-calculate required vs. user-defined)
- Load demands: $M_u, V_u, P_u$ (LRFD)
- Overstrength factors: $R_y = 1.1$, $R_t = 1.1$ for A992 steel (per **AISC 341-16 Table A3.1**)

### Output & Reporting
- Pass/Fail status for each check with code references
- Critical limit state (governing failure mode)
- Required vs. provided capacity ratios
- Material takeoff: weld lengths, plate weights, bolt counts
- **Bilingual output:** Export to PDF/Excel in **Persian (Farsi)** with English technical terms in parentheses
- Include sketch/diagram generation showing access hole dimensions and shear plate layout

### Visualization Requirements
Include 2D/3D visualization of:
- Weld access hole geometry (dimensions, slopes, finish)
- Shear plate placement and weld extents
- CJP flange welds and backing bar details
- Continuity plates (if required)
- Protected zone boundaries

---

## 5. Implementation Notes & Critical Code Details

### Shear Plate Details (AISC 358-16 Fig. 8.2)
- The shear plate must be **fillet welded** to the column flange and beam web.
- The weld between plate and beam web must extend on both sloped sides and the vertical side, terminating $12–25$ mm from the access holes.
- When backing bars are not used, a weld tab (cascade weld) within the CJP bevel at max $45°$ is permitted; these tab welds do not require NDT.
- The beam web connection to column flange is through the shear plate only; direct web-to-column CJP is not the standard WUF-W detail.

### Protected Zone
- For built-up beams: CJP groove welds + min $8$ mm reinforcing fillet welds extending from beam end to at least $d_b$ beyond the plastic hinge location.
- For rolled W-shapes: standard mill practice is acceptable if within protected zone limits.

### Panel Zone & Continuity Plates
- Check if continuity plates are required per **AISC 341-16 E3.6f.2**.
- Check panel zone thickness per **AISC 341-16 E3.6e(2)**; if insufficient, require doubler plates.

### LRFD Factors
- Use LRFD methodology exclusively
- $\phi = 0.9$ for ductile limit states (yielding, CJP welds)
- $\phi = 0.75$ for non-ductile limit states (fracture, shear, fillet welds, bolts)

---

## 6. Deliverables

1. **Core Module:** `wufw_connection.py` with full design logic
2. **Base Class:** `steel_moment_connection.py` (refactor BFP to use shared base)
3. **UI Components:** Qt widgets for WUF-W input/configuration
   - Dedicated WUF-W tab in main window
   - Graphic preview of welds, shear plate, and access holes using **matplotlib** or **PyQtGraph**
4. **Report Generator:** WUF-W specific report template (bilingual PDF/Excel)
5. **Validation Suite:** Unit tests comparing against:
   - **AISC 358-16 Design Example 8.1**
   - **Ricles et al. (2000)** experimental specimens (Baseline T1, T5, C1-C4) with exact dimensions and material properties
   - **IDEA StatiCa** verification benchmarks
6. **Documentation:** Persian user guide section explaining:
   - Differences between WUF-W and BFP
   - Plastic hinge formation mechanism
   - Importance of weld access holes and their impact on connection behavior
   - Shop fabrication and field erection steps for WUF-W

---

## 7. Constraints & Assumptions

- **Python 3.10+**, PyQt5/6 compatible, existing project dependencies only
- **LRFD methodology** exclusively
- **Overstrength factors:** $R_y = 1.1$, $R_t = 1.1$ for A992 steel (verify per **AISC 341-16 Table A3.1**)
- **Default materials:** ASTM A992 for beams/columns, A36 for plates unless specified otherwise
- **Weld electrode:** E70XX default
- **Code versions:** AISC 358-16, AISC 341-16, AWS D1.8/D1.8M:2024
- **Frame type:** SMF (Special Moment Frame) as default design basis; extendable to IMF/OMF

---

## 8. UI/UX Requirements

- **Dedicated WUF-W Tab:** Separate configuration panel in the main application window
- **Auto-Suggest:** Default values for shear plate dimensions based on selected beam section
- **Real-Time Validation:** Highlight out-of-range inputs immediately (e.g., $b_{bf}/t_{bf} > 35$)
- **Graphic Preview:**
  - 2D elevation view showing beam, column, shear plate, welds, and access holes
  - Dimension annotations for critical geometries
  - Color-coded pass/fail indicators on the diagram
- **Report Preview:** In-app preview of the generated bilingual report before export

---

## 9. Validation & Testing Requirements

Provide unit tests with exact numerical verification against:

| Reference | Test Case | Key Parameters |
|-----------|-----------|----------------|
| AISC 358-16 Example 8.1 | Design example | WUF-W with W24x62 beam, W14x120 column |
| Ricles et al. (2000) | Specimen T1 | Baseline WUF-W, verify moment capacity |
| Ricles et al. (2000) | Specimen T5 | Modified WUF-W, verify cyclic behavior |
| Ricles et al. (2000) | Specimens C1-C4 | Column continuity variations |
| IDEA StatiCa | Benchmark | Compare capacity ratios and stress distribution |

---

> **Please implement the complete WUF-W connection module following the above specifications, ensuring code quality, full compliance with AISC 358-16 Chapter 8 and AISC 341-16, and seamless integration with the existing BFP connection architecture. Prioritize the creation of the `SteelMomentConnection` base class to maximize code reuse and maintainability.**
