"""asset_breakdown.py -- per-asset analytics across one tier. Pure, no I/O.

Bias labels: based on the long-value fraction of total notional for that asset.
Thresholds (inclusive lower bound):
  >= 70% long  -> "Very Bullish"
  >= 55% long  -> "Bullish"
  >= 45% long  -> "Neutral"
  >= 30% long  -> "Bearish"
  <  30% long  -> "Very Bearish"
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from cohort_pnl.fetchers.positions import PositionRecord

# -- bias label thresholds (long_pct >= threshold -> label) ----
_BIAS_THRESHOLDS: list[tuple[float, str]] = [
    (70.0, "Very Bullish"),
    (55.0, "Bullish"),
    (45.0, "Neutral"),
    (30.0, "Bearish"),
]
_BIAS_FALLBACK = "Very Bearish"


def _bias_label(long_val: float, short_val: float) -> str:
    total = long_val + short_val
    if total <= 0:
        return "Neutral"
    long_pct = (long_val / total) * 100.0
    for threshold, label in _BIAS_THRESHOLDS:
        if long_pct >= threshold:
            return label
    return _BIAS_FALLBACK


@dataclass
class OpenPerpEntry:
    coin: str
    total_value_usd: float   # sum of notional across all positions for this coin
    long_value_usd: float
    short_value_usd: float
    bias_label: str


def top_open_perps(
    positions: list[PositionRecord],
    n: int = 10,
) -> list[OpenPerpEntry]:
    """Group by coin, sum notional, sort descending, return top N.

    notional = abs(size) * mark_px per position.
    """
    long_val: dict[str, float] = defaultdict(float)
    short_val: dict[str, float] = defaultdict(float)

    for p in positions:
        notional = abs(p.size) * p.mark_px
        if p.side == "long":
            long_val[p.coin] += notional
        else:
            short_val[p.coin] += notional

    coins = set(long_val) | set(short_val)
    entries: list[OpenPerpEntry] = []
    for coin in coins:
        lv = long_val[coin]
        sv = short_val[coin]
        entries.append(
            OpenPerpEntry(
                coin=coin,
                total_value_usd=lv + sv,
                long_value_usd=lv,
                short_value_usd=sv,
                bias_label=_bias_label(lv, sv),
            )
        )

    entries.sort(key=lambda e: e.total_value_usd, reverse=True)
    return entries[:n]


@dataclass
class LiqRiskEntry:
    coin: str
    total_open_value_usd: float
    at_risk_value_usd: float    # value within proximity_pct of liquidation
    risk_pct: float             # at_risk_value_usd / total_open_value_usd * 100


def _liq_distance_pct(position: PositionRecord) -> float | None:
    if position.liq_px is None or position.mark_px <= 0:
        return None
    return abs(position.mark_px - position.liq_px) / position.mark_px * 100.0


def liquidation_risk_by_asset(
    positions: list[PositionRecord],
    proximity_pct: float = 25.0,
) -> list[LiqRiskEntry]:
    """Per asset: fraction of open value where liq distance <= proximity_pct.

    Positions with no liq_px (cross-margin, no liquidation price returned) are
    counted in total_open_value but not in at_risk_value -- they have unknown
    proximity, so we err on the side of not overstating risk.

    Sorted descending by risk_pct.
    """
    total_val: dict[str, float] = defaultdict(float)
    risk_val: dict[str, float] = defaultdict(float)

    for p in positions:
        notional = abs(p.size) * p.mark_px
        total_val[p.coin] += notional
        dist = _liq_distance_pct(p)
        if dist is not None and dist <= proximity_pct:
            risk_val[p.coin] += notional

    entries: list[LiqRiskEntry] = []
    for coin, total in total_val.items():
        risk = risk_val[coin]
        entries.append(
            LiqRiskEntry(
                coin=coin,
                total_open_value_usd=total,
                at_risk_value_usd=risk,
                risk_pct=(risk / total) * 100.0 if total > 0 else 0.0,
            )
        )

    entries.sort(key=lambda e: e.risk_pct, reverse=True)
    return entries
