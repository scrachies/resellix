"""Parse natural-language ad-hoc search requests (Telegram /search or free text)."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

_EUR = r"(?:€|eur|euros?)?"
_NUM = r"(\d+(?:[.,]\d+)?)"

_SEARCH_PREFIXES = (
    r"^search\s+for\s+",
    r"^search\s+",
    r"^suche\s+nach\s+",
    r"^suche\s+",
    r"^find\s+",
    r"^finden\s+",
)

# (pattern, "minmax" | "min" | "max") — applied in order; matched spans removed from text
_PRICE_RULES: list[tuple[re.Pattern[str], str]] = []

def _rule(pat: str, kind: str) -> None:
    _PRICE_RULES.append((re.compile(pat, re.I), kind))


# Ranges first (single phrase)
_rule(rf"\bbetween\s+{_NUM}\s*(?:€|eur)?\s+and\s+{_NUM}\b", "minmax")
_rule(rf"\bzwischen\s+{_NUM}\s*(?:€|eur)?\s+und\s+{_NUM}\b", "minmax")
_rule(rf"\bfrom\s+{_NUM}\s*(?:€|eur)?\s+to\s+{_NUM}\b", "minmax")
_rule(rf"\bvon\s+{_NUM}\s*(?:€|eur)?\s+bis\s+{_NUM}\b", "minmax")
_rule(rf"\b{_NUM}\s*(?:€|eur)?\s+to\s+{_NUM}\b", "minmax")
_rule(rf"\b{_NUM}\s*(?:€|eur)?\s*[-–]\s*{_NUM}\s*(?:€|eur)?\b", "minmax")
_rule(rf"\bmin\s*[:=]?\s*{_NUM}\s+max\s*[:=]?\s*{_NUM}\b", "minmax")
_rule(rf"\bmax\s*[:=]?\s*{_NUM}\s+min\s*[:=]?\s*{_NUM}\b", "minmax_swap")
_rule(rf"\bprice\s+range\s+{_NUM}\s*[-–]\s*{_NUM}\b", "minmax")

# Min only
_rule(rf"\b(?:but\s+)?over\s+{_NUM}\s*{_EUR}\b", "min")
_rule(rf"\b(?:but\s+)?above\s+{_NUM}\s*{_EUR}\b", "min")
_rule(rf"\bmore\s+than\s+{_NUM}\s*{_EUR}\b", "min")
_rule(rf"\bat\s+least\s+{_NUM}\s*{_EUR}\b", "min")
_rule(rf"\bfrom\s+{_NUM}\s*{_EUR}\b", "min")
_rule(rf"\bmin(?:imum)?\s*[:=]?\s*{_NUM}\s*{_EUR}\b", "min")
_rule(rf"\bmindestens\s+{_NUM}\s*{_EUR}\b", "min")
_rule(rf"\bab\s+{_NUM}\s*{_EUR}\b", "min")
_rule(rf"\büber\s+{_NUM}\s*{_EUR}\b", "min")
_rule(rf"\bmehr\s+als\s+{_NUM}\s*{_EUR}\b", "min")
_rule(rf">\s*=\s*{_NUM}\s*{_EUR}\b", "min")
_rule(rf">\s*{_NUM}\s*{_EUR}\b", "min")

# Max only
_rule(rf"\bunder\s+{_NUM}\s*{_EUR}\b", "max")
_rule(rf"\bbelow\s+{_NUM}\s*{_EUR}\b", "max")
_rule(rf"\bless\s+than\s+{_NUM}\s*{_EUR}\b", "max")
_rule(rf"\bat\s+most\s+{_NUM}\s*{_EUR}\b", "max")
_rule(rf"\bup\s*to\s+{_NUM}\s*{_EUR}\b", "max")
_rule(rf"\bmax(?:imum)?\s*[:=]?\s*{_NUM}\s*{_EUR}\b", "max")
_rule(rf"\bmaximal\s+{_NUM}\s*{_EUR}\b", "max")
_rule(rf"\bunter\s+{_NUM}\s*{_EUR}\b", "max")
_rule(rf"\bbis\s+{_NUM}\s*{_EUR}\b", "max")
_rule(rf"\bweniger\s+als\s+{_NUM}\s*{_EUR}\b", "max")
_rule(rf"<\s*=\s*{_NUM}\s*{_EUR}\b", "max")
_rule(rf"<\s*{_NUM}\s*{_EUR}\b", "max")
_rule(rf"\bupto\s+{_NUM}\s*{_EUR}\b", "max")

# € before number: under €40, min €20
_rule(rf"\bunder\s*€\s*{_NUM}\b", "max")
_rule(rf"\bover\s*€\s*{_NUM}\b", "min")
_rule(rf"\bmin\s*€\s*{_NUM}\b", "min")
_rule(rf"\bmax\s*€\s*{_NUM}\b", "max")


@dataclass
class ParsedSearchQuery:
    keyword: str
    min_price: Optional[float] = None
    max_price: Optional[float] = None


def _num(raw: str) -> float:
    return float(raw.replace(",", "."))


def _strip_prices(text: str) -> tuple[str, Optional[float], Optional[float]]:
    min_p: Optional[float] = None
    max_p: Optional[float] = None
    work = f" {text.strip()} "

    for rx, kind in _PRICE_RULES:
        while True:
            m = rx.search(work)
            if not m:
                break
            g = m.groups()
            if kind == "minmax":
                a, b = _num(g[0]), _num(g[1])
                min_p, max_p = (a, b) if a <= b else (b, a)
            elif kind == "minmax_swap":
                a, b = _num(g[0]), _num(g[1])
                max_p, min_p = a, b
            elif kind == "min":
                min_p = _num(g[0])
            else:
                max_p = _num(g[0])
            work = work[: m.start()] + " " + work[m.end() :]

    work = re.sub(r"\bbut\b", " ", work, flags=re.I)
    work = re.sub(r"\s+", " ", work).strip(" ,.|")
    return work, min_p, max_p


def looks_like_search_request(text: str) -> bool:
    t = (text or "").strip().lower()
    if not t:
        return False
    if t.startswith("/search"):
        return True
    for p in _SEARCH_PREFIXES:
        if re.match(p, t, re.I):
            return True
    return False


def parse_search_text(text: str) -> Optional[ParsedSearchQuery]:
    raw = (text or "").strip()
    if not raw:
        return None
    if raw.lower().startswith("/search"):
        raw = raw[7:].strip()

    work = raw
    for p in _SEARCH_PREFIXES:
        work = re.sub(p, "", work, count=1, flags=re.I).strip()

    work, min_p, max_p = _strip_prices(work)
    keyword = re.sub(r"\s+", " ", work).strip()
    if not keyword:
        return None
    return ParsedSearchQuery(keyword=keyword, min_price=min_p, max_price=max_p)


def format_price_range(min_p: Optional[float], max_p: Optional[float]) -> str:
    if min_p is not None and max_p is not None:
        return f"{min_p:.0f}–{max_p:.0f}€"
    if max_p is not None:
        return f"≤{max_p:.0f}€"
    if min_p is not None:
        return f"≥{min_p:.0f}€"
    return "any price"
