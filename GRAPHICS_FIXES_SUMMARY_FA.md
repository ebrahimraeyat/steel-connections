# گرافیک نرم‌افزار - خلاصه تغییرات
## Summary of Graphics UI Changes

تاریخ: May 20, 2026

### ✅ مسئله 1: ویجت‌های چپ و راست قابل تغییر اندازه نیستند
**حل شد:** اضافه کردن `setCollapsible(index, False)` برای اسپیلتر‌های افقی و عمودی

**فایل تغییر یافته:** `src/steel_connections/main_window.py` (خطوط 272-284)

**تغییرات:**
```python
# Allow left, center, and right panels to be resizable but not collapsible
root.setCollapsible(0, False)  # Left panel
root.setCollapsible(1, False)  # Center panel
root.setCollapsible(2, False)  # Right panel
```

**نتیجه:** 
- ویجت‌های چپ و راست اکنون می‌تواند اندازه‌شان تغییر کند
- از طریق کشیدن handle اسپیلتر می‌توان عرض پانل‌ها را تنظیم کرد
- پانل‌ها هرگز collapse نمی‌شوند

---

### ✅ مسئله 2: تنظیماتی که ذخیره میشوند (پرسپکتیو، سایه) اعمال نمیشوند
**حل شد:** اصلاح ترتیب بارگذاری تنظیمات در مرحله startup

**فایل‌های تغییر یافته:** 
- `src/steel_connections/main_window.py` (خطوط 107-126، 713-725، 222-234)

**تغییرات کلیدی:**
1. حذف `_apply_saved_preferences_to_ui()` از `_load_settings()` (خط 725)
2. تنظیمات اکنون فقط بارگذاری می‌شوند، بدون فوری اعمال
3. در `_finish_startup()` تنظیمات دو بار اعمال می‌شوند:
   - یک بار فوری برای تنظیم state UI
   - یک بار بعد 100 میلی‌ثانیه برای اطمینان کامل

```python
def _finish_startup(self) -> None:
    # Apply saved preferences two times for full effect
    self._apply_saved_preferences_to_ui()
    
    if self._startup_last_file:
        self._restore_last_file()
    else:
        self.calculate_connection()
    
    # Delayed re-application to ensure full effect
    QTimer.singleShot(100, lambda: self._apply_saved_preferences_to_ui())
```

**نتیجه:**
- تنظیمات perspective (متعامد/پرسپکتیو) هنگام شروع برنامه اعمال می‌شوند
- حالت سایه (shadows) هنگام شروع بازیابی می‌شود
- ترکیب display style (shaded, wireframe, etc.) ذخیره و بازیابی می‌شود
- Dark/Light theme هنگام شروع اعمال می‌شود

---

### ✅ مسئله 3: نمایش 2D برای مقاطع تیر، ستون و ورقها
**حل شد:** اصلاح Canvas classes در `dim_sketch.py` برای نمایش 2D

**فایل تغییر یافته:** `src/steel_connections/gui/dim_sketch.py`

#### 3.1 BeamCanvas (مقطع تیر)
- **قبل:** نمایش 3D اسکنومتریک
- **بعد:** نمایش مقطع 2D (I-beam cross-section)
- **وضعیت:** فقط مقطع به‌جلو (front view)

#### 3.2 ColumnCanvas (مقطع ستون)
- **قبل:** نمایش 3D اسکنومتریک با extrusion
- **بعد:** نمایش مقطع 2D (I-section cross-section)
- **وضعیت:** فقط مقطع به‌جلو (front view)

#### 3.3 FlangePlateCanvas (ورق‌های بال)
- **قبل:** نمایش 3D با I-section ghost و extrusion
- **بعد:** نمایش 2D از بالا (top view)
- **وضعیت:** فقط دو ورق بال، بدون background
- **ویژگی:** نمایش ابعاد (عرض و طول ورقها)

#### 3.4 WebPlateCanvas (ورق جان)
- **قبل:** نمایش 3D با I-section و extrusion
- **بعد:** نمایش 2D از پهلو (side view) 
- **ویژگی:** I-section شماتیک بسیار کمرنگ (ghost)
- **ویژگی:** ورق جان برجسته
- **ویژگی:** نمایش ابعاد (عرض و ارتفاع)

**تغییرات تکنیکی:**
- حذف extrusion calculations (EX, EY)
- حذف top-face drawing
- حذف 3D perspective effects
- نگاه‌داری dimension arrows برای نمایش ابعاد
- ساده‌سازی رسم برای بهتر performance

**رنگ‌ها:**
- Beam/Column: آبی (blue faces)
- Plate: سبز (green faces)
- Ghost/Background: خیلی کمرنگ (low opacity)
- Dimensions: خاکستری (gray arrows)

---

## تست و تصدیق

✅ اسپیلتر‌های اسکنومتریک تست شدند
✅ تنظیمات بارگذاری و اعمال تست شدند
✅ Sketch widgets بدون خطا import شدند
✅ نمایش‌های 2D ترسیم می‌شوند

---

## فایل‌های تغییر یافته

1. **main_window.py** (3 محل تغییر)
   - خطوط 272-284: Splitter collapsible settings
   - خطوط 713-725: Load settings (removed early apply)
   - خطوط 222-234: Finish startup (proper apply timing)

2. **dim_sketch.py** (4 Canvas class)
   - BeamCanvas: 3D → 2D
   - ColumnCanvas: 3D → 2D
   - FlangePlateCanvas: 3D top-down → 2D
   - WebPlateCanvas: 3D side → 2D

---

## نکات اضافی

### Performance
- نمایش‌های 2D ساده‌تر و سریع‌تر are
- بدون extrusion calculations

### Usability
- کاربر می‌تواند panel‌های منوی را resize کند
- تمام تنظیمات visual بین sessions ذخیره می‌شوند
- نمایش‌های 2D واضح‌تر و متمرکز‌تر هستند

### Consistency
- تمام dimension labels و arrows حفظ شده‌اند
- رنگ‌تری کنسیستنت هستند
- Layout structure بدون تغییر

---

**توجه:** تمام تغییرات عقب‌سو compatible هستند. موجود UI widgets برای input همان‌طور کار می‌کنند.
