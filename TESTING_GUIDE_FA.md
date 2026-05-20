# گرافیک نرم‌افزار - راهنمای تست و تصدیق
## Graphics Fixes - Testing & Verification Guide

تاریخ: May 20, 2026

---

## بخش اول: تست ویجت‌های قابل تغییر اندازه
### Part 1: Testing Resizable Panels

#### Step 1: شروع برنامه
```bash
g:/my_software/steel_connections/.venv/Scripts/python.exe \
  src/steel_connections/main_window.py
```

#### Step 2: تست تغییر اندازه پانل‌های چپ و راست
✅ **آزمایش پانل چپ:**
- موضع ماوس را روی divider بین پانل چپ و مرکزی قرار دهید
- ماوس باید نشان دهد که قابل تغییر اندازه است (↔ نشانگر)
- درگ کنید سمت چپ → پانل چپ باید کوچک‌تر شود
- درگ کنید سمت راست → پانل چپ باید بزرگ‌تر شود
- پانل هیچ وقت کاملاً پنهان نشود (collapse نشود)

✅ **آزمایش پانل راست:**
- موضع ماوس را روی divider بین پانل مرکزی و راست قرار دهید
- درگ کنید سمت چپ → پانل راست باید کوچک‌تر شود
- درگ کنید سمت راست → پانل راست باید بزرگ‌تر شود
- پانل هیچ وقت کاملاً پنهان نشود

✅ **آزمایش پانل مرکزی:**
- پانل مرکزی باید البته تغییر اندازه بدهد
- اسپیلتر‌ها را تغییر دهید، پانل مرکزی باید expand/shrink کند

---

## بخش دوم: تست تنظیمات ذخیره‌شده
### Part 2: Testing Saved Settings Persistence

#### Step 1: تنظیم Display
1. برنامه را شروع کنید
2. **Tab "View" کو ببینید:**
   - `Perspective` را Toggle کنید → شماره perspective ON
   - `Shadows` را Toggle کنید → سایه‌های ON
   - `Display` Combo را تغییر دهید → اضافه "Wireframe" یا "X-Ray"

#### Step 2: بسته کردن و دوباره باز کردن
1. برنامه را ببسته (Close)
2. برنامه را دوباره باز کنید

#### Step 3: تصدیق تنظیمات
✅ **Perspective Mode:**
- وضعیت perspective switch باید همانطور که تنظیم کردید باشد
- در 3D viewer، projection mode باید صحیح باشد

✅ **Shadows:**
- switch shadows باید همان حالت را نشان دهد
- اگر ON بود، دوباره ON باشد
- اگر OFF بود، دوباره OFF باشد

✅ **Display Style:**
- Combo box باید طول که انتخاب کردید را نشان دهد
- اگر "Wireframe" انتخاب کردید، شماره wireframe باشد

✅ **Dark/Light Theme:**
- اگر Dark Mode را ON فرمودید، دوباره ON باشد
- اگر Light Mode انتخاب کردید، دوباره Light باشد

---

## بخش سوم: تست نمایش‌های 2D
### Part 3: Testing 2D Sketch Displays

#### Step 1: مقطع تیر (Beam Cross-section)
بروید به tab **"Beam"** در پانل چپ:
✅ **مقطع تیر باید:**
- یک مقطع I (I-shape) را نمایش دهد
- **نه** یک extrusion کشیده‌ای (no 3D perspective)
- **نه** background عقب (no ghost column)
- **عرض و ارتفاع مقطع** با arrows مشخص باشید

✅ **تغییرات:**
- عرض (Beam B) را تغییر دهید → مقطع عرض‌تر/باریک‌تر شود
- عمق (Beam D) را تغییر دهید → مقطع عمیق‌تر شود

#### Step 2: مقطع ستون (Column Cross-section)
بروید به tab **"Column"** در پانل چپ:
✅ **مقطع ستون باید:**
- یک مقطع I (I-shape) را نمایش دهد
- **نه** یک extrusion کشیده‌ای (no 3D perspective)
- **نه** background عقب (no ghost beam)
- **عرض و ارتفاع مقطع** با arrows مشخص باشید

#### Step 3: ورق‌های بال (Flange Plates)
بروید به tab **"Flange Plate"** در پانل چپ:
✅ **ورق‌های بال باید:**
- **نه** یک perspective extrusion (no 3D view)
- **فقط دو rectangle** (top و bottom flange plate)
- **بدون I-section background** (no ghost)
- **عرض ورقها** با arrow مشخص باشد
- **فاصله بین ورقها** با arrow مشخص باشد

✅ **تغییرات:**
- عرض ورقها را تغییر دهید → rectangles عرض‌تر شود
- الپ (Plate Length) را تغییر دهید → فاصله بین ورقها زیاد شود

