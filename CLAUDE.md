# cohort-dashboard -- Claude Code bootstrap prompt

## Context

This repo (`cohort-dashboard`) replicates the HyperTracker "Cohort
Intelligence" screen (single-tier drill view): a summary card for one PNL
tier (wallet count, open value split, in-profit/underwater %, trader
counts), a wallet table, and an asset breakdown (top open perps + liquidation
risk by asset) computed across **whatever assets that tier's wallets
actually hold**, not a fixed watchlist.

It is a sibling of `cohort-pnl` (at `../cohort-pnl`) and depends on it for
leaderboard fetch + tier classification. It is a separate repo, not an
extension of `cohort-pnl` in place, because the asset scope is fundamentally
different (open-ended vs. fixed 7-ticker watchlist) and mixing the two would
risk regressing the already-shipped `cohort-pnl` tool.

Obsidian build note for full decision history (read it, do not duplicate):
check `+Faro+ Index.md` for the link once the build note exists, create it
following the `cohort-pnl` build note as a template if it doesn't.

---

## What "v1" means here -- read this before building anything

The HyperTracker screen has more on it than v1 covers. Three things are
**explicitly out of scope for v1**, do not build them:

1. **Position Age** (the "<24h" filter and per-wallet age column like "23h",
   "6h", "49m"). Requires `userFills` history per wallet to find when a
   position was opened. This is the fills-crawl work that `cohort-pnl`
   parked as "Option B". Flagged as v2.
2. **Cohort Bias as a time-series sparkline** (the green/red wavy line in the
   summary card). Needs daily snapshots accumulated over time, same
   constraint as `cohort-pnl`'s own Bias Trend. Flagged as v2.
3. **Cohort Exposure as a time-series chart** (the 3x-6x leverage line over
   time, bottom right of the screenshot). Same reason as #2. Flagged as v2.

What v1 **does** cover, all computable from data already available via
`clearinghouseState` in a single pass, no new endpoints needed:

- Summary card: wallet count, open value split (green=long-biased /
  red=short-biased or in-profit/underwater, decide which framing matches the
  data you have and document it), in-profit % vs underwater %, trader counts
- Wallet table: address, perp equity, open value, **exposure/leverage**
  (notional / equity -- not computed anywhere yet, new calc), sum UPNL,
  closest liquidation %
- Asset breakdown: "Top Open Perps" (by total open value across the tier's
  wallets) and "Liquidation Risk by Asset" (% of open value within some
  proximity band of liquidation, per asset) -- computed over **all** assets
  the tier's wallets hold, not a fixed list

---

## Tier selection: one at a time, not all 8

```
cohort-dashboard --tier giga-rekt
```

Compute the full breakdown for one tier per run, matching the screenshot
(which shows a single selected tier, "Giga-Rekt"). Do not compute all 8
tiers' full asset breakdowns in one pass -- that is 8x the open-ended
position-fetching cost for no immediate benefit. Valid tier values match
`cohort_pnl.tiers.TIER_NAMES` (lowercased, hyphenated, e.g. `"Full Rekt"` ->
`full-rekt`, `"Giga-Rekt"` -> `giga-rekt`). Validate the flag and fail with a
clear error listing valid options if it doesn't match.

---

## Dependency on cohort-pnl -- what to reuse, what to write fresh

Add as a path dependency in `pyproject.toml`, same pattern as `depth-map`
depending on `perp-liquidity`:

```toml
dependencies = [
    "cohort-pnl @ file://../cohort-pnl",
    "httpx>=0.27",
    "pyyaml>=6.0",
    "rich>=13.0",
]
```

**Reuse directly, do not reimplement:**
- `cohort_pnl.fetchers.leaderboard.fetch_leaderboard(client)` -- identical
  need, full leaderboard pull, no watchlist involved at this stage at all.
- `cohort_pnl.tiers.classify_tier(position, rules)` and
  `cohort_pnl.tiers.load_tier_rules()` -- pure functions, watchlist-agnostic,
  work on any `PositionRecord` regardless of which coin it's for.
- `cohort_pnl.errors.VenueUnavailable` -- reuse the same error type for
  consistency.

