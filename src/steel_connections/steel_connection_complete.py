"""
steel_connections_complete.py
ماژول کامل محاسبات اتصالات فولادی بر اساس مبحث دهم مقررات ملی ساختمان (ویرایش ۱۴۰۱)

این ماژول شامل توابع محاسباتی برای:
- پیچ‌های پرمقاومت (اتکایی و اصطکاکی)
- جوش‌ها (گوشه، شیاری CJP، شیاری PJP)
- اندرکنش کشش و برش
- اتکای ورق، گسیختگی قالبی، بلوک برشی
- ورق پرکننده، سخت‌کننده‌های عرضی
- کف‌ستون، میل‌مهارها
- مهاربندهای کمانش‌تاب (BRB)
- اتصالات لرزه‌ای (RBS، BFEM، WUF-B، BFP)
- وصله‌ها و فاصله پیچ‌ها



شماره	تابع	شرح
1	bolt_shear_tension	برش/کشش خالص پیچ
2	bolt_interaction	اندرکنش کشش+برش در پیچ
3	slip_critical_bolt	پیچ اصطکاکی
4	bearing_strength	اتکای ورق
5	tearout_strength	گسیختگی قالبی
6	block_shear	بلوک برشی
7	fillet_weld_strength	جوش گوشه
8	cjp_weld_strength	جوش CJP
9	pjp_weld_strength	جوش PJP
10	combined_load_weld	اندرکنش نیروها در جوش
11	filler_plate_reduction	ضریب کاهش ورق پرکننده
12	stiffener_local_buckling_check	کمانش موضعی سخت‌کننده
13	stiffener_moment_of_inertia_required	ممان اینرسی موردنیاز سخت‌کننده
14	concrete_bearing_strength	اتکای بتن زیر کف‌ستون
15	base_plate_bending	خمش صفحه کف‌ستون
16	anchor_rod_strength	میل‌مهار
17	brb_connection_required_strength	مقاومت موردنیاز اتصال BRB
18	brb_casing_buckling_check	کمانش غلاف BRB
19	rbs_moment_strength	اتصال RBS
20	bfem_check	اتصال BFEM
21	panel_zone_strength	چشمه اتصال
22	bfp_bolt_tension	نیروی پیچ در اتصال BFP
23	column_splice_bearing	وصله اتکایی ستون
24	beam_splice_forces	نیروهای وصله تیر
25	bolt_spacing_check	بررسی فاصله پیچ‌ها
26	print_strength_result	چاپ نتایج
"""

from enum import Enum
from dataclasses import dataclass
import math
from typing import Optional, Tuple


# ============================================================================
# Enum‌های تعریف انواع
# ============================================================================

class BoltType(Enum):
    """نوع پیچ پرمقاومت"""
    A325 = "A325"
    A490 = "A490"


class LoadType(Enum):
    """نوع بارگذاری"""
    SHEAR = "shear"
    TENSION = "tension"


class DesignMethod(Enum):
    """روش طراحی"""
    LRFD = "LRFD"
    ASD = "ASD"


class SurfaceClass(Enum):
    """کلاس سطح برای اتصالات اصطکاکی"""
    CLASS_A = "A"  # μ = 0.33
    CLASS_B = "B"  # μ = 0.50
    CLASS_C = "C"  # μ = 0.33


class HoleType(Enum):
    """نوع سوراخ برای اتصالات اصطکاکی"""
    STANDARD = "standard"      # h_f = 1.0
    OVERSIZED = "oversized"    # h_f = 0.85
    SLOTTED = "slotted"        # h_f = 0.70


class ElectrodeClass(Enum):
    """کلاس الکترود جوش"""
    E60 = "E60"   # F_EXX = 420 MPa
    E70 = "E70"   # F_EXX = 480 MPa
    E80 = "E80"   # F_EXX = 550 MPa


class LimitState(Enum):
    """حالت حدی برای جوش CJP"""
    SHEAR_YIELD = "shear_yield"
    SHEAR_RUPTURE = "shear_rupture"
    TENSION_RUPTURE = "tension_rupture"


class SteelGrade(Enum):
    """گرید فولاد برای میل‌مهار"""
    A36 = "A36"           # F_ua = 400 MPa
    A449 = "A449"         # F_ua = 550 MPa
    A193_B7 = "A193_B7"   # F_ua = 725 MPa


# ============================================================================
# کلاس‌های کمکی
# ============================================================================

@dataclass
class StrengthResult:
    """
    کلاس نگهداری نتایج مقاومت
    Attributes:
        nominal: مقاومت اسمی (R_n) بر حسب N یا N·mm
        design: مقاومت طراحی (φ×R_n برای LRFD یا R_n/Ω برای ASD) بر حسب واحد مشابه
        allowable: مقاومت مجاز (R_n/Ω برای ASD یا φ×R_n برای LRFD) بر حسب واحد مشابه
    """
    nominal: float
    design: float
    allowable: float


@dataclass
class BoltSpacingResult:
    """نتیجه بررسی فاصله پیچ‌ها"""
    is_min_spacing_ok: bool
    is_max_spacing_ok: bool
    is_min_edge_ok: bool
    is_max_edge_ok: bool
    message: str


# ============================================================================
# مقادیر کمکی ثابت
# ============================================================================

E_STEEL = 200000.0  # MPa - مدول الاستیسیته فولاد
G_STEEL = 76900.0   # MPa - مدول برشی فولاد


# ============================================================================
# بخش 1: پیچ‌ها (Bolts)
# ============================================================================

def bolt_shear_tension(
    bolt_type: BoltType,
    load_type: LoadType,
    diameter_mm: float,
    has_thread: bool = False,
    design_method: DesignMethod = DesignMethod.LRFD
) -> StrengthResult:
    """
    محاسبه مقاومت پیچ در برابر برش خالص یا کشش خالص (اتکایی)
    
    Args:
        bolt_type: نوع پیچ (A325 یا A490)
        load_type: نوع بار (shear یا tension)
        diameter_mm: قطر پیچ بر حسب میلی‌متر
        has_thread: آیا رزوه در صفحه برش قرار دارد؟ (فقط برای shear معنی دارد)
        design_method: روش طراحی (LRFD یا ASD)
    
    Returns:
        StrengthResult شامل مقاومت اسمی، طراحی و مجاز
    """
    # جدول مقادیر F_n (MPa)
    bolt_data = {
        (BoltType.A325, "shear", False): 330.0,
        (BoltType.A325, "shear", True): 260.0,
        (BoltType.A325, "tension", False): 620.0,
        (BoltType.A490, "shear", False): 410.0,
        (BoltType.A490, "shear", True): 330.0,
        (BoltType.A490, "tension", False): 780.0,
    }
    
    key = (bolt_type, load_type.value, has_thread if load_type == LoadType.SHEAR else False)
    F_n = bolt_data.get(key)
    
    if F_n is None:
        raise ValueError(f"ترکیب نامعتبر: bolt_type={bolt_type}, load_type={load_type}, has_thread={has_thread}")
    
    # مساحت اسمی پیچ
    A_b = math.pi * (diameter_mm ** 2) / 4.0
    
    # مقاومت اسمی
    R_n = F_n * A_b  # N
    
    phi = 0.75
    omega = 2.00
    
    if design_method == DesignMethod.LRFD:
        strength_design = phi * R_n
        strength_allowable = R_n / omega
    else:
        strength_design = R_n / omega
        strength_allowable = phi * R_n
    
    return StrengthResult(nominal=R_n, design=strength_design, allowable=strength_allowable)


