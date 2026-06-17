"""snapshot.py -- SQLite daily snapshot writer/reader for per-tier data.

Schema: one row per (snapshot_date, tier). Accumulates over time so
the cohort bias sparkline and exposure time-series can be computed once
enough history exists (v2 display -- see README v2 section).

Two metrics stored per tier per day:
  - long_bias_pct: open_value_long / total_open_value * 100
    This is the cohort bias signal: 50 = balanced, >50 = net long, <50 = net short.
  - avg_exposure: value-weighted mean leverage across all positions in the tier
    notional_i / margin_i for each position, weighted by notional_i.

Follows cohort-pnl/src/cohort_pnl/snapshot.py pattern: idempotent setup,
explicit schema, no ORM.
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

DEFAULT_DB = Path(__file__).parent.parent.parent.parent / "data" / "cohort_dashboard_snapshots.db"


def init_db(path: Path = DEFAULT_DB) -> sqlite3.Connection:
    """Create table if it does not exist. Returns an open connection."""
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cohort_tier_snapshots (
            snapshot_date       TEXT NOT NULL,
            tier                TEXT NOT NULL,
            wallet_count        INTEGER NOT NULL,
            open_value_long_usd REAL NOT NULL,
            open_value_short_usd REAL NOT NULL,
            long_bias_pct       REAL NOT NULL,
            avg_exposure        REAL,
            pct_in_profit       REAL NOT NULL,
            created_at          TEXT NOT NULL,
            PRIMARY KEY (snapshot_date, tier)
        )
    """)
    conn.commit()
    return conn


def write_snapshot(
    conn: sqlite3.Connection,
    snapshot_date: date,
    tier: str,
    wallet_count: int,
    open_value_long_usd: float,
    open_value_short_usd: float,
    long_bias_pct: float,
    avg_exposure: float | None,
    pct_in_profit: float,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    conn.execute("""
        INSERT OR REPLACE INTO cohort_tier_snapshots
          (snapshot_date, tier, wallet_count, open_value_long_usd,
           open_value_short_usd, long_bias_pct, avg_exposure,
           pct_in_profit, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        snapshot_date.isoformat(),
        tier,
        wallet_count,
        open_value_long_usd,
        open_value_short_usd,
        long_bias_pct,
        avg_exposure,
        pct_in_profit,
        now,
    ))
    conn.commit()


def read_bias_trend(
    conn: sqlite3.Connection,
    tier: str,
    days: int = 30,
) -> list[tuple[str, float]]:
    """Return (snapshot_date, long_bias_pct) for the last `days` snapshots, oldest first."""
    rows = conn.execute("""
        SELECT snapshot_date, long_bias_pct
        FROM cohort_tier_snapshots
        WHERE tier = ?
        ORDER BY snapshot_date DESC
        LIMIT ?
    """, (tier, days)).fetchall()
    return list(reversed(rows))


def read_exposure_trend(
    conn: sqlite3.Connection,
    tier: str,
    days: int = 30,
) -> list[tuple[str, float | None]]:
    """Return (snapshot_date, avg_exposure) for the last `days` snapshots, oldest first."""
    rows = conn.execute("""
        SELECT snapshot_date, avg_exposure
        FROM cohort_tier_snapshots
        WHERE tier = ?
        ORDER BY snapshot_date DESC
        LIMIT ?
    """, (tier, days)).fetchall()
    return list(reversed(rows))
