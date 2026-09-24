"""تبدیل تاریخ شمسی (جلالی) به میلادی و استخراج تاریخ از متن فارسی."""

from __future__ import annotations

import re
from typing import Optional, Tuple

PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"

_DIGIT_MAP = {ord(c): str(i) for i, c in enumerate(PERSIAN_DIGITS)}
_DIGIT_MAP.update({ord(c): str(i) for i, c in enumerate(ARABIC_DIGITS)})

PERSIAN_MONTHS = {
    "فروردین": 1, "اردیبهشت": 2, "خرداد": 3, "تیر": 4, "مرداد": 5, "شهریور": 6,
    "مهر": 7, "آبان": 8, "ابان": 8, "آذر": 9, "اذر": 9, "دی": 10, "بهمن": 11, "اسفند": 12,
}

MONTH_NAMES = ["", "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
               "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]


def to_english_digits(text: str) -> str:
    """ارقام فارسی/عربی را به لاتین تبدیل می‌کند."""
    if not text:
        return ""
    return text.translate(_DIGIT_MAP)


def is_leap_jalali(year: int) -> bool:
    """سال کبیسه شمسی بر پایه چرخه ۳۳ ساله."""
    return year % 33 in (1, 5, 9, 13, 17, 22, 26, 30)


def jalali_to_gregorian(jy: int, jm: int, jd: int) -> Tuple[int, int, int]:
    """تبدیل (سال، ماه، روز) شمسی به میلادی."""
    jy += 1595
    days = -355668 + (365 * jy) + ((jy // 33) * 8) + (((jy % 33) + 3) // 4) + jd
    days += (jm - 1) * 31 if jm < 7 else ((jm - 7) * 30) + 186
    gy = 400 * (days // 146097)
    days %= 146097
    if days > 36524:
        days -= 1
        gy += 100 * (days // 36524)
        days %= 36524
        if days >= 365:
            days += 1
    gy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        gy += (days - 1) // 365
        days = (days - 1) % 365
    gd = days + 1
    sal_a = [0, 31,
             29 if (gy % 4 == 0 and gy % 100 != 0) or (gy % 400 == 0) else 28,
             31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    gm = 0
    for gm in range(1, 13):
        if gd <= sal_a[gm]:
            break
        gd -= sal_a[gm]
    return gy, gm, gd


def normalize_jalali(jy: int, jm: int, jd: int) -> Tuple[int, int, int]:
    """سال دو رقمی را به چهار رقمی تبدیل می‌کند (۸۵ -> ۱۳۸۵)."""
    if jy < 100:
        jy = 1400 + jy if jy < 50 else 1300 + jy
    return jy, jm, jd


def valid_jalali(jy: int, jm: int, jd: int) -> bool:
    if not (1200 <= jy <= 1499):
        return False
    if not (1 <= jm <= 12):
        return False
    if jd < 1:
        return False
    if jm <= 6:
        return jd <= 31
    if jm <= 11:
        return jd <= 30
    return jd <= (30 if is_leap_jalali(jy) else 29)


# ۱۳۹۸/۰۵/۱۲ یا ۱۳۹۸-۵-۱۲ یا ۱۳۹۸.۵.۱۲
_NUMERIC_RE = re.compile(r"(?<!\d)(\d{2,4})\s*[/\-.]\s*(\d{1,2})\s*[/\-.]\s*(\d{1,2})(?!\d)")
# ۱۲ مرداد ۱۳۹۸
_TEXTUAL_RE = re.compile(
    r"(?<!\d)(\d{1,2})\s*(?:ام\s*)?(" + "|".join(PERSIAN_MONTHS) + r")\s*(?:ماه\s*)?(\d{2,4})(?!\d)"
)


def parse_jalali_date(text: str) -> Optional[Tuple[int, int, int]]:
    """اولین تاریخ شمسی معتبر را از متن بیرون می‌کشد."""
    if not text:
        return None
    t = to_english_digits(text)

    for m in _NUMERIC_RE.finditer(t):
        a, b, c = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
        # حالت ۱۳۹۸/۰۵/۱۲
        jy, jm, jd = normalize_jalali(a, b, c)
        if valid_jalali(jy, jm, jd):
            return jy, jm, jd
        # حالت ۱۲/۰۵/۱۳۹۸
        jy, jm, jd = normalize_jalali(c, b, a)
        if valid_jalali(jy, jm, jd):
            return jy, jm, jd

    for m in _TEXTUAL_RE.finditer(t):
        jd = int(m.group(1))
        jm = PERSIAN_MONTHS[m.group(2)]
        jy = int(m.group(3))
        jy, jm, jd = normalize_jalali(jy, jm, jd)
        if valid_jalali(jy, jm, jd):
            return jy, jm, jd
    return None


def format_jalali(parts: Optional[Tuple[int, int, int]]) -> str:
    if not parts:
        return ""
    jy, jm, jd = parts
    return f"{jy:04d}/{jm:02d}/{jd:02d}"


def format_gregorian(parts: Optional[Tuple[int, int, int]]) -> str:
    if not parts:
        return ""
    gy, gm, gd = jalali_to_gregorian(*parts)
    return f"{gy:04d}-{gm:02d}-{gd:02d}"


def sort_key(parts: Optional[Tuple[int, int, int]]) -> Tuple[int, int, int]:
    """کلید مرتب‌سازی؛ رکوردهای بدون تاریخ به انتها می‌روند."""
    if not parts:
        return (9999, 99, 99)
    return parts