def bolt_interaction(
    bolt_type: BoltType,
    diameter_mm: float,
    shear_force_n: float,
    tension_force_n: float,
    has_thread: bool = False,
    design_method: DesignMethod = DesignMethod.LRFD
) -> Tuple[float, bool]:
    """
    بررسی اندرکنش کشش و برش در پیچ (روش اتکایی)
    
    شرط: (f_rv / F_nv)² + (f_rt / F_nt)² ≤ 1.0
    
    Args:
        bolt_type: نوع پیچ
        diameter_mm: قطر پیچ (mm)
        shear_force_n: نیروی برشی وارد بر پیچ (N)
        tension_force_n: نیروی کششی وارد بر پیچ (N)
        has_thread: آیا رزوه در صفحه برش است؟
        design_method: روش طراحی
    
    Returns:
        (interaction_ratio, is_acceptable) - نسبت اندرکنش و وضعیت قبولی
    """
    # محاسبه F_nv و F_nt
    shear_result = bolt_shear_tension(bolt_type, LoadType.SHEAR, diameter_mm, has_thread, design_method)
    tension_result = bolt_shear_tension(bolt_type, LoadType.TENSION, diameter_mm, False, design_method)
    
    A_b = math.pi * (diameter_mm ** 2) / 4.0
    
    # اگر روش LRFD باشد، از نیروی فاکتور شده استفاده می‌شود
    # در این تابع فرض می‌شود نیروهای ورودی قبلاً فاکتور شده‌اند
    f_rv = shear_force_n / A_b  # MPa - تنش برشی
    f_rt = tension_force_n / A_b  # MPa - تنش کششی
    
    # مقادیر اسمی F_nv و F_nt از جدول
    bolt_data = {
        (BoltType.A325, False): 330.0,
        (BoltType.A325, True): 260.0,
        (BoltType.A490, False): 410.0,
        (BoltType.A490, True): 330.0,
    }
    
    F_nv = bolt_data.get((bolt_type, has_thread))
    F_nt = 620.0 if bolt_type == BoltType.A325 else 780.0
    
    if F_nv is None:
        raise ValueError(f"ترکیب نامعتبر برای F_nv: bolt_type={bolt_type}, has_thread={has_thread}")
    
    # محاسبه نسبت اندرکنش
    ratio = (f_rv / F_nv) ** 2 + (f_rt / F_nt) ** 2
    
    is_acceptable = ratio <= 1.0
    
    return ratio, is_acceptable


def slip_critical_bolt(
    diameter_mm: float,
    bolt_grade: BoltType,
    surface_class: SurfaceClass = SurfaceClass.CLASS_A,
    hole_type: HoleType = HoleType.STANDARD,
    num_shear_planes: int = 1,
    design_method: DesignMethod = DesignMethod.LRFD
) -> StrengthResult:
    """
    محاسبه مقاومت لغزشی پیچ‌های اصطکاکی (Slip-Critical)
    
    فرمول: R_n = μ × D_u × h_f × T_b × N_s
    
    Args:
        diameter_mm: قطر پیچ (mm)
        bolt_grade: نوع پیچ (A325 یا A490)
        surface_class: کلاس سطح (A, B, C)
        hole_type: نوع سوراخ
        num_shear_planes: تعداد سطوح برش
        design_method: روش طراحی
    
    Returns:
        StrengthResult شامل مقاومت اسمی، طراحی و مجاز
    """
    # ضریب اصطکاک بر اساس کلاس سطح
    mu_values = {
        SurfaceClass.CLASS_A: 0.33,
        SurfaceClass.CLASS_B: 0.50,
        SurfaceClass.CLASS_C: 0.33,
    }
    mu = mu_values.get(surface_class, 0.33)
    
    D_u = 1.13
    
    # ضریب h_f بر اساس نوع سوراخ
    hf_values = {
        HoleType.STANDARD: 1.00,
        HoleType.OVERSIZED: 0.85,
        HoleType.SLOTTED: 0.70,
    }
    h_f = hf_values.get(hole_type, 1.00)
    
    # جدول T_b (kN) بر اساس قطر و نوع پیچ
    tb_table = {
        (16, BoltType.A325): 91.0,
        (20, BoltType.A325): 142.0,
        (22, BoltType.A325): 176.0,
        (24, BoltType.A325): 205.0,
        (27, BoltType.A325): 267.0,
        (30, BoltType.A325): 327.0,
        (36, BoltType.A325): 476.0,
        (16, BoltType.A490): 114.0,
        (20, BoltType.A490): 179.0,
        (22, BoltType.A490): 222.0,
        (24, BoltType.A490): 258.0,
        (27, BoltType.A490): 336.0,
        (30, BoltType.A490): 413.0,
        (36, BoltType.A490): 600.0,
    }
    
    # پیدا کردن نزدیک‌ترین قطر (در صورت نبود، درون‌یابی می‌شود)
    available_diameters = sorted([d for d, _ in tb_table.keys() if _[1] == bolt_grade])
    
    if diameter_mm in available_diameters:
        T_b_kN = tb_table.get((int(diameter_mm), bolt_grade))
    else:
        # درون‌یابی ساده
        if diameter_mm < available_diameters[0]:
            T_b_kN = tb_table.get((available_diameters[0], bolt_grade))
        elif diameter_mm > available_diameters[-1]:
            T_b_kN = tb_table.get((available_diameters[-1], bolt_grade))
        else:
            # پیدا کردن دو نقطه اطراف
            lower = max([d for d in available_diameters if d <= diameter_mm])
            upper = min([d for d in available_diameters if d >= diameter_mm])
            T_b_lower = tb_table.get((lower, bolt_grade))
            T_b_upper = tb_table.get((upper, bolt_grade))
            T_b_kN = T_b_lower + (T_b_upper - T_b_lower) * (diameter_mm - lower) / (upper - lower)
    
    if T_b_kN is None:
        raise ValueError(f"قطر {diameter_mm}mm برای پیچ {bolt_grade.value} پشتیبانی نمی‌شود")
    
    T_b_N = T_b_kN * 1000.0  # تبدیل به نیوتن
    
    # مقاومت اسمی
    R_n = mu * D_u * h_f * T_b_N * num_shear_planes
    
    # مقادیر φ و Ω برای اتصالات اصطکاکی
    phi = 1.00
    omega = 1.50
    
    if design_method == DesignMethod.LRFD:
        strength_design = phi * R_n
        strength_allowable = R_n / omega
    else:
        strength_design = R_n / omega
        strength_allowable = phi * R_n
    
    return StrengthResult(nominal=R_n, design=strength_design, allowable=strength_allowable)


