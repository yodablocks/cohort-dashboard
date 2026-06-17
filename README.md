# cohort-dashboard

Terminal tool that fetches every open position for one HyperTracker PNL tier and renders a summary card, wallet table, and asset breakdown across all coins those wallets actually hold.

Sibling to [cohort-pnl](../cohort-pnl). Unlike cohort-pnl's fixed 7-asset watchlist, cohort-dashboard captures every asset leaderboard wallets hold: SP500, AMZN, BRENTOIL, XYZ100, HOOD, anything listed on Hyperliquid.

## Usage

```
cohort-dashboard --tier giga-rekt
cohort-dashboard --tier giga-rekt --json
cohort-dashboard --tier giga-rekt --top 500
cohort-dashboard --tier giga-rekt --concurrency 6
```

**Flags:**

| Flag | Default | Description |
|------|---------|-------------|
| `--tier` | required | Tier to analyze (e.g. `giga-rekt`, `full-rekt`, `money-print`) |
| `--top` | 1000 | Cap wallet universe to first N leaderboard wallets (0 = all) |
| `--concurrency` | 8 | Max concurrent API calls |
| `--json` | off | Output raw JSON instead of rich tables |
| `--ages` | off | Fetch fill history to compute position age column (adds one API call per wallet) |
| `--save` | off | Write a daily snapshot to SQLite (accumulates data for v2 sparklines) |
| `--db` | `data/cohort_dashboard_snapshots.db` | Path to the snapshot database |

**Valid tiers:** `money-print`, `smart-money`, `grinder`, `humble-earner`, `exit-liquidity`, `semi-rekt`, `full-rekt`, `giga-rekt`

## Output

```
cohort-dashboard --tier giga-rekt
╭─────────────────────── Summary ───────────────────────╮
│ Tier: Giga-Rekt                                       │
│ Wallets: 35                                           │
│ Open Value: $25.8M Long  $22.3M Short  ($48.0M total) │
│ In Profit: 13 (37%)  Underwater: 22 (63%)             │
╰───────────────────────────────────────────────────────╯
                              Wallets (35 total, showing 35)

  Wallet              Open Value       Equity     Exposure       Sum UPNL    Closest Liq
 ────────────────────────────────────────────────────────────────────────────────────────
  0x020ca6...5872         $11.9M        $476K        25.0x      $96K gain           1.3%
  0x5e3ebe...97f8          $9.2M        $369K        25.0x      $54K loss           1.5%
  0x92772b...376c          $6.8M        $129K        52.2x      $36K loss           0.9%
  0x12f147...807c          $3.0M         $74K        40.0x      $965 loss           1.1%
  0xc37f3a...e903          $2.7M         $63K        42.1x       $3K loss           1.1%
  0x6d9532...ff14          $1.7M         $38K        44.1x       $3K loss           1.0%
  0x91f564...df13          $1.6M         $41K        40.0x       $1K gain           1.3%
  0x6d91e4...a39b          $1.6M         $32K        48.5x      $14K loss           0.8%
  0xbb8654...3ae3          $1.5M         $52K        29.1x       $2K gain           1.8%
  0x46560b...debd          $1.3M         $32K        40.0x      $12K gain           1.3%
  ...

                            Top Open Perps

  Asset       Total Value         Long        Short        Bias
 ────────────────────────────────────────────────────────────────
  ETH              $22.3M       $12.9M        $9.4M      Bullish
  BTC              $14.3M        $3.7M       $10.6M    Very Bearish
  SP500             $7.6M        $6.8M        $875K    Very Bullish
  XYZ100            $2.7M        $1.8M        $903K      Bullish
  AMZN              $515K        $515K           $0    Very Bullish
  JPY               $452K           $0        $452K    Very Bearish
  CL                $128K        $128K           $0    Very Bullish
  HOOD               $24K           $0         $24K    Very Bearish
  BRENTOIL           $21K         $21K           $0    Very Bullish

Liquidation Risk by Asset (within 25% of liq price)

  Asset       Total Value      At Risk     Risk %
 ─────────────────────────────────────────────────
  BTC              $14.3M       $14.3M     100.0%
  ETH              $22.3M       $22.3M     100.0%
  SP500             $7.6M        $7.6M     100.0%
  ...
```

### Semi-Rekt example

