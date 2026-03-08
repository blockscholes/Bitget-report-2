# 🔄 Handover Document — Bitget Report 2 Analysis

> **Last updated:** 2026-03-05  
> **Purpose:** Living document to maintain context across the chat session. Updated whenever the notebook changes or new tasks are completed.

---

## 1. Project Overview

This project produces a **Bitget × Block Scholes** research report examining cross-asset selloffs, 24/7 price discovery on Bitget's tokenised RWA (Real World Asset) products (XAUUSDT, XAGUSDT), and how they compare to traditional Bloomberg spot prices. The report skeleton lives in `report_skeleton.md`.

### Key files

| File | Role |
|---|---|
| `analysis.ipynb` | Main analysis notebook (21 cells) |
| `plotting_utils.py` | Reusable Plotly theme (`PlotTheme`), watermark, layout helpers |
| `report_skeleton.md` | Full report outline / brief |
| `pull_bitget_xau_xag_volume.py` | Script that pulls Bitget volume data via API |
| `keys.py` | API credentials (gitignored) |
| `requirements.txt` | Python deps |

### Key data files (`data/`)

| File | Contents |
|---|---|
| `bitget_XAUUSDT_rwa_perpetual_1m_index_px.csv` | Bitget XAUUSDT 1-min index price (24/7) |
| `bitget_XAGUSDT_rwa_perpetual_1m_index_px.csv` | Bitget XAGUSDT 1-min index price (24/7) |
| `gold silver.xlsx` | Bloomberg XAU + XAG spot (traditional hours) — **Iran airstrike weekend** |
| `bitget_XAUUSDT_maduro__perpetual_1m_20260102_20260106.csv` | Bitget XAUUSDT 1-min for **Maduro/Venezuela strike weekend** |
| `gold-maduro.xlsx` | Bloomberg XAU spot for Maduro event |
| `bitget_xau_xag_volume_raw_*.csv` | Raw 1-min USDT volume (XAU + XAG futures) around Iran airstrike |
| `bitget_xau_xag_volume_hourly_*.csv` | Hourly aggregation of above |
| `bitget_xau_xag_volume_summary_*.csv` | Summary stats of above |
| `bitget_xau_xag_volume_raw_20260103T060100Z.csv` | Raw 1-min USDT volume (BTC + XAU futures, BTC spot) around **Maduro event** |
| `bitget_xau_xag_volume_hourly_20260103T060100Z.csv` | Hourly aggregation of above |
| `bitget_xau_xag_volume_summary_20260103T060100Z.csv` | Summary stats of above |
| *(external)* `C:\Users\USER\DataGrabber\...\source_data_20260304_122714.json` | Block Scholes master JSON — contains **BTC hourly price** (`blockscholes.spot.BTC_USD.1h.index.px`) from Sep 2020 → Mar 2026, plus ETH spot, vol surfaces, etc. Also used in `bybit_may_volatility.ipynb`. |

---

## 2. Notebook Cell-by-Cell Summary

### Cell 1 — Environment check
- Prints `sys.executable` to confirm the correct Python interpreter.
- **Status:** ✅ Executed

### Cell 2 — Imports
- Imports: `pandas`, `plotly`, `numpy`, `math`, `nbformat`.
- Patches plotly's internal nbformat reference (workaround for install order).
- **Status:** ✅ Executed

### Cell 3 — Data loading & merge (Iran airstrike event)
- Loads **Bitget XAUUSDT** and **XAGUSDT** 1-min index prices, resamples to 5-min.
- Loads **Bloomberg XAU + XAG spot** from `gold silver.xlsx`, resamples to 5-min.
- Outer-joins Bitget and Bloomberg on datetime for both gold and silver.
- Sets analysis window: **Fri 27 Feb 18:00 → Mon 2 Mar 12:00 UTC** (Iran airstrike weekend).
- Creates legacy aliases (`bitget`, `bitget_5m`, `bbg_5m`, `merged`, `plot_df`) for backward compatibility.
- **Status:** ✅ Executed

