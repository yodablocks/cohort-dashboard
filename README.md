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

## Install

Requires [cohort-pnl](../cohort-pnl) installed first.

```bash
pip install -e '../cohort-pnl'
pip install -e '.'
```

## Coverage gap

Only wallets that appear on the Hyperliquid leaderboard are included. Small or dormant wallets that have never ranked are not captured.

## v2 (not yet built)

- Position age (requires `userFills` history per wallet)
- Cohort bias time-series sparkline (requires accumulated daily snapshots)
- Cohort exposure time-series chart (same)