def bearing_strength(
    plate_thickness_mm: float,
    fu_plate_mpa: float,
    edge_distance_mm: float,
    bolt_diameter_mm: float,
    center_to_center_spacing_mm: Optional[float] = None,
    design_method: DesignMethod = DesignMethod.LRFD
) -> StrengthResult:
    """
    محاسبه مقاومت اتکایی ورق (Bearing)
    
    فرمول‌ها:
    - برای لبه آزاد: R_n = 1.2 × L_c × t × F_u
    - برای داخلی: R_n = 2.4 × d × t × F_u
    - حداکثر: R_n = 1.2 × d × t × F_u
    
    Args:
        plate_thickness_mm: ضخامت ورق (mm)
        fu_plate_mpa: تنش نهایی ورق (MPa)
        edge_distance_mm: فاصله از لبه سوراخ تا لبه ورق در جهت نیرو (mm)
        bolt_diameter_mm: قطر پیچ (mm)
        center_to_center_spacing_mm: فاصله مرکز تا مرکز تا سوراخ بعدی (mm)
        design_method: روش طراحی
    
    Returns:
        StrengthResult شامل مقاومت اسمی، طراحی و مجاز
    """
    t = plate_thickness_mm
    F_u = fu_plate_mpa
    d = bolt_diameter_mm
    
    # فاصله خالص از لبه سوراخ تا لبه ورق
    L_c_edge = edge_distance_mm - (d / 2.0)
    
    # مقاومت مربوط به لبه آزاد
    R_n_edge = 1.2 * L_c_edge * t * F_u
    
    # اگر فاصله تا سوراخ بعدی مشخص باشد
    if center_to_center_spacing_mm is not None:
        L_c_inner = center_to_center_spacing_mm - d
        R_n_inner = 1.2 * L_c_inner * t * F_u
        R_n_edge = min(R_n_edge, R_n_inner)
    
    # مقاومت اتکایی داخلی
    R_n_bearing = 2.4 * d * t * F_u
    
    # حداکثر مقاومت مجاز
    R_n_max = 1.2 * d * t * F_u
    
    R_n = min(R_n_edge, R_n_bearing, R_n_max)
    
    phi = 0.75
    omega = 2.00
    
    if design_method == DesignMethod.LRFD:
        strength_design = phi * R_n
        strength_allowable = R_n / omega
    else:
        strength_design = R_n / omega
        strength_allowable = phi * R_n
    
    return StrengthResult(nominal=R_n, design=strength_design, allowable=strength_allowable)


def tearout_strength(
    plate_thickness_mm: float,
    fu_plate_mpa: float,
    edge_distance_mm: float,
    bolt_diameter_mm: float,
    design_method: DesignMethod = DesignMethod.LRFD
) -> StrengthResult:
    """
    محاسبه مقاومت گسیختگی قالبی (Tearout)
    
    فرمول: R_n = 1.5 × L_c × t × F_u
    
    Args:
        plate_thickness_mm: ضخامت ورق (mm)
        fu_plate_mpa: تنش نهایی ورق (MPa)
        edge_distance_mm: فاصله از لبه سوراخ تا لبه ورق (mm)
        bolt_diameter_mm: قطر پیچ (mm)
        design_method: روش طراحی
    
    Returns:
        StrengthResult شامل مقاومت اسمی، طراحی و مجاز
    """
    t = plate_thickness_mm
    F_u = fu_plate_mpa
    d = bolt_diameter_mm
    
    # فاصله خالص از لبه سوراخ تا لبه ورق
    L_c = edge_distance_mm - (d / 2.0)
    
    R_n = 1.5 * L_c * t * F_u
    
    phi = 0.75
    omega = 2.00
    
    if design_method == DesignMethod.LRFD:
        strength_design = phi * R_n
        strength_allowable = R_n / omega
    else:
        strength_design = R_n / omega
        strength_allowable = phi * R_n
    
    return StrengthResult(nominal=R_n, design=strength_design, allowable=strength_allowable)


def block_shear(
    fy_mpa: float,
    fu_mpa: float,
    agv_mm2: float,
    anv_mm2: float,
    ant_mm2: float,
    u_bs: float = 1.0,
    design_method: DesignMethod = DesignMethod.LRFD
) -> StrengthResult:
    """
    محاسبه مقاومت بلوک برشی (Block Shear)
    
    فرمول: R_n = min(0.6×F_u×A_nv + U_bs×F_u×A_nt, 0.6×F_y×A_gv + U_bs×F_u×A_nt)
    
    Args:
        fy_mpa: تنش تسلیم فولاد (MPa)
        fu_mpa: تنش نهایی فولاد (MPa)
        agv_mm2: سطح ناخالص برشی (mm²)
        anv_mm2: سطح خالص برشی (mm²)
        ant_mm2: سطح خالص کششی (mm²)
        u_bs: ضریب یکنواختی تنش (1.0 برای یکنواخت، 0.5 برای غیریکنواخت)
        design_method: روش طراحی
    
    Returns:
        StrengthResult شامل مقاومت اسمی، طراحی و مجاز
    """
    # حالت اول: گسیختگی برشی + تسلیم کششی
    R_n1 = 0.6 * fu_mpa * anv_mm2 + u_bs * fu_mpa * ant_mm2
    
    # حالت دوم: تسلیم برشی + گسیختگی کششی
    R_n2 = 0.6 * fy_mpa * agv_mm2 + u_bs * fu_mpa * ant_mm2
    
    R_n = min(R_n1, R_n2)
    
    phi = 0.75
    omega = 2.00
    
    if design_method == DesignMethod.LRFD:
        strength_design = phi * R_n
        strength_allowable = R_n / omega
    else:
        strength_design = R_n / omega
        strength_allowable = phi * R_n
    
    return StrengthResult(nominal=R_n, design=strength_design, allowable=strength_allowable)


# ============================================================================
# بخش 2: جوش‌ها (Welds)
# ============================================================================

