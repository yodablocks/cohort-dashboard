"""test_summary.py"""

from datetime import datetime, timezone

from cohort_pnl.fetchers.positions import PositionRecord
from cohort_dashboard.summary import compute_tier_summary, compute_long_bias_pct, compute_avg_exposure


def _pos(**kwargs) -> PositionRecord:
    defaults = dict(
        wallet="0xabc",
        coin="BTC",
        side="long",
        size=1.0,
        entry_px=50000.0,
        mark_px=50000.0,
        unrealized_pnl=1000.0,
        margin_used=5000.0,
        liq_px=40000.0,
        fetched_at=datetime.now(timezone.utc),
    )
    defaults.update(kwargs)
    return PositionRecord(**defaults)


def test_tier_summary_basic():
    positions = [
        _pos(wallet="0x1", side="long",  mark_px=50000.0, size=1.0, unrealized_pnl=500.0),
        _pos(wallet="0x2", side="short", mark_px=50000.0, size=1.0, unrealized_pnl=-200.0),
        _pos(wallet="0x3", side="long",  mark_px=50000.0, size=0.5, unrealized_pnl=-50.0),
    ]
    s = compute_tier_summary(positions)

    assert s.wallet_count == 3
    # long notional: 1.0*50000 + 0.5*50000 = 75000
    assert s.open_value_long_usd == 75000.0
    # short notional: 1.0*50000 = 50000
    assert s.open_value_short_usd == 50000.0
    # wallet 0x1: pnl=500 (profit), wallet 0x2: pnl=-200 (underwater), wallet 0x3: pnl=-50 (underwater)
    assert s.traders_in_profit == 1
    assert s.traders_underwater == 2
    assert abs(s.pct_in_profit - 33.33) < 0.1


def test_compute_long_bias_pct_balanced():
    positions = [
        _pos(wallet="0x1", side="long",  mark_px=100.0, size=1.0),
        _pos(wallet="0x2", side="short", mark_px=100.0, size=1.0),
    ]
    assert compute_long_bias_pct(positions) == 50.0


def test_compute_long_bias_pct_all_long():
    positions = [_pos(wallet="0x1", side="long", mark_px=100.0, size=2.0)]
    assert compute_long_bias_pct(positions) == 100.0


def test_compute_long_bias_pct_empty():
    assert compute_long_bias_pct([]) == 50.0


def test_compute_avg_exposure_basic():
    # notional = 1.0 * 100 = 100, margin = 10 => exposure = 10x
    # notional = 2.0 * 100 = 200, margin = 20 => exposure = 10x
    # value-weighted: (100+200) / (10+20) = 10.0
    positions = [
        _pos(wallet="0x1", mark_px=100.0, size=1.0, margin_used=10.0),
        _pos(wallet="0x2", mark_px=100.0, size=2.0, margin_used=20.0),
    ]
    result = compute_avg_exposure(positions)
    assert result is not None
    assert abs(result - 10.0) < 0.001


def test_compute_avg_exposure_zero_margin():
    positions = [_pos(wallet="0x1", mark_px=100.0, size=1.0, margin_used=0.0)]
    assert compute_avg_exposure(positions) is None


def test_tier_summary_empty():
    s = compute_tier_summary([])
    assert s.wallet_count == 0
    assert s.open_value_long_usd == 0.0
    assert s.open_value_short_usd == 0.0
    assert s.traders_in_profit == 0
    assert s.traders_underwater == 0
    assert s.pct_in_profit == 0.0
    assert s.pct_underwater == 0.0
