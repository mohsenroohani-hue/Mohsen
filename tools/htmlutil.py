# -*- coding: utf-8 -*-
"""ابزارهای سبک برای تحلیل HTML فقط با کتابخانه استاندارد پایتون.

A tiny dependency-free DOM + main-content extractor (no bs4/lxml needed).
"""

import re
from html.parser import HTMLParser

VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
    "param", "source", "track", "wbr",
}
SKIP_TAGS = {"script", "style", "noscript", "svg", "head", "iframe", "template"}
BLOCK_TAGS = {
    "p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "section",
    "article", "ul", "ol", "table", "blockquote", "header", "footer", "nav", "hr",
    "td", "th", "form", "main", "aside", "figure", "figcaption", "dd", "dt",
}
CANDIDATE_TAGS = {"div", "article", "section", "main", "td", "body", "span"}


class Node:
    __slots__ = ("tag", "attrs", "children", "parent")

    def __init__(self, tag, attrs=None, parent=None):
        self.tag = tag
        self.attrs = attrs or {}
        self.children = []
        self.parent = parent

    def __repr__(self):  # pragma: no cover - debugging helper
        return "<Node %s %s>" % (self.tag, self.attrs.get("class", ""))


class _DomBuilder(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self, convert_charrefs=True)
        self.root = Node("#document")
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        node = Node(tag, dict(attrs), self.cur)
        self.cur.children.append(node)
        if tag not in VOID_TAGS:
            self.cur = node

    def handle_startendtag(self, tag, attrs):
        self.cur.children.append(Node(tag, dict(attrs), self.cur))

    def handle_endtag(self, tag):
        node = self.cur
        while node is not None and node.tag != tag:
            node = node.parent
        if node is None or node.parent is None:
            return  # stray close tag: ignore
        self.cur = node.parent

    def handle_data(self, data):
        if data.strip():
            self.cur.children.append(data)


def parse_html(markup):
    clear_cache()  # ids are only unique per live document
    builder = _DomBuilder()
    try:
        builder.feed(markup)
        builder.close()
    except Exception:
        pass
    return builder.root


def iter_nodes(node):
    stack = [node]
    while stack:
        cur = stack.pop()
        if isinstance(cur, str):
            continue
        yield cur
        stack.extend(reversed(cur.children))


_TEXT_CACHE = {}


def node_text(node):
    """متن قابل‌مشاهده یک گره (به همراه شکست خط برای تگ‌های بلوکی)."""
    if isinstance(node, str):
        return node
    key = id(node)
    cached = _TEXT_CACHE.get(key)
    if cached is not None:
        return cached
    if node.tag in SKIP_TAGS:
        _TEXT_CACHE[key] = ""
        return ""
    parts = [node_text(child) for child in node.children]
    text = "".join(parts)
    if node.tag in BLOCK_TAGS:
        text = "\n" + text + "\n"
    _TEXT_CACHE[key] = text
    return text


def link_text_len(node):
    total = 0
    for sub in iter_nodes(node):
        if sub is not node and sub.tag == "a":
            total += len(collapse_ws(node_text(sub)))
    return total


def clear_cache():
    _TEXT_CACHE.clear()


def collapse_ws(text):
    text = text.replace("‌", "‌")
    text = re.sub(r"[ \t\r\f\v ]+", " ", text)
    text = re.sub(r"\n[ \t]*", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def get_attr(node, name):
    return (node.attrs.get(name) or "") if not isinstance(node, str) else ""


def find_first(root, tags):
    for node in iter_nodes(root):
        if node.tag in tags:
            return node
    return None


def page_title(root):
    for tag in ("h1", "h2"):
        node = find_first(root, {tag})
        if node is not None:
            text = collapse_ws(node_text(node))
            if len(text) > 3:
                return text
    node = find_first(root, {"title"})
    if node is not None:
        return collapse_ws(node_text(node))
    return ""


def meta_content(root, name):
    name = name.lower()
    for node in iter_nodes(root):
        if node.tag != "meta":
            continue
        key = (node.attrs.get("name") or node.attrs.get("property") or "").lower()
        if key == name:
            return (node.attrs.get("content") or "").strip()
    return ""


def links(root):
    """همه پیوندهای صفحه به صورت (href, text)."""
    out = []
    for node in iter_nodes(root):
        if node.tag == "a" and node.attrs.get("href"):
            out.append((node.attrs["href"].strip(), collapse_ws(node_text(node))))
    return out


def extract_main_text(root, min_len=150):
    """متن اصلی صفحه: گره‌ای با بیشترین متن و کمترین چگالی پیوند.

    Readability-lite: score = text length - 2.5 * link text length, then dive
    into the deepest child that keeps ~90% of the winning score so that page
    chrome (menus, footers) is dropped but the body stays intact.
    """
    best, best_score = None, 0.0
    for node in iter_nodes(root):
        if node.tag not in CANDIDATE_TAGS:
            continue
        text = collapse_ws(node_text(node))
        if len(text) < min_len:
            continue
        score = len(text) - 2.5 * link_text_len(node)
        if score > best_score:
            best, best_score = node, score
    if best is None:
        return collapse_ws(node_text(root))
    # go deeper while a single child keeps nearly all of the content
    changed = True
    while changed:
        changed = False
        for child in best.children:
            if isinstance(child, str) or child.tag not in CANDIDATE_TAGS:
                continue
            text = collapse_ws(node_text(child))
            if len(text) < min_len:
                continue
            score = len(text) - 2.5 * link_text_len(child)
            if score >= 0.9 * best_score:
                best, best_score, changed = child, score, True
                break
    return collapse_ws(node_text(best))