def fillet_weld_strength(
    electrode_class: ElectrodeClass,
    weld_size_mm: float,
    weld_length_mm: float,
    design_method: DesignMethod = DesignMethod.LRFD
) -> StrengthResult:
    """
    محاسبه مقاومت جوش گوشه (Fillet Weld)
    
    فرمول: R_n = 0.6 × F_EXX × A_we
    A_we = 0.707 × w × L
    
    Args:
        electrode_class: کلاس الکترود (E60, E70, E80)
        weld_size_mm: سایز جوش (mm)
        weld_length_mm: طول مؤثر جوش (mm)
        design_method: روش طراحی
    
    Returns:
        StrengthResult شامل مقاومت اسمی، طراحی و مجاز
    """
    # F_EXX بر اساس کلاس الکترود
    fexx_values = {
        ElectrodeClass.E60: 420.0,
        ElectrodeClass.E70: 480.0,
        ElectrodeClass.E80: 550.0,
    }
    F_EXX = fexx_values.get(electrode_class, 480.0)
    
    # مساحت مؤثر جوش
    A_we = 0.707 * weld_size_mm * weld_length_mm
    
    R_n = 0.6 * F_EXX * A_we
    
    phi = 0.75
    omega = 2.00
    
    if design_method == DesignMethod.LRFD:
        strength_design = phi * R_n
        strength_allowable = R_n / omega
    else:
        strength_design = R_n / omega
        strength_allowable = phi * R_n
    
    return StrengthResult(nominal=R_n, design=strength_design, allowable=strength_allowable)


def cjp_weld_strength(
    fy_base_mpa: float,
    fu_base_mpa: float,
    throat_thickness_mm: float,
    weld_length_mm: float,
    limit_state: LimitState,
    design_method: DesignMethod = DesignMethod.LRFD
) -> StrengthResult:
    """
    محاسبه مقاومت جوش شیاری با نفوذ کامل (CJP)
    
    حالات حدی:
    - تسلیم برشی: R_n = F_y × A_wc
    - گسیختگی برشی: R_n = 0.6 × F_u × A_we
    - گسیختگی کششی: R_n = F_u × A_we
    
    Args:
        fy_base_mpa: تنش تسلیم فولاد پایه (MPa)
        fu_base_mpa: تنش نهایی فولاد پایه (MPa)
        throat_thickness_mm: ضخامت گلوی جوش (mm)
        weld_length_mm: طول جوش (mm)
        limit_state: حالت حدی
        design_method: روش طراحی
    
    Returns:
        StrengthResult شامل مقاومت اسمی، طراحی و مجاز
    """
    A_w = throat_thickness_mm * weld_length_mm
    
    if limit_state == LimitState.SHEAR_YIELD:
        R_n = fy_base_mpa * A_w
        phi = 0.90
        omega = 1.67
    elif limit_state == LimitState.SHEAR_RUPTURE:
        R_n = 0.6 * fu_base_mpa * A_w
        phi = 0.75
        omega = 2.00
    elif limit_state == LimitState.TENSION_RUPTURE:
        R_n = fu_base_mpa * A_w
        phi = 0.75
        omega = 2.00
    else:
        raise ValueError(f"حالت حدی نامعتبر: {limit_state}")
    
    if design_method == DesignMethod.LRFD:
        strength_design = phi * R_n
        strength_allowable = R_n / omega
    else:
        strength_design = R_n / omega
        strength_allowable = phi * R_n
    
    return StrengthResult(nominal=R_n, design=strength_design, allowable=strength_allowable)


def pjp_weld_strength(
    electrode_class: ElectrodeClass,
    effective_throat_mm: float,
    weld_length_mm: float,
    load_type: LoadType,
    design_method: DesignMethod = DesignMethod.LRFD
) -> StrengthResult:
    """
    محاسبه مقاومت جوش شیاری با نفوذ جزئی (PJP)
    
    فرمول: R_n = 0.6 × F_EXX × A_we (برای برش و کشش عمود بر جوش)
    
    Args:
        electrode_class: کلاس الکترود
        effective_throat_mm: ضخامت گلوی مؤثر (mm)
        weld_length_mm: طول جوش (mm)
        load_type: نوع بار (shear یا tension)
        design_method: روش طراحی
    
    Returns:
        StrengthResult شامل مقاومت اسمی، طراحی و مجاز
    """
    fexx_values = {
        ElectrodeClass.E60: 420.0,
        ElectrodeClass.E70: 480.0,
        ElectrodeClass.E80: 550.0,
    }
    F_EXX = fexx_values.get(electrode_class, 480.0)
    
    # برای جوش PJP، A_we = ضخامت گلوی مؤثر × طول
    A_we = effective_throat_mm * weld_length_mm
    
    R_n = 0.6 * F_EXX * A_we
    
    phi = 0.75
    omega = 2.00
    
    if design_method == DesignMethod.LRFD:
        strength_design = phi * R_n
        strength_allowable = R_n / omega
    else:
        strength_design = R_n / omega
        strength_allowable = phi * R_n
    
    return StrengthResult(nominal=R_n, design=strength_design, allowable=strength_allowable)


def combined_load_weld(
    electrode_class: ElectrodeClass,
    weld_size_mm: float,
    weld_length_mm: float,
    normal_force_n: float,
    shear_force_n: float,
    method: str = "simplified",
    design_method: DesignMethod = DesignMethod.LRFD
) -> Tuple[float, bool]:
    """
    بررسی اندرکنش نیروهای مرکب در جوش
    
    روش ساده: (F_v/F_u)² + (F_n/F_u)² ≤ 1.0
    
    Args:
        electrode_class: کلاس الکترود
        weld_size_mm: سایز جوش (mm)
        weld_length_mm: طول جوش (mm)
        normal_force_n: نیروی عمود بر جوش (N)
        shear_force_n: نیروی موازی با جوش (N)
        method: روش محاسبه ("simplified" یا "directional")
        design_method: روش طراحی
    
    Returns:
        (interaction_ratio, is_acceptable)
    """
    fexx_values = {
        ElectrodeClass.E60: 420.0,
        ElectrodeClass.E70: 480.0,
        ElectrodeClass.E80: 550.0,
    }
    F_EXX = fexx_values.get(electrode_class, 480.0)
    
    A_we = 0.707 * weld_size_mm * weld_length_mm
    
    if method == "simplified":
        # روش ساده
        F_u = 0.6 * F_EXX  # مقاومت نهایی جوش
        
        f_n = normal_force_n / A_we
        f_v = shear_force_n / A_we
        
        ratio = (f_v / F_u) ** 2 + (f_n / F_u) ** 2
        is_acceptable = ratio <= 1.0
        
    else:  # directional method
        # روش جهت‌دار
        beta = 0.9
        gamma_M2 = 1.25
        
        sigma_w = normal_force_n / A_we
        tau_w = shear_force_n / A_we
        
        equivalent_stress = math.sqrt(sigma_w ** 2 + tau_w ** 2)
        allowable_stress = F_EXX / (beta * gamma_M2)
        
        ratio = equivalent_stress / allowable_stress
        is_acceptable = ratio <= 1.0
    
    return ratio, is_acceptable


# ============================================================================
# بخش 3: ورق پرکننده (Filler Plate)
# ============================================================================

