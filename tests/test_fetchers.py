"""test_fetchers.py -- smoke tests for open_positions fetcher.

Uses respx to mock httpx requests. Verifies that assets outside cohort-pnl's
fixed watchlist (e.g. HYPE, kPEPE) are NOT dropped.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import httpx
import pytest
import respx

from cohort_dashboard.fetchers.open_positions import fetch_open_positions

INFO_URL = "https://api.hyperliquid.xyz/info"


def _make_response(positions: list[dict]) -> dict:
    return {"assetPositions": [{"position": p} for p in positions]}


def _native_pos(coin: str, szi: str = "1.0") -> dict:
    return {
        "coin": coin,
        "szi": szi,
        "entryPx": "100.0",
        "positionValue": "100.0",
        "unrealizedPnl": "5.0",
        "marginUsed": "10.0",
        "liquidationPx": "80.0",
    }


def _xyz_pos(coin: str, szi: str = "1.0") -> dict:
    return {
        "coin": f"xyz:{coin}",
        "szi": szi,
        "entryPx": "50.0",
        "positionValue": "50.0",
        "unrealizedPnl": "-2.0",
        "marginUsed": "5.0",
        "liquidationPx": "40.0",
    }


@pytest.mark.asyncio
async def test_open_positions_no_watchlist_filter():
    """Assets not in cohort-pnl's watchlist (HYPE, kPEPE) must be kept."""
    wallet = "0xdeadbeef"

    native_data = _make_response([
        _native_pos("BTC"),
        _native_pos("HYPE"),   # not in cohort-pnl watchlist
    ])
    xyz_data = _make_response([
        _xyz_pos("SPCX"),
        _xyz_pos("kPEPE"),    # not in cohort-pnl watchlist
    ])

    with respx.mock:
        # Match native call (no dex in body) and xyz call.
        # respx matches by URL; we use a side_effect to distinguish by body.
        call_count = {"n": 0}

        def route_handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content)
            if body.get("dex") == "xyz":
                return httpx.Response(200, json=xyz_data)
            return httpx.Response(200, json=native_data)

        respx.post(INFO_URL).mock(side_effect=route_handler)

        async with httpx.AsyncClient() as client:
            positions = await fetch_open_positions(client, [wallet])

    coins = {p.coin for p in positions}
    assert "BTC" in coins,   "BTC (native watchlist asset) should be present"
    assert "HYPE" in coins,  "HYPE (non-watchlist asset) should NOT be filtered out"
    assert "SPCX" in coins,  "SPCX (xyz watchlist asset) should be present"
    assert "KPEPE" in coins, "kPEPE normalizes to KPEPE; non-watchlist xyz asset should NOT be filtered out"
    assert len(positions) == 4
