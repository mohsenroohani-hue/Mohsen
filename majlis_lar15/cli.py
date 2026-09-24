"""خط فرمان: استخراج مصوبات و ساخت فایل‌های اکسل.

نمونه‌ها:
    python -m majlis_lar15.cli all
    python -m majlis_lar15.cli scrape --max-pages 3
    python -m majlis_lar15.cli build --per-file 100
    python -m majlis_lar15.cli reparse --html-dir out/html
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from typing import List

from . import excel_builder, scraper
from .scraper import Record

DEFAULT_OUT = "out"
JSONL_NAME = "داده_خام.jsonl"


def _paths(out_dir: str):
    return (os.path.join(out_dir, JSONL_NAME),
            os.path.join(out_dir, "html"))


def cmd_scrape(args) -> int:
    os.makedirs(args.out, exist_ok=True)
    jsonl_path, html_dir = _paths(args.out)
    html_dir = html_dir if args.save_html else None

    session = scraper.make_session(timeout=args.timeout)
    print("۱) پیمایش صفحات فهرست …")
    listing = scraper.collect_listing(
        session, reference=args.reference, start_page=args.start_page,
        max_pages=args.max_pages, delay=args.delay, html_dir=html_dir)
    print(f"   مجموع مصوبات یافت‌شده در فهرست: {len(listing)}")

    if not listing:
        print("   هیچ رکوردی یافت نشد. اگر ساختار سایت تغییر کرده، "
              "با --save-html صفحه را ذخیره و ساختار را بررسی کنید.")
        return 1

    index_path = os.path.join(args.out, "فهرست_شناسه‌ها.json")
    with open(index_path, "w", encoding="utf-8") as fh:
        json.dump(listing, fh, ensure_ascii=False, indent=2)

    done = set() if args.force else scraper.load_done_ids(jsonl_path)
    if done:
        print(f"   {len(done)} مصوبه پیش‌تر ذخیره شده؛ از آن‌ها عبور می‌شود.")

    todo = [r for r in listing if r["id"] not in done]
    print(f"۲) دریافت متن کامل {len(todo)} مصوبه …")

    failed: List[str] = []
    mode = "w" if (args.force and os.path.exists(jsonl_path)) else "a"
    with open(jsonl_path, mode, encoding="utf-8") as out_fh:
        for i, item in enumerate(todo, 1):
            law_id = item["id"]
            url = scraper.SHOW_URL.format(id=law_id)
            html = scraper.fetch(session, url, timeout=args.timeout)
            if html is None:
                failed.append(law_id)
                print(f"   [{i}/{len(todo)}] {law_id} — دریافت نشد")
                continue
            if html_dir:
                os.makedirs(html_dir, exist_ok=True)
                with open(os.path.join(html_dir, f"law_{law_id}.html"), "w",
                          encoding="utf-8") as fh:
                    fh.write(html)
            rec = scraper.parse_detail_page(html, law_id, item.get("title", ""),
                                            item.get("row_text", ""))
            out_fh.write(rec.to_json() + "\n")
            out_fh.flush()
            flag = " ⚠" if rec.parse_warnings else ""
            print(f"   [{i}/{len(todo)}] {law_id} | {rec.city or '—'} | "
                  f"{rec.date_jalali or '—'} | {rec.body_length} نویسه{flag}")
            time.sleep(args.delay + random.uniform(0, 0.4))

    if failed:
        with open(os.path.join(args.out, "ناموفق.txt"), "w", encoding="utf-8") as fh:
            fh.write("\n".join(failed))
        print(f"   {len(failed)} مصوبه دریافت نشد؛ فهرست در «ناموفق.txt». "
              "دستور را دوباره اجرا کنید تا فقط همان‌ها گرفته شوند.")
    print(f"   داده خام در: {jsonl_path}")
    return 0


def cmd_reparse(args) -> int:
    """تحلیل دوباره HTMLهای ذخیره‌شده بدون دریافت مجدد از سایت."""
    html_dir = args.html_dir or os.path.join(args.out, "html")
    if not os.path.isdir(html_dir):
        print(f"پوشه {html_dir} یافت نشد.")
        return 1
    jsonl_path, _ = _paths(args.out)
    files = sorted(f for f in os.listdir(html_dir) if f.startswith("law_"))
    print(f"تحلیل دوباره {len(files)} فایل …")
    with open(jsonl_path, "w", encoding="utf-8") as out_fh:
        for i, fname in enumerate(files, 1):
            law_id = fname[len("law_"):-len(".html")]
            with open(os.path.join(html_dir, fname), encoding="utf-8") as fh:
                html = fh.read()
            rec = scraper.parse_detail_page(html, law_id)
            out_fh.write(rec.to_json() + "\n")
            if i % 50 == 0:
                print(f"   {i}/{len(files)}")
    print(f"انجام شد: {jsonl_path}")
    return 0


def cmd_build(args) -> int:
    jsonl_path, _ = _paths(args.out)
    records = scraper.load_records(jsonl_path)
    if not records:
        print(f"داده‌ای در {jsonl_path} نیست. ابتدا دستور scrape را اجرا کنید.")
        return 1
    print(f"ساخت اکسل از {len(records)} مصوبه …")
    report = excel_builder.export_all(
        records, args.out, per_file=args.per_file, write_txt=not args.no_txt)
    print("\n— خروجی —")
    print(f"  فهرست     : {report['index_file']}")
    for name in report["text_files"]:
        print(f"  متن کامل  : {name}")
    if report["txt_dir"]:
        print(f"  متن خام   : {os.path.basename(report['txt_dir'])}/")
    print(f"  مصوبات    : {report['records']}   نویسه‌ها: {report['total_chars']:,}")
    return 0


def cmd_all(args) -> int:
    code = cmd_scrape(args)
    if code != 0:
        return code
    return cmd_build(args)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="majlis_lar15",
        description="استخراج مصوبات شورای عالی شهرسازی و معماری ایران و ساخت اکسل")
    p.add_argument("--out", default=DEFAULT_OUT, help="پوشه خروجی (پیش‌فرض: out)")
    sub = p.add_subparsers(dest="command", required=True)

    def add_scrape_args(sp):
        sp.add_argument("--reference", default=scraper.DEFAULT_REFERENCE,
                        help="کد مرجع تصویب (پیش‌فرض lar15)")
        sp.add_argument("--start-page", type=int, default=1)
        sp.add_argument("--max-pages", type=int, default=0,
                        help="۰ یعنی همه صفحات")
        sp.add_argument("--delay", type=float, default=1.2,
                        help="مکث میان درخواست‌ها به ثانیه")
        sp.add_argument("--timeout", type=int, default=45)
        sp.add_argument("--save-html", action="store_true",
                        help="ذخیره HTML خام برای تحلیل دوباره")
        sp.add_argument("--force", action="store_true",
                        help="نادیده گرفتن داده‌های پیشین و شروع از نو")

    def add_build_args(sp):
        sp.add_argument("--per-file", type=int, default=150,
                        help="تعداد مصوبه در هر فایل اکسلِ متن کامل")
        sp.add_argument("--no-txt", action="store_true",
                        help="ساخته‌نشدن فایل‌های متنی پشتیبان")

    sp = sub.add_parser("scrape", help="فقط دریافت داده")
    add_scrape_args(sp)
    sp.set_defaults(func=cmd_scrape)

    sp = sub.add_parser("build", help="فقط ساخت اکسل از داده موجود")
    add_build_args(sp)
    sp.set_defaults(func=cmd_build)

    sp = sub.add_parser("all", help="دریافت داده و ساخت اکسل")
    add_scrape_args(sp)
    add_build_args(sp)
    sp.set_defaults(func=cmd_all)

    sp = sub.add_parser("reparse", help="تحلیل دوباره HTMLهای ذخیره‌شده")
    sp.add_argument("--html-dir", default="")
    add_build_args(sp)
    sp.set_defaults(func=cmd_reparse)

    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\nمتوقف شد. داده‌های ذخیره‌شده باقی می‌مانند؛ "
              "اجرای دوباره از همان‌جا ادامه می‌دهد.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
