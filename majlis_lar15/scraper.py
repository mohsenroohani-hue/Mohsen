"""استخراج مصوبات شورای عالی شهرسازی و معماری ایران از پایگاه rc.majlis.ir

نشانی فهرست: https://rc.majlis.ir/fa/law/search?lu_approve_reference=lar15&page=N
نشانی متن  : https://rc.majlis.ir/fa/law/show/<id>
"""

from __future__ import annotations

import json
import os
import random
import re
import time
from dataclasses import dataclass, asdict, field
from typing import Dict, Iterable, List, Optional, Set
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from . import cities as cities_mod
from . import jalali

BASE = "https://rc.majlis.ir"
SEARCH_URL = BASE + "/fa/law/search"
SHOW_URL = BASE + "/fa/law/show/{id}"
DEFAULT_REFERENCE = "lar15"

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fa-IR,fa;q=0.9,en;q=0.8",
}

_ID_RE = re.compile(r"/(?:fa|en)/law/show/(\d+)")
_PAGE_RE = re.compile(r"[?&]page=(\d+)")

# برچسب‌هایی که کنارشان تاریخ تصویب می‌آید
_DATE_LABELS = ["تاریخ تصویب", "تاريخ تصويب", "مصوب", "تاریخ ابلاغ", "مورخ", "تاریخ"]

_NOISE_TAGS = ["script", "style", "noscript", "nav", "header", "footer",
               "form", "aside", "iframe", "svg", "button"]

_CONTENT_HINTS = ["content", "matn", "متن", "law-text", "lawtext", "text",
                  "article", "body", "detail", "main", "post", "entry"]


# ----------------------------------------------------------------- داده‌ها
@dataclass
class Record:
    id: str = ""
    title: str = ""
    url: str = ""
    date_jalali: str = ""
    date_gregorian: str = ""
    year_jalali: str = ""
    month_jalali: str = ""
    city: str = ""
    city_source: str = ""
    province: str = ""
    approve_reference: str = ""
    document_number: str = ""
    body: str = ""
    body_length: int = 0
    fetched_at: str = ""
    parse_warnings: List[str] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


# ----------------------------------------------------------------- کمکی‌ها
def clean_text(text: str) -> str:
    """فاصله‌های اضافی را جمع می‌کند ولی پاراگراف‌ها را نگه می‌دارد."""
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t ]+", " ", text)
    text = re.sub(r"\n[ \t]*\n[ \t]*(\n[ \t]*)+", "\n\n", text)
    lines = [ln.strip() for ln in text.split("\n")]
    return "\n".join(lines).strip()


def make_session(timeout: int = 45, proxy: Optional[str] = None) -> requests.Session:
    s = requests.Session()
    s.headers.update(HEADERS)
    if proxy:
        s.proxies.update({"http": proxy, "https": proxy})
    s.request_timeout = timeout  # type: ignore[attr-defined]
    return s


def fetch(session: requests.Session, url: str, params: Optional[dict] = None,
          retries: int = 4, backoff: float = 2.0, timeout: int = 45,
          verbose: bool = True) -> Optional[str]:
    """دریافت صفحه با تلاش مجدد و تأخیر نمایی."""
    for attempt in range(1, retries + 1):
        try:
            resp = session.get(url, params=params, timeout=timeout)
            if resp.status_code == 200:
                resp.encoding = resp.encoding or "utf-8"
                if not resp.encoding or resp.encoding.lower() == "iso-8859-1":
                    resp.encoding = "utf-8"
                return resp.text
            if resp.status_code == 404:
                if verbose:
                    print(f"    [404] {url}")
                return None
            if verbose:
                print(f"    [{resp.status_code}] تلاش {attempt}/{retries} برای {url}")
        except requests.RequestException as exc:
            if verbose:
                print(f"    [خطای شبکه] تلاش {attempt}/{retries}: {exc}")
        if attempt < retries:
            time.sleep(backoff * (2 ** (attempt - 1)) + random.uniform(0, 0.8))
    return None


