#!/usr/bin/env python3
"""
استخراج همه مصوبات یک جستجوی سامانه قوانین مرکز پژوهش‌های مجلس (rc.majlis.ir)
و ذخیره آن‌ها در فایل‌های CSV، مرتب‌شده بر اساس زمان و بر اساس شهر.

Scrape every result of an rc.majlis.ir law search (default: the
``lu_approve_reference=lar15`` search), download the full text of each
resolution and export CSV files sorted by date and grouped by city.

Usage:
    pip install -r requirements.txt
    python scrape_rc_majlis.py                      # crawl + export
    python scrape_rc_majlis.py --export-only        # re-export from cache
    python scrape_rc_majlis.py --url "https://rc.majlis.ir/fa/law/search?lu_approve_reference=lar15&page=1"

Downloads are cached under <out>/raw, so an interrupted run can simply be
restarted and it continues where it stopped.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import re
import shutil
import sys
from collections import Counter
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup, NavigableString, Tag

DEFAULT_URL = "https://rc.majlis.ir/fa/law/search?lu_approve_reference=lar15&page=1"
LAW_ID_RE = re.compile(r"/fa/law/show/(\d+)")
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
# Excel shows at most 32,767 characters per cell, so long texts are split
# over several "متن" columns instead of being truncated.
CELL_LIMIT = 32000

# --------------------------------------------------------------------------
# Text helpers
# --------------------------------------------------------------------------

_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
_LETTERS = str.maketrans({"ي": "ی", "ك": "ک", "ى": "ی", "ة": "ه", "‏": "", "‎": ""})

PERSIAN_MONTHS = {
    "فروردین": 1, "اردیبهشت": 2, "خرداد": 3, "تیر": 4, "مرداد": 5, "امرداد": 5,
    "شهریور": 6, "مهر": 7, "آبان": 8, "آذر": 9, "دی": 10, "بهمن": 11, "اسفند": 12,
}

META_LABELS = [
    "شماره انتشار", "تاریخ تصویب", "تاریخ ابلاغ", "تاریخ انتشار", "تاریخ اجرا",
    "مرجع تصویب", "شماره ابلاغ", "شماره مصوبه", "شماره نامه", "شماره جلسه", "تاریخ جلسه",
    "شماره روزنامه رسمی", "تاریخ روزنامه رسمی", "شماره ویژه نامه", "نوع قانون",
    "نوع مصوبه", "نوع", "دستگاه اجرایی", "موضوع", "وضعیت", "شهر", "استان", "دوره",
]

# Words that end a city name inside a title such as
# "مصوبه شورای اسلامی شهر بندر انزلی در خصوص ..."
_CITY_STOP = (
    r"در\s*خصوص|درخصوص|درباره|در\s*مورد|راجع|مبنی|موضوع|مورخ|مصوب|مصوبه|جهت|برای|"
    r"به|با|در|و|از|که|دوره|سال|شماره|نسبت|پیرامون|مربوط|اصلاح|ابطال|بند|تبصره|ماده"
)
_CITY_END = rf"(?=\s+(?:{_CITY_STOP})(?:\s|$)|\s*[،,:؛;()\[\]«»\"\-–—/.]|\s*\d|$)"
CITY_PATTERNS = [
    re.compile(rf"شورا(?:ی|ى)?\s*(?:های\s*)?اسلامی\s*(?:کلان\s*)?شهر(?:ستان)?\s+(.{{2,40}}?){_CITY_END}"),
    re.compile(rf"شورا(?:ی|ى)?\s*(?:عالی\s*)?استان\s+(.{{2,40}}?){_CITY_END}"),
    re.compile(rf"شهرداری\s*(?:کلان\s*شهر\s*|شهر\s+)?(.{{2,40}}?){_CITY_END}"),
    re.compile(rf"(?:کلان\s*)?شهر\s+(.{{2,40}}?){_CITY_END}"),
]
_NOT_A_CITY = {"", "های", "ها", "و", "در", "به", "از", "خود", "مذکور", "مربوط", "مزبور", "جدید"}


def norm(text: str | None) -> str:
    if not text:
        return ""
    text = text.translate(_LETTERS).replace("\xa0", " ")
    return re.sub(r"[ \t\r\f\v]+", " ", text).strip()


def clean_multiline(text: str) -> str:
    lines = [norm(line) for line in text.split("\n")]
    out, blank = [], False
    for line in lines:
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
    m = re.search(r"(1[234]\d\d)\s*[/\-.]\s*(\d{1,2})\s*[/\-.]\s*(\d{1,2})", t)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return f"{y:04d}/{mo:02d}/{d:02d}"
    m = re.search(r"(\d{1,2})\s*[/\-.]\s*(\d{1,2})\s*[/\-.]\s*(1[234]\d\d)", t)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return f"{y:04d}/{mo:02d}/{d:02d}"
    months = "|".join(PERSIAN_MONTHS)
    m = re.search(rf"(\d{{1,2}})\s*({months})\s*(?:ماه\s*)?(?:سال\s*)?(1[234]\d\d)", t)
    if m:
        return f"{int(m.group(3)):04d}/{PERSIAN_MONTHS[m.group(2)]:02d}/{int(m.group(1)):02d}"
    return ""


def extract_city(*texts: str) -> str:
    for text in texts:
        t = norm(text).replace("‌", " ")
        if not t:
            continue
        for pat in CITY_PATTERNS:
            for m in pat.finditer(t):
                city = norm(m.group(1)).strip(" .،,-")
                if city and city not in _NOT_A_CITY and not city.isdigit():
                    return city
    return ""


def safe_filename(name: str) -> str:
    name = re.sub(r'[\\/:*?"<>|‌]+', " ", name)
    name = re.sub(r"\s+", "_", name.strip())
    return name[:80] or "نامشخص"


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

    def get(self, url: str) -> str | None:
        for attempt in range(1, self.retries + 1):
            try:
                resp = self.session.get(url, timeout=self.timeout)
                if resp.status_code == 404:
                    return None
                resp.raise_for_status()
                resp.encoding = resp.apparent_encoding if not resp.encoding else resp.encoding
                if self.delay:
                    time.sleep(self.delay)
                return resp.text
            except requests.RequestException as exc:
                if attempt == self.retries:
                    print(f"  ! failed {url}: {exc}", file=sys.stderr)
                    return None
                time.sleep(min(60, 2 ** attempt))
        return None


def with_page(url: str, page: int) -> str:
    parts = urlsplit(url)
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k != "page"]
    query.append(("page", str(page)))
    return urlunsplit(parts._replace(query=urlencode(query)))


# --------------------------------------------------------------------------
# Search result pages
# --------------------------------------------------------------------------


def parse_search_page(html: str, page_url: str) -> tuple[list[dict], int]:
    """Return (results, highest page number seen in the pagination)."""
    soup = BeautifulSoup(html, "lxml")
    results: dict[str, dict] = {}
    for a in soup.find_all("a", href=True):
        m = LAW_ID_RE.search(a["href"])
        if not m:
            continue
        law_id = m.group(1)
        title = norm(a.get_text(" "))
        # The surrounding row/card usually also holds the date and approver.
        row = a
        for _ in range(4):
            if row.parent is None or row.parent.name in ("body", "html"):
                break
            row = row.parent
            if row.name in ("tr", "li", "article") or len(norm(row.get_text(" "))) > len(title) + 20:
                break
        entry = results.setdefault(
            law_id,
            {"id": law_id, "url": urljoin(page_url, f"/fa/law/show/{law_id}"),
             "list_title": "", "list_text": ""},
        )
        if len(title) > len(entry["list_title"]):
            entry["list_title"] = title
        row_text = norm(row.get_text(" "))
        if len(row_text) > len(entry["list_text"]):
            entry["list_text"] = row_text

    max_page = 0
    for a in soup.find_all("a", href=True):
        m = re.search(r"[?&]page=(\d+)", a["href"])
        if m:
            max_page = max(max_page, int(m.group(1)))
    return list(results.values()), max_page


def crawl_search(fetcher: Fetcher, url: str, raw_dir: Path, max_pages: int | None) -> list[dict]:
    index_file = raw_dir / "search_index.json"
    found: dict[str, dict] = {}
    if index_file.exists():
        found = {r["id"]: r for r in json.loads(index_file.read_text(encoding="utf-8"))}

    page, last_page, empty_streak = 1, None, 0
    while True:
        if max_pages and page > max_pages:
            break
        if last_page is not None and page > last_page:
            break
        page_url = with_page(url, page)
        html = fetcher.get(page_url)
        if html is None:
            empty_streak += 1
            if empty_streak >= 2:
                break
            page += 1
            continue
        results, seen_max = parse_search_page(html, page_url)
        new = [r for r in results if r["id"] not in found]
        for r in results:
            found.setdefault(r["id"], r)["search_page"] = page
        if seen_max:
            last_page = max(last_page or 0, seen_max)
        print(f"search page {page}{'/' + str(last_page) if last_page else ''}: "
              f"{len(results)} results, {len(new)} new, {len(found)} total")
        index_file.write_text(json.dumps(list(found.values()), ensure_ascii=False, indent=1),
                              encoding="utf-8")
        # Without a visible pagination we stop at the first page with nothing new.
        if not results or (not new and last_page is None):
            empty_streak += 1
            if empty_streak >= 2 or not results:
                break
        else:
            empty_streak = 0
        page += 1
    return list(found.values())


# --------------------------------------------------------------------------
# Law pages
# --------------------------------------------------------------------------

MAIN_SELECTORS = [
    ".law-text", "#law-text", ".law_text", "#law_text", ".lawText", ".law-body", ".law_body",
    ".law-content", ".law_content", "#lawContent", ".text-law", ".body-law", ".content-law",
    "div[itemprop='articleBody']", "article .content", ".entry-content",
]
NOISE_TAGS = ["script", "style", "noscript", "nav", "header", "footer", "form", "aside",
              "iframe", "svg", "button", "select", "input"]


def _direct_text_len(el: Tag) -> int:
    return sum(len(norm(str(c))) for c in el.children if isinstance(c, NavigableString))


def find_main_element(soup: BeautifulSoup) -> Tag | None:
    for sel in MAIN_SELECTORS:
        el = soup.select_one(sel)
        if el and len(norm(el.get_text(" "))) > 80:
            return el
    # Readability-style fallback: text blocks give points to their ancestors,
    # the container collecting the most (with few links) is the law text.
    scores: dict[int, float] = {}
    elements: dict[int, Tag] = {}
    for el in soup.find_all(["p", "div", "td", "li", "span", "font", "h1", "h2", "h3", "h4",
                             "h5", "h6", "blockquote", "pre", "section", "article"]):
        n = _direct_text_len(el)
        if n < 20:
            continue
        target = el
        # A container scores as much as its own text blocks, so it is preferred
        # over any single paragraph inside it and no part of the text is lost.
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
        if len(cells) == 2:
            put(cells[0].get_text(" "), cells[1].get_text(" "))
    for dt in soup.find_all("dt"):
        dd = dt.find_next_sibling("dd")
        if dd:
            put(dt.get_text(" "), dd.get_text(" "))

    flat = "\n".join(norm(s) for s in soup.get_text("\n").split("\n"))
    lines = [line for line in flat.split("\n") if line]
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


def parse_law_page(html: str) -> dict:
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
        tag.decompose()
    main = find_main_element(soup)
    text = element_text(main) if main else ""
    if len(text) < 40 and soup.body:
        text = element_text(soup.body)
    return {"title": title, "meta": meta, "text": text}


def raw_path(raw_dir: Path, law_id: str) -> Path:
    return raw_dir / "laws" / f"{law_id}.html.gz"


def download_laws(fetcher: Fetcher, entries: list[dict], raw_dir: Path, workers: int) -> None:
    (raw_dir / "laws").mkdir(parents=True, exist_ok=True)
    todo = [e for e in entries if not raw_path(raw_dir, e["id"]).exists()]
    print(f"{len(entries)} resolutions, {len(entries) - len(todo)} already cached, "
          f"{len(todo)} to download")

    def job(entry: dict) -> tuple[str, bool]:
        html = fetcher.get(entry["url"])
        if html is None:
            return entry["id"], False
        with gzip.open(raw_path(raw_dir, entry["id"]), "wt", encoding="utf-8") as fh:
            fh.write(html)
        return entry["id"], True

    failed = []
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = [pool.submit(job, e) for e in todo]
        for n, fut in enumerate(as_completed(futures), 1):
            law_id, ok = fut.result()
            if not ok:
                failed.append(law_id)
            if n % 25 == 0 or n == len(todo):
                print(f"  downloaded {n}/{len(todo)}")
    if failed:
        print(f"WARNING: {len(failed)} pages could not be downloaded (run again to retry): "
              f"{', '.join(failed[:20])}{' ...' if len(failed) > 20 else ''}", file=sys.stderr)


# --------------------------------------------------------------------------
# Export
# --------------------------------------------------------------------------


def build_records(entries: list[dict], raw_dir: Path) -> list[dict]:
    records = []
    for entry in entries:
        path = raw_path(raw_dir, entry["id"])
        parsed = {"title": "", "meta": {}, "text": ""}
        if path.exists():
            with gzip.open(path, "rt", encoding="utf-8") as fh:
                parsed = parse_law_page(fh.read())
        meta = parsed["meta"]
        title = parsed["title"] or entry.get("list_title", "")
        approve_date = parse_date(meta.get("تاریخ تصویب")) or parse_date(meta.get("تاریخ جلسه"))
        notify_date = parse_date(meta.get("تاریخ ابلاغ"))
        any_date = (approve_date or notify_date or parse_date(meta.get("تاریخ انتشار"))
                    or parse_date(entry.get("list_text")) or parse_date(title)
                    or parse_date(parsed["text"][:500]))
        city = (norm(meta.get("شهر", "")) or extract_city(title, entry.get("list_title", ""))
                or extract_city(parsed["text"][:1500]) or norm(meta.get("استان", "")))
        records.append({
            "id": entry["id"],
            "url": entry["url"],
            "title": title,
            "date": any_date,
            "approve_date": approve_date,
            "notify_date": notify_date,
            "year": any_date[:4] if any_date else "",
            "city": city or "نامشخص",
            "approver": meta.get("مرجع تصویب", ""),
            "number": meta.get("شماره ابلاغ") or meta.get("شماره مصوبه") or meta.get("شماره نامه", ""),
            "meta": meta,
            "text": parsed["text"],
            "downloaded": path.exists(),
        })
    return records


def date_key(r: dict) -> tuple:
    return (r["date"] or "9999/99/99", int(r["id"]))


def city_key(r: dict) -> tuple:
    return ((r["city"] == "نامشخص"), r["city"]) + date_key(r)


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
              "تاریخ ابلاغ", "مرجع تصویب", "شماره", "لینک", "سایر اطلاعات", "تعداد نویسه متن",
              *text_headers]
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(fh, quoting=csv.QUOTE_ALL)
        writer.writerow(header)
        for n, (r, chunks) in enumerate(zip(rows, chunks_per_row), 1):
            chunks = chunks + [""] * (n_text_cols - len(chunks))
            writer.writerow([
                n, r["id"], r["title"], r["city"], r["date"], r["year"], r["approve_date"],
                r["notify_date"], r["approver"], r["number"], r["url"],
                json.dumps(r["meta"], ensure_ascii=False), len(r["text"]), *chunks,
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


def unify_city_spellings(records: list[dict]) -> None:
    """Group spellings such as "بندرعباس" / "بندر عباس" under the most common one."""
    def key(city: str) -> str:
        return re.sub(r"[\s\u200c]+", "", city).replace("آ", "ا")

    spellings: dict[str, Counter] = {}
    for r in records:
        spellings.setdefault(key(r["city"]), Counter())[r["city"]] += 1
    for r in records:
        r["city"] = spellings[key(r["city"])].most_common(1)[0][0]


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
        years.setdefault(r["year"] or "نامشخص", []).append(r)
    for city, rows in cities.items():
        written += write_split(csv_dir / "by_city", safe_filename(city), rows, rows_per_file)
    for year, rows in years.items():
        written += write_split(csv_dir / "by_year", safe_filename(year),
                               sorted(rows, key=city_key), rows_per_file)

    summary = csv_dir / "00_summary_by_city.csv"
    with open(summary, "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["شهر", "تعداد مصوبات", "نخستین تاریخ", "آخرین تاریخ"])
        for city, rows in sorted(cities.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            dates = [r["date"] for r in rows if r["date"]]
            writer.writerow([city, len(rows), min(dates, default=""), max(dates, default="")])

    missing = [r["id"] for r in records if not r["downloaded"]]
    empty = [r["id"] for r in records if r["downloaded"] and not r["text"]]
    print(f"\n{len(records)} resolutions exported, {len(cities)} cities, {len(years)} years")
    print(f"CSV files: {len(written) + 1} in {csv_dir}")
    if missing:
        print(f"WARNING: {len(missing)} resolutions have no downloaded page (rows kept with "
              f"title/link only): {', '.join(missing[:20])}", file=sys.stderr)
    if empty:
        print(f"WARNING: {len(empty)} pages had no detectable text: {', '.join(empty[:20])}",
              file=sys.stderr)


# --------------------------------------------------------------------------


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default=DEFAULT_URL, help="search URL (the page= parameter is replaced)")
    ap.add_argument("--out", default="output", help="output directory (default: output)")
    ap.add_argument("--delay", type=float, default=0.5, help="seconds to wait after each request")
    ap.add_argument("--timeout", type=float, default=60)
    ap.add_argument("--retries", type=int, default=5)
    ap.add_argument("--workers", type=int, default=3, help="parallel downloads of resolution pages")
    ap.add_argument("--max-pages", type=int, help="stop after this many search pages (testing)")
    ap.add_argument("--rows-per-file", type=int, default=1000,
                    help="split CSV files larger than this many rows (0 = never split)")
    ap.add_argument("--refresh-search", action="store_true", help="re-crawl the search pages even if cached")
    ap.add_argument("--export-only", action="store_true", help="only rebuild CSVs from the cache")
    args = ap.parse_args()

    out_dir = Path(args.out)
    raw_dir = out_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    index_file = raw_dir / "search_index.json"

    if args.export_only:
        if not index_file.exists():
            sys.exit(f"no cache found at {index_file}; run without --export-only first")
        entries = json.loads(index_file.read_text(encoding="utf-8"))
    else:
        fetcher = Fetcher(args.delay, args.timeout, args.retries)
        if args.refresh_search and index_file.exists():
            index_file.unlink()
        entries = crawl_search(fetcher, args.url, raw_dir, args.max_pages)
        if not entries:
            sys.exit("no resolutions found on the search pages – check the URL / network access")
        download_laws(fetcher, entries, raw_dir, args.workers)

    export(build_records(entries, raw_dir), out_dir, args.rows_per_file)


if __name__ == "__main__":
    main()
