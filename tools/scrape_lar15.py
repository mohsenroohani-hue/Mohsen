#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""استخراج «مصوبات شورای عالی شهرسازی و معماری ایران» از پایگاه مرکز پژوهش‌های مجلس.

منبع: https://rc.majlis.ir/fa/law/search?lu_approve_reference=lar15&page=N

خروجی‌ها (در پوشه --out):
  * lar15_by_date.csv   : همه مصوبات، مرتب بر اساس تاریخ تصویب
  * lar15_by_city.csv   : همه مصوبات، مرتب بر اساس استان/شهر و سپس تاریخ
  * parts/lar15_part_NN.csv : همان داده‌ها تکه‌تکه (پیش‌فرض هر ۲۰۰ ردیف) تا هیچ
                              مصوبه‌ای جا نماند و فایل‌ها قابل باز شدن باشند
  * texts/<id>.txt      : متن کامل هر مصوبه به صورت فایل جداگانه (نسخه امن)
  * lar15_all.jsonl     : داده خام همه مصوبات
  * report.txt          : گزارش پوشش (تعداد، تاریخ‌های ناشناخته، شهرهای ناشناخته)

فقط با کتابخانه استاندارد پایتون ۳ کار می‌کند (بدون نیاز به نصب چیزی).

نمونه اجرا:
    python3 tools/scrape_lar15.py --out output
    python3 tools/scrape_lar15.py --out output --max-pages 5 --delay 1.5
    python3 tools/scrape_lar15.py --out output --from-cache   # بدون شبکه