# ----------------------------------------------------------------- تحلیل HTML
def parse_search_page(html: str) -> List[Dict[str, str]]:
    """شناسه، عنوان و تاریخ احتمالی هر ردیف فهرست را بیرون می‌کشد."""
    soup = BeautifulSoup(html, "lxml")
    results: List[Dict[str, str]] = []
    seen: Set[str] = set()

    for a in soup.find_all("a", href=True):
        m = _ID_RE.search(a["href"])
        if not m:
            continue
        law_id = m.group(1)
        if law_id in seen:
            continue
        title = clean_text(a.get_text(" ", strip=True))
        if not title or len(title) < 4:
            title = clean_text(a.get("title", ""))
        # تاریخ را از نزدیک‌ترین بلوک دربرگیرنده می‌گیریم
        date_text = ""
        node = a
        for _ in range(4):
            node = node.parent
            if node is None:
                break
            chunk = clean_text(node.get_text(" ", strip=True))
            if jalali.parse_jalali_date(chunk):
                date_text = chunk
                break
        seen.add(law_id)
        results.append({"id": law_id, "title": title,
                        "url": urljoin(BASE, a["href"]), "row_text": date_text})
    return results


def max_page_number(html: str) -> int:
    """بیشترین شماره صفحه موجود در نوار صفحه‌بندی."""
    pages = [int(m.group(1)) for m in _PAGE_RE.finditer(html)]
    return max(pages) if pages else 1


def _score_node(node) -> int:
    """امتیاز یک گره بر پایه حجم متن فارسی درون آن."""
    text = node.get_text(" ", strip=True)
    if not text:
        return 0
    persian = len(re.findall(r"[؀-ۿ]", text))
    links = sum(len(a.get_text(strip=True)) for a in node.find_all("a"))
    return persian - links  # بلوک‌های پر از لینک (منو) جریمه می‌شوند


def extract_body(soup: BeautifulSoup) -> str:
    """متن اصلی مصوبه را پیدا می‌کند."""
    for tag in soup.find_all(_NOISE_TAGS):
        tag.decompose()

    candidates = []
    for node in soup.find_all(["div", "section", "article", "td", "main"]):
        ident = " ".join(filter(None, [
            node.get("id", ""), " ".join(node.get("class", []) or [])
        ])).lower()
        bonus = 400 if any(h in ident for h in _CONTENT_HINTS) else 0
        score = _score_node(node)
        if score > 150:
            candidates.append((score + bonus, node))

    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        best = candidates[0][1]
        # اگر فرزندی تقریباً همان متن را دارد، فرزند دقیق‌تر را برمی‌داریم
        for child in best.find_all(["div", "section", "article"], recursive=False):
            if _score_node(child) >= _score_node(best) * 0.92:
                best = child
                break
        return clean_text(best.get_text("\n", strip=True))

    body = soup.body or soup
    return clean_text(body.get_text("\n", strip=True))


def _find_labelled_value(soup: BeautifulSoup, labels: Iterable[str],
                         window: int = 120) -> str:
    """مقدار کنار یک برچسب مانند «تاریخ تصویب» را برمی‌گرداند."""
    text = soup.get_text(" ", strip=True)
    for label in labels:
        idx = text.find(label)
        while idx != -1:
            snippet = text[idx: idx + window]
            if jalali.parse_jalali_date(snippet[len(label):]):
                return snippet
            idx = text.find(label, idx + 1)
    return ""