```
cohort-dashboard --tier semi-rekt
╭───────────────────────── Summary ─────────────────────────╮
│ Tier: Semi-Rekt                                           │
│ Wallets: 192                                              │
│ Open Value: $317.5M Long  $839.2M Short  ($1156.8M total) │
│ In Profit: 0 (0%)  Underwater: 192 (100%)                 │
╰───────────────────────────────────────────────────────────╯

  Wallet              Open Value       Equity     Exposure       Sum UPNL    Closest Liq
 ────────────────────────────────────────────────────────────────────────────────────────
  0x92ea19...50e9         $83.6M       $16.7M         5.0x    $12.9M loss          84.2%
  0xd47587...1a91         $68.4M       $16.4M         4.2x    $18.5M loss          32.9%
  0x7fdafd...17d1         $66.3M        $4.5M        14.6x     $2.4M loss          62.9%
  0xb83de0...6e36         $60.0M       $12.0M         5.0x     $6.9M loss          29.6%
  0x32008f...c407         $58.4M        $4.4M        13.2x     $2.7M loss          20.6%
  ...

                            Top Open Perps

  Asset       Total Value         Long        Short        Bias
 ────────────────────────────────────────────────────────────────
  HYPE            $282.7M           $0      $282.7M    Very Bearish
  BTC             $254.8M      $109.6M      $145.2M      Bearish
  ETH             $121.4M       $30.3M       $91.2M    Very Bearish
  SOL              $49.2M       $14.3M       $34.9M    Very Bearish
  MU               $48.2M           $0       $48.2M    Very Bearish
  NVDA             $43.2M       $43.0M        $226K    Very Bullish
  XRP              $31.3M        $9.2M       $22.1M    Very Bearish
  SKHX             $26.1M           $0       $26.1M    Very Bearish
  XYZ100           $21.7M        $665K       $21.0M    Very Bearish
  SP500            $20.8M           $0       $20.8M    Very Bearish

Liquidation Risk by Asset (within 25% of liq price)

  Asset       Total Value      At Risk     Risk %
 ─────────────────────────────────────────────────
  CRWV              $2.5M        $2.5M     100.0%
  CL               $18.3M       $18.2M      99.3%
  NVDA             $43.2M       $42.3M      97.9%
  ARM               $2.3M        $2.2M      94.8%
  SKHX             $26.1M       $24.1M      92.2%
  HOOD              $2.5M        $2.1M      82.0%
  DRAM              $8.2M        $6.0M      73.0%
  SPCX             $11.6M        $5.5M      47.5%
  MU               $48.2M       $21.7M      45.1%
  SP500            $20.8M        $5.3M      25.3%
  HYPE            $282.7M       $65.1M      23.0%
  ETH             $121.4M       $17.7M      14.5%
  BTC             $254.8M       $32.4M      12.7%
  ...
```

**Reading the output:**

- **Closest Liq**: distance between mark price and liquidation price. Closer to 0% means liquidation is imminent. Values above 100% are short positions where price would need to more than double to trigger liquidation -- they are far from liquidation despite appearing in a rekt tier.
- **N/A on Closest Liq**: cross-margin position. The API does not return a per-position liquidation price for cross-margin accounts.
- **Semi-rekt vs Giga-rekt**: semi-rekt is a PNL% tier (deep underwater but not necessarily near liquidation). Giga-rekt is a liq-proximity tier (about to be liquidated regardless of PNL%). A wallet can be semi-rekt with 64% liq distance -- bad PNL, but not immediately at risk.
- **Age column** (requires `--ages`): how long the wallet's youngest tier position has been open. Format: "6h", "23h", "3d 4h". A `>` prefix (e.g. ">2d") means the position predates the 2000-fill API window -- the number is a floor, not the exact age. High-frequency wallets can exhaust the 2000-fill cap in under 24 hours.
- **--ages on large tiers**: fetches are batched (20 wallets at a time, 2s between batches) to stay within `userFills` rate limits. On tiers with 100+ wallets a note is printed about expected wait time. Some wallets may still show `n/a` if the API rejects individual requests.

### Money-Print example

