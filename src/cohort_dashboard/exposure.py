"""exposure.py -- leverage / exposure ratio. Pure, no I/O."""

from __future__ import annotations

from cohort_pnl.fetchers.positions import PositionRecord


def compute_exposure(position: PositionRecord) -> float | None:
    """Return notional / margin_used for this position.

    notional = abs(size) * mark_px
    exposure = notional / margin_used

    Returns None if margin_used is zero or missing (avoids divide-by-zero;
    cross-margin positions may legitimately report margin_used=0).
    """
    if position.margin_used <= 0:
        return None
    notional = abs(position.size) * position.mark_px
    return notional / position.margin_used
