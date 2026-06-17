"""test_fills.py -- position age algorithm tests."""

from datetime import datetime, timezone

from cohort_dashboard.fetchers.fills import _find_open_time, PositionAge
from cohort_dashboard.age import format_position_age, _format_duration


# -- _find_open_time unit tests ----

def _fill(coin: str, time_ms: int, start_pos: float) -> dict:
    return {"coin": coin, "time": time_ms, "startPosition": str(start_pos)}


def test_find_open_time_flat_start():
    """Fill with startPosition=0 means position opened from flat."""
    fills = [
        _fill("ETH", 1_000_000, 0.0),   # opening fill (flat -> long), 1000s epoch
    ]
    result = _find_open_time(fills, "ETH", "long")
    assert result is not None
    assert not result.is_lower_bound
    assert result.opened_at == datetime.fromtimestamp(1000.0, tz=timezone.utc)


def test_find_open_time_opposite_sign_flip():
    """Fill where startPosition flips sign = current position started here."""
    # Wallet was short (-5.0) and then flipped to long. The flip fill's
    # startPosition is negative (opposite of current "long" side).
    fills = [
        _fill("BTC", 2_000_000, -5.0),  # short -> (closed short, opened long)
    ]
    result = _find_open_time(fills, "BTC", "long")
    assert result is not None
    assert not result.is_lower_bound


def test_find_open_time_lower_bound_when_no_crossing():
    """If no zero-crossing in fills, return oldest fill as lower bound."""
    # All fills have startPosition with same sign as current side (always long).
    fills = [
        _fill("ETH", 3_000_000, 5.0),   # newest
        _fill("ETH", 2_000_000, 3.0),
        _fill("ETH", 1_000_000, 1.0),   # oldest
    ]
    result = _find_open_time(fills, "ETH", "long")
    assert result is not None
    assert result.is_lower_bound
    # oldest fill time_ms=1_000_000 -> 1000.0 seconds epoch
    assert result.opened_at == datetime.fromtimestamp(1000.0, tz=timezone.utc)


def test_find_open_time_no_fills_for_coin():
    fills = [_fill("BTC", 1_000_000, 0.0)]
    result = _find_open_time(fills, "ETH", "long")
    assert result is None


def test_find_open_time_coin_case_insensitive():
    """coin matching should be case-insensitive."""
    fills = [_fill("eth", 1_000_000, 0.0)]
    result = _find_open_time(fills, "ETH", "long")
    assert result is not None


# -- format_position_age tests ----

def test_format_duration_minutes():
    assert _format_duration(30 * 60) == "30m"


def test_format_duration_hours():
    assert _format_duration(6 * 3600) == "6h"


def test_format_duration_days_and_hours():
    assert _format_duration(3 * 86400 + 4 * 3600) == "3d 4h"


def test_format_duration_days_only():
    assert _format_duration(2 * 86400) == "2d"


def test_format_position_age_none():
    assert format_position_age(None) == "n/a"


def test_format_position_age_lower_bound():
    opened = datetime(2026, 6, 15, 0, 0, 0, tzinfo=timezone.utc)
    age = PositionAge(coin="ETH", wallet="0xabc", opened_at=opened, is_lower_bound=True)
    result = format_position_age(age)
    assert result.startswith(">")


def test_format_position_age_exact():
    opened = datetime(2026, 6, 15, 0, 0, 0, tzinfo=timezone.utc)
    age = PositionAge(coin="ETH", wallet="0xabc", opened_at=opened, is_lower_bound=False)
    result = format_position_age(age)
    assert not result.startswith(">")
    assert result != "n/a"
