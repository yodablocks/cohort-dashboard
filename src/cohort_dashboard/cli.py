"""cli.py -- entry point.

Usage:
    cohort-dashboard --tier giga-rekt
    cohort-dashboard --tier giga-rekt --json
    cohort-dashboard --tier giga-rekt --concurrency 8
    cohort-dashboard --tier giga-rekt --top 100
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

import httpx

from cohort_dashboard.tier_view import get_tier_positions, _canonical_tier_name, valid_tier_slugs
from cohort_dashboard.summary import compute_tier_summary
from cohort_dashboard.asset_breakdown import top_open_perps, liquidation_risk_by_asset
from cohort_dashboard.output import (
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
    args = ap.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