def filler_plate_reduction(
    filler_thickness_mm: float,
    bolt_extends_through: bool = False
) -> float:
    """
    محاسبه ضریب کاهش ظرفیت پیچ اصطکاکی به دلیل ورق پرکننده
    
    Args:
        filler_thickness_mm: ضخامت ورق پرکننده (mm)
        bolt_extends_through: آیا پیچ از ورق پرکننده عبور می‌کند؟
    
    Returns:
        ضریب کاهش (بین 0 تا 1)
    """
    if bolt_extends_through:
        # اگر پیچ طول کافی دارد
        return 1.0
    else:
        # فرمول کاهش: 1/(1 + 0.5 × t_fill)
        return 1.0 / (1.0 + 0.5 * filler_thickness_mm)


# ============================================================================
# بخش 4: سخت‌کننده‌های عرضی (Transverse Stiffeners)
# ============================================================================

def stiffener_local_buckling_check(
    width_mm: float,
    thickness_mm: float,
    fy_stiffener_mpa: float,
    e_steel_mpa: float = E_STEEL
) -> Tuple[bool, float]:
    """
    بررسی کمانش موضعی سخت‌کننده عرضی
    
    شرط: (b/t)_st ≤ 0.56 × √(E / F_y,st)
    
    Args:
        width_mm: پهنای سخت‌کننده (mm)
        thickness_mm: ضخامت سخت‌کننده (mm)
        fy_stiffener_mpa: تنش تسلیم سخت‌کننده (MPa)
        e_steel_mpa: مدول الاستیسیته فولاد (MPa)
    
    Returns:
        (is_ok, ratio) - وضعیت قبولی و نسبت (b/t) / حد مجاز
    """
    b_t_ratio = width_mm / thickness_mm
    limit = 0.56 * math.sqrt(e_steel_mpa / fy_stiffener_mpa)
    
    is_ok = b_t_ratio <= limit
    ratio = b_t_ratio / limit
    
    return is_ok, ratio


def stiffener_moment_of_inertia_required(
    web_height_mm: float,
    stiffener_clear_spacing_mm: float,
    rho_w: float = 1.0
) -> float:
    """
    محاسبه ممان اینرسی موردنیاز سخت‌کننده عرضی
    
    Args:
        web_height_mm: ارتفاع جان (mm)
        stiffener_clear_spacing_mm: فاصله آزاد بین سخت‌کننده‌ها (mm)
        rho_w: نسبت نیروهای برشی در چشمه مجاور
    
    Returns:
        ممان اینرسی موردنیاز (mm⁴)
    """
    h = web_height_mm
    a = stiffener_clear_spacing_mm
    rho = max(rho_w, 0.0)
    
    if a == 0:
        # اگر فاصله صفر باشد (سخت‌کننده پیوسته)
        I_st_min = (h ** 4 * rho) / 50.0
    else:
        term1 = (h ** 4 * rho) / 50.0
        term2 = (h ** 4 * (0.5 + 1.5 * (a / h) ** 2)) / (100.0 * (a / h))
        I_st_min = max(term1, term2)
    
    return I_st_min


# ============================================================================
# بخش 5: کف‌ستون و میل‌مهارها (Base Plates & Anchor Rods)
# ============================================================================

def concrete_bearing_strength(
    fc_prime_mpa: float,
    area_plate_mm2: float,
    area_pier_mm2: Optional[float] = None,
    design_method: DesignMethod = DesignMethod.LRFD
) -> StrengthResult:
    """
    محاسبه مقاومت اتکایی بتن زیر صفحه کف‌ستون
    
    فرمول: R_n = min(0.85×f'_c×A₁×√(A₂/A₁), 1.7×f'_c×A₁)
    
    Args:
        fc_prime_mpa: مقاومت فشاری بتن (MPa)
        area_plate_mm2: مساحت صفحه کف‌ستون A₁ (mm²)
        area_pier_mm2: مساحت کامل پی A₂ (mm²) - حداکثر 4 برابر A₁
        design_method: روش طراحی
    
    Returns:
        StrengthResult شامل مقاومت اسمی، طراحی و مجاز
    """
    A1 = area_plate_mm2
    
    if area_pier_mm2 is not None:
        A2 = min(area_pier_mm2, 4.0 * A1)
        sqrt_ratio = math.sqrt(A2 / A1)
    else:
        sqrt_ratio = 1.0
    
    R_n1 = 0.85 * fc_prime_mpa * A1 * sqrt_ratio
    R_n2 = 1.7 * fc_prime_mpa * A1
    
    R_n = min(R_n1, R_n2)
    
    phi = 0.65
    omega = 2.31
    
    if design_method == DesignMethod.LRFD:
        strength_design = phi * R_n
        strength_allowable = R_n / omega
    else:
        strength_design = R_n / omega
        strength_allowable = phi * R_n
    
    return StrengthResult(nominal=R_n, design=strength_design, allowable=strength_allowable)


def base_plate_bending(
    moment_nmm: float,
    plate_thickness_mm: float,
    fy_plate_mpa: float,
    design_method: DesignMethod = DesignMethod.LRFD
) -> Tuple[bool, float]:
    """
    بررسی مقاومت خمشی صفحه کف‌ستون
    
    Args:
        moment_nmm: لنگر خمشی وارد بر صفحه (N·mm)
        plate_thickness_mm: ضخامت صفحه (mm)
        fy_plate_mpa: تنش تسلیم صفحه (MPa)
        design_method: روش طراحی
    
    Returns:
        (is_ok, ratio) - وضعیت قبولی و نسبت لنگر وارد به مقاومت
    """
    # ممان مقاوم پلاستیک صفحه به ازای عرض واحد
    Z = (plate_thickness_mm ** 2) / 4.0  # mm³/mm
    
    phi = 0.90
    omega = 1.67
    
    if design_method == DesignMethod.LRFD:
        Mn = phi * fy_plate_mpa * Z
        ratio = moment_nmm / Mn if Mn > 0 else float('inf')
    else:
        Mn = (fy_plate_mpa * Z) / omega
        ratio = moment_nmm / Mn if Mn > 0 else float('inf')
    
    is_ok = ratio <= 1.0
    
    return is_ok, ratio


