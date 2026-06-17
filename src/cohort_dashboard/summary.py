"""summary.py -- tier-level summary card. Pure, no I/O.

Framing choice: the screenshot's summary card shows "open value split" as
green (long-biased) / red (short-biased) and separate counts for traders in
profit vs underwater. We use:
  - open_value_long_usd / open_value_short_usd: sum of notional for long vs short
    positions (not margin_used, which is a risk measure, not a size measure).
    notional = abs(size) * mark_px.
  - in_profit / underwater: per wallet, summed across all of the wallet's
    positions in this tier. profit = net unrealized_pnl > 0, underwater = net
    <= 0. wallet_count is unique wallets with at least one qualifying position
    in this tier (matching the screenshot's "576 Wallets" framing).
"""

from __future__ import annotations

from dataclasses import dataclass

from cohort_pnl.fetchers.positions import PositionRecord


@dataclass
class TierSummary:
    wallet_count: int
    open_value_long_usd: float
    open_value_short_usd: float
    traders_in_profit: int
    traders_underwater: int
    pct_in_profit: float   # by wallet count
    pct_underwater: float  # by wallet count


def compute_tier_summary(positions: list[PositionRecord]) -> TierSummary:
    """Compute summary card numbers from all positions classified into one tier.

    wallet_count: unique wallets with at least one position in this tier.
    open_value_long_usd / short_usd: notional (not margin_used).
    in_profit: wallet's net unrealized_pnl across all its positions in this tier > 0.
    underwater: net unrealized_pnl <= 0.
    pct_* fractions: by wallet count, same basis as the screenshot's trader counts.
    """
    if not positions:
        return TierSummary(
            wallet_count=0,
            open_value_long_usd=0.0,
            open_value_short_usd=0.0,
            traders_in_profit=0,
            traders_underwater=0,
            pct_in_profit=0.0,
            pct_underwater=0.0,
        )

    # -- notional split ----
    long_val = 0.0
    short_val = 0.0
    for p in positions:
        notional = abs(p.size) * p.mark_px
        if p.side == "long":
            long_val += notional
        else:
            short_val += notional

    # -- per-wallet profit/loss ----
    # Group unrealized_pnl by wallet; a wallet is "in profit" if sum > 0.
    wallet_pnl: dict[str, float] = {}
    for p in positions:
        wallet_pnl[p.wallet] = wallet_pnl.get(p.wallet, 0.0) + p.unrealized_pnl

    wallets = list(wallet_pnl.keys())
    in_profit = sum(1 for v in wallet_pnl.values() if v > 0)
    underwater = sum(1 for v in wallet_pnl.values() if v <= 0)
    total = len(wallets)

    return TierSummary(
        wallet_count=total,
        open_value_long_usd=long_val,
        open_value_short_usd=short_val,
        traders_in_profit=in_profit,
        traders_underwater=underwater,
        pct_in_profit=(in_profit / total) * 100.0 if total > 0 else 0.0,
        pct_underwater=(underwater / total) * 100.0 if total > 0 else 0.0,
    )