```
cohort-dashboard --tier money-print
╭──────────────────────── Summary ─────────────────────────╮
│ Tier: Money Print                                        │
│ Wallets: 176                                             │
│ Open Value: $438.6M Long  $244.8M Short  ($683.4M total) │
│ In Profit: 176 (100%)  Underwater: 0 (0%)                │
╰──────────────────────────────────────────────────────────╯

  Wallet              Open Value       Equity     Exposure       Sum UPNL    Closest Liq
 ────────────────────────────────────────────────────────────────────────────────────────
  0x6315c7...074a         $50.8M        $3.9M        13.0x     $6.9M gain          69.7%
  0x32008f...c407         $48.3M        $2.9M        16.4x     $8.1M gain          42.0%
  0x8af700...fa05         $36.7M        $3.9M         9.3x    $10.4M gain          88.7%
  0x9e8b1e...afc4         $31.8M        $5.8M         5.5x     $3.2M gain          15.2%
  0x8def9f...2dae         $25.5M        $2.5M        10.0x     $6.8M gain            N/A
  ...

                            Top Open Perps

  Asset       Total Value         Long        Short        Bias
 ────────────────────────────────────────────────────────────────
  HYPE            $155.5M      $155.5M           $0    Very Bullish
  BTC             $109.8M       $58.2M       $51.6M      Neutral
  ETH              $95.0M       $46.4M       $48.6M      Neutral
  ZEC              $49.8M       $37.9M       $11.9M    Very Bullish
  CL               $31.8M           $0       $31.8M    Very Bearish
  SP500            $27.3M       $27.3M           $0    Very Bullish
  NEAR             $26.3M       $16.3M       $10.0M      Bullish
  SOL              $20.8M       $14.3M        $6.5M      Bullish
  WLD              $20.6M       $20.6M         $38K    Very Bullish
  LIT              $18.0M       $18.0M           $0    Very Bullish

Liquidation Risk by Asset (within 25% of liq price)

  Asset       Total Value      At Risk     Risk %
 ─────────────────────────────────────────────────
  CL               $31.8M       $31.8M     100.0%
  DRAM              $3.6M        $3.6M      99.9%
  SPCX              $1.9M        $1.6M      84.4%
  SOL              $20.8M       $12.4M      59.5%
  BTC             $109.8M       $35.8M      32.6%
  XRP              $17.1M        $4.2M      24.7%
  ETH              $95.0M       $15.6M      16.5%
  HYPE            $155.5M       $23.5M      15.1%
  ZEC              $49.8M        $1.9M       3.8%
  WLD              $20.6M        $665K       3.2%
  ...
```

## Install

Requires [cohort-pnl](../cohort-pnl) installed first.

```bash
pip install -e '../cohort-pnl'
pip install -e '.'
```

## Coverage gap

Only wallets that appear on the Hyperliquid leaderboard are included. Small or dormant wallets that have never ranked are not captured.

## v2 (in progress)

- **Position age**: `--ages` flag adds an Age column to the wallet table. Uses `userFills` API. Values with `>` prefix are floors (position older than the 2000-fill history window).
- **Cohort bias sparkline** (requires accumulated daily snapshots -- start accumulating with `--save`)
- **Cohort exposure time-series** (same -- start accumulating with `--save`)

### Giga-Rekt with --ages example

