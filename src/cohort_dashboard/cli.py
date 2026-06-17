"""cli.py -- entry point.

Usage:
    cohort-dashboard --tier giga-rekt
    cohort-dashboard --tier giga-rekt --json
    cohort-dashboard --tier giga-rekt --concurrency 8
    cohort-dashboard --tier giga-rekt --top 100
    cohort-dashboard --tier giga-rekt --save
    cohort-dashboard --tier giga-rekt --save --db /path/to/snapshots.db
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from datetime import date
from pathlib import Path

import httpx

from cohort_dashboard.tier_view import get_tier_positions, _canonical_tier_name, valid_tier_slugs
from cohort_dashboard.summary import compute_tier_summary, compute_long_bias_pct, compute_avg_exposure
from cohort_dashboard.asset_breakdown import top_open_perps, liquidation_risk_by_asset
from cohort_dashboard.output import (
    console,
    print_summary_card,
    print_wallet_table,
    print_top_open_perps,
    print_liq_risk_table,
    to_json,
)

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


async def run(args: argparse.Namespace) -> None:
    canonical = _canonical_tier_name(args.tier)
    if canonical is None:
        slugs = ", ".join(valid_tier_slugs())
        print(f"Error: unknown tier '{args.tier}'.\nValid tiers: {slugs}", file=sys.stderr)
        sys.exit(1)

    async with httpx.AsyncClient() as client:
        positions = await get_tier_positions(
            client,
            canonical,
            concurrency=args.concurrency,
            top=args.top,
        )

    summary = compute_tier_summary(positions)
    top_perps = top_open_perps(positions, n=10)
    liq_risk = liquidation_risk_by_asset(positions, proximity_pct=25.0)

    if args.json:
        print(to_json(canonical, summary, positions, top_perps, liq_risk))
    else:
        print_summary_card(canonical, summary)
        print_wallet_table(positions)
        print_top_open_perps(top_perps)
        print_liq_risk_table(liq_risk)

    if args.save:
        from cohort_dashboard.snapshot import init_db, write_snapshot, DEFAULT_DB
        db_path = Path(args.db) if args.db else DEFAULT_DB
        conn = init_db(db_path)
        write_snapshot(
            conn,
            snapshot_date=date.today(),
            tier=canonical,
            wallet_count=summary.wallet_count,
            open_value_long_usd=summary.open_value_long_usd,
            open_value_short_usd=summary.open_value_short_usd,
            long_bias_pct=compute_long_bias_pct(positions),
            avg_exposure=compute_avg_exposure(positions),
            pct_in_profit=summary.pct_in_profit,
        )
        conn.close()
        if not args.json:
            console.print(f"[dim]Snapshot saved to {db_path}[/dim]")


def main() -> None:
    ap = argparse.ArgumentParser(description="HyperTracker Cohort Intelligence -- single-tier drill view")
    ap.add_argument(
        "--tier",
        required=True,
        metavar="TIER",
        help="tier to analyze (e.g. giga-rekt, full-rekt, money-print)",
    )
    ap.add_argument(
        "--json",
        action="store_true",
        help="output JSON instead of rich tables",
    )
    ap.add_argument(
        "--concurrency",
        type=int,
        default=8,
        help="max concurrent clearinghouseState calls (default 8)",
    )
    ap.add_argument(
        "--top",
        type=int,
        default=1000,
        help="cap wallet universe to first N leaderboard wallets (default 1000, 0 = all)",
    )
    ap.add_argument(
        "--save",
        action="store_true",
        help="write a daily snapshot to SQLite (starts accumulating data for v2 sparklines)",
    )
    ap.add_argument(
        "--db",
        default=None,
        metavar="PATH",
        help="path to snapshot database (default: data/cohort_dashboard_snapshots.db in repo root)",
    )
    args = ap.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