def parse_detail_page(html: str, law_id: str, fallback_title: str = "",
                      fallback_row_text: str = "") -> Record:
    """صفحه مصوبه را به یک رکورد کامل تبدیل می‌کند."""
    rec = Record(id=law_id, url=SHOW_URL.format(id=law_id))
    warnings: List[str] = []
    soup = BeautifulSoup(html, "lxml")

    # ---- عنوان
    title = ""
    h1 = soup.find(["h1", "h2"])
    if h1:
        title = clean_text(h1.get_text(" ", strip=True))
    if not title:
        og = soup.find("meta", attrs={"property": "og:title"})
        if og and og.get("content"):
            title = clean_text(og["content"])
    if not title and soup.title:
        title = clean_text(soup.title.get_text(" ", strip=True))
    if not title:
        title = fallback_title
        warnings.append("عنوان از صفحه فهرست گرفته شد")
    rec.title = re.sub(r"\s*[|\-–]\s*مرکز پژوهش.*$", "", title).strip()

    # ---- تاریخ
    labelled = _find_labelled_value(soup, _DATE_LABELS)
    parts = jalali.parse_jalali_date(labelled)
    if not parts:
        parts = jalali.parse_jalali_date(fallback_row_text)
    if not parts:
        parts = jalali.parse_jalali_date(rec.title)
    if not parts:
        head = clean_text(soup.get_text(" ", strip=True))[:2500]
        parts = jalali.parse_jalali_date(head)
    if parts:
        rec.date_jalali = jalali.format_jalali(parts)
        rec.date_gregorian = jalali.format_gregorian(parts)
        rec.year_jalali = str(parts[0])
        rec.month_jalali = jalali.MONTH_NAMES[parts[1]]
    else:
        warnings.append("تاریخ یافت نشد")

    # ---- شماره نامه/مصوبه
    num = re.search(r"شماره\s*[:：]?\s*([\d۰-۹/\-]{3,25})",
                    soup.get_text(" ", strip=True))
    if num:
        rec.document_number = jalali.to_english_digits(num.group(1)).strip()

    # ---- متن
    rec.body = extract_body(soup)
    rec.body_length = len(rec.body)
    if rec.body_length < 60:
        warnings.append("متن بسیار کوتاه است؛ نیاز به بررسی دستی")

    # ---- شهر و استان
    rec.city, rec.city_source = cities_mod.extract_city(rec.title, rec.body)
    rec.province = cities_mod.extract_province(rec.title, rec.body, rec.city)

    rec.approve_reference = "شورای عالی شهرسازی و معماری ایران"
    rec.fetched_at = time.strftime("%Y-%m-%d %H:%M:%S")
    rec.parse_warnings = warnings
    return rec


# ----------------------------------------------------------------- خزنده
def collect_listing(session: requests.Session, reference: str = DEFAULT_REFERENCE,
                    start_page: int = 1, max_pages: int = 0, delay: float = 1.0,
                    html_dir: Optional[str] = None,
                    verbose: bool = True) -> List[Dict[str, str]]:
    """همه صفحات فهرست را پیمایش و ردیف‌ها را جمع می‌کند."""
    items: Dict[str, Dict[str, str]] = {}
    page = start_page
    empty_streak = 0
    total_pages_hint = None

    while True:
        if max_pages and page - start_page + 1 > max_pages:
            break
        html = fetch(session, SEARCH_URL,
                     params={"lu_approve_reference": reference, "page": page},
                     verbose=verbose)
        if html is None:
            if verbose:
                print(f"  صفحه {page}: دریافت نشد؛ توقف.")
            break

        if html_dir:
            os.makedirs(html_dir, exist_ok=True)
            with open(os.path.join(html_dir, f"search_{page:04d}.html"), "w",
                      encoding="utf-8") as fh:
                fh.write(html)

        if total_pages_hint is None:
            total_pages_hint = max_page_number(html)
            if verbose:
                print(f"  تعداد صفحات اعلام‌شده در صفحه‌بندی: {total_pages_hint}")

        rows = parse_search_page(html)
        new = [r for r in rows if r["id"] not in items]
        for r in new:
            items[r["id"]] = r
        if verbose:
            print(f"  صفحه {page}: {len(rows)} ردیف ({len(new)} تازه) — مجموع {len(items)}")

        if not new:
            empty_streak += 1
            if empty_streak >= 2:
                if verbose:
                    print("  دو صفحه پیاپی بدون رکورد تازه؛ پایان فهرست.")
                break
        else:
            empty_streak = 0

        page += 1
        if total_pages_hint and page > total_pages_hint and empty_streak >= 1:
            break
        time.sleep(delay + random.uniform(0, 0.4))

    return list(items.values())


def load_done_ids(path: str) -> Set[str]:
    """شناسه‌های پیش‌تر ذخیره‌شده را برای ادامه کار می‌خواند."""
    done: Set[str] = set()
    if not os.path.exists(path):
        return done
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                done.add(str(json.loads(line).get("id", "")))
            except json.JSONDecodeError:
                continue
    done.discard("")
    return done


def load_records(path: str) -> List[Record]:
    """رکوردها را از فایل JSONL می‌خواند (آخرین نسخه هر شناسه)."""
    by_id: Dict[str, Record] = {}
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            known = {f for f in Record.__dataclass_fields__}
            by_id[str(data.get("id", ""))] = Record(
                **{k: v for k, v in data.items() if k in known})
    by_id.pop("", None)
    return list(by_id.values())
