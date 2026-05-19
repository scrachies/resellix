"""Trend scanner — ranks Vinted niches with the most underpriced listings right now."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, Optional

from config import TRENDS_OUTPUT_PATH, AppConfig
from listing_utils import (
    TREND_VINTED_QUERIES,
    filter_relevant_listings,
    median_listing_price,
)

log = logging.getLogger("trends")


@dataclass
class TrendResult:
    name: str
    score: int
    sample_snippet: str = ""
    median_eur: float = 0.0


def scan_trends(
    cfg: AppConfig,
    queries: Optional[list[str]] = None,
    top_n: int = 20,
    progress_cb: Optional[Callable[[str], None]] = None,
) -> list[TrendResult]:
    """Find product niches on Vinted with the most listings priced well below median."""
    from vinted import VintedClient, estimate_resale_eur, VintedAuthError, VintedError

    queries = queries or TREND_VINTED_QUERIES
    client = VintedClient(cfg)
    results: list[TrendResult] = []

    for i, q in enumerate(queries, 1):
        if progress_cb:
            try:
                progress_cb(f"({i}/{len(queries)}) Vinted: {q}")
            except Exception:
                pass
        try:
            listings = client.search(keyword=q, per_page=36)
        except VintedAuthError:
            raise
        except VintedError as exc:
            log.warning("trend skip %r: %s", q, exc)
            continue

        relevant = filter_relevant_listings(listings, q)
        if len(relevant) < 4:
            continue

        med = median_listing_price(relevant)
        if med <= 0:
            continue

        steals: list[tuple[float, object]] = []
        for item in relevant:
            price = float(getattr(item, "price", 0) or 0)
            if price <= 0:
                continue
            expected = estimate_resale_eur(item, keyword=q, market_median=med)
            ref = max(expected, med)
            ratio = (ref - price) / ref if ref > 0 else 0
            if ratio >= 0.35 and price < med * 0.72:
                steals.append((ratio, item))

        if not steals:
            continue

        steals.sort(key=lambda x: -x[0])
        best_ratio = steals[0][0]
        results.append(
            TrendResult(
                name=q,
                score=len(steals),
                median_eur=med,
                sample_snippet=(
                    f"Median on Vinted ~€{med:.0f} • {len(steals)} underpriced "
                    f"(best ~{int(best_ratio * 100)}% below value)"
                ),
            )
        )

    results.sort(key=lambda r: (-r.score, -r.median_eur))
    return results[:top_n]


def format_trends(results: list[TrendResult]) -> str:
    if not results:
        return "No underpriced niches found. Check Vinted auth and try again."
    lines = ["Vinted resell opportunities (underpriced vs median):", ""]
    for i, r in enumerate(results, 1):
        lines.append(f"{i:>2}. {r.name}  —  {r.score} steals  |  {r.sample_snippet}")
    return "\n".join(lines)


def save_trends(results: list[TrendResult]) -> str:
    text = format_trends(results)
    TRENDS_OUTPUT_PATH.write_text(text, encoding="utf-8")
    return str(TRENDS_OUTPUT_PATH)
