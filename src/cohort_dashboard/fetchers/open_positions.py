"""open_positions.py -- per-wallet clearinghouseState, NO watchlist filter.

Same two-dex architecture as cohort-pnl/fetchers/positions.py:
- Native HL perps: clearinghouseState with no "dex" param.
- HIP-3 perps (xyz dex): clearinghouseState with "dex": "xyz".
  Coin field has "xyz:" prefix that _normalize_coin() strips.

Key difference from cohort-pnl: every non-zero position is kept regardless of
coin. No watchlist, no early filter. HIP-3 assets like kPEPE, WLD, HYPE, INTC
and any future listings will appear.

Two requests per wallet. Both share the same semaphore so total concurrency
is bounded across all outstanding requests. Default concurrency is lower than
cohort-pnl (8 vs 10) because this fetcher runs with no pre-filtering, which
means more returned data per wallet and slightly higher pressure on the API.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

import httpx

from cohort_pnl.errors import VenueUnavailable
from cohort_pnl.fetchers.positions import PositionRecord

log = logging.getLogger(__name__)

INFO_URL = "https://api.hyperliquid.xyz/info"
TIMEOUT = 15.0
CONCURRENCY = 8

XYZ_DEX = "xyz"

# Retry delays for successive 429s: 2s then 5s before giving up.
_RETRY_DELAYS = [2.0, 5.0]


def _normalize_coin(raw: str) -> str:
    """Strip the xyz: dex prefix to get the plain ticker."""
    if ":" in raw:
        return raw.split(":", 1)[1].strip().upper()
    return raw.strip().upper()


def _parse_all_positions(
    wallet: str,
    data: dict,
    fetched_at: datetime,
) -> list[PositionRecord]:
    """Extract all non-zero positions from a clearinghouseState response."""
    records: list[PositionRecord] = []

    asset_positions = data.get("assetPositions", [])
    for entry in asset_positions:
        pos = entry.get("position", {})
        raw_coin = pos.get("coin", "")
        coin = _normalize_coin(raw_coin)

        szi = pos.get("szi", "0")
        try:
            size = float(szi)
        except (TypeError, ValueError):
            continue

        if size == 0.0:
            continue  # closed position still in response

        side = "long" if size > 0 else "short"

        try:
            entry_px = float(pos.get("entryPx", 0))
            unrealized_pnl = float(pos.get("unrealizedPnl", 0))
            margin_used = float(pos.get("marginUsed", 0))
        except (TypeError, ValueError):
            continue

        try:
            pos_value = float(pos.get("positionValue", 0))
            mark_px = pos_value / abs(size) if abs(size) > 0 else entry_px
        except (TypeError, ValueError, ZeroDivisionError):
            mark_px = entry_px

        raw_liq = pos.get("liquidationPx")
        try:
            liq_px = float(raw_liq) if raw_liq is not None else None
        except (TypeError, ValueError):
            liq_px = None

        records.append(
            PositionRecord(
                wallet=wallet,
                coin=coin,
                side=side,
                size=abs(size),
                entry_px=entry_px,
                mark_px=mark_px,
                unrealized_pnl=unrealized_pnl,
                margin_used=margin_used,
                liq_px=liq_px,
                fetched_at=fetched_at,
            )
        )

    return records


async def _fetch_dex(
    client: httpx.AsyncClient,
    wallet: str,
    sem: asyncio.Semaphore,
    dex: str | None,
) -> list[PositionRecord]:
    """Fetch clearinghouseState for one wallet on one dex.

    Retries up to 2 times on 429 (2s then 5s backoff). Any other failure is
    logged and returns an empty list so one bad wallet does not abort the run.
    """
    body: dict = {"type": "clearinghouseState", "user": wallet}
    if dex is not None:
        body["dex"] = dex

    for attempt in range(len(_RETRY_DELAYS) + 1):
        async with sem:
            try:
                resp = await client.post(INFO_URL, json=body, timeout=TIMEOUT)
                is_429 = resp.status_code == 429
                if not is_429:
                    resp.raise_for_status()
                    data = resp.json()
                    fetched_at = datetime.now(timezone.utc)
                    return _parse_all_positions(wallet, data, fetched_at)
            except httpx.HTTPError as e:
                is_429 = "429" in str(e)
                if not is_429:
                    log.warning(
                        "clearinghouseState failed for %s dex=%s: %s",
                        wallet, dex, e,
                    )
                    return []

        if attempt < len(_RETRY_DELAYS):
            await asyncio.sleep(_RETRY_DELAYS[attempt])
        else:
            log.warning(
                "clearinghouseState gave up after retries for %s dex=%s",
                wallet, dex,
            )

    return []


async def _fetch_one(
    client: httpx.AsyncClient,
    wallet: str,
    sem: asyncio.Semaphore,
) -> list[PositionRecord]:
    """Fetch native HL perps + xyz HIP-3 perps for one wallet."""
    native, xyz = await asyncio.gather(
        _fetch_dex(client, wallet, sem, dex=None),
        _fetch_dex(client, wallet, sem, dex=XYZ_DEX),
    )
    return native + xyz


async def fetch_open_positions(
    client: httpx.AsyncClient,
    wallets: list[str],
    *,
    concurrency: int = CONCURRENCY,
) -> list[PositionRecord]:
    """Fetch clearinghouseState for every wallet, return ALL non-zero positions.

    No watchlist filter. Every coin returned by the API is kept, including
    HIP-3 assets and any future listings not tracked by cohort-pnl.

    Makes two requests per wallet: native HL perps and xyz HIP-3 dex. Both
    share the same semaphore so concurrency is bounded across all requests.

    Individual wallet failures are logged and skipped.
    """
    sem = asyncio.Semaphore(concurrency)
    tasks = [_fetch_one(client, w, sem) for w in wallets]
    results = await asyncio.gather(*tasks)

    all_positions: list[PositionRecord] = []
    for batch in results:
        all_positions.extend(batch)

    log.info(
        "open_positions: %d wallets queried, %d total positions found",
        len(wallets),
        len(all_positions),
    )
    return all_positions