**Do NOT reuse `cohort_pnl.fetchers.positions.fetch_positions`.** Read
`cohort_pnl/fetchers/positions.py` first to understand the two-dex query
pattern (native HL perps with no `dex` param, HIP-3 perps with
`"dex": "xyz"`, coin normalization stripping the `xyz:` prefix), then write
a **new** fetcher in this repo, `fetchers/open_positions.py`, that mirrors
the same two-dex `clearinghouseState` call shape but has **no watchlist
filter at all** -- keep every non-zero position for every coin returned.
Do not try to pass a fake "match everything" watchlist into the existing
function; that is a hack that couples this repo's correctness to an
implementation detail of `cohort-pnl`'s filter logic. A fresh fetcher with no
filter parameter is the simpler, more honest implementation.

This means: same retry/backoff pattern (429 handling, 2s then 5s), same
semaphore-bounded concurrency, same `PositionRecord`-shaped dataclass
(consider importing the dataclass shape itself from `cohort_pnl.fetchers.
positions` if it has no watchlist coupling baked into its fields -- check
before deciding).

---

## What to build

### 1. Project scaffold

```
cohort-dashboard/
  src/
    cohort_dashboard/
      __init__.py
      fetchers/
        __init__.py
        open_positions.py   # two-dex clearinghouseState, NO watchlist filter
      tier_view.py            # orchestrates: leaderboard -> filter to one
                               # tier's wallets -> fetch open positions
      exposure.py             # pure: notional / equity calc
      summary.py               # pure: per-tier summary card numbers
      asset_breakdown.py       # pure: top open perps + liq risk by asset
      output.py                 # rich terminal tables
      cli.py
  config/
    (reuses cohort-pnl's config/tiers.yaml via the import -- do not
    duplicate tier boundaries here)
  tests/
    test_exposure.py
    test_summary.py
    test_asset_breakdown.py
    test_fetchers.py
  pyproject.toml
  CLAUDE.md
  README.md
```

### 2. Tier-scoped wallet selection: `tier_view.py`

```python
async def get_tier_positions(
    client: httpx.AsyncClient,
    tier_name: str,
    concurrency: int = 10,
) -> list[PositionRecord]:
    """
    1. Pull the full leaderboard (cohort_pnl.fetchers.leaderboard).
    2. For each wallet, fetch ALL open positions (this repo's
       open_positions.fetch_open_positions, no watchlist filter).
    3. Classify each position with cohort_pnl.tiers.classify_tier.
    4. Keep only positions whose tier label matches tier_name.

    Note: classification happens per-POSITION, same as cohort-pnl, not per
    wallet. A wallet can have one position in Giga-Rekt and another in
    Money Print. Only the matching positions are kept, not the whole wallet's
    portfolio -- decide if the screenshot's "576 Wallets" count means unique
    wallets with at least one Giga-Rekt position (likely, given the
    screenshot's framing) and implement accordingly. Document the choice.
    """
```

This is the expensive step: every leaderboard wallet gets a full open-position
fetch (no watchlist to cheaply filter on), then gets classified after the
fact. Cost is higher than `cohort-pnl`'s per-wallet cost since there's no
early filtering. Keep the same concurrency-limited batching, default to a
lower concurrency than `cohort-pnl` if early testing shows more rate-limiting
pressure -- watch for this, don't assume the same `CONCURRENCY = 10` is
still right.

### 3. Exposure: `exposure.py`

```python
def compute_exposure(position: PositionRecord) -> float | None:
    """
    Leverage / exposure ratio: notional value / margin used (equity at risk
    for this position). Returns None if margin_used is zero or missing.

    notional = abs(position.size) * position.mark_px
    exposure = notional / position.margin_used
    """
```

Pure function, test against hand-computed examples.

### 4. Summary card: `summary.py`

```python
def compute_tier_summary(positions: list[PositionRecord]) -> dict:
    """
    Given all positions classified into one tier:
      - wallet_count: unique wallets represented
      - open_value_long_usd / open_value_short_usd (or in-profit/underwater
        split -- pick the framing the data naturally supports and document
        which)
      - pct_in_profit / pct_underwater (by wallet count or by value -- decide
        and document, the screenshot shows trader counts so likely by wallet)
      - traders_in_profit / traders_underwater (counts)
    """
```

### 5. Asset breakdown: `asset_breakdown.py`