def anchor_rod_strength(
    steel_grade: SteelGrade,
    rod_diameter_mm: float,
    load_type: LoadType,
    concrete_fc_mpa: Optional[float] = None,
    embedment_depth_mm: Optional[float] = None,
    design_method: DesignMethod = DesignMethod.LRFD
) -> StrengthResult:
    """
    محاسبه مقاومت میل‌مهارها (Anchor Rods)
    
    حالات حدی:
    - کشش فولاد: R_n = 0.75 × F_ua × A_se
    - برش فولاد: R_n = 0.4 × F_ua × A_se
    - بیرون کشی بتن (Pullout): R_n = 8 × f'_c × A_brg
    - مخروط شکست بتن: R_n = k_c × √(f'_c) × h_ef^1.5
    
    Args:
        steel_grade: گرید فولاد میل‌مهار
        rod_diameter_mm: قطر میل‌مهار (mm)
        load_type: نوع بار (shear یا tension)
        concrete_fc_mpa: مقاومت فشاری بتن (MPa) - برای حالت‌های بتنی لازم است
        embedment_depth_mm: عمق مدفون شدن (mm) - برای حالت‌های بتنی لازم است
        design_method: روش طراحی
    
    Returns:
        StrengthResult شامل مقاومت اسمی، طراحی و مجاز
    """
    # F_ua بر اساس گرید فولاد
    fua_values = {
        SteelGrade.A36: 400.0,
        SteelGrade.A449: 550.0,
        SteelGrade.A193_B7: 725.0,
    }
    F_ua = fua_values.get(steel_grade, 400.0)
    
    # مساحت تنش‌گیر (برای میل‌مهار رزوه‌دار)
    A_se = 0.75 * math.pi * (rod_diameter_mm ** 2) / 4.0
    
    if load_type == LoadType.SHEAR:
        R_n_steel = 0.4 * F_ua * A_se
        phi = 0.65
        omega = 2.31
        R_n = R_n_steel
        
    else:  # TENSION
        R_n_steel = 0.75 * F_ua * A_se
        phi = 0.75
        omega = 2.00
        R_n = R_n_steel
        
        # اگر اطلاعات بتن داده شده باشد، حالت‌های بتنی نیز محاسبه می‌شوند
        if concrete_fc_mpa is not None and embedment_depth_mm is not None:
            # بیرون کشی بتن (Pullout)
            # فرض می‌شود A_brg ≈ 0.5 × مساحت سر میل‌مهار
            A_brg = 1.5 * math.pi * (rod_diameter_mm ** 2) / 4.0
            R_n_pullout = 8.0 * concrete_fc_mpa * A_brg
            
            # مخروط شکست بتن (Concrete breakout)
            k_c = 10.0  # برای میل‌مهار پیش‌تنیده
            h_ef = embedment_depth_mm
            R_n_breakout = k_c * math.sqrt(concrete_fc_mpa) * (h_ef ** 1.5)
            
            R_n = min(R_n, R_n_pullout, R_n_breakout)
            
            # برای حالت کشش با مشارکت بتن، φ و Ω تغییر می‌کنند
            phi = 0.70
            omega = 2.14
    
    if design_method == DesignMethod.LRFD:
        strength_design = phi * R_n
        strength_allowable = R_n / omega
    else:
        strength_design = R_n / omega
        strength_allowable = phi * R_n
    
    return StrengthResult(nominal=R_n, design=strength_design, allowable=strength_allowable)


# ============================================================================
# بخش 6: مهاربندهای کمانش‌تاب (BRB)
# ============================================================================

def brb_connection_required_strength(
    fy_mpa: float,
    gross_area_mm2: float,
    ry: float = 1.1,
    design_method: DesignMethod = DesignMethod.LRFD
) -> float:
    """
    محاسبه حداقل مقاومت موردنیاز اتصال مهاربند کمانش‌تاب (BRB)
    
    فرمول‌ها:
    - LRFD: P_u,connection ≥ 1.2 × R_y × F_y × A_g
    - ASD: P_a,connection ≥ (1.2 × R_y × F_y × A_g) / 1.5
    
    Args:
        fy_mpa: تنش تسلیم هسته فولادی (MPa)
        gross_area_mm2: سطح مقطع ناخالص هسته (mm²)
        ry: ضریب اضافه مقاومت فولاد (1.1 برای فولاد معمولی، 1.0 برای فولاد ویژه لرزه‌ای)
        design_method: روش طراحی
    
    Returns:
        حداقل مقاومت موردنیاز اتصال (N)
    """
    P_y = ry * fy_mpa * gross_area_mm2
    
    if design_method == DesignMethod.LRFD:
        required_strength = 1.2 * P_y
    else:
        required_strength = (1.2 * P_y) / 1.5
    
    return required_strength


def brb_casing_buckling_check(
    axial_load_n: float,
    yield_load_n: float,
    e_casing_mpa: float,
    i_casing_mm4: float,
    length_casing_mm: float
) -> Tuple[bool, float]:
    """
    بررسی کمانش غلاف در مهاربند کمانش‌تاب (BRB)
    
    شرط: P_no / P_y ≤ 0.8 × (π² × E × I) / L²
    
    Args:
        axial_load_n: نیروی محوری وارد بر غلاف (N)
        yield_load_n: نیروی تسلیم هسته (P_y = R_y × F_y × A_g)
        e_casing_mpa: مدول الاستیسیته غلاف (MPa)
        i_casing_mm4: ممان اینرسی غلاف (mm⁴)
        length_casing_mm: طول غلاف (mm)
    
    Returns:
        (is_ok, ratio) - وضعیت قبولی و نسبت P_no/P_y
    """
    P_no = axial_load_n
    
    # نیروی کمانش اویلر
    P_cr = math.pi ** 2 * e_casing_mpa * i_casing_mm4 / (length_casing_mm ** 2)
    
    P_y = yield_load_n
    
    ratio = P_no / P_y if P_y > 0 else float('inf')
    buckling_limit = 0.8 * P_cr / P_y if P_y > 0 else float('inf')
    
    is_ok = ratio <= buckling_limit
    
    return is_ok, ratio


# ============================================================================
# بخش 7: اتصالات لرزه‌ای ویژه
# ============================================================================

def rbs_moment_strength(
    fy_mpa: float,
    fu_mpa: float,
    z_rbs_mm3: float,
    steel_seismic: bool = False,
    design_method: DesignMethod = DesignMethod.LRFD
) -> StrengthResult:
    """
    محاسبه مقاومت خمشی اتصال تیر با مقطع کاهش‌یافته (RBS)
    
    فرمول‌ها:
    - M_pr = C_pr × R_y × F_y × Z_RBS
    - C_pr = min((F_y + F_u) / (2 × F_y), 1.2)
    
    Args:
        fy_mpa: تنش تسلیم فولاد (MPa)
        fu_mpa: تنش نهایی فولاد (MPa)
        z_rbs_mm3: اساس پلاستیک مقطع در ناحیه RBS (mm³)
        steel_seismic: فولاد ویژه لرزه‌ای (R_y=1.0) یا معمولی (R_y=1.1)
        design_method: روش طراحی
    
    Returns:
        StrengthResult شامل مقاومت اسمی، طراحی و مجاز
    """
    R_y = 1.0 if steel_seismic else 1.1
    
    # ضریب C_pr
    C_pr = min((fy_mpa + fu_mpa) / (2.0 * fy_mpa), 1.2)
    
    # لنگر پلاستیک مورد انتظار در ناحیه RBS
    M_pr = C_pr * R_y * fy_mpa * z_rbs_mm3  # N·mm
    
    phi = 0.90
    omega = 1.67
    
    if design_method == DesignMethod.LRFD:
        strength_design = phi * M_pr
        strength_allowable = M_pr / omega
    else:
        strength_design = M_pr / omega
        strength_allowable = phi * M_pr
    
    return StrengthResult(nominal=M_pr, design=strength_design, allowable=strength_allowable)