### Cell 4 — Gold price discovery chart (Iran airstrike)
- Plotly line chart: **Bitget XAUUSDT (24/7)** vs **Bloomberg XAU Spot** over the weekend window.
- Annotation: Trump announces Iran airstrikes — Sat 28 Feb 07:30 UTC.
- Shaded rectangle for traditional market closure (Fri 22:00 → Sun 23:00 UTC).
- Uses `update_timeseries_layout()` + `add_watermark()` from `plotting_utils`.
- Colours: Bitget = `#00E5A0` (green), Bloomberg = `#FFD700` (gold).
- **Status:** ✅ Executed, produces interactive Plotly chart

### Cell 5 — Silver price discovery chart (Iran airstrike)
- Same structure as Cell 4 but for **XAGUSDT vs Bloomberg XAG Spot**.
- Colours: Bitget Silver = `""` (empty string — likely needs fixing), Bloomberg Silver = `white`.
- **Status:** ✅ Executed

### Cell 6 — Price discovery timeline stats (Iran airstrike, gold)
- Computes and prints key datapoints:
  - Bloomberg Friday close price & time
  - Bitget price at airstrike announcement (Sat 07:30 UTC)
  - Bitget weekend peak price & time
  - Bloomberg Sunday reopen price & time
  - Bitget price at the exact moment Bloomberg reopened
  - Bloomberg weekend gap, Bitget move, convergence gap at reopen
- **Status:** ✅ Executed

### Cell 7 — Data loading (Maduro/Venezuela strike event)
- Loads **Bitget XAUUSDT** 1-min from `bitget_XAUUSDT_maduro__perpetual_1m_20260102_20260106.csv`.
- Loads **Bloomberg XAU** from `gold-maduro.xlsx` (Sheet2).
- Merges, sets window: **Fri 02 Jan 18:00 → Tue 06 Jan 12:00 UTC**.
- **Status:** ✅ Executed

### Cell 8 — Gold price discovery chart (Maduro event)
- Plotly chart: Bitget XAUUSDT vs Bloomberg XAU Spot over the Maduro weekend.
- Annotation: "US Military Strike in Venezuela — Sat 03 Jan 07:30 UTC" (time may be approximate).
- Shaded rectangle: Fri 02 Jan 22:00 → Sun 04 Jan 23:00 UTC.
- Same colour scheme as Cell 4.
- **Status:** ✅ Executed

### Cell 9 — Load BTC hourly price
- Loads BTC spot price from Block Scholes JSON (`source_data_20260304_122714.json`).
- Filters to `blockscholes.spot.BTC_USD.1h.index.px`, renames to `BTC`, tz-localises to UTC.
- 47,880 rows, Sep 2020 → Mar 2026.
- **Status:** ✅ Executed

### Cell 10 — BTC vs XAU summary stats (both weekends)
- Extracts BTC and Bitget XAUUSDT (resampled to 1h) for both event windows.
- Normalises both to 100 at window start.
- Prints peak/low/range for each asset in each event.
- **Key finding:**
  - **Maduro:** BTC +4.55%, XAU +3.31% — both rallied.
  - **Iran:** BTC −3.77%, XAU +3.01% — divergent, gold only.
- **Status:** ✅ Executed

### Cell 11 — Maduro weekend chart: BTC vs XAUUSDT (normalised)
- Plotly chart with BTC (orange `#F7931A`) and Bitget XAUUSDT (green) indexed to 100.
- Venezuela strike annotation, shaded traditional-market closure.
- Shows BTC and gold co-moving upward post-event.
- **Status:** ✅ Executed

### Cell 12 — Iran weekend chart: BTC vs XAUUSDT (normalised)
- Same structure as Cell 11 but for the Iran airstrike weekend.
- Shows BTC selling off while gold rallies — clear divergence.
- **Status:** ✅ Executed

