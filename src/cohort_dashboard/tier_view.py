"""tier_view.py -- orchestrates: leaderboard -> filter to one tier's wallets
-> fetch open positions -> classify.

Wallet count semantics: wallet_count in the summary card means unique wallets
with at least one position classified into the target tier. The wallet table
shows one aggregated row per wallet (worst/closest liq position as the
"Closest Liq" value), matching the screenshot's layout.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import httpx

from cohort_pnl.fetchers.leaderboard import fetch_leaderboard
from cohort_pnl.tiers import TierRule, load_tier_rules, classify_tier, TIER_NAMES
from cohort_pnl.fetchers.positions import PositionRecord

from cohort_dashboard.fetchers.open_positions import fetch_open_positions

log = logging.getLogger(__name__)

# tiers.yaml lives in cohort-pnl's source tree. load_tier_rules() resolves its
# default path relative to the installed package location, which breaks when
# cohort-pnl is installed into a non-editable site-packages. Pass the absolute
# path explicitly so it always resolves correctly regardless of install mode.
_TIERS_YAML = Path(__file__).parent.parent.parent.parent / "cohort-pnl" / "config" / "tiers.yaml"


def _canonical_tier_name(tier_slug: str) -> str | None:
    """Map a CLI --tier slug back to the canonical tier name, or return None.

    Accepts both the canonical form ("Giga-Rekt") and the lowercased-hyphenated
    form ("giga-rekt"). The slug is the canonical name lowercased with spaces
    replaced by hyphens.
    """
    slug = tier_slug.strip().lower().replace(" ", "-")
    for name in TIER_NAMES:
        if name.lower().replace(" ", "-") == slug:
            return name
    return None


def valid_tier_slugs() -> list[str]:
    return [n.lower().replace(" ", "-") for n in TIER_NAMES]


async def get_tier_positions(
    client: httpx.AsyncClient,
    tier_name: str,
    concurrency: int = 8,
    top: int = 0,
) -> list[PositionRecord]:
    """Return all positions classified into tier_name across leaderboard wallets.

    Steps:
    1. Pull the full leaderboard.
    2. Fetch ALL open positions for every wallet (no watchlist filter).
    3. Classify each position; keep only those matching tier_name.

    Classification is per-position, not per-wallet (a wallet can have one
    position in Giga-Rekt and another in Money Print; only the Giga-Rekt
    position is kept here).

    This is I/O-heavy: every leaderboard wallet gets two API calls. Default
    concurrency is 8 to reduce 429 pressure vs cohort-pnl's 10, since there
    is no watchlist to narrow down the result set.
    """
    rules = load_tier_rules(_TIERS_YAML)

    entries = await fetch_leaderboard(client)
    wallets = [e.eth_address for e in entries]
    if top > 0:
        wallets = wallets[:top]
    log.info("tier_view: %d leaderboard wallets, fetching open positions...", len(wallets))

    all_positions = await fetch_open_positions(client, wallets, concurrency=concurrency)
    log.info("tier_view: %d total positions fetched, classifying...", len(all_positions))

    matching = [p for p in all_positions if classify_tier(p, rules) == tier_name]
    log.info(
        "tier_view: %d positions in tier '%s'",
        len(matching),
        tier_name,
    )
    return matching
