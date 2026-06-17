"""test_snapshot.py -- SQLite snapshot round-trip tests."""

import sqlite3
import tempfile
from datetime import date
from pathlib import Path

from cohort_dashboard.snapshot import init_db, write_snapshot, read_bias_trend, read_exposure_trend


def _tmp_db() -> tuple[sqlite3.Connection, Path]:
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    path = Path(tmp.name)
    tmp.close()
    conn = init_db(path)
    return conn, path


def test_write_and_read_bias_trend():
    conn, _ = _tmp_db()
    d1 = date(2026, 6, 15)
    d2 = date(2026, 6, 16)
    write_snapshot(conn, d1, "Giga-Rekt", 30, 10_000.0, 5_000.0, 66.7, 20.0, 40.0)
    write_snapshot(conn, d2, "Giga-Rekt", 35, 12_000.0, 6_000.0, 70.0, 22.0, 38.0)

    rows = read_bias_trend(conn, "Giga-Rekt")
    assert len(rows) == 2
    # oldest first
    assert rows[0][0] == "2026-06-15"
    assert abs(rows[0][1] - 66.7) < 0.01
    assert rows[1][0] == "2026-06-16"
    assert abs(rows[1][1] - 70.0) < 0.01


def test_write_and_read_exposure_trend():
    conn, _ = _tmp_db()
    write_snapshot(conn, date(2026, 6, 16), "Semi-Rekt", 100, 50_000.0, 80_000.0, 38.0, 8.5, 10.0)

    rows = read_exposure_trend(conn, "Semi-Rekt")
    assert len(rows) == 1
    assert rows[0][0] == "2026-06-16"
    assert abs(rows[0][1] - 8.5) < 0.01


def test_write_idempotent_same_day():
    """INSERT OR REPLACE -- second write for same (date, tier) overwrites first."""
    conn, _ = _tmp_db()
    d = date(2026, 6, 16)
    write_snapshot(conn, d, "Giga-Rekt", 30, 10_000.0, 5_000.0, 60.0, 15.0, 40.0)
    write_snapshot(conn, d, "Giga-Rekt", 35, 11_000.0, 5_500.0, 65.0, 16.0, 42.0)

    rows = read_bias_trend(conn, "Giga-Rekt")
    assert len(rows) == 1
    assert abs(rows[0][1] - 65.0) < 0.01


def test_exposure_none_stored_as_null():
    conn, _ = _tmp_db()
    write_snapshot(conn, date(2026, 6, 16), "Money Print", 50, 20_000.0, 10_000.0, 66.7, None, 90.0)

    rows = read_exposure_trend(conn, "Money Print")
    assert len(rows) == 1
    assert rows[0][1] is None


def test_different_tiers_isolated():
    conn, _ = _tmp_db()
    d = date(2026, 6, 16)
    write_snapshot(conn, d, "Giga-Rekt",  30, 10_000.0, 5_000.0, 70.0, 20.0, 30.0)
    write_snapshot(conn, d, "Money Print", 80, 50_000.0, 20_000.0, 70.0, 8.0, 95.0)

    giga = read_bias_trend(conn, "Giga-Rekt")
    money = read_bias_trend(conn, "Money Print")
    assert len(giga) == 1
    assert len(money) == 1
    assert giga[0][0] == money[0][0]  # same date
