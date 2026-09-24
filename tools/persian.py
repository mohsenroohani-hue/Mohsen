# -*- coding: utf-8 -*-
"""نرمال‌سازی متن فارسی، تاریخ شمسی و تبدیل شمسی به میلادی."""

import re

_DIGIT_MAP = {}
for i in range(10):
    _DIGIT_MAP[chr(0x06F0 + i)] = str(i)   # Persian digits
    _DIGIT_MAP[chr(0x0660 + i)] = str(i)   # Arabic-Indic digits
_DIGIT_TABLE = str.maketrans(_DIGIT_MAP)

_CHAR_TABLE = str.maketrans({
    "ي": "ی",  # ي -> ی
    "ى": "ی",  # ى -> ی
    "ك": "ک",  # ك -> ک
    "ۀ": "ه",  # ۀ -> ه
    "‎": "",
    "‏": "",
    "﻿": "",
    " ": " ",
})

_DIACRITICS = re.compile(r"[ً-ْـ]")

MONTHS = [
    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
]
_MONTH_ALIASES = {
    "فروردين": 1, "ارديبهشت": 2, "امرداد": 5, "شهريور": 6, "آبان": 8, "ابان": 8,
    "اذر": 9, "دي": 10, "بهمن": 11, "اسفند": 12,
}


def fix_digits(text):
    return (text or "").translate(_DIGIT_TABLE)


def normalize(text, keep_zwnj=True, convert_digits=True):
    """یکسان‌سازی حروف عربی/فارسی، ارقام و فاصله‌ها.

    با convert_digits=False ارقام فارسی دست‌نخورده می‌مانند (برای متن کامل
    مصوبه که باید عین سند باقی بماند).
    """
    if not text:
        return ""
    text = text.translate(_CHAR_TABLE)
    if convert_digits:
        text = text.translate(_DIGIT_TABLE)
    text = _DIACRITICS.sub("", text)
    if not keep_zwnj:
        text = text.replace("‌", " ")
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def match_key(text):
    """کلید مقایسه: نیم‌فاصله و فاصله یکی می‌شوند."""
    return re.sub(r"\s+", " ", normalize(text, keep_zwnj=False)).strip()


_NUM_DATE = re.compile(r"(1[2-4]\d{2})\s*[/\-\.]\s*(\d{1,2})\s*[/\-\.]\s*(\d{1,2})")
_NUM_DATE_REV = re.compile(r"(\d{1,2})\s*[/\-\.]\s*(\d{1,2})\s*[/\-\.]\s*(1[2-4]\d{2})")
_TEXT_DATE = re.compile(
    r"(\d{1,2})\s*(?:ام\s*)?(" + "|".join(MONTHS + list(_MONTH_ALIASES)) + r")\s*(?:ماه\s*)?(1[2-4]\d{2})"
)


def month_number(name):
    name = match_key(name)
    for idx, month in enumerate(MONTHS, start=1):
        if match_key(month) == name:
            return idx
    return _MONTH_ALIASES.get(name.replace(" ", ""), 0)


def find_jalali_date(text):
    """اولین تاریخ شمسی معتبر متن را به صورت (سال، ماه، روز) برمی‌گرداند."""
    if not text:
        return None
    text = normalize(text)
    for match in _NUM_DATE.finditer(text):
        y, m, d = (int(g) for g in match.groups())
        if 1 <= m <= 12 and 1 <= d <= 31:
            return (y, m, d)
    for match in _TEXT_DATE.finditer(text):
        d, name, y = match.group(1), match.group(2), match.group(3)
        m = month_number(name)
        if m and 1 <= int(d) <= 31:
            return (int(y), m, int(d))
    for match in _NUM_DATE_REV.finditer(text):
        d, m, y = (int(g) for g in match.groups())
        if 1 <= m <= 12 and 1 <= d <= 31:
            return (y, m, d)
    return None


def format_jalali(date_tuple):
    if not date_tuple:
        return ""
    return "%04d/%02d/%02d" % date_tuple


def jalali_to_gregorian(jy, jm, jd):
    """تبدیل تاریخ شمسی به میلادی (الگوریتم استاندارد jalaali)."""
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
    leap = (gy % 4 == 0 and gy % 100 != 0) or (gy % 400 == 0)
    month_days = [0, 31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    gm = 0
    while gm < 13 and gd > month_days[gm]:
        gd -= month_days[gm]
        gm += 1
    return gy, gm, gd


def gregorian_iso(date_tuple):
    if not date_tuple:
        return ""
    try:
        gy, gm, gd = jalali_to_gregorian(*date_tuple)
        return "%04d-%02d-%02d" % (gy, gm, gd)
    except Exception:
        return ""