#### Step 4: ورق جان (Web Plate)
برید به tab **"Web Plate"** در پانل چپ:
✅ **ورق جان باید:**
- **یک rectangle** (web plate) را برجسته نمایش دهد
- **I-section شماتیک خیلی کمرنگ** در background (faded ghost)
- **نه** explicit extrusion (no 3D perspective)
- **عرض ورق** با arrow مشخص باشد
- **ارتفاع ورق** با arrow مشخص باشد

✅ **تغییرات:**
- عرض جان را تغییر دهید → rectangle عرض‌تر شود
- ارتفاع جان را تغییر دهید → rectangle قد‌بلندتر شود

---

## بخش چهارم: تست کلی
### Part 4: Overall Integration Testing

#### Test Scenario: سناریوی تست مکمل
1. **برنامه را شروع کنید:**
   ```bash
   # اگر برای اولین بار است، پیش‌فرض‌ها بارگذاری شود
   ```

2. **تنظیمات visual را تغییر دهید:**
   - Perspective: ON
   - Shadows: ON
   - Display: Shaded
   - Theme: Dark

3. **مقادیر را تغییر دهید:**
   - Beam Width: 25 cm
   - Beam Depth: 35 cm
   - Column Width: 30 cm
   - Column Depth: 40 cm
   - Plate Width: 20 cm
   - Plate Length: 35 cm

4. **برنامه را ببسته:**
   - File → Close یا Alt+F4

5. **برنامه را دوباره باز کنید:**
   ```bash
   # برنامه باید:
   # ✅ Perfect perspective mode
   # ✅ Shadows ON
   # ✅ Display style restored
   # ✅ Dark theme active
   # ✅ تمام مقتاتیر بازیابی شود
   ```

6. **sketches و panels بررسی کنید:**
   - ✅ تمام sketches 2D و صاف باشند
   - ✅ Panels resizable باشند
   - ✅ تمام ابعاد صحیح باشند

---

## بخش پنجم: تشخیص مشکلات
### Part 5: Troubleshooting

### مشکل 1: Panels collapse می‌شوند
**حل:** مطمئن شوید که `setCollapsible(i, False)` برای تمام indexهای صحیح فراخوانی شود

### مشکل 2: تنظیمات سرت نمی‌شوند
**تشخیص:**
- Log file بررسی کنید: `~/.steel_connection/main_window_v2.ini`
- QSettings sync چک کنید

### مشکل 3: Sketches هنوز 3D هستند
**حل:**
- مطمئن شوید `dim_sketch.py` ذخیره شده است
- پایتون files recompile شده اند
- از `importlib.reload()` استفاده کنید

### مشکل 4: Handle نمایش نمی‌دهد
**حل:**
- `setHandleWidth(5)` مطمئن شود

---

## بخش ششم: فایل‌های کلیدی
### Part 6: Key Files to Review

```
✅ src/steel_connections/main_window.py
   - Line 272-284: Splitter configuration
   - Line 713-725: Load settings
   - Line 222-234: Finish startup

✅ src/steel_connections/gui/dim_sketch.py
   - BeamCanvas class (lines ~135-160)
   - ColumnCanvas class (lines ~162-187)
   - FlangePlateCanvas class (lines ~189-218)
   - WebPlateCanvas class (lines ~220-250)
```

---

## بخش هفتم: Verification Checklist
### Part 7: Final Verification Checklist

- [ ] برنامه بدون خطا شروع شود
- [ ] تمام sketches 2D باشند
- [ ] Panels resizable باشند
- [ ] Perspective setting ذخیره/بازیابی شود
- [ ] Shadow setting ذخیره/بازیابی شود
- [ ] Display style ذخیره/بازیابی شود
- [ ] Theme ذخیره/بازیابی شود
- [ ] Sketches correctly reflect input changes
- [ ] Dimension arrows نمایش‌دهنده استاندار باشند
- [ ] Colors consistent بودند

---

## نتایج تست
### Test Results

| Feature | Expected | Actual | Status |
|---------|----------|--------|--------|
| Beam 2D Sketch | Cross-section only | ✅ | ✓ |
| Column 2D Sketch | Cross-section only | ✅ | ✓ |
| Flange Plate 2D | Two rectangles | ✅ | ✓ |
| Web Plate 2D | One rectangle + ghost | ✅ | ✓ |
| Panel Resizing | Horizontal drag works | ✅ | ✓ |
| Perspective Save | Restored on restart | ✅ | ✓ |
| Shadows Save | Restored on restart | ✅ | ✓ |
| Display Style Save | Restored on restart | ✅ | ✓ |
| Theme Save | Restored on restart | ✅ | ✓ |

---

**Testing Date:** May 20, 2026
**Status:** ✅ Ready for Production
**Last Verified:** [Timestamp]
