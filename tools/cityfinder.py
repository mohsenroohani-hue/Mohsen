# -*- coding: utf-8 -*-
"""تشخیص شهر/استان هر مصوبه از روی عنوان و متن."""

import re

from gazetteer import PROVINCE_CITIES, NEW_TOWNS, PROVINCES
from persian import match_key, normalize

# واژه‌هایی که نباید به عنوان نام شهر برداشته شوند
STOP_WORDS = {
    "های", "ها", "هاي", "و", "در", "با", "به", "از", "که", "این", "آن", "مذکور",
    "مورد", "مربوط", "مزبور", "مصوب", "جدید", "قدیم", "جامع", "تفصیلی", "هادی",
    "ویژه", "منطقه", "ناحیه", "محدوده", "حریم", "طرح", "بزرگ", "کوچک", "مرکزی",
    "شهرک", "جهت", "برای", "طبق", "بر", "را", "یک", "دو", "سه", "کل", "اصلاح",
    "الحاق", "تصویب", "بازنگری", "تغییر", "کاربری", "اراضی", "زمین", "شورای",
    "عالی", "معماری", "شهرسازی", "ایران", "استان", "شهرستان", "شهر", "روستای",
    "توسعه", "عمران", "مسکن", "اجرای", "ابلاغ", "موضوع", "خصوص", "پیرامون",
}

_CITY_TO_PROVINCE = {}
for _province, _cities in PROVINCE_CITIES.items():
    for _city in _cities:
        _CITY_TO_PROVINCE.setdefault(match_key(_city), _province)
for _town, _province in NEW_TOWNS.items():
    _CITY_TO_PROVINCE.setdefault(match_key(_town), _province)

_PROVINCE_KEYS = {match_key(p): p for p in PROVINCES}

# نام‌های بلندتر اول بررسی شوند تا «بندر عباس» پیش از «بندر» گرفته شود
_KNOWN_SORTED = sorted(_CITY_TO_PROVINCE.keys(), key=len, reverse=True)
_KNOWN_RE = re.compile(
    r"(?<![؀-ۿ])(" + "|".join(re.escape(k) for k in _KNOWN_SORTED) + r")(?![؀-ۿ])"
)
_PROVINCE_RE = re.compile(
    r"استان\s+(" + "|".join(re.escape(k) for k in sorted(_PROVINCE_KEYS, key=len, reverse=True)) + r")"
)

_WORD = r"[؀-ۿ‌]+"
_PATTERNS = [
    (re.compile(r"شهر\s*جدید\s+(" + _WORD + r"(?:\s+" + _WORD + r")?)"), "شهر جدید"),
    (re.compile(r"شهرک\s+(" + _WORD + r"(?:\s+" + _WORD + r")?)"), "شهرک"),
    (re.compile(r"شهرستان\s+(" + _WORD + r"(?:\s+" + _WORD + r")?)"), "شهرستان"),
    (re.compile(r"(?<!؀-ۿ)شهر\s+(" + _WORD + r"(?:\s+" + _WORD + r")?)"), "شهر"),
    (re.compile(r"روستای\s+(" + _WORD + r"(?:\s+" + _WORD + r")?)"), "روستا"),
    (re.compile(r"بندر\s+(" + _WORD + r")"), "بندر"),
    (re.compile(r"منطقه\s+(" + _WORD + r"(?:\s+" + _WORD + r")?)"), "منطقه"),
]


def _clean_candidate(raw):
    """پاک‌سازی نام گرفته‌شده از الگو (حذف واژه‌های اضافه)."""
    words = [w for w in match_key(raw).split() if w]
    while words and words[-1] in STOP_WORDS:
        words.pop()
    while words and words[0] in STOP_WORDS:
        words.pop(0)
    name = " ".join(words)
    if len(name) < 3 or name in STOP_WORDS:
        return ""
    return name


def _known_hits(text):
    """نام شهرهای شناخته‌شده به ترتیب ظهور در متن."""
    seen, out = set(), []
    for match in _KNOWN_RE.finditer(text):
        name = match.group(1)
        if name in seen:
            continue
        seen.add(name)
        out.append(name)
    return out


def find_province(*texts):
    for text in texts:
        if not text:
            continue
        key = match_key(text)
        match = _PROVINCE_RE.search(key)
        if match:
            return _PROVINCE_KEYS[match.group(1)]
    return ""