"""

import argparse
import csv
import json
import os
import random
import re
import sys
import time
from urllib import error, parse, request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import htmlutil as H
from cityfinder import find_cities, subject_type
from persian import (find_jalali_date, format_jalali, gregorian_iso, match_key,
                     normalize)

BASE = "https://rc.majlis.ir"
SEARCH_URL = BASE + "/fa/law/search?lu_approve_reference=lar15&page=%d"
SHOW_RE = re.compile(r"/(?:fa|en)/law/show/(\d+)")
USER_AGENT = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

LABELS = [
    ("approval_date_raw", ["تاریخ تصویب", "تاريخ تصويب"]),
    ("approval_body", ["مرجع تصویب", "مرجع تصويب", "مصوبه"]),
    ("announcement_number", ["شماره ابلاغ", "شماره نامه", "شماره مصوبه", "شماره"]),
    ("announcement_date_raw", ["تاریخ ابلاغ", "تاريخ ابلاغ"]),
    ("status", ["وضعیت", "وضعيت"]),
    ("executor", ["دستگاه مجری", "مجری"]),
    ("law_type", ["نوع قانون", "نوع سند", "دسته"]),
]

COLUMNS = [
    "id", "url", "title", "approval_date_jalali", "approval_date_gregorian",
    "year", "month", "day", "city", "city_kind", "province", "all_cities",
    "subject_type", "approval_body", "announcement_number", "announcement_date",
    "status", "text_length", "full_text",
]


# ---------------------------------------------------------------- HTTP layer
class Fetcher:
    def __init__(self, cache_dir, delay=1.0, retries=4, timeout=60, offline=False):
        self.cache_dir = cache_dir
        self.delay = delay
        self.retries = retries
        self.timeout = timeout
        self.offline = offline
        self.last_request = 0.0
        os.makedirs(cache_dir, exist_ok=True)

    def _cache_path(self, key):
        safe = re.sub(r"[^A-Za-z0-9_.-]", "_", key)[:120]
        return os.path.join(self.cache_dir, safe + ".html")

    def get(self, url, key, force=False):
        path = self._cache_path(key)
        if not force and os.path.exists(path):
            with open(path, "r", encoding="utf-8", errors="replace") as handle:
                return handle.read()
        if self.offline:
            return None
        html = self._download(url)
        if html is None:
            return None
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(html)
        return html

    def _download(self, url):
        wait = 2.0
        for attempt in range(1, self.retries + 1):
            gap = time.time() - self.last_request
            if gap < self.delay:
                time.sleep(self.delay - gap)
            req = request.Request(url, headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "fa,en;q=0.8",
            })
            try:
                with request.urlopen(req, timeout=self.timeout) as resp:
                    raw = resp.read()
                charset = "utf-8"
                self.last_request = time.time()
                return raw.decode(charset, errors="replace")
            except error.HTTPError as exc:
                self.last_request = time.time()
                if exc.code in (404, 410):
                    sys.stderr.write("  ! %s -> HTTP %d\n" % (url, exc.code))
                    return None
                sys.stderr.write("  ! HTTP %d on %s (try %d/%d)\n"
                                 % (exc.code, url, attempt, self.retries))
            except Exception as exc:  # network/timeout/TLS
                self.last_request = time.time()
                sys.stderr.write("  ! %s on %s (try %d/%d)\n"
                                 % (exc.__class__.__name__, url, attempt, self.retries))
            if attempt < self.retries:
                time.sleep(wait + random.uniform(0, 1))
                wait *= 2
        return None


# ------------------------------------------------------------- page parsing
def parse_search_page(html):
    """(فهرست (شناسه، عنوان، تاریخ متن فهرست)، آیا صفحه بعدی وجود دارد)"""
    doc = H.parse_html(html)
    items, seen = [], set()
    for href, text in H.links(doc):
        match = SHOW_RE.search(href)
        if not match:
            continue
        law_id = match.group(1)
        if law_id in seen:
            continue
        seen.add(law_id)
        items.append({"id": law_id,
                      "url": parse.urljoin(BASE, href.split("?")[0]),
                      "list_title": normalize(text)})
    page_text = H.collapse_ws(H.node_text(doc))
    has_next = bool(re.search(r"صفحه\s*بعد|بعدی|next", page_text, re.I))
    return items, has_next


def _label_value(text, names):
    for name in names:
        pattern = re.compile(re.escape(name) + r"\s*[:：]?\s*([^\n]{1,160})")
        match = pattern.search(text)
        if match:
            value = match.group(1).strip(" :-–—،")
            if value:
                return normalize(value)
    return ""


def parse_law_page(html, url, law_id, list_title=""):
    doc = H.parse_html(html)
    title = normalize(H.page_title(doc)) or list_title
    title = re.sub(r"\s*\|\s*مرکز پژوهش.*$", "", title).strip()
    body = H.extract_main_text(doc)
    # متن کامل عیناً نگه داشته می‌شود؛ فقط حروف عربی به فارسی یکسان‌سازی می‌شود
    body = normalize(body, keep_zwnj=True, convert_digits=False)
    page_text = normalize(H.collapse_ws(H.node_text(doc)))

    meta = {}
    for field, names in LABELS:
        meta[field] = _label_value(page_text, names)

    date = (find_jalali_date(meta.get("approval_date_raw", ""))
            or find_jalali_date(title)
            or find_jalali_date(body[:2000])
            or find_jalali_date(page_text))
    ann_date = find_jalali_date(meta.get("announcement_date_raw", ""))

    city, kind, province, all_cities, _src = find_cities(title, body)

    record = {
        "id": law_id,
        "url": url,
        "title": title,
        "approval_date_jalali": format_jalali(date),
        "approval_date_gregorian": gregorian_iso(date),
        "year": date[0] if date else "",
        "month": date[1] if date else "",
        "day": date[2] if date else "",
        "city": city,
        "city_kind": kind,
        "province": province,
        "all_cities": "؛ ".join(all_cities),
        "subject_type": subject_type(title) or subject_type(body[:400]),
        "approval_body": meta.get("approval_body", "")
                          or "شورای عالی شهرسازی و معماری ایران",
        "announcement_number": meta.get("announcement_number", ""),
        "announcement_date": format_jalali(ann_date) or meta.get("announcement_date_raw", ""),
        "status": meta.get("status", ""),
        "text_length": len(body),
        "full_text": body,
    }
    return record


# ------------------------------------------------------------------ outputs
def sort_key_date(record):
    if record["approval_date_jalali"]:
        return (0, record["approval_date_jalali"], record["title"])
    return (1, "", record["title"])  # بدون تاریخ: انتهای فهرست


def sort_key_city(record):
    province = record["province"] or "ۿ"      # بدون استان: آخر
    city = record["city"] or "ۿ"
    return (province, city, record["approval_date_jalali"] or "9999")


def write_csv(path, rows, columns=COLUMNS):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns,
                                extrasaction="ignore", quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return path


def write_outputs(records, out_dir, rows_per_part=200):
    os.makedirs(out_dir, exist_ok=True)
    by_date = sorted(records, key=sort_key_date)
    by_city = sorted(records, key=sort_key_city)

    written = [write_csv(os.path.join(out_dir, "lar15_by_date.csv"), by_date),
               write_csv(os.path.join(out_dir, "lar15_by_city.csv"), by_city)]

    parts_dir = os.path.join(out_dir, "parts")
    for old in sorted(os.listdir(parts_dir)) if os.path.isdir(parts_dir) else []:
        if old.startswith("lar15_part_") and old.endswith(".csv"):
            os.remove(os.path.join(parts_dir, old))
    for index in range(0, len(by_date), rows_per_part):
        chunk = by_date[index:index + rows_per_part]
        name = "lar15_part_%02d.csv" % (index // rows_per_part + 1)
        written.append(write_csv(os.path.join(parts_dir, name), chunk))

    texts_dir = os.path.join(out_dir, "texts")
    os.makedirs(texts_dir, exist_ok=True)
    for record in records:
        with open(os.path.join(texts_dir, "%s.txt" % record["id"]), "w",
                  encoding="utf-8") as handle:
            handle.write("%s\n%s\n\n" % (record["title"], record["url"]))
            handle.write("تاریخ تصویب: %s\n" % record["approval_date_jalali"])
            handle.write("شهر: %s   استان: %s\n\n" % (record["city"], record["province"]))
            handle.write(record["full_text"])

    with open(os.path.join(out_dir, "lar15_all.jsonl"), "w", encoding="utf-8") as handle:
        for record in by_date:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    report = build_report(records)
    with open(os.path.join(out_dir, "report.txt"), "w", encoding="utf-8") as handle:
        handle.write(report)
    written.append(os.path.join(out_dir, "report.txt"))
    return written, report


def build_report(records):
    total = len(records)
    no_date = [r for r in records if not r["approval_date_jalali"]]
    no_city = [r for r in records if not r["city"]]
    short = [r for r in records if r["text_length"] < 200]
    years = {}
    cities = {}
    for record in records:
        if record["year"]:
            years[record["year"]] = years.get(record["year"], 0) + 1
        if record["city"]:
            cities[record["city"]] = cities.get(record["city"], 0) + 1
    lines = ["گزارش استخراج مصوبات (lar15)", "=" * 40,
             "تعداد کل مصوبات: %d" % total,
             "بدون تاریخ تصویب: %d" % len(no_date),
             "بدون شهر تشخیص‌داده‌شده: %d" % len(no_city),
             "متن کوتاه‌تر از ۲۰۰ نویسه (نیازمند بررسی): %d" % len(short),
             "تعداد شهرهای متمایز: %d" % len(cities), "",
             "پراکندگی سالانه:"]
    for year in sorted(years):
        lines.append("  %s : %d" % (year, years[year]))
    lines.append("")
    lines.append("پرتکرارترین شهرها:")
    for city, count in sorted(cities.items(), key=lambda kv: -kv[1])[:25]:
        lines.append("  %s : %d" % (city, count))
    if short:
        lines.append("")
        lines.append("شناسه مصوبات با متن کوتاه:")
        lines.append("  " + ", ".join(r["id"] for r in short[:100]))
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------- main
def crawl(fetcher, max_pages, start_page=1, verbose=True):
    """پیمایش صفحات جست‌وجو و برگرداندن فهرست مصوبات (بدون تکرار)."""
    found, order = {}, []
    page = start_page
    empty_pages = 0
    while page <= max_pages:
        url = SEARCH_URL % page
        html = fetcher.get(url, "search_p%03d" % page)
        if html is None:
            if verbose:
                print("صفحه %d در دسترس نیست؛ توقف." % page)
            break
        items, _ = parse_search_page(html)
        fresh = [i for i in items if i["id"] not in found]
        if verbose:
            print("صفحه %-3d : %d پیوند (%d تازه)" % (page, len(items), len(fresh)))
        if not fresh:
            empty_pages += 1
            if empty_pages >= 2:
                break
        else:
            empty_pages = 0
        for item in fresh:
            found[item["id"]] = item
            order.append(item)
        page += 1
    return order


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="استخراج مصوبات شورای عالی شهرسازی و معماری (rc.majlis.ir)")
    parser.add_argument("--out", default="output", help="پوشه خروجی")
    parser.add_argument("--cache", default=".cache_lar15", help="پوشه ذخیره صفحات خام")
    parser.add_argument("--max-pages", type=int, default=500, help="حداکثر تعداد صفحات فهرست")
    parser.add_argument("--start-page", type=int, default=1)
    parser.add_argument("--delay", type=float, default=1.0, help="فاصله بین درخواست‌ها (ثانیه)")
    parser.add_argument("--retries", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--rows-per-part", type=int, default=200)
    parser.add_argument("--limit", type=int, default=0, help="فقط N مصوبه اول (برای آزمایش)")
    parser.add_argument("--from-cache", action="store_true",
                        help="فقط از صفحات ذخیره‌شده استفاده کن (بدون شبکه)")
    parser.add_argument("--self-test", action="store_true", help="اجرای آزمون آفلاین")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()

    fetcher = Fetcher(args.cache, delay=args.delay, retries=args.retries,
                      timeout=args.timeout, offline=args.from_cache)

    print("۱) پیمایش صفحات فهرست ...")
    items = crawl(fetcher, args.max_pages, args.start_page)
    if args.limit:
        items = items[:args.limit]
    print("   مجموع مصوبات یافت‌شده: %d" % len(items))
    if not items:
        print("هیچ مصوبه‌ای یافت نشد (دسترسی به سایت یا ساختار صفحه را بررسی کنید).")
        return 2

    print("۲) دریافت متن کامل هر مصوبه ...")
    records, failed = [], []
    for index, item in enumerate(items, start=1):
        html = fetcher.get(item["url"], "law_%s" % item["id"])
        if html is None:
            failed.append(item)
            continue
        record = parse_law_page(html, item["url"], item["id"], item["list_title"])
        if not record["title"]:
            record["title"] = item["list_title"]
        records.append(record)
        if index % 25 == 0 or index == len(items):
            print("   %d/%d" % (index, len(items)))

    if failed:
        path = os.path.join(args.out, "failed.txt")
        os.makedirs(args.out, exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            for item in failed:
                handle.write("%s\t%s\n" % (item["id"], item["url"]))
        print("   ! %d مصوبه دریافت نشد؛ فهرست در %s" % (len(failed), path))

    print("۳) نوشتن فایل‌های خروجی ...")
    written, report = write_outputs(records, args.out, args.rows_per_part)
    print("\n".join("   " + p for p in written[:6]))
    print()
    print(report)
    return 0


def self_test():
    """آزمون آفلاین با فایل‌های نمونه در tests/fixtures."""
    here = os.path.dirname(os.path.abspath(__file__))
    fixtures = os.path.join(os.path.dirname(here), "tests", "fixtures")
    search_html = open(os.path.join(fixtures, "search_page.html"), encoding="utf-8").read()
    law_html = open(os.path.join(fixtures, "law_page.html"), encoding="utf-8").read()

    items, _ = parse_search_page(search_html)
    assert len(items) == 3, items
    assert items[0]["id"] == "802645", items[0]

    record = parse_law_page(law_html, BASE + "/fa/law/show/802645", "802645")
    assert "طرح جامع" in record["title"], record["title"]
    assert record["approval_date_jalali"] == "1398/05/12", record["approval_date_jalali"]
    assert record["approval_date_gregorian"] == "2019-08-03", record
    assert record["city"] == "اردبیل", record["city"]
    assert record["province"] == "اردبیل", record["province"]
    assert record["subject_type"] == "طرح جامع", record["subject_type"]
    assert "ماده واحده" in record["full_text"], record["full_text"][:200]
    assert "منوی اصلی" not in record["full_text"], "منوی سایت حذف نشده است"
    assert record["text_length"] > 300, record["text_length"]

    rows = [record,
            dict(record, id="1", title="ب", approval_date_jalali="1400/01/01",
                 city="تهران", province="تهران"),
            dict(record, id="2", title="ج", approval_date_jalali="", city="", province="")]
    assert [r["id"] for r in sorted(rows, key=sort_key_date)] == ["802645", "1", "2"]
    assert sorted(rows, key=sort_key_city)[0]["province"] == "اردبیل"
    print("همه آزمون‌ها با موفقیت انجام شد ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())
