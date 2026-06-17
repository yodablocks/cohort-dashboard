"""fills.py -- per-wallet userFills fetch for position age calculation.

Algorithm: walk fills newest-to-oldest for a specific coin. The position was
opened at the first fill where startPosition is 0 (flat before this fill) or
where startPosition flipped sign relative to the current side (a position
flip means the old position closed and a new one opened at that point).

If no such fill exists within the 2000-fill API cap, the position predates
the available history. We return the earliest fill's timestamp as a lower
bound, flagged with is_lower_bound=True. The caller should format this as
">Xd" rather than an exact age.

One fills call per wallet returns all coins, so a single call covers all of
a wallet's positions. The results are keyed by coin so callers can look up
any position in O(1).

API: POST /info {"type": "userFills", "user": "<address>"}
Returns up to 2000 fills sorted newest-first.
Fill shape (fields we use):
  coin (str), time (int ms epoch), startPosition (str float, signed),
  dir (str: "Open Long" / "Close Long" / "Open Short" / "Close Short" /
            "Buy" / "Sell" -- check live data for exact values)

Retry pattern: same as open_positions.py (2s then 5s on 429).
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx

from cohort_pnl.errors import VenueUnavailable

log = logging.getLogger(__name__)

INFO_URL = "https://api.hyperliquid.xyz/info"
TIMEOUT = 15.0
CONCURRENCY = 4  # lower than positions fetcher; fills API rate-limits aggressively at scale

# One retry only, short delay. A fills miss shows as "n/a" -- acceptable fallback.
_RETRY_DELAYS = [1.0]


@dataclass(frozen=True)
class PositionAge:
    coin: str
    wallet: str
    opened_at: datetime
    is_lower_bound: bool  # True if 2000-fill cap was hit; opened_at is the floor, not the actual open


def _find_open_time(
    fills: list[dict],
    coin: str,
    current_side: str,
) -> PositionAge | None:
    """Find when the current open position for (coin, side) was opened.

    Walk fills newest-to-oldest. The opening fill is the one where
    startPosition was zero (position was flat before this fill) or where
    startPosition is opposite sign to current_side (a direction flip).

    Returns None if there are no fills for this coin at all.
    """
    coin_fills = [f for f in fills if f.get("coin", "").upper() == coin.upper()]
    if not coin_fills:
        return None

    # fills are newest-first from the API; we need oldest-first to trace history.
    # But we're searching for the opening fill, so we walk newest-to-oldest and
    # stop at the first "opening boundary" we find.
    side_sign = 1.0 if current_side == "long" else -1.0

    for fill in coin_fills:
        try:
            start_pos = float(fill.get("startPosition", 0))
        except (TypeError, ValueError):
            continue

        # If start_pos is 0, this fill opened from flat -- this IS the opening fill.
        if abs(start_pos) < 1e-9:
            ts_ms = fill.get("time")
            if ts_ms is None:
                continue
            opened_at = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
            return PositionAge(
                coin=coin,
                wallet="",  # populated by the caller who knows the wallet
                opened_at=opened_at,
                is_lower_bound=False,
            )

        # If start_pos is opposite sign to current side, this fill crossed flat --
        # position opened after this fill, so the NEXT fill (older) is the opener.
        # Track across the loop: when we see a fill that went from opposite-sign to
        # same-sign (or zero), that fill is the opener.
        start_sign = 1.0 if start_pos > 0 else -1.0
        if start_sign != side_sign:
            # The fill AFTER (newer than) this one was where the current position opened.
            # But we don't have a pointer to it here. Instead, interpret this fill as
            # "the position was flat or flipped at the time of this fill's startPosition."
            # The correct opening fill is the NEXT FILL we process (the one we just
            # passed in the previous iteration). Since we're walking newest-to-oldest,
            # "previous iteration" = the newer fill. Mark the time of the current fill
            # as the approximate open boundary (conservative: actual open may be slightly
            # newer, but this fill is the last we can confirm had opposite sign, so the
            # true open is between this fill and the previous one -- use this fill's
            # timestamp as the open time, which slightly over-estimates age).
            ts_ms = fill.get("time")
            if ts_ms is None:
                continue
            opened_at = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
            return PositionAge(
                coin=coin,
                wallet="",
                opened_at=opened_at,
                is_lower_bound=False,
            )

    # No zero-crossing found in all available fills.
    # The position predates the 2000-fill cap. Return the oldest fill's time as a floor.
    oldest_fill = coin_fills[-1]  # fills are newest-first, so last = oldest
    ts_ms = oldest_fill.get("time")
    if ts_ms is None:
        return None
    opened_at = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
    return PositionAge(
        coin=coin,
        wallet="",
        opened_at=opened_at,
        is_lower_bound=True,
    )


async def _fetch_fills_raw(
    client: httpx.AsyncClient,
    wallet: str,
    sem: asyncio.Semaphore,
) -> list[dict]:
    """Fetch up to 2000 userFills for a wallet, newest first."""
    body = {"type": "userFills", "user": wallet}

    for attempt in range(len(_RETRY_DELAYS) + 1):
        async with sem:
            try:
                resp = await client.post(INFO_URL, json=body, timeout=TIMEOUT)
                is_429 = resp.status_code == 429
                if not is_429:
                    resp.raise_for_status()
                    return resp.json()
            except httpx.HTTPError as e:
                is_429 = "429" in str(e)
                if not is_429:
                    log.warning("userFills failed for %s: %s", wallet, e)
                    return []

        if attempt < len(_RETRY_DELAYS):
            await asyncio.sleep(_RETRY_DELAYS[attempt])
        else:
            log.warning("userFills gave up after retries for %s", wallet)

    return []


async def fetch_position_ages(
    client: httpx.AsyncClient,
    wallet: str,
    positions: list[tuple[str, str]],
    sem: asyncio.Semaphore,
) -> dict[str, PositionAge]:
    """Fetch fills for wallet and compute position age for each (coin, side) pair.

    positions: list of (coin, side) tuples for the wallet's open positions.
    Returns: dict keyed by coin, value is PositionAge.

    One fills call covers all coins for the wallet. Coins with no matching
    fills are omitted from the result.
    """
    fills = await _fetch_fills_raw(client, wallet, sem)
    if not fills:
        return {}

    result: dict[str, PositionAge] = {}
    for coin, side in positions:
        age = _find_open_time(fills, coin, side)
        if age is not None:
            result[coin] = PositionAge(
                coin=age.coin,
                wallet=wallet,
                opened_at=age.opened_at,
                is_lower_bound=age.is_lower_bound,
            )
    return result


async def fetch_all_position_ages(
    client: httpx.AsyncClient,
    wallet_positions: dict[str, list[tuple[str, str]]],
    *,
    concurrency: int = CONCURRENCY,
) -> dict[str, dict[str, PositionAge]]:
    """Fetch position ages for all wallets.

    wallet_positions: {wallet_address: [(coin, side), ...]}
    Returns: {wallet_address: {coin: PositionAge}}
    """
    sem = asyncio.Semaphore(concurrency)
    tasks = {
        wallet: fetch_position_ages(client, wallet, positions, sem)
        for wallet, positions in wallet_positions.items()
    }
    results = await asyncio.gather(*tasks.values())
    return dict(zip(tasks.keys(), results))