### Cell 13 — Side-by-side comparison & 24h post-event stats
- Measures BTC and XAU from announcement time, 24h forward.
- Prints narrative interpretation of the two regimes.
- **Status:** ✅ Executed

### Cell 14 — Full-window comparison table & key takeaways
- Tabular comparison of indexed peak/low/range for both events.
- Prints three key takeaways:
  1. Maduro: BTC acted as geopolitical safe-haven alongside gold
  2. Iran: traders went direct to tokenised gold, no BTC bid
  3. Implication: liquid 24/7 gold perps removed the need for BTC proxy hedging
- **Status:** ✅ Executed

### Cell 15 — Volume data loading
- Loads raw, hourly, and summary volume CSVs produced by `pull_bitget_xau_xag_volume.py`.
- Displays `summary_vol_df`.
- **Status:** ❌ Not executed (has stale output from a previous session)

### Cell 16 — Hourly volume preview  *(renumbered)*

### Cell 16 — Hourly volume preview
- Displays `hourly_vol_df` DataFrame.
- **Status:** ❌ Not executed (has stale output)

### Cell 17 — Volume chart (Iran airstrike weekend)
- Filters raw volume for XAUUSDT + XAGUSDT futures.
- Pivots to 1-min USDT volume by symbol.
- Plotly line chart of 1-min volume for both, with same airstrike annotation and shaded weekend region.
- Colours: XAU = gold, XAG = white.
- **Status:** ❌ Not executed (has stale output)

### Cell 18 — Volume data load (both events)
- Loads raw + summary CSVs for **both** Iran (`20260228T073000Z`) and Maduro (`20260103T060100Z`) events.
- Now includes **BTCUSDT** (spot + futures) alongside XAUUSDT and XAGUSDT.
- Prints full phase-by-phase volume breakdown for both events.
- **Status:** ✅ Executed

### Cell 19 — Iran weekend: BTC vs XAUUSDT hourly volume chart
- `make_subplots` with 2 rows: XAUUSDT futures hourly bar chart (top), BTCUSDT futures hourly bar chart (bottom).
- Shows massive XAUUSDT volume spike post-announcement vs flat/declining BTC volume.
- Airstrike annotation + shaded traditional-market closure on both subplots.
- **Status:** ✅ Executed

### Cell 20 — Maduro weekend: BTC vs XAUUSDT hourly volume chart
- Same layout as Cell 19 but for Maduro event window.
- Shows BTC futures volume holding steady while XAU volume is more muted.
- Note: XAGUSDT was not listed yet in January (no data).
- **Status:** ✅ Executed

### Cell 21 — Volume ratio comparison table
- Pivoted table showing event-vs-pre volume ratios for all venues/symbols across both events.
- **Key findings:**
  - Iran: XAUUSDT **3.67x** ↑↑↑ | BTCUSDT futures 0.81x ↓ | BTC spot **0.77x** ↓
  - Maduro: BTC spot **1.25x** ↑ | XAUUSDT 1.13x ↑ | BTCUSDT futures 0.88x ↓
- **Status:** ✅ Executed

---

## 3. Key Variables in Kernel

