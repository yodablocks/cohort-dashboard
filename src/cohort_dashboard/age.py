"""age.py -- position age formatting. Pure, no I/O.

Position age is derived from the last zero-crossing of net position size in
the wallet's fill history. For wallets that have been continuously in a
position for longer than the 2000-fill API cap (roughly 1-2 days for the
most active wallets), the true open time is unknowable. In those cases
opened_at is the oldest available fill timestamp, and is_lower_bound=True.

Display format:
  - is_lower_bound=False: "49m", "6h", "23h", "3d 4h"
  - is_lower_bound=True:  ">2d", ">30d" (floor only)
  - None (fills API returned nothing): "n/a"
"""

from __future__ import annotations

from datetime import datetime, timezone

from cohort_dashboard.fetchers.fills import PositionAge


def _format_duration(seconds: float) -> str:
    """Format a duration in seconds to a human-readable string."""
    minutes = int(seconds // 60)
    hours = int(seconds // 3600)
    days = int(seconds // 86400)

    if days >= 1:
        remaining_hours = hours - days * 24
        if remaining_hours > 0:
            return f"{days}d {remaining_hours}h"
        return f"{days}d"
    if hours >= 1:
        return f"{hours}h"
    if minutes >= 1:
        return f"{minutes}m"
    return "<1m"


def format_position_age(age: PositionAge | None) -> str:
    """Format a PositionAge for display in the wallet table."""
    if age is None:
        return "n/a"
    now = datetime.now(timezone.utc)
    elapsed = (now - age.opened_at).total_seconds()
    if elapsed < 0:
        elapsed = 0.0
    label = _format_duration(elapsed)
    if age.is_lower_bound:
        return f">{label}"
    return label
