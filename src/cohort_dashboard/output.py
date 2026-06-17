"""output.py -- terminal (rich) and JSON output. Matches cohort-pnl style."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from cohort_pnl.fetchers.positions import PositionRecord
from cohort_dashboard.summary import TierSummary
from cohort_dashboard.asset_breakdown import OpenPerpEntry, LiqRiskEntry
from cohort_dashboard.exposure import compute_exposure

console = Console()

_LIQ_DIST_MAX_DISPLAY = 500.0


def _fmt_value(v: float) -> str:
    if v >= 1_000_000:
        return f"${v/1_000_000:.1f}M"
    if v >= 1_000:
        return f"${v/1_000:.0f}K"
    return f"${v:.0f}"


def _fmt_liq(dist: float | None) -> str:
    if dist is None or dist > _LIQ_DIST_MAX_DISPLAY:
        return "N/A"
    return f"{dist:.1f}%"


def _liq_distance_pct(position: PositionRecord) -> float | None:
    if position.liq_px is None or position.mark_px <= 0:
        return None
    return abs(position.mark_px - position.liq_px) / position.mark_px * 100.0


def _pnl_pct(position: PositionRecord) -> float | None:
    if position.margin_used <= 0:
        return None
    return (position.unrealized_pnl / position.margin_used) * 100.0


def print_summary_card(tier_name: str, summary: TierSummary) -> None:
    total_val = summary.open_value_long_usd + summary.open_value_short_usd
    lines = [
        f"Tier: [bold]{tier_name}[/bold]",
        f"Wallets: [bold]{summary.wallet_count}[/bold]",
        f"Open Value: [green]{_fmt_value(summary.open_value_long_usd)} Long[/green]"
        f"  [red]{_fmt_value(summary.open_value_short_usd)} Short[/red]"
        f"  ({_fmt_value(total_val)} total)",
        f"In Profit: [green]{summary.traders_in_profit}[/green] "
        f"({summary.pct_in_profit:.0f}%)  "
        f"Underwater: [red]{summary.traders_underwater}[/red] "
        f"({summary.pct_underwater:.0f}%)",
    ]
    console.print(Panel("\n".join(lines), title="Summary", expand=False))


def print_wallet_table(
    positions: list[PositionRecord],
    *,
    max_rows: int = 50,
) -> None:
    """One row per wallet, aggregated. Closest liq = min liq_distance_pct."""
    from collections import defaultdict

    # Aggregate per wallet: sum notional, sum margin, sum upnl, track closest liq.
    wallet_notional: dict[str, float] = defaultdict(float)
    wallet_equity: dict[str, float] = defaultdict(float)
    wallet_upnl: dict[str, float] = defaultdict(float)
    wallet_closest_liq: dict[str, float | None] = {}

    for p in positions:
        notional = abs(p.size) * p.mark_px
        wallet_notional[p.wallet] += notional
        wallet_equity[p.wallet] += p.margin_used
        wallet_upnl[p.wallet] += p.unrealized_pnl

        dist = _liq_distance_pct(p)
        prev = wallet_closest_liq.get(p.wallet)
        if dist is not None:
            if prev is None or dist < prev:
                wallet_closest_liq[p.wallet] = dist
        elif p.wallet not in wallet_closest_liq:
            wallet_closest_liq[p.wallet] = None

    # Sort by open value descending.
    wallets = sorted(wallet_notional.keys(), key=lambda w: wallet_notional[w], reverse=True)
    wallets = wallets[:max_rows]

    table = Table(
        title=f"Wallets ({len(wallet_notional)} total, showing {len(wallets)})",
        box=box.SIMPLE_HEAD,
        show_lines=False,
        expand=False,
    )
    table.add_column("Wallet", style="dim", min_width=14)
    table.add_column("Open Value", justify="right", min_width=12)
    table.add_column("Equity", justify="right", min_width=10)
    table.add_column("Exposure", justify="right", min_width=10)
    table.add_column("Sum UPNL", justify="right", min_width=12)
    table.add_column("Closest Liq", justify="right", min_width=12)

    for w in wallets:
        notional = wallet_notional[w]
        equity = wallet_equity[w]
        upnl = wallet_upnl[w]
        exposure = (notional / equity) if equity > 0 else None
        closest = wallet_closest_liq.get(w)

        upnl_style = "green" if upnl > 0 else "red"
        exp_str = f"{exposure:.1f}x" if exposure is not None else "N/A"
        upnl_str = f"[{upnl_style}]{_fmt_value(abs(upnl))} {'gain' if upnl > 0 else 'loss'}[/{upnl_style}]"

        table.add_row(
            w[:8] + "..." + w[-4:],
            _fmt_value(notional),
            _fmt_value(equity),
            exp_str,
            upnl_str,
            _fmt_liq(closest),
        )

    console.print(table)


def print_top_open_perps(entries: list[OpenPerpEntry]) -> None:
    table = Table(
        title="Top Open Perps",
        box=box.SIMPLE_HEAD,
        show_lines=False,
        expand=False,
    )
    table.add_column("Asset", min_width=8)
    table.add_column("Total Value", justify="right", min_width=12)
    table.add_column("Long", justify="right", min_width=10)
    table.add_column("Short", justify="right", min_width=10)
    table.add_column("Bias", justify="center", min_width=14)

    for e in entries:
        bias_style = (
            "bold green" if "Very Bullish" in e.bias_label
            else "green" if "Bullish" in e.bias_label
            else "red" if "Very Bearish" in e.bias_label
            else "dark_orange" if "Bearish" in e.bias_label
            else "white"
        )
        table.add_row(
            e.coin,
            _fmt_value(e.total_value_usd),
            _fmt_value(e.long_value_usd),
            _fmt_value(e.short_value_usd),
            f"[{bias_style}]{e.bias_label}[/{bias_style}]",
        )

    console.print(table)


def print_liq_risk_table(entries: list[LiqRiskEntry]) -> None:
    table = Table(
        title="Liquidation Risk by Asset (within 25% of liq price)",
        box=box.SIMPLE_HEAD,
        show_lines=False,
        expand=False,
    )
    table.add_column("Asset", min_width=8)
    table.add_column("Total Value", justify="right", min_width=12)
    table.add_column("At Risk", justify="right", min_width=10)
    table.add_column("Risk %", justify="right", min_width=8)

    for e in entries:
        risk_style = (
            "bold red" if e.risk_pct >= 50
            else "red" if e.risk_pct >= 25
            else "dark_orange" if e.risk_pct >= 10
            else "white"
        )
        table.add_row(
            e.coin,
            _fmt_value(e.total_open_value_usd),
            _fmt_value(e.at_risk_value_usd),
            f"[{risk_style}]{e.risk_pct:.1f}%[/{risk_style}]",
        )

    console.print(table)


def _wallet_rows(positions: list[PositionRecord]) -> list[dict[str, Any]]:
    """Aggregate positions per wallet for JSON output, matching the terminal wallet table."""
    from collections import defaultdict

    wallet_notional: dict[str, float] = defaultdict(float)
    wallet_equity: dict[str, float] = defaultdict(float)
    wallet_upnl: dict[str, float] = defaultdict(float)
    wallet_closest_liq: dict[str, float | None] = {}

    for p in positions:
        notional = abs(p.size) * p.mark_px
        wallet_notional[p.wallet] += notional
        wallet_equity[p.wallet] += p.margin_used
        wallet_upnl[p.wallet] += p.unrealized_pnl
        dist = _liq_distance_pct(p)
        prev = wallet_closest_liq.get(p.wallet)
        if dist is not None:
            if prev is None or dist < prev:
                wallet_closest_liq[p.wallet] = dist
        elif p.wallet not in wallet_closest_liq:
            wallet_closest_liq[p.wallet] = None

    rows = []
    for w in sorted(wallet_notional, key=lambda x: wallet_notional[x], reverse=True):
        notional = wallet_notional[w]
        equity = wallet_equity[w]
        exposure = (notional / equity) if equity > 0 else None
        rows.append({
            "wallet": w,
            "open_value_usd": notional,
            "equity_usd": equity,
            "exposure": exposure,
            "sum_upnl_usd": wallet_upnl[w],
            "closest_liq_pct": wallet_closest_liq.get(w),
        })
    return rows


def to_json(
    tier_name: str,
    summary: TierSummary,
    positions: list[PositionRecord],
    top_perps: list[OpenPerpEntry],
    liq_risk: list[LiqRiskEntry],
) -> str:
    out: dict[str, Any] = {
        "tier": tier_name,
        "summary": {
            "wallet_count": summary.wallet_count,
            "open_value_long_usd": summary.open_value_long_usd,
            "open_value_short_usd": summary.open_value_short_usd,
            "traders_in_profit": summary.traders_in_profit,
            "traders_underwater": summary.traders_underwater,
            "pct_in_profit": summary.pct_in_profit,
            "pct_underwater": summary.pct_underwater,
        },
        "wallets": _wallet_rows(positions),
        "top_open_perps": [
            {
                "coin": e.coin,
                "total_value_usd": e.total_value_usd,
                "long_value_usd": e.long_value_usd,
                "short_value_usd": e.short_value_usd,
                "bias_label": e.bias_label,
            }
            for e in top_perps
        ],
        "liquidation_risk_by_asset": [
            {
                "coin": e.coin,
                "total_open_value_usd": e.total_open_value_usd,
                "at_risk_value_usd": e.at_risk_value_usd,
                "risk_pct": e.risk_pct,
            }
            for e in liq_risk
        ],
    }
    return json.dumps(out, indent=2)