| Variable | Type | Description |
|---|---|---|
| `plot_df_xau` | DataFrame | 5-min merged Bitget + Bloomberg gold, Iran weekend window |
| `plot_df_xag` | DataFrame | 5-min merged Bitget + Bloomberg silver, Iran weekend window |
| `plot_df_xau_maduro` | DataFrame | 1-min merged Bitget + Bloomberg gold, Maduro weekend window |
| `fig` | Plotly Figure | Gold price discovery chart (Iran) |
| `fig_ag` | Plotly Figure | Silver price discovery chart (Iran) |
| `fig_maduro` | Plotly Figure | Gold price discovery chart (Maduro) |
| `announcement_time` | Timestamp | `2026-02-28 07:30 UTC` |
| `maduro_announcement_time` | Timestamp | `2026-01-03 06:01 UTC` |
| `bbg_fri_close` | float | Bloomberg gold close on Fri 27 Feb |
| `bitget_at_announce` | float | Bitget gold at airstrike announcement |
| `bitget_peak` / `bitget_peak_time` | float / Timestamp | Bitget weekend peak |
| `bbg_sun_open` | float | Bloomberg gold reopen on Sun 01 Mar |
| `btc` | DataFrame | Hourly BTC/USD spot price (Sep 2020 → Mar 2026) |
| `btc_maduro` / `btc_iran` | DataFrame | BTC filtered to each event window |
| `btc_maduro_norm` / `btc_iran_norm` | Series | BTC normalised to 100 at window start |
| `xau_maduro_norm` / `xau_iran_norm` | Series | XAUUSDT normalised to 100 at window start |
| `fig_maduro_btc` | Plotly Figure | Maduro weekend: BTC vs XAU normalised chart |
| `fig_iran_btc` | Plotly Figure | Iran weekend: BTC vs XAU normalised chart |
| `iran_raw` / `iran_summary` | DataFrame | Raw volume + summary for Iran event (BTC+XAU+XAG) |
| `maduro_raw` / `maduro_summary` | DataFrame | Raw volume + summary for Maduro event (BTC+XAU) |
| `iran_hourly` | DataFrame | Hourly pivoted USDT volume (BTCUSDT, XAUUSDT) — Iran |
| `maduro_hourly_vol` | DataFrame | Hourly pivoted USDT volume (BTCUSDT, XAUUSDT) — Maduro |
| `fig_iran_vol` | Plotly Figure | Iran weekend: BTC vs XAU volume subplots |
| `fig_maduro_vol` | Plotly Figure | Maduro weekend: BTC vs XAU volume subplots |

---

## 4. Styling & Conventions

- **Theme:** Dark background (`#101A2E`), white font, from `PlotTheme` dataclass in `plotting_utils.py`.
- **Watermark:** Block Scholes logo, 40% size, 50% opacity, centred.
- **Chart dimensions:** 1450 × 650 px.
- **Colour palette:**
  - Bitget green: `#00E5A0`
  - Bloomberg gold: `#FFD700`
  - Bloomberg silver: `white`
  - XAU volume: `gold`
  - BTC orange: `#F7931A`
  - XAG volume: `white`
- **Time format on x-axis:** `%a %d %b\n%H:%M UTC`, 6-hour tick interval.

---

## 5. Known Issues / Notes

1. **Cell 5 (Silver chart):** `BITGET_SILVER_COLOR` is set to an empty string `""` — may default to Plotly's auto-colour. Might need an explicit colour.
2. **Cells 10–12** have stale outputs from a previous kernel session but have not been re-executed in the current session.
3. The `bbg` variable gets **overwritten** in Cell 7 (Maduro load) — it changes from the multi-column gold+silver Bloomberg DataFrame to the Maduro-specific one. Cells relying on the original `bbg` should be run before Cell 7, or the variable should be renamed.

---

## 6. Task Log

| # | Date | Task | Status |
|---|---|---|---|
| 1 | 2026-03-05 | Created handover document from existing notebook state | ✅ Done |
| 2 | 2026-03-05 | BTC vs XAUUSDT comparison: loaded BTC from Block Scholes JSON, built normalised charts for both weekends, computed stats. **Finding:** Maduro → BTC+gold co-rally; Iran → gold only, BTC sold off. Supports hypothesis that tokenised gold perps displaced BTC as weekend geopolitical hedge. | ✅ Done |
| 3 | 2026-03-05 | Pulled BTCUSDT volume (spot + futures) from Bitget API for both events. Built hourly volume bar charts (2-row subplots: XAU top, BTC bottom) for Iran and Maduro weekends. Created volume ratio comparison table. **Finding:** Iran → XAU vol 3.67x spike, BTC vol dropped (0.77–0.81x). Maduro → BTC spot vol spiked 1.25x, XAU modest 1.13x. Confirms traders shifted from BTC-as-hedge to direct gold perp. | ✅ Done |

---

*This document will be updated as work progresses.*
