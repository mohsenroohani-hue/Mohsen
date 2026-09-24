#!/usr/bin/env python3
"""
استخراج همه مصوبات یک صفحه فهرست و ذخیره متن کامل آن‌ها در فایل‌های CSV،
مرتب‌شده بر اساس زمان و بر اساس شهر.

Scrape every item of an approvals listing and export CSV files sorted by date
and grouped by city. Two sites are known presets, any other listing URL is
handled with generic heuristics:

    mrud    مصوبات شورای عالی شهرسازی و معماری ایران (mrud.ir)
    majlis  سامانه قوانین مرکز پژوهش‌های مجلس، جستجوی lu_approve_reference=lar15

Usage:
    pip install -r requirements.txt
    python scrape_approvals.py mrud
    python scrape_approvals.py majlis
    python scrape_approvals.py "https://example.ir/approvals/..."
    python scrape_approvals.py mrud --export-only     # rebuild CSVs from the cache

Downloads are cached under <out>/raw, so an interrupted run can simply be
restarted and it continues where it stopped. Attached PDF / Word files are
downloaded as well and their text is appended to the item's text.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import html as html_lib
import json
import re
import shutil
import sys
import time
import unicodedata
import zipfile
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urlencode, urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup, NavigableString, Tag

try:
    from pypdf import PdfReader
# A broken optional "cryptography" install makes pypdf raise a pyo3 PanicException
# (a BaseException); PDF attachments are then kept as links only.
except BaseException:
    PdfReader = None

PRESETS = {
    "mrud": "https://mrud.ir/approvals/%D9%85%D8%B5%D9%88%D8%A8%D8%A7%D8%AA-%D8%B4%D9%88%D8%B1%D8%A7%DB%8C%D8%B9%D8%A7%D9%84%DB%8C-%D8%B4%D9%87%D8%B1%D8%B3%D8%A7%D8%B2%DB%8C-%D9%88-%D9%85%D8%B9%D9%85%D8%A7%D8%B1%DB%8C",
    "majlis": "https://rc.majlis.ir/fa/law/search?lu_approve_reference=lar15&page=1",
}
LAW_ID_RE = re.compile(r"/fa/law/show/(\d+)")
FILE_RE = re.compile(r"\.(pdf|docx?|xlsx?|pptx?|zip|rar|jpe?g|png|gif|tiff?)$", re.I)
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
# Excel shows at most 32,767 characters per cell, so long texts are split
# over several "متن" columns instead of being truncated.
CELL_LIMIT = 32000
UNKNOWN = "نامشخص"

# --------------------------------------------------------------------------
# Text helpers
# --------------------------------------------------------------------------

_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
_LETTERS = str.maketrans({"ي": "ی", "ك": "ک", "ى": "ی", "‏": "", "‎": ""})

PERSIAN_MONTHS = {
    "فروردین": 1, "اردیبهشت": 2, "خرداد": 3, "تیر": 4, "مرداد": 5, "امرداد": 5,
    "شهریور": 6, "مهر": 7, "آبان": 8, "آذر": 9, "دی": 10, "بهمن": 11, "اسفند": 12,
}

META_LABELS = [
    "شماره انتشار", "تاریخ تصویب", "تاریخ ابلاغ", "تاریخ انتشار", "تاریخ اجرا", "تاریخ جلسه",
    "تاریخ ارسال", "تاریخ درج", "مرجع تصویب", "شماره ابلاغ", "شماره مصوبه", "شماره نامه",
    "شماره جلسه", "شماره روزنامه رسمی", "تاریخ روزنامه رسمی", "شماره ویژه نامه", "نوع قانون",
    "نوع مصوبه", "نوع", "دستگاه اجرایی", "موضوع", "وضعیت", "شهر", "استان", "دوره",
]

# Words that end a city name inside a title such as
# "مصوبه شورای اسلامی شهر بندر انزلی در خصوص ..."
_STOP_WORDS = [
    "در خصوص", "درخصوص", "درباره", "در مورد", "راجع", "مبنی", "موضوع", "مورخ", "مصوب", "مصوبه",
    "جهت", "برای", "به", "با", "در", "و", "از", "که", "دوره", "سال", "شماره", "نسبت", "پیرامون",
    "مربوط", "اصلاح", "ابطال", "بند", "تبصره", "ماده", "طرح", "جلسه", "شورای", "شورا", "استان",
    "شهرستان", "منطقه", "ناحیه", "محدوده", "حریم", "تا", "را", "این", "آن", "ها", "های",
]
_STOP_SET = {w for w in _STOP_WORDS if " " not in w}
_CITY_STOP = "|".join(re.escape(w).replace(r"\ ", r"\s*") for w in _STOP_WORDS)
_CITY_END = rf"(?=\s+(?:{_CITY_STOP})(?:\s|$)|\s*[،,:؛;()\[\]«»\"\-–—/.]|\s*\d|$)"
CITY_PATTERNS = [
    re.compile(rf"شورا(?:ی|ى)?\s*(?:های\s*)?اسلامی\s*(?:کلان\s*)?شهر(?:ستان)?\s+(.{{2,40}}?){_CITY_END}"),
    re.compile(rf"شهرداری\s*(?:کلان\s*شهر\s*|شهر\s+)?(.{{2,40}}?){_CITY_END}"),
    re.compile(rf"(?:کلان\s*)?شهر(?:ستان)?\s+(.{{2,40}}?){_CITY_END}"),
    re.compile(rf"شورا(?:ی|ى)?\s*(?:عالی\s*)?استان\s+(.{{2,40}}?){_CITY_END}"),
]

# Fallback for titles such as "طرح تفصیلی منطقه ۲۲ تهران" that never say "شهر ...".
_KNOWN_CITIES_SRC = """
تهران|مشهد|اصفهان|کرج|شیراز|تبریز|قم|اهواز|کرمانشاه|ارومیه|رشت|زاهدان|همدان|کرمان|یزد|اردبیل
بندرعباس|اراک|زنجان|سنندج|قزوین|خرم آباد|گرگان|ساری|بجنورد|بوشهر|بیرجند|ایلام|شهرکرد|سمنان|یاسوج
کاشان|دزفول|آمل|نیشابور|سبزوار|بابل|قائمشهر|خوی|ساوه|بروجرد|ملایر|ورامین|اسلامشهر|شهریار|پاکدشت
قرچک|نظرآباد|سیرجان|رفسنجان|بم|جیرفت|بندر انزلی|لاهیجان|لنگرود|آستارا|تالش|چالوس|نوشهر|رامسر
بهشهر|گنبد کاووس|بندر ترکمن|علی آباد کتول|شاهرود|دامغان|گرمسار|مراغه|مرند|میانه|اهر|بناب|سراب
مهاباد|بوکان|میاندوآب|نقده|پیرانشهر|سقز|بانه|مریوان|قروه|بیجار|اسلام آباد غرب|کنگاور|هرسین|پاوه
سرپل ذهاب|دهلران|آبادان|خرمشهر|بندر ماهشهر|ماهشهر|بهبهان|اندیمشک|شوشتر|ایذه|مسجد سلیمان|شوش
رامهرمز|دورود|الیگودرز|کوهدشت|ازنا|نهاوند|تویسرکان|اسدآباد|کبودرآهنگ|بروجن|فارسان|لردگان|دهدشت
گچساران|دوگنبدان|برازجان|کنگان|بندر گناوه|گناوه|دیلم|عسلویه|کیش|قشم|میناب|بندر لنگه|چابهار
ایرانشهر|زابل|خاش|سراوان|کاشمر|تربت حیدریه|تربت جام|قوچان|شیروان|اسفراین|گناباد|فردوس|طبس|قائن
نهبندان|اردکان|میبد|بافق|ابرکوه|مهریز|تفت|نجف آباد|خمینی شهر|شاهین شهر|فولادشهر|مبارکه|شهرضا
گلپایگان|خوانسار|نائین|اردستان|نطنز|فلاورجان|زرین شهر|مرودشت|جهرم|فسا|کازرون|لار|داراب|آباده
فیروزآباد|اقلید|نی ریز|لامرد|تاکستان|آبیک|بوئین زهرا|محلات|خمین|دلیجان|تفرش|آشتیان|شازند|ابهر
خرمدره|پردیس|پرند|هشتگرد|اشتهارد|فردیس|ماهدشت|دماوند|فیروزکوه|رباط کریم|ملارد|بهارستان|پیشوا
لواسان|اندیشه|صدرا|سهند|هشترود|آذرشهر|شبستر|سلماس|ماکو|اشنویه|سردشت|تکاب|شاهین دژ
"""
KNOWN_CITIES = sorted({c.strip() for c in re.split(r"[\n|]", _KNOWN_CITIES_SRC) if c.strip()},
                      key=len, reverse=True)
_KNOWN_CITY_RE = re.compile(
    r"(?<![\w‌])("
    + "|".join(r"[\s‌]*".join(map(re.escape, c.split())) for c in KNOWN_CITIES)
    + r")(?![\w‌])"
)


def norm(text: str | None) -> str:
    if not text:
        return ""
    text = text.translate(_LETTERS).replace("\xa0", " ")
    return re.sub(r"[ \t\r\f\v]+", " ", text).strip()


def clean_multiline(text: str) -> str:
    out, blank = [], False
    for line in text.split("\n"):
        line = norm(line)
        if line:
            out.append(line)
            blank = False
        elif not blank and out:
            out.append("")
            blank = True
    return "\n".join(out).strip()


def parse_date(text: str | None) -> str:
    """Return the first Jalali date in *text* as YYYY/MM/DD (or "")."""
    if not text:
        return ""
    t = norm(text).translate(_DIGITS)
    m = re.search(r"(1[234]\d\d)\s*[/\-.]\s*(\d{1,2})\s*[/\-.]\s*(\d{1,2})(?!\d)", t)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= mo <= 12 and 1 <= d <= 31:
            return f"{y:04d}/{mo:02d}/{d:02d}"
    m = re.search(r"(?<!\d)(\d{1,2})\s*[/\-.]\s*(\d{1,2})\s*[/\-.]\s*(1[234]\d\d)", t)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= mo <= 12 and 1 <= d <= 31:
            return f"{y:04d}/{mo:02d}/{d:02d}"
    months = "|".join(PERSIAN_MONTHS)
    m = re.search(rf"(\d{{1,2}})\s*({months})\s*(?:ماه\s*)?(?:سال\s*)?(1[234]\d\d)", t)
    if m:
        return f"{int(m.group(3)):04d}/{PERSIAN_MONTHS[m.group(2)]:02d}/{int(m.group(1)):02d}"
    return ""


def _valid_city(city: str) -> bool:
    words = city.split()
    return (0 < len(words) <= 3 and words[0] not in _STOP_SET
            and not any(ch.isdigit() for ch in city.translate(_DIGITS)))


def extract_city(*texts: str) -> str:
    texts = [norm(t).replace("‌", " ") for t in texts if t]
    for t in texts:
        for pat in CITY_PATTERNS:
            for m in pat.finditer(t):
                city = norm(m.group(1)).strip(" .،,-")
                if _valid_city(city):
                    known = _KNOWN_CITY_RE.match(city)
                    return norm(known.group(1)) if known else city
    for t in texts:
        m = _KNOWN_CITY_RE.search(t)
        if m:
            return norm(m.group(1))
    return ""


def safe_filename(name: str) -> str:
    name = re.sub(r'[\\/:*?"<>|‌]+', " ", name)
    name = re.sub(r"\s+", "_", name.strip())
    return name[:80] or UNKNOWN


def url_key(url: str) -> str:
    parts = urlsplit(url)
    host = parts.netloc.lower().removeprefix("www.")
    return f"{host}{unquote(parts.path).rstrip('/')}?{unquote(parts.query)}"


def short_hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------


class Fetcher:
    def __init__(self, delay: float, timeout: float, retries: int):
        self.delay = delay
        self.timeout = timeout
        self.retries = retries
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": USER_AGENT, "Accept-Language": "fa-IR,fa;q=0.9,en;q=0.5"}
        )

    def _get(self, url: str) -> requests.Response | None:
        for attempt in range(1, self.retries + 1):
            try:
                resp = self.session.get(url, timeout=self.timeout)
                if resp.status_code == 404:
                    print(f"  ! not found: {url}", file=sys.stderr)
                    return None
                resp.raise_for_status()
                if self.delay:
                    time.sleep(self.delay)
                return resp
            except requests.RequestException as exc:
                if attempt == self.retries:
                    print(f"  ! failed {url}: {exc}", file=sys.stderr)
                    return None
                time.sleep(min(60, 2 ** attempt))
        return None

    def get(self, url: str) -> str | None:
        resp = self._get(url)
        if resp is None:
            return None
        if not resp.encoding or resp.encoding.lower() == "iso-8859-1":
            resp.encoding = resp.apparent_encoding
        return resp.text

    def get_bytes(self, url: str) -> bytes | None:
        resp = self._get(url)
        return resp.content if resp is not None else None


def with_page(url: str, page: int) -> str:
    parts = urlsplit(url)
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k != "page"]
    query.append(("page", str(page)))
    return urlunsplit(parts._replace(query=urlencode(query)))


# --------------------------------------------------------------------------
# Listing pages
# --------------------------------------------------------------------------

NOISE_TAGS = ["script", "style", "noscript", "nav", "header", "footer", "form", "aside",
              "iframe", "svg", "button", "select", "input"]
PAGER_WORDS = {"بعدی", "قبلی", "صفحه بعد", "صفحه قبل", "اولین", "آخرین", "اول", "آخر", "next",
               "prev", "previous", "first", "last", "»", "«", "›", "‹", ">>", "<<", ">", "<", "..."}
PAGER_QUERY = re.compile(r"(?:^|&)(?:page|p|pg|pageindex|paged|pagenumber|currentpage|pn)=\d+", re.I)


def row_text(a: Tag, title: str) -> str:
    """Text of the table row / card around a result link (often holds the date)."""
    row = a
    for _ in range(4):
        if row.parent is None or row.parent.name in ("body", "html", "[document]"):
            break
        row = row.parent
        if row.name in ("tr", "li", "article") or len(norm(row.get_text(" "))) > len(title) + 20:
            break
    return norm(row.get_text(" "))


def crawl_majlis(fetcher: Fetcher, url: str, max_pages: int | None) -> list[dict]:
    found: dict[str, dict] = {}
    page, last_page = 1, None
    while not (max_pages and page > max_pages) and not (last_page and page > last_page):
        page_url = with_page(url, page)
        html = fetcher.get(page_url)
        if html is None:
            break
        soup = BeautifulSoup(html, "lxml")
        results = 0
        new = 0
        for a in soup.find_all("a", href=True):
            m = LAW_ID_RE.search(a["href"])
            if not m:
                continue
            results += 1
            title = norm(a.get_text(" "))
            if m.group(1) not in found:
                new += 1
            entry = found.setdefault(m.group(1), {
                "id": m.group(1), "kind": "page", "list_title": "", "list_text": "",
                "url": urljoin(page_url, f"/fa/law/show/{m.group(1)}")})
            if len(title) > len(entry["list_title"]):
                entry["list_title"] = title
            text = row_text(a, title)
            if len(text) > len(entry["list_text"]):
                entry["list_text"] = text
        for a in soup.find_all("a", href=True):
            m = re.search(r"[?&]page=(\d+)", a["href"])
            if m:
                last_page = max(last_page or 0, int(m.group(1)))
        print(f"listing page {page}{'/' + str(last_page) if last_page else ''}: "
              f"{new} new, {len(found)} total")
        if not new:
            break
        page += 1
    return list(found.values())


def _is_pager(href: str, text: str, start_url: str) -> bool:
    s, st = urlsplit(href), urlsplit(start_url)
    path, start_path = unquote(s.path).rstrip("/"), unquote(st.path).rstrip("/")
    if path == start_path and PAGER_QUERY.search(s.query):
        return True
    if re.fullmatch(re.escape(start_path) + r"/(?:page/)?\d+", path):
        return True
    t = norm(text).translate(_DIGITS).lower()
    return path == start_path and (t.isdigit() or t in PAGER_WORDS)


def crawl_generic(fetcher: Fetcher, start_url: str, max_pages: int | None,
                  link_pattern: str | None) -> list[dict]:
    """Follow the listing's pagination and collect the links of its items.

    Item links are told apart from menus by (a) dropping links that appear on
    almost every listing page and (b) keeping the largest group of links sharing
    the first path segment with descriptive titles. Files linked
    directly from the listing (PDF, Word, ...) are items too.
    """
    start_host = urlsplit(start_url).netloc.lower().removeprefix("www.")
    queue, queued = [start_url], {url_key(start_url)}
    links: dict[str, dict] = {}
    files: dict[str, dict] = {}
    seen_pages: set[frozenset] = set()
    n_pages = 0
    while queue and not (max_pages and n_pages >= max_pages):
        page_url = queue.pop(0)
        html = fetcher.get(page_url)
        if html is None:
            continue
        soup = BeautifulSoup(html, "lxml")
        for tag in soup.find_all(NOISE_TAGS):
            if tag.name != "form":  # ASP.NET pages wrap everything in one <form>
                tag.decompose()
        found = []
        for a in soup.find_all("a", href=True):
            href = urljoin(page_url, a["href"].strip()).split("#")[0]
            if not href.startswith(("http://", "https://")):
                continue
            text = norm(a.get_text(" ")) or norm(a.get("title", ""))
            key = url_key(href)
            is_file = bool(FILE_RE.search(unquote(urlsplit(href).path)))
            if not is_file and urlsplit(href).netloc.lower().removeprefix("www.") != start_host:
                continue
            if not is_file and _is_pager(href, text, start_url):
                if key not in queued:
                    queued.add(key)
                    queue.append(href)
                continue
            if key in (url_key(start_url), url_key(page_url)):
                continue
            found.append((key, href, is_file, text, a))
        # "?page=1" usually repeats the start page; counting it twice would make
        # its items look like menu links that appear on every page.
        signature = frozenset(key for key, *_ in found)
        if signature in seen_pages:
            continue
        seen_pages.add(signature)
        n_pages += 1
        before = len(links) + len(files)
        for key, href, is_file, text, a in found:
            item = (files if is_file else links).setdefault(
                key, {"url": href, "list_title": "", "list_text": "", "pages": set()})
            item["pages"].add(n_pages)
            if len(text) > len(item["list_title"]):
                item["list_title"] = text
            rtext = row_text(a, text)
            if len(rtext) > len(item["list_text"]) and len(rtext) < 2000:
                item["list_text"] = rtext
        print(f"listing page {n_pages} ({len(queue)} queued): "
              f"{len(links) + len(files) - before} new links")

    def is_menu(item: dict) -> bool:
        # Menus and sidebars repeat on (nearly) every listing page, items do not.
        return n_pages >= 3 and len(item["pages"]) >= max(3, n_pages * 0.8)

    candidates = [v for v in links.values() if not is_menu(v)]
    if link_pattern:
        items = [v for v in candidates if re.search(link_pattern, unquote(v["url"]))]
    else:
        groups: dict[str, list[dict]] = {}
        for v in candidates:
            segs = [s for s in unquote(urlsplit(v["url"]).path).split("/") if s]
            if segs and segs[0].lower() in ("fa", "en", "ar"):
                segs = segs[1:]
            groups.setdefault(segs[0] if segs else "", []).append(v)

        def score(group: list[dict]) -> int:
            return sum(1 for v in group if len(v["list_title"]) >= 12)

        ranked = sorted(groups.items(), key=lambda kv: score(kv[1]), reverse=True)
        items = ranked[0][1] if ranked and score(ranked[0][1]) else []
        print("link groups found (first path segment -> links with titles):")
        for seg, group in ranked[:6]:
            print(f"   /{seg}/…: {score(group)} of {len(group)}"
                  f"{'   <- used as items' if group is items else ''}")
        if items:
            print("   use --link-pattern REGEX to choose the item links yourself")
    file_items = [v for v in files.values() if not is_menu(v)]
    entries = []
    for v in items:
        entries.append({"id": short_hash(url_key(v["url"])), "kind": "page", "url": v["url"],
                        "list_title": v["list_title"], "list_text": v["list_text"]})
    for v in file_items:
        entries.append({"id": short_hash(url_key(v["url"])), "kind": "file", "url": v["url"],
                        "list_title": v["list_title"], "list_text": v["list_text"]})
    print(f"{n_pages} listing pages, {len(items)} item pages, {len(file_items)} files")
    return entries


# --------------------------------------------------------------------------
# Item pages
# --------------------------------------------------------------------------

MAIN_SELECTORS = [
    ".law-text", "#law-text", ".law_text", "#law_text", ".lawText", ".law-body", ".law_body",
    ".law-content", ".law_content", "#lawContent", ".text-law", ".body-law", ".content-law",
    "div[itemprop='articleBody']", ".news-body", ".newsBody", ".news-text", ".post-content",
    ".entry-content", ".body-content", "article .content",
]


def _direct_text_len(el: Tag) -> int:
    return sum(len(norm(str(c))) for c in el.children if isinstance(c, NavigableString))


def find_main_element(soup: BeautifulSoup) -> Tag | None:
    for sel in MAIN_SELECTORS:
        el = soup.select_one(sel)
        if el and len(norm(el.get_text(" "))) > 80:
            return el
    # Readability-style fallback: text blocks give points to their ancestors,
    # the container collecting the most (with few links) is the item text.
    scores: dict[int, float] = {}
    elements: dict[int, Tag] = {}
    for el in soup.find_all(["p", "div", "td", "li", "span", "font", "h1", "h2", "h3", "h4",
                             "h5", "h6", "blockquote", "pre", "section", "article", "strong"]):
        n = _direct_text_len(el)
        if n < 20:
            continue
        # A container scores as much as its own text blocks, so it is preferred
        # over any single paragraph inside it and no part of the text is lost.
        target = el
        for weight in (1.0, 1.0, 0.5, 0.25):
            if not isinstance(target, Tag) or target.name in ("body", "html", "[document]"):
                break
            scores[id(target)] = scores.get(id(target), 0) + n * weight
            elements[id(target)] = target
            target = target.parent
    best, best_score, best_depth = None, 0.0, 0
    for key, score in scores.items():
        el = elements[key]
        total = len(norm(el.get_text(" "))) or 1
        links = sum(len(norm(a.get_text(" "))) for a in el.find_all("a"))
        score *= 1 - min(0.9, links / total)
        depth = len(list(el.parents))
        # On a tie keep the innermost element, i.e. the one without extra page chrome.
        if score > best_score * 1.001 or (score >= best_score * 0.999 and depth > best_depth):
            best, best_score, best_depth = el, score, depth
    return best


def element_text(el: Tag) -> str:
    for br in el.find_all("br"):
        br.replace_with("\n")
    for block in el.find_all(["p", "div", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6",
                              "blockquote", "table"]):
        block.insert_before("\n")
        block.insert_after("\n")
    for cell in el.find_all(["td", "th"]):
        cell.insert_after(" | ")
    return clean_multiline(el.get_text(""))


def extract_metadata(soup: BeautifulSoup) -> dict[str, str]:
    meta: dict[str, str] = {}

    def put(label: str, value: str) -> None:
        label, value = norm(label).rstrip(":： "), norm(value).lstrip(":： ")
        if label and value and len(label) <= 40 and len(value) <= 300 and label not in meta:
            meta[label] = value

    for tr in soup.find_all("tr"):
        cells = tr.find_all(["th", "td"], recursive=False)
        if len(cells) == 2 and any(lbl in norm(cells[0].get_text(" ")) for lbl in META_LABELS):
            put(cells[0].get_text(" "), cells[1].get_text(" "))
    for dt in soup.find_all("dt"):
        dd = dt.find_next_sibling("dd")
        if dd:
            put(dt.get_text(" "), dd.get_text(" "))

    lines = [line for line in (norm(s) for s in soup.get_text("\n").split("\n")) if line]
    for label in META_LABELS:
        if label in meta:
            continue
        for i, line in enumerate(lines):
            m = re.match(rf"^{re.escape(label)}\s*[:：]?\s*(.*)$", line)
            if not m:
                continue
            value = m.group(1).strip()
            if not value and i + 1 < len(lines):
                value = lines[i + 1]
            if value and value not in META_LABELS:
                put(label, value)
                break
    return meta


def parse_page(html: str, base_url: str, attachments_in_main_only: bool) -> dict:
    soup = BeautifulSoup(html, "lxml")
    title = ""
    h1 = soup.find("h1")
    if h1:
        title = norm(h1.get_text(" "))
    if not title:
        og = soup.find("meta", attrs={"property": "og:title"})
        if og and og.get("content"):
            title = norm(og["content"])
    if not title and soup.title:
        title = norm(re.split(r"\s[|\-–]\s", soup.title.get_text())[0])

    meta = extract_metadata(soup)
    for tag in soup.find_all(NOISE_TAGS):
        if tag.name != "form":
            tag.decompose()
    headings = [norm(h.get_text(" ")) for h in soup.find_all(["h1", "h2", "h3"])]
    canonical = soup.find("link", rel="canonical")
    canonical = urljoin(base_url, canonical["href"]) if canonical and canonical.get("href") else ""
    main = find_main_element(soup)

    attachments: list[str] = []
    for a in (main if (main and attachments_in_main_only) else soup).find_all("a", href=True):
        href = urljoin(base_url, a["href"].strip()).split("#")[0]
        if FILE_RE.search(unquote(urlsplit(href).path)) and href not in attachments:
            attachments.append(href)

    text = element_text(main) if main else ""
    if len(text) < 40 and soup.body:
        text = element_text(soup.body)
    return {"title": title, "meta": meta, "text": text, "attachments": attachments,
            "headings": [h for h in headings if h], "canonical": canonical}


def file_text(path: Path) -> str:
    """Text of a downloaded PDF / DOCX attachment ("" for scans, images, other types)."""
    ext = path.suffix.lower()
    try:
        if ext == ".pdf" and PdfReader is not None:
            reader = PdfReader(str(path))
            text = "\n".join((page.extract_text() or "") for page in reader.pages)
        elif ext == ".docx":
            with zipfile.ZipFile(path) as zf:
                xml = zf.read("word/document.xml").decode("utf-8")
            xml = re.sub(r"</w:p>", "\n", xml)
            xml = re.sub(r"<w:tab/>", "\t", xml)
            text = html_lib.unescape(re.sub(r"<[^>]+>", "", xml))
        else:
            return ""
    except Exception as exc:  # broken or encrypted files must not stop the export
        print(f"  ! could not read {path.name}: {exc}", file=sys.stderr)
        return ""
    # NFKC turns Arabic presentation forms (common in Persian PDFs) into normal letters.
    return clean_multiline(unicodedata.normalize("NFKC", text))


# --------------------------------------------------------------------------
# Download
# --------------------------------------------------------------------------


def page_path(raw_dir: Path, entry_id: str) -> Path:
    return raw_dir / "pages" / f"{entry_id}.html.gz"


def file_path(raw_dir: Path, url: str) -> Path:
    ext = Path(unquote(urlsplit(url).path)).suffix.lower()[:6]
    return raw_dir / "files" / f"{short_hash(url_key(url))}{ext}"


def read_page(raw_dir: Path, entry_id: str) -> str | None:
    path = page_path(raw_dir, entry_id)
    if not path.exists():
        return None
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return fh.read()


def download_all(fetcher: Fetcher, entries: list[dict], raw_dir: Path, workers: int,
                 attachments_in_main_only: bool, with_files: bool) -> None:
    (raw_dir / "pages").mkdir(parents=True, exist_ok=True)
    (raw_dir / "files").mkdir(parents=True, exist_ok=True)

    def fetch_file(url: str) -> bool:
        path = file_path(raw_dir, url)
        if path.exists():
            return True
        data = fetcher.get_bytes(url)
        if data is None:
            return False
        path.write_bytes(data)
        return True

    def job(entry: dict) -> tuple[str, bool]:
        if entry["kind"] == "file":
            return entry["url"], fetch_file(entry["url"]) if with_files else True
        html = read_page(raw_dir, entry["id"])
        if html is None:
            html = fetcher.get(entry["url"])
            if html is None:
                return entry["url"], False
            with gzip.open(page_path(raw_dir, entry["id"]), "wt", encoding="utf-8") as fh:
                fh.write(html)
        ok = True
        if with_files:
            for url in parse_page(html, entry["url"], attachments_in_main_only)["attachments"]:
                ok = fetch_file(url) and ok
        return entry["url"], ok

    print(f"downloading {len(entries)} items (cached ones are skipped)")
    failed = []
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = [pool.submit(job, e) for e in entries]
        for n, fut in enumerate(as_completed(futures), 1):
            url, ok = fut.result()
            if not ok:
                failed.append(url)
            if n % 25 == 0 or n == len(entries):
                print(f"  {n}/{len(entries)}")
    if failed:
        print(f"WARNING: {len(failed)} items (or their attachments) could not be downloaded; "
              f"run the same command again to retry:\n  " + "\n  ".join(failed[:20]),
              file=sys.stderr)


# --------------------------------------------------------------------------
# Export
# --------------------------------------------------------------------------


def build_records(entries: list[dict], raw_dir: Path, attachments_in_main_only: bool) -> list[dict]:
    records = []
    for entry in entries:
        downloaded = True
        if entry["kind"] == "page":
            html = read_page(raw_dir, entry["id"])
            downloaded = html is not None
            parsed = (parse_page(html, entry["url"], attachments_in_main_only) if downloaded else
                      {"title": "", "meta": {}, "text": "", "attachments": [], "headings": []})
        else:
            name = unquote(Path(urlsplit(entry["url"]).path).name)
            parsed = {"title": entry.get("list_title") or name, "meta": {}, "text": "",
                      "attachments": [entry["url"]], "headings": []}
            downloaded = file_path(raw_dir, entry["url"]).exists()

        parts = [parsed["text"]] if parsed["text"] else []
        for url in parsed["attachments"]:
            path = file_path(raw_dir, url)
            text = file_text(path) if path.exists() else ""
            if text:
                name = unquote(Path(urlsplit(url).path).name)
                parts.append(text if entry["kind"] == "file" else f"--- پیوست: {name} ---\n{text}")
        text = "\n\n".join(parts)

        meta = parsed["meta"]
        title = parsed["title"] or entry.get("list_title", "")
        approve_date = parse_date(meta.get("تاریخ تصویب")) or parse_date(meta.get("تاریخ جلسه"))
        notify_date = parse_date(meta.get("تاریخ ابلاغ"))
        publish_date = (parse_date(meta.get("تاریخ انتشار")) or parse_date(meta.get("تاریخ درج"))
                        or parse_date(meta.get("تاریخ ارسال")))
        records.append({
            "id": entry["id"], "url": entry["url"], "kind": entry["kind"],
            "title": title, "list_title": entry.get("list_title", ""),
            "list_text": entry.get("list_text", ""),
            "approve_date": approve_date, "notify_date": notify_date,
            "publish_date": publish_date, "city_meta": norm(meta.get("شهر", "")),
            "province": norm(meta.get("استان", "")),
            "approver": meta.get("مرجع تصویب", ""),
            "number": (meta.get("شماره ابلاغ") or meta.get("شماره مصوبه")
                       or meta.get("شماره نامه") or meta.get("شماره جلسه", "")),
            "meta": meta, "text": text, "downloaded": downloaded,
            "attachments": parsed["attachments"], "headings": parsed["headings"],
            "canonical": parsed.get("canonical", ""),
        })

    # A heading repeated on most pages is the site name, not the item's title:
    # use the next heading of the page, or else the link text from the listing.
    counts = Counter(r["title"] for r in records)
    for r in records:
        if len(records) >= 3 and counts[r["title"]] > max(2, len(records) * 0.3):
            others = [h for h in r["headings"] if counts[h] <= max(2, len(records) * 0.3)
                      and len(h) >= 8]
            r["title"] = others[0] if others else (r["list_title"] or r["title"])

    records = merge_duplicates(records)

    for r in records:
        date = (r["approve_date"] or parse_date(r["title"]) or r["notify_date"]
                or r["publish_date"] or parse_date(r["list_text"]) or parse_date(r["text"][:600]))
        r["date"] = date
        r["year"] = date[:4] if date else ""
        r["city"] = (r["city_meta"] or extract_city(r["title"], r["list_title"])
                     or extract_city(r["text"][:1500]) or r["province"] or UNKNOWN)
    return records


GENERIC_LINK_TEXT = {"ادامه مطلب", "ادامه", "بیشتر", "مشاهده", "مشاهده بیشتر", "جزئیات",
                     "اطلاعات بیشتر", "more", "read more"}


def merge_duplicates(records: list[dict]) -> list[dict]:
    """Merge pages reached through two links (e.g. the title and "ادامه مطلب")."""
    merged: dict[str, dict] = {}
    out = []
    for r in records:
        if r["canonical"]:
            key = "url:" + url_key(r["canonical"])
        elif r["kind"] == "page" and len(r["text"]) >= 50:
            key = "text:" + short_hash(r["title"] + "\n" + r["text"])
        else:
            out.append(r)
            continue
        first = merged.get(key)
        if first is None:
            merged[key] = r
            out.append(r)
        elif (first["list_title"] in GENERIC_LINK_TEXT
              and r["list_title"] not in GENERIC_LINK_TEXT):
            first["list_title"], first["url"] = r["list_title"], r["url"]
    return out


def unify_city_spellings(records: list[dict]) -> None:
    """Group spellings such as "بندرعباس" / "بندر عباس" under the most common one."""
    def key(city: str) -> str:
        return re.sub(r"[\s‌]+", "", city).replace("آ", "ا")

    spellings: dict[str, Counter] = {}
    for r in records:
        spellings.setdefault(key(r["city"]), Counter())[r["city"]] += 1
    for r in records:
        r["city"] = spellings[key(r["city"])].most_common(1)[0][0]


def _id_key(r: dict) -> str:
    return r["id"].zfill(12)


def date_key(r: dict) -> tuple:
    return (r["date"] or "9999/99/99", _id_key(r))


def city_key(r: dict) -> tuple:
    return (r["city"] == UNKNOWN, r["city"]) + date_key(r)


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    chunks_per_row = [
        [r["text"][i:i + CELL_LIMIT] for i in range(0, len(r["text"]), CELL_LIMIT)] or [""]
        for r in rows
    ]
    n_text_cols = max((len(c) for c in chunks_per_row), default=1)
    text_headers = (["متن کامل مصوبه"] if n_text_cols == 1 else
                    [f"متن کامل مصوبه (بخش {i + 1})" for i in range(n_text_cols)])
    header = ["ردیف", "شناسه", "عنوان", "شهر", "تاریخ (مبنای مرتب‌سازی)", "سال", "تاریخ تصویب",
              "تاریخ ابلاغ", "تاریخ انتشار", "مرجع تصویب", "شماره", "لینک", "پیوست‌ها",
              "سایر اطلاعات", "تعداد نویسه متن", *text_headers]
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(fh, quoting=csv.QUOTE_ALL)
        writer.writerow(header)
        for n, (r, chunks) in enumerate(zip(rows, chunks_per_row), 1):
            chunks = chunks + [""] * (n_text_cols - len(chunks))
            writer.writerow([
                n, r["id"], r["title"], r["city"], r["date"], r["year"], r["approve_date"],
                r["notify_date"], r["publish_date"], r["approver"], r["number"], r["url"],
                "\n".join(r["attachments"]), json.dumps(r["meta"], ensure_ascii=False),
                len(r["text"]), *chunks,
            ])


def write_split(out_dir: Path, stem: str, rows: list[dict], rows_per_file: int) -> list[Path]:
    if rows_per_file <= 0 or len(rows) <= rows_per_file:
        path = out_dir / f"{stem}.csv"
        write_csv(path, rows)
        return [path]
    paths = []
    for part, start in enumerate(range(0, len(rows), rows_per_file), 1):
        path = out_dir / f"{stem}_part{part:02d}.csv"
        write_csv(path, rows[start:start + rows_per_file])
        paths.append(path)
    return paths


def export(records: list[dict], out_dir: Path, rows_per_file: int) -> None:
    csv_dir = out_dir / "csv"
    if csv_dir.exists():
        shutil.rmtree(csv_dir)
    unify_city_spellings(records)
    by_date = sorted(records, key=date_key)
    by_city = sorted(records, key=city_key)
    written = []
    written += write_split(csv_dir, "01_all_by_date", by_date, rows_per_file)
    written += write_split(csv_dir, "02_all_by_city", by_city, rows_per_file)

    cities: dict[str, list[dict]] = {}
    years: dict[str, list[dict]] = {}
    for r in by_date:
        cities.setdefault(r["city"], []).append(r)
        years.setdefault(r["year"] or UNKNOWN, []).append(r)
    for city, rows in cities.items():
        written += write_split(csv_dir / "by_city", safe_filename(city), rows, rows_per_file)
    for year, rows in years.items():
        written += write_split(csv_dir / "by_year", safe_filename(year),
                               sorted(rows, key=city_key), rows_per_file)

    with open(csv_dir / "00_summary_by_city.csv", "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["شهر", "تعداد مصوبات", "نخستین تاریخ", "آخرین تاریخ"])
        for city, rows in sorted(cities.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            dates = [r["date"] for r in rows if r["date"]]
            writer.writerow([city, len(rows), min(dates, default=""), max(dates, default="")])

    missing = [r["url"] for r in records if not r["downloaded"]]
    empty = [r["url"] for r in records if r["downloaded"] and not r["text"]]
    print(f"\n{len(records)} items exported, {len(cities)} cities, {len(years)} years")
    print(f"{len(written) + 1} CSV files in {csv_dir}")
    if missing:
        print(f"WARNING: {len(missing)} items were not downloaded (kept with title/link only):\n  "
              + "\n  ".join(missing[:20]), file=sys.stderr)
    if empty:
        print(f"NOTE: {len(empty)} items have no extractable text (e.g. scanned images); "
              f"they are kept with their title, link and attachment links:\n  "
              + "\n  ".join(empty[:20]), file=sys.stderr)
    if PdfReader is None and any(u.lower().endswith(".pdf") for r in records for u in r["attachments"]):
        print("NOTE: install pypdf (pip install pypdf) to include the text of PDF attachments.",
              file=sys.stderr)


# --------------------------------------------------------------------------


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", nargs="?", default="mrud",
                    help="preset name (mrud, majlis) or listing URL (default: mrud)")
    ap.add_argument("--out", help="output directory (default: output/<preset or host>)")
    ap.add_argument("--delay", type=float, default=0.5, help="seconds to wait after each request")
    ap.add_argument("--timeout", type=float, default=60)
    ap.add_argument("--retries", type=int, default=5)
    ap.add_argument("--workers", type=int, default=3, help="parallel downloads")
    ap.add_argument("--max-pages", type=int, help="stop after this many listing pages (testing)")
    ap.add_argument("--link-pattern", help="regex that item URLs must match (generic sites)")
    ap.add_argument("--no-files", action="store_true", help="do not download attachments")
    ap.add_argument("--rows-per-file", type=int, default=1000,
                    help="split CSV files larger than this many rows (0 = never split)")
    ap.add_argument("--refresh-list", action="store_true", help="re-crawl the listing even if cached")
    ap.add_argument("--export-only", action="store_true", help="only rebuild CSVs from the cache")
    args = ap.parse_args()

    url = PRESETS.get(args.source, args.source)
    if not url.startswith(("http://", "https://")):
        sys.exit(f"unknown source {args.source!r}; use one of {', '.join(PRESETS)} or a URL")
    host = urlsplit(url).netloc.lower()
    is_majlis = host.endswith("rc.majlis.ir")
    out_dir = Path(args.out or Path("output") / (args.source if args.source in PRESETS else host))
    raw_dir = out_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    index_file = raw_dir / "index.json"
    # rc.majlis.ir attachments outside the law text are other formats of the same law.
    main_only = is_majlis

    if index_file.exists() and not args.refresh_list:
        entries = json.loads(index_file.read_text(encoding="utf-8"))
        print(f"using cached list of {len(entries)} items ({index_file}; --refresh-list to re-crawl)")
    elif args.export_only:
        sys.exit(f"no cache found at {index_file}; run without --export-only first")
    else:
        fetcher = Fetcher(args.delay, args.timeout, args.retries)
        entries = (crawl_majlis(fetcher, url, args.max_pages) if is_majlis else
                   crawl_generic(fetcher, url, args.max_pages, args.link_pattern))
        if not entries:
            sys.exit("no items found on the listing page – check the URL / network access. If the "
                     "site loads its list with JavaScript, save the page from your browser and "
                     "send it for analysis.")
        index_file.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf-8")

    if not args.export_only:
        download_all(Fetcher(args.delay, args.timeout, args.retries), entries, raw_dir,
                     args.workers, main_only, not args.no_files)

    export(build_records(entries, raw_dir, main_only), out_dir, args.rows_per_file)


if __name__ == "__main__":
    main()