```python
def top_open_perps(positions: list[PositionRecord], n: int = 10) -> list[dict]:
    """
    Group by coin, sum open value (notional), sort descending, top N.
    Per asset: total value, bias label (e.g. "Very Bullish" / "Bullish" /
    "Bearish" / "Very Bearish" based on long vs short value split -- define
    the thresholds for each label and put them in a constant, not magic
    numbers inline).
    """

def liquidation_risk_by_asset(
    positions: list[PositionRecord],
    proximity_pct: float = 25.0,
) -> list[dict]:
    """
    Per asset: % of total open value where liq_distance_pct <= proximity_pct
    (reuse the same liq-distance calc cohort_pnl.tiers uses internally --
    check if it's exposed as a standalone function, if not, write a small
    one here rather than reimplementing the math differently).
    """
```

### 6. Output: `output.py`

Rich terminal tables, matching `cohort-pnl`'s existing rendering style:
summary card panel, wallet table (sorted by some sensible default, e.g.
largest open value first), asset breakdown table. `--json` flag for raw
output, matching `cohort-pnl`'s CLI convention.

### 7. CLI: `cli.py`

```
cohort-dashboard --tier giga-rekt
cohort-dashboard --tier giga-rekt --json
cohort-dashboard --tier giga-rekt --concurrency 8
```

No `--save` flag in v1 -- there is no time-series data to snapshot yet (see
v2 deferrals above). Do not add a stub `--save` that doesn't do anything
meaningful.

---

## Unit traps to document in code comments

- Wallet count semantics: "576 Wallets" in the screenshot likely means
  unique wallets with at least one position in this tier, not unique
  positions. Get this right in `get_tier_positions`, it affects every number
  downstream.
- A wallet can appear with multiple positions in the SAME tier (e.g. two
  different Giga-Rekt positions on different assets). Decide whether the
  wallet table shows one row per wallet (aggregated) or one row per
  qualifying position, and document the choice -- the screenshot's table
  looks like one row per wallet with a "Closest Liq" single value, suggesting
  aggregation to the worst/closest position per wallet.
- No watchlist filter means HIP-3 assets you don't already track
  (kPEPE, WLD, LITE, HYPE, INTC, SNDK, SP500, XYZ100 in the screenshot) will
  show up. Coin normalization (stripping `xyz:` prefix) still applies the
  same way `cohort-pnl` does it -- reuse that logic exactly, do not write a
  second slightly-different normalizer.
- Exposure calc divides by `margin_used`. Cross-margin positions may report
  this differently than isolated positions -- check live data for both cases
  before assuming the field always means the same thing.

---

## Tests to write

`tests/test_exposure.py`:
1. `test_compute_exposure_basic` -- known notional and margin, verify ratio
2. `test_compute_exposure_zero_margin` -- returns None, not a crash

`tests/test_summary.py`:
3. `test_tier_summary_basic` -- mixed long/short, profit/underwater wallets
4. `test_tier_summary_empty` -- zero positions returns zeros, not an exception

`tests/test_asset_breakdown.py`:
5. `test_top_open_perps_ranking` -- verify sort order and top-N truncation
6. `test_top_open_perps_bias_labels` -- verify bias label thresholds
7. `test_liquidation_risk_by_asset` -- verify the proximity-band % calc

`tests/test_fetchers.py` -- smoke tests with httpx mock:
8. `test_open_positions_no_watchlist_filter` -- mock a response with assets
   outside the cohort-pnl watchlist, verify they are NOT dropped

---

## Style conventions (match cohort-pnl / perp-liquidity / depth-map)

- All IO async (`httpx.AsyncClient`)
- Frozen dataclasses with `fetched_at` timestamps
- No em dashes anywhere in code, comments, docstrings, or commit messages
- Section headers: `# -- section name ----`
- Honest "not available" over fake coverage
- Surgical edits once the skeleton exists, no full-file rewrites
- Reuse `cohort_pnl`'s error hierarchy rather than inventing a parallel one

---

## Do not build yet

- Position Age (needs `userFills`, v2)
- Cohort Bias time-series sparkline (needs accumulated snapshots, v2)
- Cohort Exposure time-series chart (needs accumulated snapshots, v2)
- All-8-tiers-at-once view
- A live dashboard / web UI -- terminal output + JSON is the target
- `--save` / SQLite snapshotting -- nothing to snapshot yet in v1

---

## Start here

Read `../cohort-pnl/src/cohort_pnl/fetchers/positions.py` and
`../cohort-pnl/src/cohort_pnl/tiers.py` first to understand exactly what to
reuse vs. what to write fresh (see the "Dependency on cohort-pnl" section
above), then scaffold the repo structure before writing fetcher logic.