def _kind_before(text, idx):
    """نوع عارضه از روی واژه پیش از نام (شهر، شهر جدید، شهرستان، ...)"""
    before = text[max(0, idx - 16):idx].rstrip()
    for needle, label in (
        ("شهر جدید", "شهر جدید"), ("شهرستان", "شهرستان"), ("شهرک", "شهرک"),
        ("روستای", "روستا"), ("منطقه", "منطقه"), ("بندر", "بندر"),
        ("استان", "استان"), ("شهر", "شهر"),
    ):
        if before.endswith(needle):
            return label
    return "شهر"


def _scan(text):
    """(فهرست (نام، نوع) شناخته‌شده، فهرست (نام، نوع) حدس‌زده‌شده) برای یک متن."""
    known, guessed, taken = [], [], []
    for match in _KNOWN_RE.finditer(text):
        name = match.group(1)
        before = text[:match.start()].rstrip()
        if before.endswith("استان"):
            continue  # نام استان است نه شهر
        taken.append((match.start(), match.end()))
        if name not in [n for n, _ in known]:
            known.append((name, _kind_before(text, match.start())))
    for pattern, label in _PATTERNS:
        for match in pattern.finditer(text):
            span = match.span(1)
            if any(span[0] < end and start < span[1] for start, end in taken):
                continue  # همان چیزی است که از فهرست شهرها گرفته شد
            name = _clean_candidate(match.group(1))
            if not name or name in [n for n, _ in known + guessed]:
                continue
            guessed.append((name, label))
    return known, guessed


def find_cities(title, body="", body_limit=1500):
    """(شهر اصلی، نوع، استان، همه شهرهای یافت‌شده، منبع تشخیص)

    اول با فهرست شهرهای کشور تطبیق داده می‌شود (طولانی‌ترین نام اولویت دارد)
    و اگر چیزی پیدا نشد، از الگوهای متنی مثل «شهر ...» استفاده می‌شود.
    """
    title_key = match_key(title or "")
    body_key = match_key((body or "")[:body_limit])

    primary, kind, source, all_hits = "", "", "", []
    for scope, text in (("عنوان", title_key), ("متن", body_key)):
        if not text:
            continue
        known, guessed = _scan(text)
        hits = known + guessed
        if not hits:
            continue
        primary, kind = hits[0]
        source = scope
        all_hits = [n for n, _ in hits]
        break

    province = find_province(title, (body or "")[:body_limit])
    if not province and primary:
        province = _CITY_TO_PROVINCE.get(primary, "")
    if not province:
        for name in all_hits:
            province = _CITY_TO_PROVINCE.get(name, "")
            if province:
                break

    if primary in {match_key(t) for t in NEW_TOWNS} and kind == "شهر":
        kind = "شهر جدید"

    return primary, kind, province, all_hits[:10], source


def is_known_city(name):
    return match_key(name) in _CITY_TO_PROVINCE


def subject_type(title):
    """نوع موضوع مصوبه (طرح جامع، طرح تفصیلی، ...)"""
    key = match_key(title or "")
    table = [
        ("طرح جامع", "طرح جامع"),
        ("طرح تفصیلی", "طرح تفصیلی"),
        ("طرح هادی", "طرح هادی"),
        ("طرح ویژه", "طرح ویژه"),
        ("طرح مجموعه شهری", "طرح مجموعه شهری"),
        ("مجموعه شهری", "مجموعه شهری"),
        ("طرح ناحیه", "طرح ناحیه"),
        ("منطقه ویژه", "منطقه ویژه"),
        ("حریم", "حریم شهر"),
        ("محدوده", "محدوده شهر"),
        ("کاربری", "تغییر کاربری"),
        ("بلندمرتبه", "بلندمرتبه‌سازی"),
        ("ضوابط", "ضوابط و مقررات"),
        ("آیین نامه", "آیین‌نامه"),
        ("شهر جدید", "شهر جدید"),
        ("بافت فرسوده", "بافت فرسوده"),
        ("بافت تاریخی", "بافت تاریخی"),
        ("گردشگری", "گردشگری"),
        ("صنعتی", "شهرک صنعتی"),
    ]
    for needle, label in table:
        if needle in key:
            return label
    return ""
