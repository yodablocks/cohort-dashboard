"""test_asset_breakdown.py"""

from datetime import datetime, timezone

from cohort_pnl.fetchers.positions import PositionRecord
from cohort_dashboard.asset_breakdown import (
    top_open_perps,
    liquidation_risk_by_asset,
)


def _pos(**kwargs) -> PositionRecord:
    defaults = dict(
        wallet="0xabc",
        coin="BTC",
        side="long",
        size=1.0,
        entry_px=50000.0,
        mark_px=50000.0,
        unrealized_pnl=0.0,
        margin_used=5000.0,
        liq_px=40000.0,
        fetched_at=datetime.now(timezone.utc),
    )
    defaults.update(kwargs)
    return PositionRecord(**defaults)


def test_top_open_perps_ranking():
    positions = [
        _pos(coin="BTC",  size=1.0, mark_px=50000.0),  # 50k
        _pos(coin="ETH",  size=5.0, mark_px=3000.0),   # 15k
        _pos(coin="SPCX", size=100.0, mark_px=200.0),  # 20k
    ]
    result = top_open_perps(positions, n=10)
    assert result[0].coin == "BTC"
    assert result[1].coin == "SPCX"
    assert result[2].coin == "ETH"


def test_top_open_perps_top_n_truncation():
    positions = [_pos(coin=f"COIN{i}", size=float(10 - i), mark_px=100.0) for i in range(10)]
    result = top_open_perps(positions, n=3)
    assert len(result) == 3


def test_top_open_perps_bias_labels():
    positions = [
        # 90% long -> Very Bullish
        _pos(coin="BTC", side="long",  size=9.0, mark_px=1.0),
        _pos(coin="BTC", side="short", size=1.0, mark_px=1.0),
        # 20% long -> Very Bearish
        _pos(coin="ETH", side="long",  size=2.0, mark_px=1.0),
        _pos(coin="ETH", side="short", size=8.0, mark_px=1.0),
        # 60% long -> Bullish
        _pos(coin="SPCX", side="long",  size=6.0, mark_px=1.0),
        _pos(coin="SPCX", side="short", size=4.0, mark_px=1.0),
    ]
    result = {e.coin: e.bias_label for e in top_open_perps(positions, n=10)}
    assert result["BTC"] == "Very Bullish"
    assert result["ETH"] == "Very Bearish"
    assert result["SPCX"] == "Bullish"


def test_liquidation_risk_by_asset():
    positions = [
        # BTC: 2 positions, both within 25% of liq
        _pos(coin="BTC", size=1.0, mark_px=50000.0, liq_px=45000.0),  # 10% away
        _pos(coin="BTC", size=1.0, mark_px=50000.0, liq_px=40000.0),  # 20% away
        # ETH: 1 position far from liq, 1 at risk
        _pos(coin="ETH", size=5.0, mark_px=3000.0,  liq_px=2900.0),   # 3.3% away -> at risk
        _pos(coin="ETH", size=5.0, mark_px=3000.0,  liq_px=1000.0),   # 66.7% away -> not at risk
    ]
    result = {e.coin: e for e in liquidation_risk_by_asset(positions, proximity_pct=25.0)}

    # BTC: both positions at risk -> risk_pct = 100%
    assert result["BTC"].risk_pct == 100.0

    # ETH: 5 * 3000 = 15000 at risk, 5 * 3000 = 15000 safe, total 30000 -> 50%
    assert abs(result["ETH"].risk_pct - 50.0) < 0.01