def bfem_check(
    moment_capacity_flange_nmm: float,
    moment_capacity_beam_nmm: float
) -> Tuple[bool, float]:
    """
    بررسی اتصال تیر با بال پهن‌شده (BFEM)
    
    شرط: M_f ≥ 1.1 × M_p,beam
    
    Args:
        moment_capacity_flange_nmm: ظرفیت خمشی ناحیه پهن‌شده بال (N·mm)
        moment_capacity_beam_nmm: ظرفیت خمشی تیر اصلی (N·mm)
    
    Returns:
        (is_ok, ratio) - وضعیت قبولی و نسبت M_f / (1.1×M_p)
    """
    required = 1.1 * moment_capacity_beam_nmm
    ratio = moment_capacity_flange_nmm / required if required > 0 else float('inf')
    is_ok = moment_capacity_flange_nmm >= required
    
    return is_ok, ratio


def panel_zone_strength(
    fy_column_mpa: float,
    dc_mm: float,
    tw_mm: float,
    db_mm: float,
    bcf_mm: Optional[float] = None,
    tcf_mm: Optional[float] = None,
    design_method: DesignMethod = DesignMethod.LRFD
) -> StrengthResult:
    """
    محاسبه مقاومت چشمه اتصال (Panel Zone) در قاب‌های خمشی
    
    فرمول‌ها:
    - بدون سخت‌کننده: R_n = 0.6 × F_y × d_c × t_w
    - با سخت‌کننده: R_n = 0.6 × F_y × d_c × t_w × (1 + (3 × b_cf × t_cf²) / (d_b × d_c × t_w))
    
    Args:
        fy_column_mpa: تنش تسلیم ستون (MPa)
        dc_mm: ارتفاع ستون (mm)
        tw_mm: ضخامت جان ستون (mm)
        db_mm: ارتفاع تیر (mm)
        bcf_mm: عرض بال ستون (mm) - در صورت وجود سخت‌کننده
        tcf_mm: ضخامت بال ستون (mm) - در صورت وجود سخت‌کننده
        design_method: روش طراحی
    
    Returns:
        StrengthResult شامل مقاومت اسمی، طراحی و مجاز
    """
    R_n_base = 0.6 * fy_column_mpa * dc_mm * tw_mm
    
    if bcf_mm is not None and tcf_mm is not None and tcf_mm > 0:
        # با سخت‌کننده
        term = (3.0 * bcf_mm * tcf_mm ** 2) / (db_mm * dc_mm * tw_mm)
        R_n = R_n_base * (1.0 + term)
    else:
        # بدون سخت‌کننده
        R_n = R_n_base
    
    phi = 0.90
    omega = 1.67
    
    if design_method == DesignMethod.LRFD:
        strength_design = phi * R_n
        strength_allowable = R_n / omega
    else:
        strength_design = R_n / omega
        strength_allowable = phi * R_n
    
    return StrengthResult(nominal=R_n, design=strength_design, allowable=strength_allowable)


def bfp_bolt_tension(
    fy_beam_mpa: float,
    zx_beam_mm3: float,
    beam_depth_mm: float,
    ry: float = 1.1
) -> float:
    """
    محاسبه نیروی کششی در پیچ اتصال پیچی با جفت سپری (BFP)
    
    فرمول: T = (1.2 × R_y × F_y × Z_x) / d_b
    
    Args:
        fy_beam_mpa: تنش تسلیم تیر (MPa)
        zx_beam_mm3: اساس پلاستیک تیر (mm³)
        beam_depth_mm: عمق تیر (فاصله مرکز تا مرکز بال‌ها) (mm)
        ry: ضریب اضافه مقاومت فولاد
    
    Returns:
        نیروی کششی موردنیاز در هر پیچ (N)
    """
    M_pr = 1.2 * ry * fy_beam_mpa * zx_beam_mm3
    T = M_pr / beam_depth_mm
    
    return T


# ============================================================================
# بخش 8: وصله‌ها (Splices)
# ============================================================================

def column_splice_bearing(
    axial_load_n: float,
    contact_area_mm2: float,
    fy_column_mpa: float,
    design_method: DesignMethod = DesignMethod.LRFD
) -> Tuple[bool, float]:
    """
    بررسی وصله اتکایی ستون فشاری
    
    شرط: P_u ≤ φ × 0.7 × F_y × A_contact
    
    Args:
        axial_load_n: نیروی فشاری وارد بر وصله (N)
        contact_area_mm2: سطح تماس (mm²)
        fy_column_mpa: تنش تسلیم ستون (MPa)
        design_method: روش طراحی
    
    Returns:
        (is_ok, ratio) - وضعیت قبولی و نسبت نیروی وارد به ظرفیت
    """
    phi = 0.75
    omega = 2.00
    
    capacity_nominal = 0.7 * fy_column_mpa * contact_area_mm2
    
    if design_method == DesignMethod.LRFD:
        capacity = phi * capacity_nominal
        ratio = axial_load_n / capacity if capacity > 0 else float('inf')
    else:
        capacity = capacity_nominal / omega
        ratio = axial_load_n / capacity if capacity > 0 else float('inf')
    
    is_ok = ratio <= 1.0
    
    return is_ok, ratio


def beam_splice_forces(
    moment_plastic_nmm: float,
    shear_factored_n: float,
    beam_depth_mm: float,
    flange_area_required_mm2: Optional[float] = None
) -> dict:
    """
    محاسبه نیروهای وصله تیر خمشی
    
    Args:
        moment_plastic_nmm: لنگر پلاستیک تیر (M_p) (N·mm)
        shear_factored_n: برش فاکتور شده (N)
        beam_depth_mm: عمق تیر (فاصله مرکز تا مرکز بال‌ها) (mm)
        flange_area_required_mm2: سطح مقطع موردنیاز بال (اختیاری)
    
    Returns:
        دیکشنری شامل نیروی بال، برش جان، و سطح مقطع موردنیاز
    """
    # نیروی بال ناشی از لنگر
    flange_force = moment_plastic_nmm / beam_depth_mm
    
    # برش منتقل شده توسط جان
    web_shear = shear_factored_n
    
    # سطح مقطع موردنیاز بال
    if flange_area_required_mm2 is None:
        # فرض می‌شود تنش تسلیم 345 MPa
        flange_area_required_mm2 = flange_force / 345.0
    
    return {
        "flange_force_n": flange_force,
        "web_shear_n": web_shear,
        "flange_area_required_mm2": flange_area_required_mm2,
    }


# ============================================================================
# بخش 9: ضوابط فاصله پیچ‌ها
# ============================================================================

