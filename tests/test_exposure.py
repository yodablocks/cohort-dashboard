"""test_exposure.py"""

from datetime import datetime, timezone

from cohort_pnl.fetchers.positions import PositionRecord
from cohort_dashboard.exposure import compute_exposure


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


def test_compute_exposure_basic():
    # notional = 2.0 * 60000 = 120000; margin_used = 10000; exposure = 12x
    p = _pos(size=2.0, mark_px=60000.0, margin_used=10000.0)
    result = compute_exposure(p)
    assert result == 12.0


def test_compute_exposure_zero_margin():
    p = _pos(margin_used=0.0)
    assert compute_exposure(p) is None
