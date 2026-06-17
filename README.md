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
- **--ages rate limiting**: fills are fetched one wallet at a time with 300ms between each to stay within `userFills` rate limits. On 429, retries after 3s then 5s before giving up. On tiers with 100+ wallets a note is printed about expected wait time (~1s per wallet). Some wallets may still show `n/a` if the API rejects all retries.

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
│ Wallets: 36                                           │
│ Open Value: $29.1M Long  $10.8M Short  ($39.9M total) │
│ In Profit: 5 (14%)  Underwater: 31 (86%)              │
╰───────────────────────────────────────────────────────╯
Data as of 2026-06-17 20:00 UTC

  Wallet              Open Value       Equity     Exposure       Sum UPNL    Closest Liq        Age
 ───────────────────────────────────────────────────────────────────────────────────────────────────
  0xc1a1a3...e3eb          $8.2M        $132K        62.2x      $74K loss           0.4%        38m
  0x92772b...376c          $8.2M        $207K        39.5x       $7K gain           1.5%        n/a
  0x2fc319...3460          $5.4M         $93K        58.4x      $84K loss           0.5%         6h
  0x020ca6...5872          $5.0M        $201K        25.0x      $92K loss           0.6%       >11h
  0xf9140f...11c3          $3.4M        $336K        10.0x     $115K loss           1.8%        n/a
  0x130925...4a8e          $1.5M         $37K        40.0x       $3K loss           1.5%        n/a
  0xe81908...3d1c          $926K         $23K        40.0x      $20K loss           1.0%      1d 2h
  0x6d91e4...a39b          $816K         $19K        42.5x      $789 loss           1.1%         6m
  0xda12da...3973          $706K         $18K        40.1x      $207 gain           1.3%        18m
  0x46560b...debd          $633K         $16K        40.0x       $6K loss           1.6%        38m
  0xb86c32...7db9          $594K         $20K        30.1x      $447 loss           1.7%        n/a
  0x6bde78...87d3          $527K         $13K        40.0x       $2K gain           1.7%        27m
  0x1e2897...0e41          $510K         $26K        20.0x      $10K loss           0.8%        n/a
  0x0facac...7a0a          $454K         $11K        41.1x      $12K loss           1.4%        n/a
  0x21ed86...6995          $430K         $11K        40.0x       $7K loss           0.4%      8d 3h
  0x135d89...f7b9          $383K         $15K        25.0x      $13K loss           0.6%     >2d 9h
  0x5899e3...ab46          $323K          $8K        40.0x       $5K gain           1.5%         1h
  0x6d9532...ff14          $298K          $9K        32.0x       $2K gain           1.8%        39m
  0x5581dc...293a          $257K          $6K        40.0x       $7K loss           1.4%         1h
  ...

                            Top Open Perps
  Asset       Total Value         Long        Short        Bias
 ────────────────────────────────────────────────────────────────
  BTC              $18.9M       $16.7M        $2.2M    Very Bullish
  SP500             $9.7M        $1.5M        $8.2M    Very Bearish
  ETH               $5.4M        $5.4M         $28K    Very Bullish
  ZEC               $3.4M        $3.4M           $0    Very Bullish
  XYZ100            $713K        $713K           $0    Very Bullish
  AMZN              $510K        $510K           $0    Very Bullish
  JPY               $454K           $0        $454K    Very Bearish
  SMH               $286K        $286K           $0    Very Bullish
  DRAM              $197K        $197K           $0    Very Bullish
  CRCL              $180K        $180K           $0    Very Bullish
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