def bolt_spacing_check(
    bolt_diameter_mm: float,
    plate_thickness_mm: float,
    edge_distance_mm: float,
    center_to_center_mm: float,
    is_shear_edge: bool = True
) -> BoltSpacingResult:
    """
    بررسی حداقل و حداکثر فاصله پیچ‌ها
    
    ضوابط:
    - حداقل فاصله مرکز تا مرکز: 2.67 × d_b
    - حداکثر فاصله مرکز تا مرکز: min(24 × t, 300 mm)
    - حداقل فاصله لبه: 1.5 × d_b (لبه برش خورده)، 1.25 × d_b (لبه نورد شده)
    - حداکثر فاصله لبه: 12 × t
    
    Args:
        bolt_diameter_mm: قطر پیچ (mm)
        plate_thickness_mm: ضخامت ورق (mm)
        edge_distance_mm: فاصله از لبه ورق تا مرکز سوراخ (mm)
        center_to_center_mm: فاصله مرکز تا مرکز پیچ‌ها (mm)
        is_shear_edge: آیا لبه برش خورده است؟ (True=برش خورده، False=نورد شده)
    
    Returns:
        BoltSpacingResult شامل نتایج بررسی
    """
    d = bolt_diameter_mm
    t = plate_thickness_mm
    
    # بررسی فاصله مرکز تا مرکز
    min_c2c = 2.67 * d
    max_c2c = min(24.0 * t, 300.0)
    
    is_min_spacing_ok = center_to_center_mm >= min_c2c
    is_max_spacing_ok = center_to_center_mm <= max_c2c
    
    # بررسی فاصله لبه
    if is_shear_edge:
        min_edge = 1.5 * d
    else:
        min_edge = 1.25 * d
    
    max_edge = 12.0 * t
    
    is_min_edge_ok = edge_distance_mm >= min_edge
    is_max_edge_ok = edge_distance_mm <= max_edge
    
    # پیام خطا
    errors = []
    if not is_min_spacing_ok:
        errors.append(f"فاصله مرکز تا مرکز ({center_to_center_mm:.1f}mm) کمتر از حداقل ({min_c2c:.1f}mm)")
    if not is_max_spacing_ok:
        errors.append(f"فاصله مرکز تا مرکز ({center_to_center_mm:.1f}mm) بیشتر از حداکثر ({max_c2c:.1f}mm)")
    if not is_min_edge_ok:
        errors.append(f"فاصله لبه ({edge_distance_mm:.1f}mm) کمتر از حداقل ({min_edge:.1f}mm)")
    if not is_max_edge_ok:
        errors.append(f"فاصله لبه ({edge_distance_mm:.1f}mm) بیشتر از حداکثر ({max_edge:.1f}mm)")
    
    message = "; ".join(errors) if errors else "تمامی فاصله‌ها در محدوده مجاز هستند"
    
    return BoltSpacingResult(
        is_min_spacing_ok=is_min_spacing_ok,
        is_max_spacing_ok=is_max_spacing_ok,
        is_min_edge_ok=is_min_edge_ok,
        is_max_edge_ok=is_max_edge_ok,
        message=message
    )


# ============================================================================
# بخش 10: تابع کمکی برای نمایش نتایج
# ============================================================================

def print_strength_result(title: str, result: StrengthResult, unit: str = "N"):
    """
    چاپ نتایج مقاومت به صورت خوانا
    
    Args:
        title: عنوان
        result: شیء StrengthResult
        unit: واحد (N, kN, N·mm, kN·m)
    """
    print(f"\n{title}")
    print(f"  R_n (اسمی)     = {result.nominal:,.1f} {unit}")
    print(f"  طراحی (LRFD)   = {result.design:,.1f} {unit}")
    print(f"  مجاز (ASD)     = {result.allowable:,.1f} {unit}")


# ============================================================================
# مثال‌های استفاده
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("ماژول محاسبات اتصالات فولادی - مبحث دهم مقررات ملی ساختمان")
    print("=" * 70)
    
    # مثال 1: پیچ A325 در برش
    print("\n--- مثال 1: پیچ A325 قطر 20mm در برش (بدون رزوه) ---")
    result = bolt_shear_tension(BoltType.A325, LoadType.SHEAR, 20, has_thread=False)
    print_strength_result("پیچ A325 برشی", result, "N")
    
    # مثال 2: اندرکنش کشش و برش در پیچ
    print("\n--- مثال 2: اندرکنش کشش و برش ---")
    ratio, ok = bolt_interaction(BoltType.A325, 20, shear_force_n=40000, tension_force_n=30000)
    print(f"  نسبت اندرکنش = {ratio:.3f}")
    print(f"  وضعیت: {'✓ قبول' if ok else '✗ رد'}")
    
    # مثال 3: جوش گوشه E70
    print("\n--- مثال 3: جوش گوشه E70 با سایز 8mm و طول 100mm ---")
    result = fillet_weld_strength(ElectrodeClass.E70, 8, 100)
    print_strength_result("جوش گوشه", result, "N")
    
    # مثال 4: پیچ اصطکاکی
    print("\n--- مثال 4: پیچ اصطکاکی A325 قطر 20mm (کلاس A) ---")
    result = slip_critical_bolt(20, BoltType.A325, SurfaceClass.CLASS_A, HoleType.STANDARD, 2)
    print_strength_result("پیچ اصطکاکی", result, "N")
    
    # مثال 5: اتصال RBS لرزه‌ای
    print("\n--- مثال 5: اتصال RBS با Z_RBS=1.2e6 mm³ ---")
    result = rbs_moment_strength(fy_mpa=345, fu_mpa=450, z_rbs_mm3=1.2e6, steel_seismic=False)
    print_strength_result("اتصال RBS", result, "N·mm")
    print(f"  معادل kN·m: {result.nominal/1e6:.1f} kN·m")
    
    # مثال 6: کف‌ستون
    print("\n--- مثال 6: کف‌ستون با بتن C25 و صفحه 300x300mm ---")
    result = concrete_bearing_strength(fc_prime_mpa=25, area_plate_mm2=300*300)
    print_strength_result("اتکای بتن", result, "N")
    print(f"  معادل kN: {result.nominal/1000:.1f} kN")
    
    # مثال 7: بررسی فاصله پیچ
    print("\n--- مثال 7: بررسی فاصله پیچ قطر 20mm در ورق 15mm ---")
    spacing_result = bolt_spacing_check(
        bolt_diameter_mm=20,
        plate_thickness_mm=15,
        edge_distance_mm=35,
        center_to_center_mm=70
    )
    print(f"  {spacing_result.message}")
    
    # مثال 8: BRB
    print("\n--- مثال 8: BRB با F_y=345MPa و A_g=5000mm² ---")
    required = brb_connection_required_strength(fy_mpa=345, gross_area_mm2=5000, ry=1.1)
    print(f"  حداقل مقاومت موردنیاز اتصال: {required/1000:.1f} kN (LRFD)")
    
    print("\n" + "=" * 70)
    print("تمام محاسبات با موفقیت انجام شد.")
    print("=" * 70)