```
cohort-dashboard --tier giga-rekt --ages
╭─────────────────────── Summary ───────────────────────╮
│ Tier: Giga-Rekt                                       │
│ Wallets: 30                                           │
│ Open Value: $11.7M Long  $39.6M Short  ($51.3M total) │
│ In Profit: 8 (27%)  Underwater: 22 (73%)              │
╰───────────────────────────────────────────────────────╯
Data as of 2026-06-17 18:43 UTC

  Wallet              Open Value       Equity     Exposure       Sum UPNL    Closest Liq        Age
 ───────────────────────────────────────────────────────────────────────────────────────────────────
  0x5e3ebe...97f8          $9.2M        $369K        25.0x      $59K loss           1.4%        10h
  0x020ca6...5872          $8.9M        $355K        25.0x      $71K gain           2.0%        >1d
  0x4e2328...20c3          $6.5M        $457K        14.3x     $198K loss           1.9%        n/a
  0xc1a1a3...e3eb          $6.0M        $120K        49.9x      $28K loss           0.7%        30m
  0x92772b...376c          $4.5M         $96K        47.0x      $15K loss           1.1%        n/a
  0x12f147...807c          $2.9M         $74K        40.0x      $10K gain           1.5%     1d 17h
  0x91f564...df13          $2.6M         $66K        40.0x       $1K gain           0.8%         2h
  0x52e6c3...7725          $1.1M         $35K        31.8x       $9K loss           1.2%        n/a
  0xe31062...d444          $903K         $30K        30.3x      $253 loss           1.6%        n/a
  0x5581dc...293a          $813K         $26K        30.8x      $668 loss           1.6%        n/a
  0x6d91e4...a39b          $781K         $19K        41.6x       $4K loss           1.1%         3h
  0x196556...17f9          $757K         $15K        50.0x       $6K gain           1.6%        n/a
  0xda12da...3973          $750K         $16K        48.3x       $3K loss           0.8%        31m
  0x46560b...debd          $736K         $18K        40.0x       $3K loss           0.9%         6m
  0xa72dc2...1807          $601K         $26K        23.1x       $4K loss           1.8%        n/a
  0x87cabd...c10c          $581K         $17K        33.9x       $3K gain           1.8%        36m
  0x6d9532...ff14          $567K         $16K        36.1x       $2K gain           1.5%        22m
  0x1e2897...0e41          $514K         $26K        20.0x       $6K loss           1.5%        n/a
  0x0facac...7a0a          $453K         $12K        38.2x      $11K loss           1.6%        n/a
  0x9ca4d4...4fb9          $451K         $11K        40.0x      $535 loss           1.2%        12h
  0x760faa...74c9          $437K          $8K        53.7x       $3K loss           0.6%        28m
  0x5da043...8efa          $338K          $8K        40.0x       $1K loss           0.7%        20m
  0x991068...297d          $301K         $11K        27.2x       $1K gain           2.0%        n/a
  0xf1b671...26b3          $210K          $5K        40.0x       $3K loss           1.3%         8h
  0x2c82a5...111b          $157K          $6K        25.0x      $205 gain           1.1%        13h
  0xf68385...746c          $100K          $4K        24.7x       $1K loss           1.6%        n/a
  0xda3cf9...f159           $58K          $1K        40.0x      $293 loss           0.7%         8m
  0x07d431...2160            $6K         $244        23.1x       $36 loss           1.8%        n/a
  0x663c79...2a2f            $6K         $139        40.0x       $29 loss           0.8%        10m
  0xaea149...af38            $3K         $152        17.5x      $104 loss           0.7%        n/a

                            Top Open Perps
  Asset       Total Value         Long        Short        Bias
 ────────────────────────────────────────────────────────────────
  ETH              $18.3M        $8.9M        $9.4M      Neutral
  BTC              $16.0M        $699K       $15.3M    Very Bearish
  WDC               $6.5M           $0        $6.5M    Very Bearish
  SP500             $5.7M        $450K        $5.3M    Very Bearish
  XYZ100            $2.0M           $0        $2.0M    Very Bearish
  GOLD              $1.1M        $1.1M           $0    Very Bullish
  CL                $701K        $100K        $601K    Very Bearish
  AMZN              $514K        $514K           $0    Very Bullish
  JPY               $453K           $0        $453K    Very Bearish
  SMH                 $6K           $0          $6K    Very Bearish

Liquidation Risk by Asset (within 25% of liq price)
  Asset       Total Value      At Risk     Risk %
 ─────────────────────────────────────────────────
  WDC               $6.5M        $6.5M     100.0%
  SMH                 $6K          $6K     100.0%
  XYZ100            $2.0M        $2.0M     100.0%
  BTC              $16.0M       $16.0M     100.0%
  ETH              $18.3M       $18.3M     100.0%
  JPY               $453K        $453K     100.0%
  CL                $701K        $701K     100.0%
  SP500             $5.7M        $5.7M     100.0%
  MRVL                $3K          $3K     100.0%
  GOLD              $1.1M        $1.1M     100.0%
  AMZN              $514K        $514K     100.0%
```


### Snapshot schema

`--save` writes one row per (date, tier) to `cohort_tier_snapshots`:

| Column | Description |
|--------|-------------|
| `snapshot_date` | ISO date of the run |
| `tier` | Canonical tier name (e.g. "Giga-Rekt") |
| `wallet_count` | Unique wallets with at least one position in this tier |
| `open_value_long_usd` | Total notional of long positions |
| `open_value_short_usd` | Total notional of short positions |
| `long_bias_pct` | Long notional / total notional * 100 (cohort bias signal) |
| `avg_exposure` | Value-weighted mean leverage across all positions (null if all cross-margin) |
| `pct_in_profit` | % of wallets with net positive unrealized PNL |

Run `cohort-dashboard --tier giga-rekt --save` daily to build up history for the sparklines.
